"""Episode store — SQLite append-only (kiêm DecisionRecord audit trail) + exact-key cache.

Research đợt 7: TUYỆT ĐỐI KHÔNG semantic cache (false-positive vs faithfulness).
Key = hash(driver + state_digest + policy_v + solver_v + prompt_v + model). TTL 6h.
Schema log bandit-compatible (context, action, propensity, reward nullable) cho v2.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

CACHE_TTL_S = 6 * 3600


def _key(driver_id, state_digest, policy_version, solver_version,
         prompt_version, model_id) -> str:
    raw = "|".join([driver_id, state_digest, policy_version, solver_version,
                     prompt_version, model_id])
    return hashlib.sha256(raw.encode()).hexdigest()


class EpisodeStore:
    def __init__(self, db_path: str | Path):
        self.db = sqlite3.connect(str(db_path))
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS episodes (
            episode_id TEXT PRIMARY KEY, driver_id TEXT, ts REAL, feature TEXT,
            state_digest TEXT, solver_report_refs TEXT, advice_spec TEXT,
            message TEXT, confidence REAL, route TEXT, fallback_used INTEGER,
            residual_path TEXT,
            -- bandit-compatible (v2 đọc lại log): propensity=1.0, reward nullable
            propensity REAL DEFAULT 1.0, shown INTEGER, accepted INTEGER, reward REAL
        );
        CREATE TABLE IF NOT EXISTS advice_cache (
            key TEXT PRIMARY KEY, advice_json TEXT, created_at REAL
        );
        """)

    def append_episode(self, ep: dict) -> None:
        self.db.execute(
            "INSERT INTO episodes (episode_id, driver_id, ts, feature, state_digest,"
            " solver_report_refs, advice_spec, message, confidence, route,"
            " fallback_used, residual_path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (ep["episode_id"], ep["driver_id"], ep.get("ts", time.time()),
             ep.get("feature"), ep.get("state_digest"),
             json.dumps(ep.get("solver_report_refs", []), ensure_ascii=False),
             json.dumps(ep.get("advice_spec"), ensure_ascii=False),
             ep.get("message"), ep.get("confidence"), ep.get("route"),
             1 if ep.get("fallback_used") else 0, ep.get("residual_path")))
        self.db.commit()

    def count_episodes(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

    def cache_get(self, **key_parts):
        k = _key(**key_parts)
        row = self.db.execute(
            "SELECT advice_json, created_at FROM advice_cache WHERE key=?", (k,)
        ).fetchone()
        if row is None or (time.time() - row[1]) > CACHE_TTL_S:
            return None
        return json.loads(row[0])

    def cache_put(self, advice: dict, **key_parts) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO advice_cache (key, advice_json, created_at)"
            " VALUES (?,?,?)",
            (_key(**key_parts), json.dumps(advice, ensure_ascii=False), time.time()))
        self.db.commit()
