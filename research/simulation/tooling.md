# Research — Stack công cụ cho simulator twin-world + visualization

Ngày: 2026-07-21 · Nguồn: T-016 (research đợt 3) · Phục vụ: `specs/simulation-twin-world.md`

## Stack đề xuất (chốt cho v1)

| Hạng mục | Lựa chọn chính | Thay thế | Lý do |
| --- | --- | --- | --- |
| Engine | **SimPy 4** (discrete-event, MIT) + domain code tự viết trên H3 | Mesa 3 (ABM, có DataCollector/batch_run) | Mô phỏng mức kinh tế/điều phối trên lưới hex, không cần traffic-level; SimPy process = generator Python khớp lifecycle tài xế; API nhỏ, dễ seed/tái lập |
| Lưới | **h3-py v4** — res **8** chính (~0.737 km²/cell), res 7 tổng hợp vùng | res 9 khi cần heatmap mịn (số cell ×7) | API v4 snake_case: `latlng_to_cell`, `grid_disk`, `grid_distance`, `h3shape_to_cells` (code mẫu cũ trên mạng dùng tên v3 camelCase — đừng copy nhầm) |
| Storage/event log | **Parquet + DuckDB** (community extension `h3` — aggregate theo cell ngay trong SQL) | Polars cho pipeline dataframe | Mỗi run = folder `run_id/` chứa `manifest.json` (config+seed+git hash) + `events.parquet` + `metrics.parquet`; DuckDB query xuyên nhiều run, out-of-core |
| Dashboard | **Streamlit + Plotly** (nhúng map qua `st.pydeck_chart`) | Plotly Dash | Nhanh nhất cho team 2 người |
| Spatial replay | **kepler.gl** (widget Python `keplergl` → `save_to_html`; time playback + Trip layer + H3 layer) | pydeck `TripsLayer` + `H3HexagonLayer` với `current_time` | kepler.gl replay tốt nhất nhóm; xuất HTML tự chạy gửi cho nhau không cần server |
| Experiment tracking | **Tự log parquet + manifest + DuckDB/notebook** | MLflow local (file store, `mlflow ui`, free) | Sim sweep bản chất là data; W&B là SaaS → loại |

## Đánh giá engine chi tiết (snapshot GitHub 2026-07-21)

- **SimPy**: PyPI 4.1.x, MIT, maintained. Không có sẵn grid/data collection — tự viết (đơn giản với H3). **Chọn.**
- **Mesa**: 3.7k⭐, Apache-2.0, v3.5.1 (03/2026), rất active. Space built-in là grid vuông/network — H3 vẫn phải tự map; step-based kém tự nhiên cho đơn đến Poisson.
- **SUMO** (4.1k⭐)/**MATSim**/**CityFlow** (1.0k⭐, chậm lại từ 08/2025): traffic-microsim/RL đèn tín hiệu — **quá nặng, sai mức trừu tượng** cho bài toán thu nhập/policy.
- **FleetPy** (TUM-VT, 104⭐, MIT, v1.0.2 03/2026): fleet sim học thuật đầy đủ (pooling, dispatching, sạc EV) — learning curve cao, kéo Gurobi/OR-Tools; **đọc tham khảo kiến trúc** (tách operator/vehicle/request).
- **tomslee/ridehail** (~1.8k commits, MIT, active): đúng bài toán kinh tế ride-hailing nhất (utilization, wait, pricing, sweep, animation) nhưng grid vuông — **tham khảo kiến trúc số 1** (trạng thái tài xế P1/P2/P3, cách sweep).
- DRSP-Sim (ngưng 2023), aaivu (chết 2021): bỏ.

**Kết luận**: không có simulator dùng ngay cho twin-world + H3 + policy GSM; viết engine riêng vài trăm dòng trên SimPy, chạy 2 instance cùng seed + chung stream sinh đơn.

## Bảng H3 resolution

| Res | Edge (km) | Diện tích cell (km²) |
| --- | --- | --- |
| 6 | 3.72 | 36.13 |
| 7 | 1.41 | 5.16 |
| **8** | **0.53** | **0.737** |
| 9 | 0.20 | 0.105 |

Nội thành HN ~300 km² → ~400–420 cells ở res 8. deck.gl/pydeck có `H3HexagonLayer` native; kepler.gl có H3 layer nhận cột hex ID.

## .env / API keys

- **pydeck: KHÔNG cần key** — từ v0.6 basemap mặc định là Carto; chỉ set `MAPBOX_API_KEY` nếu muốn style Mapbox.
- **kepler.gl**: style Mapbox mặc định cần token (issue #3139 từng nhúng token vào HTML export); né bằng basemap **CARTO Positron/Dark Matter hoặc OSM** (không token). Khuyến nghị: pipeline mặc định dùng CARTO/OSM để HTML chia sẻ được không lộ token; `.env` có `MAPBOX_API_KEY` là optional.
- SimPy, Mesa, h3-py, DuckDB, Polars, MLflow local, Streamlit: không cần key.

## Nguồn chính

SimPy [PyPI](https://pypi.org/project/simpy/)/[docs](https://simpy.readthedocs.io/) · [Mesa](https://github.com/projectmesa/mesa) · [SUMO](https://github.com/eclipse-sumo/sumo) · [CityFlow](https://github.com/cityflow-project/CityFlow) · [FleetPy](https://github.com/TUM-VT/FleetPy) · [tomslee/ridehail](https://github.com/tomslee/ridehail) · [h3-py](https://github.com/uber/h3-py)/[API v4](https://uber.github.io/h3-py/api_quick.html)/[res table](https://h3geo.org/docs/core-library/restable/) · [deck.gl H3HexagonLayer](https://deck.gl/docs/api-reference/geo-layers/h3-hexagon-layer) · [DuckDB h3 extension](https://duckdb.org/community_extensions/extensions/h3) · kepler.gl [Playback](https://docs.kepler.gl/docs/user-guides/h-playback)/[Trip layer](https://docs.kepler.gl/docs/user-guides/c-types-of-layers/k-trip)/[token issue #3139](https://github.com/keplergl/kepler.gl/issues/3139) · [pydeck TripsLayer](https://deckgl.readthedocs.io/en/latest/gallery/trips_layer.html)/[Carto default](https://deckgl.readthedocs.io/en/latest/installation.html) · [Streamlit pydeck perf #1491](https://github.com/streamlit/streamlit/issues/1491) · [DuckDB vs Polars](https://www.codecentric.de/en/knowledge-hub/blog/duckdb-vs-polars-performance-and-memory-with-massive-parquet-data) · [MLflow vs W&B](https://www.zenml.io/blog/mlflow-vs-weights-and-biases)

Giới hạn: stars/ngày là snapshot; chưa chạy thử code repo nào; hiệu năng slider pydeck-trong-Streamlit với data lớn cần kiểm chứng khi prototype.
