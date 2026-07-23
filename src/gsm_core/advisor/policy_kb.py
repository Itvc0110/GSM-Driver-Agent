"""F0 policy KB từ corpus T-004 (UTF-8, 7 records first-party).

Guardrail T-004 (BẤT BIẾN): filter CỨNG theo f0_tracks; record generic
(f0_tracks=[]) KHÔNG BAO GIỜ auto-match track cụ thể. Thiếu track → need_track
(R1 clarify — không trả số/eligibility khi chưa biết track). 7 records →
keyword match đủ, không cần vector.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from gsm_core.advisor._text import normalize_vi as _norm

VALID_TRACKS = {"core_owned", "platform", "rto"}
EXCERPT_CHARS = 400


class PolicyKB:
    def __init__(self, corpus_path: str | Path):
        data = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
        self.records: list[dict] = data["records"]
        self.corpus_id = data.get("corpus_id", "t004")
        self.snapshot_date = data.get("snapshot_date")

    @property
    def n_records(self) -> int:
        return len(self.records)

    def retrieve(self, track: str | None, query_text: str, top_k: int = 3):
        """Trả list excerpt (đã filter track) hoặc 'need_track' nếu thiếu track."""
        if track not in VALID_TRACKS:
            return "need_track"
        # filter CỨNG: chỉ record có track trong f0_tracks (generic [] tự loại)
        pool = [r for r in self.records if track in r.get("f0_tracks", [])]
        q = _norm(query_text or "")
        q_words = [w for w in re.split(r"\W+", q) if len(w) >= 3]
        scored = []
        for r in pool:
            hay = _norm(" ".join([r.get("title", ""),
                                   " ".join(r.get("policy_families", [])),
                                   r.get("main_text", "")]))
            score = sum(hay.count(w) for w in q_words) if q_words else 1
            if score > 0:
                scored.append((score, r))
        scored.sort(key=lambda x: (-x[0], x[1]["source_id"]))
        out = []
        for score, r in scored[:top_k]:
            text = r.get("main_text", "")
            # excerpt quanh keyword đầu tiên match
            pos = 0
            hay = _norm(text)
            for w in q_words:
                i = hay.find(w)
                if i >= 0:
                    pos = max(0, i - 100)
                    break
            out.append({
                "source_id": r["source_id"], "title": r["title"],
                "source_url": r["source_url"], "f0_tracks": r["f0_tracks"],
                "lifecycle": r.get("lifecycle"), "status": r.get("status"),
                "retrieved_at": r.get("retrieved_at"),
                "excerpt": text[pos:pos + EXCERPT_CHARS],
                "match_score": score,
            })
        return out
