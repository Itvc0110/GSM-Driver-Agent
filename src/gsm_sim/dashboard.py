"""Dashboard Streamlit — xem + control sim (slice v0).

Chạy:  uv run --extra viz streamlit run src/gsm_sim/dashboard.py

- Sidebar: chỉnh tham số chính (seed, demand, actors, dispatcher) → Run.
- Tab Bản đồ: H3 hexagon (demand / cuốc hoàn thành theo cell) + trạm pin, lọc theo giờ.
- Tab Thời gian: cuốc & demand theo giờ, chờ đổi pin.
- Tab Tài xế: bảng per-actor + payout theo archetype.
Basemap Carto (không cần API key). MỌI SỐ LÀ DỮ LIỆU MÔ PHỎNG (MOCK).
"""

from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

from gsm_sim.config import Config
from gsm_sim.metrics import summarize, trips_by_hour
from gsm_sim.runner import run_once

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "configs" / "pilot_dongda.yaml"

st.set_page_config(page_title="GSM Sim — Đống Đa (MOCK)", layout="wide")


# ---------- Sim run (cached) ----------


@st.cache_resource(show_spinner="Đang chạy sim...")
def run_sim(seed: int, orders_per_day: int, n_actors: int, eta_max: float, ring_k: int, expire_s: int):
    base = Config.load(CONFIG_PATH)
    data = copy.deepcopy(base.data)
    data["demand"]["orders_per_day"] = orders_per_day
    data["actors"]["n"] = n_actors
    data["dispatcher"]["eta_max_min"] = eta_max
    data["dispatcher"]["candidate_ring_k"] = ring_k
    data["dispatcher"]["order_expire_s"] = expire_s
    cfg = Config(data, base.root_dir)
    return run_once(cfg, seed)


# ---------- Sidebar controls ----------

st.sidebar.title("GSM Sim control")
st.sidebar.caption("Pilot Đống Đa · H3 res 9 · arm B · **DỮ LIỆU MÔ PHỎNG**")

seed = st.sidebar.number_input("Seed", 0, 9999, 1)
orders_per_day = st.sidebar.slider("Đơn/ngày (kỳ vọng)", 600, 2400, 1200, step=100)
n_actors = st.sidebar.slider("Số tài xế", 20, 100, 50, step=5)

with st.sidebar.expander("Dispatcher (calibration levers)"):
    eta_max = st.slider("ETA max (phút)", 4.0, 15.0, 8.0, step=0.5)
    ring_k = st.slider("Bán kính tìm tài xế (rings res9)", 2, 8, 4)
    expire_s = st.slider("Đơn expire (giây)", 60, 300, 90, step=15)

result = run_sim(seed, orders_per_day, n_actors, eta_max, ring_k, expire_s)
m = summarize(result)

# ---------- Header metrics ----------

st.title("GSM Sim — Đống Đa (arm B) · dữ liệu mô phỏng")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Đơn phát sinh", m["orders_total"])
c2.metric("Hoàn thành", m["orders_completed"], f"served {m['served_rate']:.0%}")
c3.metric("Unserved", f"{m['unserved_rate']:.0%}", "target 15–20%", delta_color="off")
c4.metric("Cuốc/tài xế FT (median)", m["trips_fulltime_median"], "target 15–30", delta_color="off")
c5.metric("Payout FT median", f"{m['payout_fulltime_median']:,}đ")

tab_map, tab_time, tab_actor = st.tabs(["🗺️ Bản đồ H3", "📈 Theo thời gian", "🛵 Tài xế"])

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

    hex_layer = pdk.Layer(
        "H3HexagonLayer",
        cell_counts,
        get_hexagon="cell",
        get_fill_color="[255, 140 - count, 0, 160]",
        get_elevation="count",
        elevation_scale=8,
        extruded=True,
        pickable=True,
    )
    stations_df = pd.DataFrame(
        [{"lat": s.lat, "lon": s.lon, "name": f"Tủ pin {s.node_id}"} for s in result.grid.stations]
    )
    station_layer = pdk.Layer(
        "ScatterplotLayer",
        stations_df,
        get_position="[lon, lat]",
        get_radius=60,
        get_fill_color="[0, 122, 255, 220]",
        pickable=True,
    )
    deck = pdk.Deck(
        layers=[hex_layer, station_layer],
        initial_view_state=pdk.ViewState(latitude=21.013, longitude=105.825, zoom=13, pitch=40),
        tooltip={"text": "{cell}\n{count} | {name}"},
        map_style="light",
    )
    st.pydeck_chart(deck, width='stretch')
    st.caption("Cột cam = số đơn/cuốc theo cell H3 res 9 · chấm xanh = 11 tủ đổi pin (OSM thật). MOCK.")

with tab_time:
    tbh = trips_by_hour(result)
    dem_bh = orders_df.assign(h=(orders_df.t_min // 60).astype(int)).groupby("h").size()
    df_time = pd.DataFrame(
        {
            "giờ": sorted(set(dem_bh.index) | set(tbh.keys())),
        }
    )
    df_time["đơn phát sinh"] = df_time["giờ"].map(dem_bh).fillna(0)
    df_time["cuốc hoàn thành"] = df_time["giờ"].map(tbh).fillna(0)
    fig = px.bar(df_time, x="giờ", y=["đơn phát sinh", "cuốc hoàn thành"], barmode="group")
    st.plotly_chart(fig, width='stretch')

    swaps = ev[ev.kind == "swap_done"]
    if len(swaps):
        swaps = swaps.assign(h=(swaps.t_min // 60).astype(int))
        fig2 = px.scatter(swaps, x="t_min", y="wait_min", title="Chờ đổi pin theo thời điểm (phút)")
        st.plotly_chart(fig2, width='stretch')

with tab_actor:
    act = pd.DataFrame(
        [
            {
                "id": a.actor_id,
                "archetype": a.archetype,
                "fleet": a.fleet.value,
                "cuốc": a.trips_done,
                "payout (đ)": a.payout_vnd,
                "điểm": a.points,
                "acceptance": round(a.acceptance_rate, 2),
                "online (phút)": round(a.online_min),
                "SOC cuối": round(a.soc_pct),
            }
            for a in result.actors
        ]
    )
    fig3 = px.box(act, x="archetype", y="payout (đ)", points="all", title="Payout theo archetype (MOCK)")
    st.plotly_chart(fig3, width='stretch')
    st.dataframe(act.sort_values("payout (đ)", ascending=False), width='stretch', height=420)
