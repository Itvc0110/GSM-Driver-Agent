import streamlit as st
import leafmap.foliumap as leafmap
import requests

st.set_page_config(page_title="GSM Driver Simulator - Hanoi Geo-fenced", layout="wide")

st.title("🚗 GSM Driver Simulator & Reviewer Analytics Dashboard (Hà Nội)")
st.markdown("Hệ thống quan sát, phân tích nhu cầu H3 và replay dữ liệu mô phỏng khoanh vùng **Chỉ nội thành Hà Nội**.")

# Sidebar controls
st.sidebar.header("⚙️ Cấu hình Mô phỏng")
backend_url = st.sidebar.text_input("Backend API Gateway URL", value="http://localhost:8000")
scenario_id = st.sidebar.selectbox("Scenario ID", ["default_hanoi", "peak_hour_hoankiem", "rain_storm_badinh"])
seed = st.sidebar.number_input("Random Seed", value=42, step=1)

if st.sidebar.button("🔄 Tải lại Snapshot Dữ liệu"):
    st.experimental_rerun()

# Fetch data from API Gateway
try:
    map_res = requests.get(f"{backend_url}/api/v1/map-context", params={"scenario_id": scenario_id, "seed": seed}, timeout=5)
    driver_res = requests.get(f"{backend_url}/api/v1/driver/state", params={"scenario_id": scenario_id, "seed": seed}, timeout=5)
    
    if map_res.status_code == 200 and driver_res.status_code == 200:
        map_data = map_res.json()
        driver_data = driver_res.json()
        
        # Display Driver Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tài Xế", driver_data.get("driver_name", "N/A"), driver_data.get("driver_id"))
        col2.metric("Trạng Thái Ca", driver_data.get("shift_status"), f"Pin SOC: {driver_data.get('soc_percent')}%")
        col3.metric("Quãng Đường Còn Lại", f"{driver_data.get('vehicle_range_km')} km")
        payout = driver_data.get("payout_summary", {})
        col4.metric("Thu Nhập Tạm Tính (Synthetic)", f"{payout.get('value', 0):,.0f} {payout.get('currency', 'VND')}", f"{payout.get('trips_count')} cuốc")

        st.divider()

        # Render Leafmap Map centered on Hanoi
        col_map, col_info = st.columns([3, 1])
        
        with col_map:
            st.subheader("🗺️ Bản đồ Vùng Nhu Cầu & Trạm Sạc (Khoanh vùng Hà Nội)")
            
            driver_loc = map_data.get("driver_location", {"lat": 21.0285, "lng": 105.8542})
            m = leafmap.Map(center=[driver_loc["lat"], driver_loc["lng"]], zoom=14)
            
            # Driver Marker
            m.add_marker(
                location=[driver_loc["lat"], driver_loc["lng"]],
                popup=f"Driver Location ({driver_loc['speed_kmh']} km/h)",
                icon_style="color: blue; icon: car;"
            )
            
            # Demand Zones
            for zone in map_data.get("demand_zones", []):
                radius = int(zone["intensity"] * 400)
                m.add_circle(
                    location=[zone["lat"], zone["lng"]],
                    radius=radius,
                    color="red",
                    fill=True,
                    fill_color="orange",
                    fill_opacity=0.4,
                    popup=f"H3 Zone: {zone['h3_index']}<br>Cường độ: {zone['intensity']}"
                )
                
            # Charging Stations
            for stn in map_data.get("charging_stations", []):
                m.add_marker(
                    location=[stn["lat"], stn["lng"]],
                    popup=f"<b>{stn['name']}</b><br>Cổng khả dụng: {stn['available_ports']}/{stn['total_ports']}",
                    icon_style="color: green; icon: battery-charging;"
                )

            m.to_streamlit(height=520)

        with col_info:
            st.subheader("⚠️ Cảnh Báo & Rủi Ro (Hà Nội)")
            for alert in map_data.get("alerts", []):
                if alert["severity"] == "critical":
                    st.error(f"**{alert['title']}**\n\n{alert['message']}")
                else:
                    st.warning(f"**{alert['title']}**\n\n{alert['message']}")

    else:
        st.error(f"Không thể kết nối API Backend. Status code: Map={map_res.status_code}, Driver={driver_res.status_code}")

except Exception as e:
    st.info("⚠️ Vui lòng bật Backend FastAPI tại `http://localhost:8000` để xem dữ liệu snapshot mô phỏng.")
