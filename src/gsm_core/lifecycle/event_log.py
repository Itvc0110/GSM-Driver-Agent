"""AdviceEventLog — SQLite event log APPEND-ONLY cho vòng đời advice (ĐA-05, Cycle W).

Nguồn sự thật canonical: mọi trạng thái đọc qua projections (rebuild được từ events).
KHÔNG có UPDATE/DELETE ở bất kỳ đường code nào — sửa sai = append event mới
(`superseded`), không đụng lịch sử.

Quyết định đã duyệt (audit `04-*` §6 + verdict Cường PENDING-REVIEW ĐA-05):

- idempotency theo `event_id` (INSERT OR IGNORE — bản ĐẦU thắng, không ghi đè);
- validate qua `SchemaRegistry` TRƯỚC khi ghi (registry đa phiên bản Cycle V ⇒ replay
  qua migration hoạt động từ ngày đầu);
- 1 writer tại một thời điểm: `busy_timeout` + bounded retry, đếm `sqlite_busy_count`;
- KHÔNG bật WAL (WAL-reset bug ≤3.51.2 — audit §6, nguồn sqlite.org/wal.html);
- `close()` + context manager — đóng LAYEROUT-16 (connection giữ file ⇒ PermissionError
  khi cleanup TemporaryDirectory trên Windows);
- sim KHÔNG ghi vào đây trong tick loop (events sim ở RAM + `run_id`, xem projections).
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

_COLUMNS = ("event_id", "decision_id", "display_id", "driver_id", "run_id",
            "event_type", "reason_code", "occurred_at", "observed_at",
            "actor", "origin", "source", "context_revision", "schema_version",
            "payload")

_BUSY_RETRIES = 5
_BUSY_TIMEOUT_MS = 2000


def _registry():
    from gsm_core.schema_registry import SchemaRegistry
    return SchemaRegistry(Path(__file__).resolve().parents[3] / "schemas")


def _normalize(v):
    """Chuẩn hoá giá trị payload về kiểu Python thuần, GIỮ NGUYÊN GIÁ TRỊ.

    Sim detail mang numpy scalar (`np.float64` từ acceptance/lift của bridge) — `json.dumps`
    thô nổ `TypeError: Object of type int64 is not JSON serializable` ở đúng đường export
    sim→store. Reproduce được trong review đối kháng Cycle W.

    KHÔNG dùng `default=str`: str hoá làm hỏng số im lặng (1.5 thành "1.5" — consumer đọc
    ra chuỗi, phép so sánh/tổng sai mà không ai biết). Kiểu lạ thật sự thì để `json.dumps`
    nổ tường minh — đúng nguyên tắc normalize-hoặc-fail-loud ở boundary dữ liệu ngoài.
    """
    item = getattr(v, "item", None)          # numpy scalar → int/float/bool Python
    if item is not None and type(v).__module__ != "builtins":
        return item()
    if isinstance(v, dict):
        return {k: _normalize(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_normalize(x) for x in v]
    return v


class AdviceEventLog:
    """Append-only. API cố ý KHÔNG có update/delete — test canh bằng hasattr."""

    def __init__(self, db_path: str | Path):
        self.db = sqlite3.connect(str(db_path))
        self.db.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS advice_events (
            event_id TEXT PRIMARY KEY,
            decision_id TEXT NOT NULL, display_id TEXT, driver_id TEXT NOT NULL,
            run_id TEXT, event_type TEXT NOT NULL, reason_code TEXT,
            occurred_at TEXT NOT NULL, observed_at TEXT NOT NULL,
            actor TEXT NOT NULL, origin TEXT NOT NULL, source TEXT NOT NULL,
            context_revision TEXT, schema_version TEXT NOT NULL,
            payload TEXT NOT NULL
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS ix_ae_decision"
                        " ON advice_events(decision_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS ix_ae_run ON advice_events(run_id)")
        self.db.commit()
        self._registry = _registry()
        self.sqlite_busy_count = 0

    # -- lifecycle của chính store (LAYEROUT-16) --

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "AdviceEventLog":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- ghi --

    def append(self, event: dict) -> bool:
        """Ghi event; trả False nếu `event_id` đã tồn tại (idempotent, bản đầu thắng).

        Event hỏng schema ⇒ ValueError TRƯỚC khi chạm DB — log không bao giờ chứa
        record không validate được (điều kiện để replay qua upcaster tin được).
        """
        errs = self._registry.validate("advice_lifecycle_event", event)
        if errs:
            raise ValueError(f"advice_lifecycle_event không hợp lệ: {errs}")
        payload = json.dumps(_normalize(event["payload"]), ensure_ascii=False)
        row = tuple(payload if c == "payload" else event.get(c) for c in _COLUMNS)
        for attempt in range(_BUSY_RETRIES):
            try:
                cur = self.db.execute(
                    f"INSERT OR IGNORE INTO advice_events ({','.join(_COLUMNS)})"
                    f" VALUES ({','.join('?' * len(_COLUMNS))})", row)
                self.db.commit()
                return cur.rowcount == 1
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc) and "busy" not in str(exc):
                    raise
                self.sqlite_busy_count += 1
                if attempt == _BUSY_RETRIES - 1:
                    raise
                time.sleep(0.05 * (attempt + 1))
        raise AssertionError("unreachable")

    # -- đọc (nguyên liệu cho projections — không diễn giải gì ở đây) --

    def events(self, decision_id: str | None = None,
               run_id: str | None = None) -> list[dict]:
        """Events (dict đúng hình dạng schema), lọc tuỳ chọn. Thứ tự không đảm bảo —
        projections tự sort theo (occurred_at, event_id)."""
        q, args = "SELECT * FROM advice_events", []
        conds = []
        if decision_id is not None:
            conds.append("decision_id = ?")
            args.append(decision_id)
        if run_id is not None:
            conds.append("run_id = ?")
            args.append(run_id)
        if conds:
            q += " WHERE " + " AND ".join(conds)
        cur = self.db.execute(q, args)
        cols = [d[0] for d in cur.description]
        out = []
        for r in cur.fetchall():
            d = dict(zip(cols, r))
            d["payload"] = json.loads(d["payload"])
            out.append(d)
        return out
