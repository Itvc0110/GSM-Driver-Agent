"""Dashboard Streamlit — xem + control sim (slice v0 + biến môi trường).

Chạy:  uv run --extra viz streamlit run src/gsm_sim/dashboard.py

- Sidebar: chỉnh MỌI tham số chính trực tiếp (seed, demand, actors, dispatcher, behavior)
  + kịch bản MÔI TRƯỜNG (mưa / ngày trong tuần / nhiệt độ / sự kiện) — mọi factor tắt được về 1.
- Tab Bản đồ: H3 hexagon (demand / cuốc hoàn thành theo cell) + trạm pin, lọc theo giờ.
- Tab Thời gian: cuốc & demand theo giờ, chờ đổi pin.
- Tab Môi trường: mưa mm/h, demand factor, speed factor theo giờ (visualize biến env).
- Tab Tài xế: bảng per-actor + payout theo archetype.
- Tùy chọn So sánh baseline khô (dry_weekday) để thấy DELTA do môi trường/tham số.
Basemap Carto (không cần API key). MỌI SỐ LÀ DỮ LIỆU MÔ PHỎNG (MOCK).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from gsm_sim.config import Config
from gsm_sim.dashboard_theme import (
    ACCENT, ACTIVITY_COLORS, CSS, SEQ_AQUA, SERIES, STATUS, SURFACE_DIM, TEXT_2,
    VN_KIND, register_template,
)
from gsm_sim.geo import build_grid
from gsm_sim.journey import build_journey
from gsm_sim.metrics import summarize, trips_by_hour
from gsm_sim.runner import run_once

register_template()   # plotly template chung — grid recessive, palette VALIDATED

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "configs" / "pilot_dongda.yaml"

st.set_page_config(page_title="XanhSM Sim — Đống Đa (MOCK)", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    '<div class="xanh-header"><span class="brand">XanhSM Sim</span>'
    '<span class="sub">Đống Đa · đường thật OSRM · engine đa-ngày</span>'
    '<span class="xanh-badge">MOCK DATA</span></div>', unsafe_allow_html=True)


# ---------- Helpers ----------


def _deep_update(dst: dict, src: dict) -> dict:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


@st.cache_resource(show_spinner=False)
def load_base():
    """Nạp config gốc + grid (để lấy danh sách cell cho chọn venue sự kiện)."""
    base = Config.load(CONFIG_PATH)
    data_dir = base.resolve_path("world.data_dir")
    grid = build_grid(
        geom_path=data_dir / base.get("world.geom_file"),
        stations_path=data_dir / base.get("world.stations_file"),
        poi_path=data_dir / base.get("world.poi_file"),
        res=int(base.get("world.h3_res")),
        res_report=int(base.get("world.h3_res_report")),
    )
    # cell nhiều POI nhất → mặc định venue sự kiện (điểm nóng)
    poi_count: dict[str, int] = {}
    for p in grid.pois:
        poi_count[p.cell] = poi_count.get(p.cell, 0) + 1
    busy_cell = max(poi_count, key=poi_count.get) if poi_count else grid.core_cells[0]
    return base, grid, busy_cell


@st.cache_resource(show_spinner="Đang chạy sim...")
def run_sim(overrides_json: str, seed: int):
    base, _, _ = load_base()
    data = copy.deepcopy(base.data)
    _deep_update(data, json.loads(overrides_json))
    cfg = Config(data, base.root_dir)
    return run_once(cfg, seed)


base, grid, busy_cell = load_base()

# ---------- Sidebar: tham số cơ bản ----------

st.sidebar.title("GSM Sim control")
st.sidebar.caption("Pilot Đống Đa · H3 res 9 · arm B · **DỮ LIỆU MÔ PHỎNG**")

seed = st.sidebar.number_input("Seed", 0, 9999, 1)

overrides: dict = {"demand": {}, "actors": {}, "dispatcher": {}, "behavior": {}, "environment": {}}

# AUDIT A1 BEHAV-2 (UPDATE-065): default slider = giá trị CONFIG đã hiệu chỉnh —
# hardcode cũ (center 6000, n 50, eta 8...) làm mọi run dashboard chạy kinh tế học SIM-1.
from gsm_sim.dashboard_defaults import SLIDER_KEYS, slider_defaults  # noqa: E402

_DEF = slider_defaults(base)
_RNG = SLIDER_KEYS

with st.sidebar.expander("📦 Nhu cầu (demand)", expanded=True):
    lo, hi = _RNG["demand.orders_per_day"]
    overrides["demand"]["orders_per_day"] = st.slider(
        "Đơn/ngày (kỳ vọng)", int(lo), int(hi), int(_DEF["demand.orders_per_day"]), step=100)
    lo, hi = _RNG["demand.trip_km_median"]
    overrides["demand"]["trip_km_median"] = st.slider(
        "Quãng đường median (km)", lo, hi, float(_DEF["demand.trip_km_median"]), step=0.1)
    lo, hi = _RNG["demand.detour_factor"]
    overrides["demand"]["detour_factor"] = st.slider(
        "Hệ số detour FALLBACK (đường thật đã dùng OSRM)", lo, hi,
        float(_DEF["demand.detour_factor"]), step=0.05,
        help="Chỉ áp cho cặp cell NGOÀI ma trận OSRM (fallback) — factor thật median 1.46.")

with st.sidebar.expander("🛵 Tài xế (actors)"):
    lo, hi = _RNG["actors.n"]
    overrides["actors"]["n"] = st.slider("Số tài xế", int(lo), int(hi), int(_DEF["actors.n"]), step=5)

with st.sidebar.expander("🎯 Dispatcher"):
    lo, hi = _RNG["dispatcher.eta_max_min"]
    overrides["dispatcher"]["eta_max_min"] = st.slider(
        "ETA max (phút)", lo, hi, float(_DEF["dispatcher.eta_max_min"]), step=0.5)
    lo, hi = _RNG["dispatcher.candidate_ring_k"]
    overrides["dispatcher"]["candidate_ring_k"] = st.slider(
        "Bán kính tìm tài xế (rings res9)", int(lo), int(hi), int(_DEF["dispatcher.candidate_ring_k"]))
    lo, hi = _RNG["dispatcher.patience_median_min"]
    overrides["dispatcher"]["patience_median_min"] = st.slider(
        "Kiên nhẫn khách median (phút)", lo, hi, float(_DEF["dispatcher.patience_median_min"]),
        step=0.5, help="Khách hủy nếu chưa match sau ~ lognormal(median).")

with st.sidebar.expander("🤝 Hành vi nhận đơn (behavior)"):
    lo, hi = _RNG["behavior.accept_logit_center_vnd"]
    overrides["behavior"]["accept_logit_center_vnd"] = st.slider(
        "Ngưỡng net hấp dẫn (đ)", int(lo), int(hi),
        int(_DEF["behavior.accept_logit_center_vnd"]), step=500,
        help="A5: net cao hơn ngưỡng → xác suất nhận > 50%. Đã re-baseline theo đường THẬT (21.2k).")
    lo, hi = _RNG["behavior.accept_cost_per_pickup_km_vnd"]
    overrides["behavior"]["accept_cost_per_pickup_km_vnd"] = st.slider(
        "Chi phí cảm nhận /km đón (đ)", int(lo), int(hi),
        int(_DEF["behavior.accept_cost_per_pickup_km_vnd"]), step=500)

# ---------- Sidebar: kịch bản MÔI TRƯỜNG ----------

st.sidebar.markdown("---")
st.sidebar.subheader("🌦️ Kịch bản môi trường")
st.sidebar.caption("Mọi factor tắt được về 1 · dry_weekday = baseline")

PRESETS = ["dry_weekday", "rain_peak", "prolonged_rain", "weekend", "heat", "event_day", "Tùy chỉnh"]
scenario = st.sidebar.selectbox("Kịch bản", PRESETS, index=0)

env: dict = {"scenario": scenario, "rain": {}, "temp": {}, "dow": {}, "events": []}


def _rain_window_series(h_lo: float, h_hi: float, peak: float) -> list:
    """Series mưa tam giác 0→peak→0 trong [h_lo, h_hi] (giờ)."""
    t0, t1 = h_lo * 60, h_hi * 60
    return [[t0, 0.0], [(t0 + t1) / 2, peak], [t1, 0.0]]


if scenario == "dry_weekday":
    env["rain"]["series"] = []
    env["dow"]["type"] = "weekday"
    env["temp"]["const_c"] = 28.0
elif scenario == "rain_peak":
    env["rain"]["series"] = _rain_window_series(17, 19, 15.0)
    env["dow"]["type"] = "weekday"
    env["temp"]["const_c"] = 26.0
elif scenario == "prolonged_rain":
    env["rain"]["series"] = [[300, 8.0], [1440, 8.0]]
    env["dow"]["type"] = "weekday"
    env["temp"]["const_c"] = 25.0
elif scenario == "weekend":
    env["rain"]["series"] = []
    env["dow"]["type"] = "weekend"
    env["temp"]["const_c"] = 30.0
elif scenario == "heat":
    env["rain"]["series"] = []
    env["dow"]["type"] = "weekday"
    env["temp"]["const_c"] = 40.0
elif scenario == "event_day":
    env["rain"]["series"] = []
    env["dow"]["type"] = "friday"
    env["temp"]["const_c"] = 30.0
    env["events"] = [{
        "venue_cell": busy_cell, "t_start_min": 1140, "t_end_min": 1320,
        "attendance": 20000, "capture_rate": 0.10, "sigma_cells": 2.0,
        "ramp_in_min": 180, "ramp_lead_min": 15, "egress_min": 60, "egress_boost": 2.0,
    }]
else:  # Tùy chỉnh — chỉnh trực tiếp mọi biến môi trường trên UI
    with st.sidebar.expander("🌧️ Mưa", expanded=True):
        rain_on = st.checkbox("Bật mưa", value=False)
        if rain_on:
            mode = st.radio("Chế độ", ["Cửa sổ mưa", "Tự động ~30ph/ngày"], horizontal=True)
            if mode == "Cửa sổ mưa":
                h_lo, h_hi = st.slider("Khung giờ mưa", 5, 24, (17, 19))
                peak = st.slider("Cường độ đỉnh (mm/h)", 1.0, 40.0, 15.0, step=1.0)
                env["rain"]["series"] = _rain_window_series(h_lo, h_hi, peak)
                env["rain"]["auto"] = None
            else:
                dur = st.slider("Tổng thời lượng mưa/ngày (phút)", 10, 120, 30, step=5)
                peak = st.slider("Cường độ đỉnh (mm/h)", 1.0, 40.0, 12.0, step=1.0)
                w_lo, w_hi = st.slider("Cửa sổ có thể mưa (giờ)", 5, 24, (15, 20))
                env["rain"]["series"] = None
                env["rain"]["auto"] = {"duration_min_per_day": dur, "peak_mmph": peak,
                                       "window_min": [w_lo * 60, w_hi * 60]}
            env["rain"]["demand"] = {"delta_peak": st.slider("Mưa → demand +tối đa", 0.0, 0.5, 0.22, step=0.02),
                                     "r_peak_mmph": 8.0}
            env["rain"]["speed"] = {"r_max": st.slider("Mưa → tốc độ -tối đa", 0.0, 0.5, 0.28, step=0.02),
                                    "r0_mmph": 9.0, "v_floor_kmh": 7.0}
            env["rain"]["supply"] = {"p_cap": st.slider("Mưa → nghỉ (offline) tối đa", 0.0, 0.8, 0.5, step=0.05),
                                     "r_s_mmph": 10.0,
                                     "alpha": {"P1": 0.45, "P2": 0.20, "P3": 0.10, "P4": 0.15, "P5": 0.30}}
        else:
            env["rain"]["series"] = []

    with st.sidebar.expander("🗓️ Ngày & 🌡️ Nhiệt độ"):
        env["dow"]["type"] = st.selectbox("Ngày trong tuần", ["weekday", "friday", "weekend"], index=0)
        env["temp"]["const_c"] = st.slider("Nhiệt độ (°C)", 15.0, 42.0, 28.0, step=1.0,
                                           help=">30°C bắt đầu giảm tầm pin (tiêu hao/km tăng).")

    with st.sidebar.expander("🎉 Sự kiện (concert/thể thao)"):
        ev_on = st.checkbox("Bật 1 sự kiện", value=False)
        if ev_on:
            venue = st.selectbox("Cell địa điểm (venue)", grid.core_cells,
                                 index=grid.core_cells.index(busy_cell) if busy_cell in grid.core_cells else 0)
            att = st.slider("Số người tham dự", 2000, 50000, 20000, step=1000)
            cap = st.slider("Tỷ lệ bắt cuốc (capture)", 0.02, 0.20, 0.10, step=0.01)
            h_s, h_e = st.slider("Giờ diễn ra", 8, 24, (19, 22))
            sig = st.slider("Bán kính lan (sigma cells)", 1.0, 4.0, 2.0, step=0.5)
            env["events"] = [{
                "venue_cell": venue, "t_start_min": h_s * 60, "t_end_min": h_e * 60,
                "attendance": att, "capture_rate": cap, "sigma_cells": sig,
                "ramp_in_min": 180, "ramp_lead_min": 15, "egress_min": 60, "egress_boost": 2.0,
            }]

overrides["environment"] = env

compare_dry = st.sidebar.checkbox("So sánh với baseline khô (dry)", value=(scenario != "dry_weekday"))

# ---------- Chạy sim ----------

overrides_json = json.dumps(overrides, sort_keys=True)
result = run_sim(overrides_json, seed)
m = summarize(result)

base_result = None
mb = None
if compare_dry:
    dry_over = copy.deepcopy(overrides)
    dry_over["environment"] = {"scenario": "dry_weekday", "rain": {"series": [], "auto": None},
                               "dow": {"type": "weekday"}, "temp": {"const_c": 28.0}, "events": []}
    base_result = run_sim(json.dumps(dry_over, sort_keys=True), seed)
    mb = summarize(base_result)


def _delta(key, fmt=lambda x: x):
    if mb is None:
        return None
    return f"{fmt(m[key])} (dry {fmt(mb[key])})"


# ---------- Header metrics ----------

st.title("GSM Sim — Đống Đa (arm B) · dữ liệu mô phỏng")
st.caption(f"Kịch bản: **{scenario}** · seed {seed}" + (" · so với dry_weekday" if mb else ""))

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Đơn phát sinh", m["orders_total"],
          None if mb is None else f"{m['orders_total'] - mb['orders_total']:+d} vs dry")
c2.metric("Hoàn thành", m["orders_completed"], f"served {m['served_rate']:.0%}")
c3.metric("Unserved", f"{m['unserved_rate']:.0%}",
          None if mb is None else f"{(m['unserved_rate']-mb['unserved_rate'])*100:+.1f}pp vs dry",
          delta_color="inverse")
c4.metric("Cuốc/tài xế FT (median)", m["trips_fulltime_median"], "target 15–30", delta_color="off")
c5.metric("Payout FT median", f"{m['payout_fulltime_median']:,}đ",
          None if mb is None else f"{m['payout_fulltime_median']-mb['payout_fulltime_median']:+,}đ vs dry")

# cảnh báo clamp môi trường (quan sát)
if result.env is not None and result.env.clamp_hits() > 0:
    st.warning(f"⚠️ demand factor bị bó (clamp) {result.env.clamp_hits()} lần — "
               f"factor tổng vượt [{result.env.m_min}, {result.env.m_max}]. Cân nhắc giảm cường độ.")

tab_map, tab_replay, tab_time, tab_env, tab_actor, tab_journey, tab_ab = st.tabs(
    ["Bản đồ", "Replay", "Nhịp ngày", "Môi trường", "Đội xe", "Hành trình", "Thế giới song song"])

# ---------- Data frames ----------

ev = pd.DataFrame(
    [{"t_min": e.t_min, "actor_id": e.actor_id, "kind": e.kind, "cell": e.cell, **e.detail} for e in result.events]
)
orders_df = pd.DataFrame(
    [{"t_min": o.t_min, "cell": o.pickup_cell, "gross": o.gross_vnd} for o in result.orders]
)

with tab_map:
    lo, hi = st.slider("Khung giờ hiển thị", 5, 24, (5, 24))
    dem = orders_df[(orders_df.t_min >= lo * 60) & (orders_df.t_min < hi * 60)]
    drops = ev[(ev.kind == "dropoff") & (ev.t_min >= lo * 60) & (ev.t_min < hi * 60)]

    layer_choice = st.radio(
        "Lớp hiển thị", ["Demand (đơn đặt)", "Cuốc hoàn thành (điểm trả)"], horizontal=True
    )
    src = dem if layer_choice.startswith("Demand") else drops
    cell_counts = src.groupby("cell").size().reset_index(name="count") if len(src) else pd.DataFrame({"cell": [], "count": []})

    # --- FIX VISUAL: cột H3 3D ĐÈ LÊN chấm tủ pin ---
    # Nguyên nhân: hex extruded cao `count × elevation_scale` mét, còn trạm nằm ở MẶT ĐẤT
    # (z=0). deck.gl dùng depth buffer ⇒ cột 3D che trạm bất kể thứ tự layer (đổi thứ tự
    # KHÔNG sửa được). Hai đường xử lý, cả hai đều thuần hình học nên không phụ thuộc
    # phiên bản deck.gl:
    #   1. cho phép xem PHẲNG (tắt extrude) — nhìn trạm rõ nhất;
    #   2. khi xem 3D thì NHẤC trạm lên cao hơn cột cao nhất.
    flat = st.checkbox("Xem phẳng (2D) — nhìn rõ tủ pin, không bị cột H3 che", value=False)
    ELEV_SCALE = 8
    max_count = int(cell_counts["count"].max()) if len(cell_counts) else 0

    hex_layer = pdk.Layer(
        "H3HexagonLayer",
        cell_counts,
        get_hexagon="cell",
        # sequential MỘT hue (aqua) — magnitude job; không rainbow/cam-đỏ tuỳ hứng
        get_fill_color="[25 + count * 2, 158, 112, 170]",
        get_elevation="count",
        elevation_scale=ELEV_SCALE,
        extruded=not flat,
        pickable=True,
    )
    # nhấc trạm lên trên đỉnh cột cao nhất (+40m đệm) để không bị depth-test cắt
    station_z = 0.0 if flat else max_count * ELEV_SCALE + 40.0
    stations_df = pd.DataFrame(
        [{"lat": s.lat, "lon": s.lon, "z": station_z, "name": f"Tủ pin {s.node_id}",
          "cell": "", "count": ""} for s in result.grid.stations]
    )
    station_layer = pdk.Layer(
        "ScatterplotLayer",
        stations_df,
        get_position="[lon, lat, z]",
        get_radius=60,
        radius_min_pixels=6,          # không teo mất khi zoom xa
        get_fill_color="[201, 133, 0, 240]",   # trạm = amber (job: điểm dịch vụ, khác cầu)
        stroked=True,                 # viền trắng: nổi trên nền cam của hex
        get_line_color=[255, 255, 255],
        line_width_min_pixels=2,
        billboard=True,               # luôn hướng về camera khi pitch != 0
        pickable=True,
    )
    if len(cell_counts):              # tooltip sạch: hex không hiện "{name}" trống
        cell_counts["name"] = ""
    deck = pdk.Deck(
        layers=[hex_layer, station_layer],   # trạm vẽ SAU + ở trên → không bị che
        initial_view_state=pdk.ViewState(latitude=21.013, longitude=105.825, zoom=13,
                                         pitch=0 if flat else 40),
        tooltip={"text": "{name}{cell} {count}"},
        map_style="dark",
    )
    st.pydeck_chart(deck, width='stretch')
    st.caption("Cột cam = số đơn/cuốc theo cell H3 res 9 · chấm xanh viền trắng = 11 tủ đổi pin "
               "(OSM thật). Ở chế độ 3D, trạm được nhấc lên trên đỉnh cột để không bị che. MOCK.")

with tab_time:
    tbh = trips_by_hour(result)
    dem_bh = orders_df.assign(h=(orders_df.t_min // 60).astype(int)).groupby("h").size()
    df_time = pd.DataFrame({"giờ": sorted(set(dem_bh.index) | set(tbh.keys()))})
    df_time["đơn phát sinh"] = df_time["giờ"].map(dem_bh).fillna(0)
    df_time["cuốc hoàn thành"] = df_time["giờ"].map(tbh).fillna(0)
    if mb is not None:
        dry_orders = pd.DataFrame([{"h": int(o.t_min // 60)} for o in base_result.orders])
        df_time["đơn (dry)"] = df_time["giờ"].map(dry_orders.groupby("h").size()).fillna(0)
    fig = px.bar(df_time, x="giờ", y=[c for c in df_time.columns if c != "giờ"], barmode="group",
                 title="Đơn & cuốc theo giờ")
    st.plotly_chart(fig, width='stretch')

    swaps = ev[ev.kind == "swap_done"]
    if len(swaps):
        fig2 = px.scatter(swaps.assign(h=(swaps.t_min // 60).astype(int)),
                          x="t_min", y="wait_min", title="Chờ đổi pin theo thời điểm (phút)")
        st.plotly_chart(fig2, width='stretch')

with tab_env:
    if result.env is None:
        st.info("Không có biến môi trường (env=None).")
    else:
        e = result.env
        hours = list(range(5, 24))
        mids = [h * 60 + 30 for h in hours]
        df_env = pd.DataFrame({
            "giờ": hours,
            "mưa (mm/h)": [round(e.rain_mm(t), 2) for t in mids],
            "demand factor": [round(e.demand_factor(t), 3) for t in mids],
            "speed factor": [round(e.speed_factor(t), 3) for t in mids],
            "range factor (pin)": [round(e.range_factor(t), 3) for t in mids],
        })
        st.markdown("**Biến môi trường theo giờ** — factor = 1 nghĩa là không tác động.")
        colA, colB = st.columns(2)
        with colA:
            st.plotly_chart(px.area(df_env, x="giờ", y="mưa (mm/h)", title="Cường độ mưa (mm/h)"),
                            width='stretch')
            st.plotly_chart(px.line(df_env, x="giờ", y="demand factor", title="Demand factor (mưa×ngày×nhiệt)",
                                    markers=True), width='stretch')
        with colB:
            st.plotly_chart(px.line(df_env, x="giờ", y="speed factor", title="Speed factor (survival mưa×tắc)",
                                    markers=True), width='stretch')
            st.plotly_chart(px.line(df_env, x="giờ", y="range factor (pin)", title="Range factor (nhiệt→tầm pin)",
                                    markers=True), width='stretch')

        st.markdown("**Xác suất tài xế nghỉ vì mưa (offline) theo cường độ** — MOCK, độ tin thấp (chờ hỏi tài xế).")
        rr = [0, 2, 5, 8, 12, 20, 30]
        df_off = pd.DataFrame({"mm/h": rr})
        for arch in ("P1", "P2", "P3", "P4", "P5"):
            df_off[arch] = [round(e.rain_offline_prob(r, arch), 3) for r in rr]
        st.plotly_chart(px.line(df_off, x="mm/h", y=["P1", "P2", "P3", "P4", "P5"],
                                title="p(offline | mưa) theo archetype", markers=True), width='stretch')

        if e.events:
            st.markdown(f"**Sự kiện:** {len(e.events)} · venue `{e.events[0].venue_cell}` · "
                        f"tham dự {e.events[0].attendance:,} × capture {e.events[0].capture_rate:.0%}. "
                        "Cuốc sự kiện được CỘNG (không nhân) quanh venue theo Gauss + profile ingress/egress.")
        st.caption(f"clamp_hits = {e.clamp_hits()} (số lần demand factor tổng bị bó về [{e.m_min}, {e.m_max}]).")

with tab_actor:
    act = pd.DataFrame(
        [
            {
                "id": a.actor_id, "archetype": a.archetype, "fleet": a.fleet.value,
                "cuốc": a.trips_done, "payout (đ)": a.payout_vnd, "điểm": a.points,
                "acceptance": round(a.acceptance_rate, 2), "online (phút)": round(a.online_min),
                "SOC cuối": round(a.soc_pct),
            }
            for a in result.actors
        ]
    )
    fig3 = px.box(act, x="archetype", y="payout (đ)", points="all", title="Payout theo archetype (MOCK)")
    st.plotly_chart(fig3, width='stretch')
    st.dataframe(act.sort_values("payout (đ)", ascending=False), width='stretch', height=420)

# ---------- SIM-2: hành trình chi tiết của MỘT tài xế ----------
with tab_journey:
    ARCH_LABEL = {"P1": "part-time tối", "P2": "full-time 2 đỉnh", "P3": "top performer",
                  "P4": "TÂN BINH (lệch khung)", "P5": "lão làng chiều-tối",
                  "P6": "ca sáng sớm", "P7": "ca tối-đêm"}
    opts = sorted(result.actors, key=lambda a: (a.archetype, -a.trips_done))
    pick = st.selectbox(
        "Chọn tài xế", opts, index=0,
        format_func=lambda a: (f"d-{a.actor_id} · {a.archetype} {ARCH_LABEL.get(a.archetype, '')}"
                               f" · {a.trips_done} cuốc · {a.payout_vnd:,}đ"))
    j = build_journey(result, pick.actor_id)
    m = j.metrics

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cuốc hoàn thành", m["trips_completed"], f"{m['cancelled_after_accept']} huỷ sau nhận")
    c2.metric("Tỷ lệ nhận", f"{(m['acceptance_rate'] or 0):.0%}", f"{m['declined']} từ chối")
    c3.metric("Hoàn thành", f"{(m['completion_rate'] or 0):.0%}")
    c4.metric("Utilization", f"{m['utilization']:.0%}", f"idle {m['idle_min']:.0f}ph")
    c5.metric("Payout", f"{m['payout_vnd']:,}đ",
              f"{m['points']} điểm · ngoài cuốc {m['bonus_share']:.0%}")
    a_pick = next(x for x in result.actors if x.actor_id == pick.actor_id)
    c6, c7, c8 = st.columns(3)
    stars = (a_pick.ratings_sum / a_pick.ratings_n) if a_pick.ratings_n else None
    c6.metric("Điểm sao (ngày)", f"{stars:.2f}" if stars else "chưa có",
              f"{a_pick.ratings_5}/{a_pick.ratings_n} lượt 5 sao" if a_pick.ratings_n else None)
    c7.metric("Mission", f"+{m['mission_reward_vnd']:,}đ",
              " · ".join(f"{k.split('-')[1]} {v}" for k, v in a_pick.mission_progress.items()) or None)
    c8.metric("Tân binh", f"+{m['newbie_vnd']:,}đ",
              f"thâm niên {a_pick.tenure_days} ngày")

    st.markdown("**Timeline phiên làm việc** — mọi phút đều có nhãn; `idle` = chờ đơn tại chỗ")
    tl = pd.DataFrame([{
        "kind": b.kind, "Hoạt động": VN_KIND.get(b.kind, b.kind),
        "start": pd.Timestamp("2026-07-01") + pd.to_timedelta(b.t0, unit="m"),
        "end": pd.Timestamp("2026-07-01") + pd.to_timedelta(b.t1, unit="m"),
        "phút": round(b.minutes, 1), "đơn": b.order_id,
    } for b in j.timeline])
    color_map = {VN_KIND.get(k, k): v for k, v in ACTIVITY_COLORS.items()}
    figj = px.timeline(tl, x_start="start", x_end="end", y="Hoạt động", color="Hoạt động",
                       color_discrete_map=color_map, hover_data=["phút", "đơn"],
                       title=f"Hành trình d-{pick.actor_id} (MOCK)")
    figj.update_yaxes(autorange="reversed")
    # SIM-XANH P4: đánh dấu các mốc ADVICE trên timeline (đọc từ event thật, không tự tính)
    adv_events = [e for e in result.events if e.actor_id == pick.actor_id
                  and e.kind in ("advice_given", "advice_bonus_gate", "advice_rest_window",
                                 "mission_completed", "newbie_week1_bonus")]
    for e in adv_events:
        x = pd.Timestamp("2026-07-01") + pd.to_timedelta(e.t_min, unit="m")
        figj.add_vline(x=x, line_width=1, line_dash="dot", line_color=ACCENT, opacity=0.7)
    st.plotly_chart(figj, width='stretch')
    if adv_events:
        st.caption(f"Vạch chấm = {len(adv_events)} mốc advice/mission/thưởng (đọc từ event sim).")

    cA, cB = st.columns(2)
    with cA:
        st.markdown(f"**Thu nhập tích luỹ** — cuốc {m['trip_payout_vnd']:,}đ "
                    f"+ **thưởng ngày {m['day_bonus_vnd']:,}đ** (bậc cuối)")
        inc = pd.DataFrame(j.income_curve, columns=["t_min", "payout"])
        inc["giờ"] = inc.t_min / 60
        st.plotly_chart(px.line(inc, x="giờ", y="payout", markers=True), width='stretch')
    with cB:
        st.markdown("**Thời gian đi đâu?**")
        mk = pd.DataFrame(sorted(m["minutes_by_kind"].items(), key=lambda kv: -kv[1]),
                          columns=["Hoạt động", "phút"])
        st.plotly_chart(px.bar(mk, x="phút", y="Hoạt động", orientation="h"), width='stretch')

    dr = m["decline_reasons"]
    st.markdown(
        f"**Vì sao từ chối?** kinh tế (cuốc xa/rẻ): **{dr['economics']}** · "
        f"tính cách/mệt/sắp kết ca: **{dr['base_behavior']}** · pin không đủ: **{m['skipped_soc']}**")
    st.dataframe(pd.DataFrame([{
        "phút": round(o.t_min, 1), "đơn": o.order_id, "quyết định": o.decision,
        "lý do": o.reason, "gross (đ)": o.gross_vnd, "net (đ)": o.net_vnd,
        "đón (km)": o.pickup_km, "P(nhận)": o.p_accept, "kết cục": o.outcome,
    } for o in j.offers]), width='stretch', height=320)
    st.caption("Mỗi dòng = một lần được chào đơn. `net` = gross − chi phí quãng đón; "
               "`P(nhận)` = xác suất nhận tại thời điểm đó. MOCK — không phải số thật GSM.")


# ---------- SIM-XANH P4: REPLAY — xem thị trường CHUYỂN ĐỘNG ----------
with tab_replay:
    st.markdown("**Replay chuyển động đội xe** — mỗi vệt là một chặng di chuyển thật của sim; "
                "màu theo loại hoạt động (bảng màu cố định toàn dashboard).")
    rc1, rc2 = st.columns([3, 1])
    t_now = rc1.slider("Thời điểm trong ngày (phút)", 300, 1440, 700, step=5,
                       format="%d ph")
    trail = rc2.slider("Đuôi vệt (phút)", 10, 120, 45, step=5)

    def _rgb(hexcol):
        h = hexcol.lstrip("#")
        return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]

    seg_rows = []
    for sgm in result.segments:
        if sgm["t1"] < t_now - trail or sgm["t0"] > t_now:
            continue
        seg_rows.append({
            "path": [[sgm["from_lon"], sgm["from_lat"]], [sgm["to_lon"], sgm["to_lat"]]],
            "timestamps": [sgm["t0"], min(sgm["t1"], t_now)],
            "color": _rgb(ACTIVITY_COLORS.get(sgm["kind"], "#3987e5")),
        })
    trips_layer = pdk.Layer(
        "TripsLayer", seg_rows, get_path="path", get_timestamps="timestamps",
        get_color="color", width_min_pixels=3, trail_length=trail, current_time=t_now,
        opacity=0.85,
    )
    # trạm pin: bán kính theo hàng chờ hiện KHÔNG có timeline per-phút trong RunResult —
    # hiển thị vị trí (amber); queue động là follow-up (ghi UPDATE, không giả số)
    st_layer = pdk.Layer(
        "ScatterplotLayer",
        [{"lat": s_.lat, "lon": s_.lon, "name": f"Tủ pin {s_.node_id}"} for s_ in result.grid.stations],
        get_position="[lon, lat]", get_radius=45, radius_min_pixels=4,
        get_fill_color=_rgb("#c98500") + [235], stroked=True,
        get_line_color=[255, 255, 255], line_width_min_pixels=1, pickable=True,
    )
    active_now = sum(1 for sgm in result.segments if sgm["t0"] <= t_now <= sgm["t1"])
    st.pydeck_chart(pdk.Deck(
        layers=[trips_layer, st_layer],
        initial_view_state=pdk.ViewState(latitude=21.013, longitude=105.825, zoom=13, pitch=45),
        map_style="dark", tooltip={"text": "{name}"},
    ), width="stretch")
    hh, mm = int(t_now // 60), int(t_now % 60)
    st.caption(f"{hh:02d}:{mm:02d} · {len(seg_rows)} chặng trong cửa sổ · "
               f"{active_now} tài xế đang di chuyển. Chú giải: "
               + " · ".join(f"{VN_KIND[k]}" for k in ("on_trip", "enroute", "charge", "relocate"))
               + ". MOCK.")


# ---------- SIM-XANH P4: THẾ GIỚI SONG SONG — trả nợ tab A/B từ SIM-4 ----------
with tab_ab:
    st.markdown("**Tự làm (A) vs làm theo chỉ dẫn (B)** — cùng seed, chung đơn hàng/thời tiết "
                "(CRN); Δ là hiệu THEO CẶP. Mọi số từ máy đo `parallel.py`, dashboard không tự tính.")
    ab1, ab2 = st.columns([1, 2])
    with ab1:
        ab_seed = st.number_input("Seed cặp A/B", 1, 99999, int(seed), step=1)
        ch_lift = st.checkbox("Kênh accept_lift", value=True)
        ch_ext = st.checkbox("Kênh shift_extend", value=False)
        ch_rest = st.checkbox("Kênh rest_window", value=False)
        run_ab = st.button("Chạy cặp A/B", type="primary")

    @st.cache_resource(show_spinner="Đang chạy 2 thế giới (A + B)...")
    def _run_pair_cached(seed_i: int, lift: bool, ext: bool, rest: bool):
        from gsm_sim.parallel import CHANNEL_LADDER, pick_target, run_pair
        base_cfg, _, _ = load_base()
        channels = {"shift_plan": True, "accept_lift": lift,
                    "shift_extend": ext, "rest_window": rest}
        pr = run_pair(base_cfg, seed_i, channels=channels)
        return pr

    if run_ab or st.session_state.get("_ab_done"):
        st.session_state["_ab_done"] = True
        pr = _run_pair_cached(int(ab_seed), ch_lift, ch_ext, ch_rest)
        with ab2:
            st.markdown(f"Tài xế đích: `d-{pr.actor_id}` (P4 tân binh, người được chào đơn "
                        f"nhiều nhất World A).")
            rows = []
            LBL = {"payout_vnd": "Payout (đ)", "day_bonus_vnd": "Thưởng ngày (đ)",
                   "mission_reward_vnd": "Mission (đ)", "newbie_vnd": "Tân binh (đ)",
                   "trips_completed": "Cuốc", "acceptance_rate": "Tỷ lệ nhận",
                   "utilization": "Utilization", "idle_min": "Idle (phút)",
                   "online_min": "Online (phút)"}
            for k, lbl in LBL.items():
                if k not in pr.a:
                    continue
                va, vb = pr.a[k], pr.b[k]
                rows.append({"Chỉ số": lbl, "World A (tự làm)": va,
                             "World B (theo chỉ dẫn)": vb,
                             "Δ (B−A)": round((vb or 0) - (va or 0), 4)})
            st.dataframe(pd.DataFrame(rows), width="stretch", height=360, hide_index=True)
            g = pr.system_a["served_rate"], pr.system_b["served_rate"]
            ok_guard = abs(g[1] - g[0]) < 0.02
            (st.success if ok_guard else st.warning)(
                f"Guardrail hệ thống: served A {g[0]:.3f} → B {g[1]:.3f} "
                f"({'không đổi đáng kể' if ok_guard else 'CÓ dịch chuyển — xem lại'})")
        st.caption("LƯU Ý ĐỌC SỐ: 1 seed = 1 ngày — kết luận cần 30 seed + CI "
                   "(`uv run python scripts/run_parallel.py --seeds 30`). "
                   "Δ dương một ngày không có nghĩa 'ngày nào cũng lợi'. MOCK.")

    # kết quả sweep D-SIM-06 nếu đã chạy (đọc file, không tính lại)
    sweep_path = ROOT / "research" / "experiments" / "sensitivity" / "dsim06_sweep.json"
    if sweep_path.exists():
        st.divider()
        st.markdown("**Bản đồ độ nhạy D-SIM-06** (30 seed/ô, CI bootstrap — đọc từ file sweep):")
        data = json.loads(sweep_path.read_text(encoding="utf-8"))
        for arch in ("P4", "P1"):
            if arch not in data:
                continue
            cells = data[arch]["cells"]
            hm = []
            for key, c in cells.items():
                adh = float(key.split("|")[0].split("=")[1])
                lift = float(key.split("|")[1].split("=")[1])
                hm.append({"adherence": adh, "lift_max": lift,
                           "delta": c["delta_mean"], "sig": c["significant"],
                           "n_pos": c["n_positive"]})
            df_hm = pd.DataFrame(hm)
            piv = df_hm.pivot(index="adherence", columns="lift_max", values="delta")
            fig_hm = px.imshow(piv, text_auto=",.0f", aspect="auto",
                               color_continuous_scale=[[0, "#e66767"], [0.5, SURFACE_DIM],
                                                       [1, ACCENT]],
                               color_continuous_midpoint=0,
                               title=f"{arch}: Δ payout (đ/ngày) theo adherence × lift_max")
            st.plotly_chart(fig_hm, width="stretch")
        st.caption("Ô sáng xanh = advice giúp; đỏ = hại; giữa xám = không rõ. "
                   "Diverging đúng chuẩn: 2 cực + trung tính ở 0.")
