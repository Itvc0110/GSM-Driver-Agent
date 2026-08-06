local HEAD  = merge PR #6 Khánh + E-program UPDATE-151..158 (đã commit + push 2026-08-06)
suite       = 1356 passed / 4 skipped / **2 FAILED** (đo 2026-08-06 SAU merge PR #6)
              uv run pytest -q                  -> 1155 / 2 fail / 4 skip  (26-53′ tuỳ tải)
              uv run pytest -q ui/backend/tests -> 201 passed — 🎉 KHÔNG cần --ignore nữa
                 (K-02 được pythonpath=[".", "src"] của Khánh chữa — PR #6)
              2 F còn lại ĐỀU của Khánh: test_demo_trace_neutrality (import `app`) +
                 K-03 test_money_manifest (4 hàm demo_trace/World.log chưa phân loại).
              K-01 ×3 ĐÃ HẾT: (a) pythonpath fix; (b) test safety-vs-driving đổi theo B-03
                 CÓ NHÃN — còn chờ Cường ACK câu chữ (PENDING K-01)
