"""Smoke-test endpoint LLM (ai-box.vn) — verify trước khi chốt stack advisor.

Kiểm: (1) chat cơ bản deepseek-v4-flash; (2) JSON mode pass-through; (3) usage fields
(cache hit?); (4) fallback gpt-4o-mini; (5) latency.

Chạy:  uv run python scripts/smoke_llm_endpoint.py
Đọc .env ở repo root (không commit). KHÔNG in key ra console.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        raise SystemExit(".env không tồn tại — copy từ .env.example và điền key")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def main():
    load_env()
    from openai import OpenAI

    base_url = os.environ["OPENAI_BASE_URL"]
    key = os.environ["OPENAI_API_KEY"]
    primary = os.environ.get("DEFAULT_MODEL", "deepseek-v4-flash")
    fallback = os.environ.get("FALLBACK_MODEL", "gpt-4o-mini")

    client = OpenAI(base_url=base_url, api_key=key, max_retries=1, timeout=45.0)
    print(f"endpoint: {base_url}")

    results = {}

    # 1) chat cơ bản + latency
    for model in (primary, fallback):
        t0 = time.perf_counter()
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Trả lời đúng 1 từ: 'ok'"}],
                max_tokens=500,  # thinking mode ăn reasoning tokens trước khi ra content
            )
            dt = time.perf_counter() - t0
            content = (r.choices[0].message.content or "").strip()
            results[f"chat_{model}"] = {"ok": True, "latency_s": round(dt, 2), "reply": content[:40],
                                        "usage": r.usage.model_dump() if r.usage else None}
        except Exception as e:
            results[f"chat_{model}"] = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}

    # 2) JSON mode
    try:
        t0 = time.perf_counter()
        r = client.chat.completions.create(
            model=primary,
            messages=[{
                "role": "user",
                "content": ('Trả về json đúng schema {"action": string, "confidence": number 0-1}. '
                            'Ví dụ: {"action": "rest", "confidence": 0.8}. '
                            "Tình huống: tài xế đã chạy 6 tiếng, SOC 18%. Chọn action."),
            }],
            response_format={"type": "json_object"},
            max_tokens=800,  # đủ chỗ cho reasoning tokens + JSON output
        )
        dt = time.perf_counter() - t0
        content = r.choices[0].message.content or ""
        parsed = json.loads(content)
        results["json_mode"] = {"ok": True, "latency_s": round(dt, 2), "parsed": parsed,
                                "valid_schema": isinstance(parsed.get("action"), str)}
    except Exception as e:
        results["json_mode"] = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}

    # 3) cache field check (gọi 2 lần cùng prompt dài để xem prompt_cache_hit)
    try:
        long_sys = "Bạn là advisor cho tài xế xe điện. " * 50
        usages = []
        for _ in range(2):
            r = client.chat.completions.create(
                model=primary,
                messages=[{"role": "system", "content": long_sys},
                          {"role": "user", "content": "Nói 'ok'"}],
                max_tokens=5,
            )
            usages.append(r.usage.model_dump() if r.usage else {})
        results["cache_fields"] = {"ok": True, "call1_usage": usages[0], "call2_usage": usages[1]}
    except Exception as e:
        results["cache_fields"] = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}

    print(json.dumps(results, ensure_ascii=False, indent=2))

    verdicts = {
        "primary_chat": results.get(f"chat_{primary}", {}).get("ok", False),
        "fallback_chat": results.get(f"chat_{fallback}", {}).get("ok", False),
        "json_mode": results.get("json_mode", {}).get("ok", False),
    }
    print("\nVERDICT:", json.dumps(verdicts))


if __name__ == "__main__":
    main()
