# UPDATE-120 — Routing 3-tier: OSRM → GraphHopper → đường thẳng trung thực (bỏ fake sine-curve)

> ⚠ Đánh số lại từ UPDATE-119 → **UPDATE-120** khi rebase 2026-08-03: `origin/main` đã dùng số 119
> cho một việc khác (`UPDATE-119-week2-report-mentor.md`, báo cáo Week 2 gửi mentor) trước khi
> nhánh này push. Không đổi nội dung, chỉ đổi số + tên file + mọi tham chiếu chéo (`V-23` trong
> `PENDING-REVIEW.md` cũng đổi thành `V-24` vì cùng lý do trùng số).

- **Ngày:** 2026-08-03
- **Người thực hiện:** Khánh (agent), theo yêu cầu Khánh trong hội thoại
- **Loại:** fix / ui
- **TODO / User story liên quan:** tiếp nối audit map lib sim vs UI (claim Khánh 2026-08-02 ở `ASSIGNMENTS.md`); liên quan `UI-FARE-01` (claim Cường, `WAITING-VERDICT`) — chỉ đụng cơ chế routing/fallback, không đụng fare logic.

## Tóm tắt

Audit cycle trước xác định root cause của "chỉ đường xuyên nhà/chim bay": khi cả 2 OSRM public
demo server chết, `routing.py` rơi về một đường cong sin GIẢ, gắn nhãn sai
`source: "hanoi_street_graph_engine"`. Cycle này thêm **GraphHopper làm tier-2** (Khánh đã có API
key thật, free tier) và sửa tier-3 thành **ước lượng đường thẳng trung thực** — không còn fake
curve nào trong hệ thống.

## Chi tiết cập nhật

- 3 tier rõ ràng trong `routing.py`: `try_osrm()` (giữ nguyên hành vi 2 mirror cũ) →
  `try_graphhopper()` (MỚI — đọc `GRAPHHOPPER_API_KEY`, thiếu key thì skip êm) →
  `straight_line_fallback()` (sửa — bỏ hẳn `sin`/`cos` giả, chỉ còn lerp tuyến tính).
- Field mới **bắt buộc** `route_is_real_road: bool` trên `RouteCalculateResponse` — tier 1/2 = `True`,
  tier 3 = `False`. Frontend (`app.js`) đọc field này để: (a) polyline liền nét cyan (thật) vs nét đứt
  amber (ước lượng), (b) `nav-state` hiện đúng "CHỈ ĐƯỜNG THỰC" vs "ƯỚC LƯỢNG THẲNG" thay vì hardcode
  "(OSRM)" bất kể nguồn thật.
- Tái dùng `load_env()` có sẵn từ `gsm_core.advisor.llm_client` (không thêm dependency
  `python-dotenv`). Đổi tên biến `.env` `apikey_graphhopper` → `GRAPHHOPPER_API_KEY` khớp convention
  `SCREAMING_SNAKE_CASE`; thêm placeholder vào `.env.example`.
- Đơn vị đã verify khác nhau giữa 2 provider: OSRM `duration` = giây, GraphHopper `time` = **mili-giây**
  — convert đúng (`/60000.0` ra phút). Toạ độ: OSRM `lng,lat`, GraphHopper input `point=lat,lon` nhưng
  output geometry cũng GeoJSON `[lon,lat]` — cả 2 cùng cần swap sang `[lat,lng]` cho Leaflet.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `ui/backend/app/routers/routing.py` | sửa | 3-tier + `build_route_response()` dùng chung, thay `generate_street_snapped_segment` → `interpolate_straight_line_segment` |
| `ui/backend/app/models.py` | sửa | thêm `route_is_real_road: bool` (bắt buộc, không default) |
| `ui/web/js/app.js` | sửa | polyline dash/color + nav-state theo `route_is_real_road` |
| `ui/backend/tests/test_routing_api.py` | sửa | test fallback cũ thêm `delenv GRAPHHOPPER_API_KEY` + assertion mới; thêm `test_graphhopper_tier_used_when_osrm_fails` |
| `.env` | sửa | đổi tên biến (local, gitignored, không track) |
| `.env.example` | sửa | thêm placeholder `GRAPHHOPPER_API_KEY=` + block comment giải thích rõ 3 tier + note đổi tên từ `apikey_graphhopper` |
| `tracking/ASSIGNMENTS.md` | sửa | claim Khánh cập nhật DONE-CODE |
| `tracking/PENDING-REVIEW.md` | sửa | thêm `V-23` chờ Cường xem visual |

## Docs đã cập nhật kèm theo

SCOPE/TODO/DEFERRED/USER_STORIES: không đổi (đây là bugfix trong scope hiện hành, không mở rộng
scope). `D-LOCAL-01` (production infra) **không** bị ảnh hưởng — GraphHopper là SaaS free-tier
key-based, không phải hạ tầng tự host, nên không đụng quyết định đó.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| GraphHopper key hoạt động, endpoint/param đúng như tài liệu Khánh dán | `OBSERVED-CODE` (live test) | `curl` thật tới `graphhopper.com/api/1/route`, HTTP 200, đã xem cả `distance/time/points` và `instructions[].text` | Cao | Nếu key hết hạn/hết quota, tier 2 tự skip êm (không crash), rơi tier 3 |
| Free tier 500 credit/ngày đủ cho pilot demo | `ASSUMPTION` (từ tài liệu Khánh dán, có trích dẫn nhưng chưa tự verify số credit thật đã dùng) | Guide Khánh cung cấp (graphhopper.com/pricing, support article) | Trung bình | Nếu quota cạn nhanh hơn dự kiến, tier 2 sẽ lỗi HTTP → rơi tier 3 (không silent fail sai, vẫn an toàn) |
| OSRM self-host (Docker) khả thi, nhẹ | `OBSERVED-CODE` (benchmark thật cycle trước) | Đo RAM/CPU thật trên máy này (xem hội thoại) | Cao | Không ảnh hưởng cycle này — self-host vẫn `D-LOCAL-01`, chưa triển khai |

## Kiểm chứng

- `.venv/bin/python -m pytest -q ui/backend/tests` → **66 passed** (gồm 1 test mới
  `test_graphhopper_tier_used_when_osrm_fails`, không network thật trong test — monkeypatch theo
  `request.full_url`).
- Live smoke test (ngoài suite tự động): `curl` thật tới GraphHopper với `instructions=true` — xác
  nhận `instructions[1].text` có nội dung thật ("Rẽ trái vào Phố Hồ Đắc Di"), khớp code parse.
- `.venv/bin/python -m pytest -q` (suite chính `tests/`) → **935 passed, 4 skipped** (1102s) — khớp
  baseline đã ghi ở `BOOTSTRAP-SESSION.md` (935 + 65 UI, nay 66 UI vì thêm 1 test). Cycle này không
  đụng `src/gsm_sim`/`src/gsm_core` nên kết quả này xác nhận KHÔNG có hồi quy, không phải kiểm chứng
  trực tiếp thay đổi. **Cả hai lệnh nay đã xanh** — đủ điều kiện gọi "suite xanh" theo CLAUDE.md §2.

### Seeds và scenarios

Không áp dụng (đây là đường sản phẩm deterministic, không có seed/scenario ngẫu nhiên).

## Visual verification

- **Status:** `WAIVED` — Khánh xác nhận trực tiếp trong hội thoại 2026-08-03 waive gate (đồng sở
  hữu dự án, quyết định push ngay). Cường **chưa xem** — `V-23` ở `PENDING-REVIEW.md` vẫn còn hiệu
  lực để Cường xem SAU khi push (hoãn ≠ waive nội dung, chỉ waive điều kiện chặn push).
- **Cách launch:** `.venv/bin/python -m uvicorn app.main:app --app-dir ui/backend --port 8000`, mở
  `http://localhost:8000/app/`, bấm CTA nhận cuốc → xem polyline + `nav-state`.
- **Bằng chứng đã thu thập:** Playwright headless Chromium (cài tạm ở scratchpad, không vào repo),
  screenshot thật cho cả 3 tier:
  - Tier 1 (OSRM thật, trạng thái mặc định): polyline liền nét cyan bám đường thật, `nav-state` =
    "ĐANG ĐẾN ĐIỂM ĐÓN (CHỈ ĐƯỜNG THỰC)".
  - Tier 2 (GraphHopper — OSRM bị ép lỗi tạm thời để test, đã revert ngay sau): polyline vẫn liền
    nét cyan (route thật, khác hình dạng OSRM — 8,2km vs 7,4km), `nav-state` vẫn "CHỈ ĐƯỜNG THỰC".
  - Tier 3 (cả 2 provider bị ép lỗi tạm thời): polyline nét đứt AMBER thẳng từ A→B, `nav-state` =
    "ĐANG ĐẾN ĐIỂM ĐÓN (ƯỚC LƯỢNG THẲNG)" — không còn hình dạng giả nào đánh lừa là đường thật.
  - `console --errors` tương đương (kiểm tra qua Playwright `pageerror`/`console` listener): **0 lỗi**
    ở cả 3 lần chạy.
- **Người review + verdict:** chưa — Khánh mới tự xem, Cường chưa xem.

## Adversarial self-review / flaws found

1. **Key GraphHopper có thể lọt vào log?** Đã kiểm: nhánh lỗi network chỉ `print(type(e).__name__)`,
   không in `url`/`e.url`. Nhánh OSRM (không đổi) vẫn in `str(e)` như cũ — OSRM URL không chứa secret
   nên an toàn, nhưng đây là bất đối xứng cố ý (đã giải thích trong plan), không phải sai sót.
2. **`route_is_real_road` không có default** — cố ý (fail loud): nếu một tier nào quên set, Pydantic
   validation lỗi ngay thay vì âm thầm thiếu field. Đã verify cả 3 tier đều đi qua
   `build_route_response()` dùng chung nên không thể quên.
3. **Đơn vị `time` (ms) của GraphHopper dễ nhầm với `duration` (s) của OSRM** — đã bắt bằng test
   `test_graphhopper_tier_used_when_osrm_fails` pin đúng số (212.203ms → 4 phút, không phải 3.537 phút
   nếu lỡ coi là giây).
4. **Test cũ `test_fallback_route_uses_same_base_fare` có thể pass giả** nếu máy chạy test có
   `GRAPHHOPPER_API_KEY` export sẵn trong shell (vì `load_env` dùng `setdefault`, không override biến
   đã set) — đã sửa bằng `monkeypatch.delenv(..., raising=False)` tường minh, không dựa vào network
   fail để suy luận tier nào bị bỏ qua.
5. **Weakest evidence:** GraphHopper free-tier quota/ToS (500 credit/ngày, giới hạn dev-only) đến từ
   tài liệu Khánh dán (có trích dẫn), agent chưa tự xác minh số credit còn lại thật sự qua dashboard
   tài khoản — nếu sai, hệ quả chỉ là tier 2 sớm rơi xuống tier 3 (an toàn, không sai số hiển thị).
6. **So baseline nào:** so trực tiếp response tier 1 vs tier 2 cho CÙNG cặp toạ độ Đống Đa (Ô Chợ
   Dừa→Ngã Tư Sở) — hai route thật khác nhau về khoảng cách (~18% lệch, do provider khác chọn đường
   khác) nhưng cả hai đều là polyline bám đường thật, không phải điều cần lo (đã giải thích trong hội
   thoại: hai router độc lập có thể chọn path khác nhau khi có nhiều lựa chọn hợp lệ).
7. **Chưa mở:** không có flaw nào cần map vào TODO/DEFERRED mới từ chính thay đổi này. Việc dead-code
   `hanoi_graph.py` (chưa xoá, đã ghi nhận cycle trước) và sim-replay straight-line (MODEL GAP, thuộc
   claim SIM) vẫn đứng riêng, không phải phát sinh từ cycle này.

## Expansion checkpoint

Không tự triển khai — chỉ ghi đề xuất:
1. **Schema**: không cần đổi (RouteCalculateResponse chỉ có 1 field mới, không ảnh hưởng entity khác).
2. **Bài toán tối ưu**: không có residual mới.
3. **Tính năng**: nếu muốn UI hiển thị "provider đang dùng" rõ hơn (không chỉ dashArray), có thể thêm
   badge nhỏ đọc `source` — Cường quyết định nếu muốn.

## Follow-up / defer phát sinh

- Không phát sinh mục DEFERRED mới. Hai mục đã ghi ở cycle trước (dead-code `hanoi_graph.py`, sim
  replay straight-line) vẫn giữ nguyên trạng thái, chưa quyết định thêm.
- Đã push lên `origin/main` — Khánh waive gate trực tiếp trong hội thoại 2026-08-03. `V-23`
  (PENDING-REVIEW.md) vẫn còn hiệu lực, Cường xem SAU khi code đã lên main.
