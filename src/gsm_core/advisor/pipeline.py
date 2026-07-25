"""Pipeline orchestrator: AdviceRequest → Router → (solvers song song đã chạy ngoài,
nhận reports) → Context Pack → Composer (LLM/template) → Verifier → ComposedAdvice
+ episode. Loop bounds cứng: clarify ≤2 (F0 track), repair ≤1 (composer).

v1: solver_reports truyền vào từ caller (solver chạy song song ở feature layer);
pipeline lo phần advise. LLM_MODE=off → template fallback (đường bắt buộc).
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid

from gsm_core.advisor.policy_kb import PolicyKB
from gsm_core.advisor.router import route
from gsm_core.advisor.context_pack import build_context_pack, render_number_vn
from gsm_core.advisor.templates import render_template
from gsm_core.advisor.episode_store import EpisodeStore
from gsm_core.advisor import verifier as V


def _trusted_spans(solver_reports: list[dict]) -> list[str]:
    """Text do SOLVER (deterministic, verified) tạo ra mà template có thể nhúng
    nguyên văn — digest/heuristic_note/reason. Là DATA truy vết được (§5: số đến từ
    analytics component), không phải claim tự do → verifier bỏ qua khi soi số trần."""
    spans: list[str] = []
    for rep in solver_reports:
        if rep.get("problem_digest"):
            spans.append(rep["problem_digest"])
        sol = rep.get("solution") or {}
        tp = sol.get("top_pattern")
        if isinstance(tp, dict) and tp.get("heuristic_note"):
            spans.append(tp["heuristic_note"])
        na = sol.get("next_action")
        if isinstance(na, dict) and na.get("reason"):
            spans.append(na["reason"])
        # PI-5a: TÊN nhiệm vụ lấy nguyên văn từ `public_mission.name` (catalog nền tảng)
        # thường chứa số — vd "2 chuyến khung vàng". Cùng trust-class với tiêu đề policy
        # (BUG-C6-03): là DATA trích dẫn, không phải số agent bịa. Giá trị thưởng vẫn
        # BẮT BUỘC đến từ numbers_registry.
        for m in sol.get("chosen_missions") or []:
            if isinstance(m, dict) and m.get("name"):
                spans.append(str(m["name"]))
    return spans


class AdvisorPipeline:
    def __init__(self, corpus_path, store_path, llm_mode: str = "off",
                 composer=None, recorder=None):
        self.kb = PolicyKB(corpus_path)
        self.store = EpisodeStore(store_path)
        self.llm_mode = llm_mode
        self.composer = composer  # tranche B inject; None = template only
        self.recorder = recorder  # observability optional; None = no-op
        self.last_verify_result: dict = {}

    def handle(self, req: dict, solver_reports: list[dict],
               kb_track: str | None = None) -> dict:
        self._t0 = time.perf_counter()
        feature = req["feature"]
        r = route(feature, req.get("free_text_query"))

        # R5: ngoài phạm vi → từ chối lịch sự (template, không LLM)
        if r["intent"] == "out_of_taxonomy":
            return self._finish(req, r, {
                "message": ("Xin lỗi anh/chị, câu hỏi này nằm ngoài phạm vi tư vấn "
                            "thu nhập/chính sách của trợ lý. Anh/chị có thể hỏi về "
                            "thưởng, lịch chạy, hoặc tổng kết ca nhé."),
                "citations": [], "advice_spec": None,
                "caveats": [], "fallback_used": True,
            }, [], residual="R5")

        # F0: KB retrieve với track guardrail
        kb_excerpts: list[dict] = []
        if r.get("use_kb"):
            got = self.kb.retrieve(kb_track, req.get("free_text_query") or "")
            if got == "need_track":
                # R1 clarify: hỏi lại track — KHÔNG trả số khi chưa biết track
                out = {
                    "schema_version": "1.0.0", "advice_id": f"adv-{uuid.uuid4().hex[:10]}",
                    "request_id": req["request_id"],
                    "message": ("Để trả lời chính xác, anh/chị cho biết mình chạy theo "
                                "hình thức nào: xe công ty (core), xe cá nhân lên nền tảng "
                                "(platform), hay thuê-mua xe (RTO)?"),
                    "citations": [], "numbers": [], "confidence": 0.9,
                    "caveats": ["cần biết track trước khi trả lời chính sách"],
                    "advice_spec": None, "fallback_used": True,
                    "residual_path": "R1", "clarify_needed": True,
                }
                # clarify không ghi episode advice (chưa phải advice)
                self.last_verify_result = {"passed": True, "errors": []}
                return out
            kb_excerpts = got

        pack = build_context_pack(feature, solver_reports, kb_excerpts,
                                  driver_id=req["driver_id"])

        # Composer: LLM (tranche B) hoặc template
        rendered = [render_number_vn(n["value"], n["unit"])
                    for n in pack["numbers_registry"].values()]
        if self.llm_mode == "live" and self.composer is not None:
            composed = self.composer.compose(pack, feature)
            # composer đã bỏ cuộc (LLM chết/repair fail) → luôn hạ template,
            # KHÔNG tin message rỗng "lọt" verify (empty pass V1/V2/V3 nhưng vi phạm schema)
            llm_gave_up = bool(composed.get("fallback_used"))
        else:
            composed = render_template(feature, solver_reports, kb_excerpts,
                                       pack["numbers_registry"])
            llm_gave_up = False  # template CHÍNH là fallback rồi

        # Verifier tầng 1 (CODE, quyền veto)
        cited_titles = [e["title"] for e in kb_excerpts] + _trusted_spans(solver_reports)
        vres = V.verify(composed["message"], composed.get("advice_spec"),
                        composed.get("citations", []), feature,
                        used_kb=bool(kb_excerpts), rendered_numbers=rendered,
                        cited_texts=cited_titles)
        self.last_verify_result = vres
        if llm_gave_up or not vres["passed"]:
            # veto/bỏ cuộc → template fallback (fail-closed; template pass by construction)
            composed = render_template(feature, solver_reports, kb_excerpts,
                                       pack["numbers_registry"])
            vres2 = V.verify(composed["message"], composed.get("advice_spec"),
                             composed.get("citations", []), feature,
                             used_kb=bool(kb_excerpts), rendered_numbers=rendered,
                             cited_texts=cited_titles)
            self.last_verify_result = vres2

        return self._finish(req, r, composed,
                            list(pack["numbers_registry"].values()),
                            residual=composed.get("residual_path"),
                            solver_reports=solver_reports)

    def _finish(self, req, r, composed, numbers, residual=None,
                solver_reports=None) -> dict:
        advice = {
            "schema_version": "1.0.0",
            "advice_id": f"adv-{uuid.uuid4().hex[:10]}",
            "request_id": req["request_id"],
            "message": composed["message"],
            "citations": composed.get("citations", []),
            "numbers": [{"value": n["value"], "unit": n["unit"], "source": n["source"]}
                        for n in numbers],
            "confidence": composed.get("confidence", 0.7),
            "caveats": composed.get("caveats", []),
            "advice_spec": composed.get("advice_spec"),
            "fallback_used": bool(composed.get("fallback_used")),
            "residual_path": residual,
        }
        state_digest = hashlib.sha256(
            json.dumps([req["driver_id"], req["feature"],
                        [n["value"] for n in numbers]], default=str).encode()
        ).hexdigest()[:16]
        self.store.append_episode({
            "episode_id": advice["advice_id"], "driver_id": req["driver_id"],
            "feature": req["feature"], "state_digest": state_digest,
            "solver_report_refs": [],
            "advice_spec": advice["advice_spec"], "message": advice["message"],
            "confidence": advice["confidence"], "route": r["intent"],
            "fallback_used": advice["fallback_used"],
            "residual_path": residual,
        })
        if self.recorder is not None:
            latency_ms = (time.perf_counter() - getattr(self, "_t0", time.perf_counter())) * 1000
            self.recorder.record(
                request_id=req["request_id"], driver_id=req["driver_id"],
                feature=req["feature"], route=r,
                solver_reports=solver_reports or [], advice=advice,
                verify_result=self.last_verify_result or {"passed": True, "errors": []},
                latency_ms=latency_ms)
        return advice
