// app.js — GSM Driver web app (Track UI U2).
// Nguyên tắc: UI CHỈ RENDER số từ backend (contract-first). Cuốc "demo" là mô phỏng
// interaction — cước demo KHÔNG được cộng vào payout (payout đến từ data mock).

import { api, fmtVnd } from "./api.js";

const S = {
  driverId: null, date: null,
  state: null, history: null, mapCtx: null, catalog: null,
  demoTrips: [], tripStep: 0, activeRoute: null,
};

const $ = (id) => document.getElementById(id);

/* ================= MAP ================= */
let map, demandLayer, stationLayer, routeLayers = [], driverMarker, moveTimer;

function initMap() {
  map = L.map("map", { zoomControl: false }).setView([21.013, 105.827], 13.5);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 19, subdomains: "abcd", attribution: "© OSM · © CARTO" }).addTo(map);
  demandLayer = L.layerGroup().addTo(map);
  stationLayer = L.layerGroup().addTo(map);
  driverMarker = L.marker([21.013, 105.827], {
    icon: L.divIcon({
      className: "drv-pin",
      html: `<div style="width:30px;height:30px;border-radius:50%;background:var(--accent);
             border:2px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.35);display:flex;
             align-items:center;justify-content:center;color:#fff;font-size:13px">🛵</div>`,
      iconSize: [30, 30], iconAnchor: [15, 15],
    }),
  }).addTo(map);
}

function renderMapContext(mc) {
  demandLayer.clearLayers();
  stationLayer.clearLayers();
  // demand: sequential cyan theo intensity (magnitude — 1 hue, dataviz tokens)
  const seq = ["#c3ebee", "#95dbe0", "#5ec4cc", "#22a9b4", "#068c96"];
  for (const z of mc.demand_zones) {
    const c = seq[Math.min(seq.length - 1, Math.floor(z.intensity * seq.length))];
    L.circle([z.lat, z.lng], {
      radius: 220 + z.intensity * 420, color: c, weight: 1,
      fillColor: c, fillOpacity: 0.42,
    }).bindPopup(`Số đơn đặt (mô phỏng): cường độ ${(z.intensity * 100).toFixed(0)}%<br>
      <small>hex ${z.h3_index} · không đảm bảo đơn về tay bạn</small>`)
      .addTo(demandLayer);
  }
  for (const st of mc.charging_stations) {
    L.circleMarker([st.lat, st.lng], {
      radius: 7, color: "#fff", weight: 2, fillColor: "var(--viz-charge)".includes("var")
        ? "#eda100" : "#eda100", fillOpacity: 1,
    }).bindPopup(`<b>${st.name}</b><br><small>tủ đổi pin (OSM — vị trí thật)</small>`)
      .addTo(stationLayer);
  }
  const alertSlot = $("alert-slot");
  alertSlot.innerHTML = "";
  for (const a of mc.alerts) {
    alertSlot.insertAdjacentHTML("beforeend", `
      <div class="alert-card"><div class="ico">📈</div>
        <div><b>${a.title}</b><p>${a.message}</p></div></div>`);
  }
}

/* ================= DATA LOAD ================= */
async function loadProfile(driverId, date) {
  S.driverId = driverId; S.date = date;
  const [st, hist, mc] = await Promise.all([
    api.state(driverId, date),
    api.history(driverId, date, 14),
    api.mapContext(date, 18, driverId),
  ]);
  S.state = st; S.history = hist; S.mapCtx = mc;
  renderHeader(); renderIncome(); renderEv(); renderSettings(); renderMapContext(mc);
  $("bot-dot").classList.remove("hidden");
}

function renderHeader() {
  const m = S.state.money;
  $("pill-payout").innerHTML = `${fmtVnd(m.payout_vnd)}
    <span class="sub">Thu nhập tài xế (payout) · ${S.date} · mô phỏng</span>`;
  $("pill-trips").textContent = `${S.state.payout_summary.trips_count} cuốc`;
  const soc = S.state.soc_percent;
  const socEl = $("pill-soc");
  socEl.textContent = `⚡ ${soc}%`;
  socEl.classList.toggle("low", soc < 25);
}

/* ================= THU NHẬP ================= */
function renderIncome() {
  const m = S.state.money;
  $("inc-date").textContent = S.date;
  $("inc-payout").textContent = fmtVnd(m.payout_vnd);
  const bd = m.payout_breakdown || {};
  $("inc-breakdown").textContent =
    `cuốc ${fmtVnd(bd.trip_payout_vnd)} · mission ${fmtVnd(bd.mission_reward_vnd || 0)}`
    + " · thưởng ngày/tân binh: xem khu Mô phỏng";
  $("inc-gross").textContent = fmtVnd(m.gross_vnd);
  $("inc-net").textContent = "—";

  const days = S.history.days;
  Plotly.newPlot("chart-income", [{
    x: days.map((d) => d.date.slice(5)),
    y: days.map((d) => d.payout_vnd),
    type: "bar",
    marker: { color: "#2a78d6", cornerradius: 4 },
    hovertemplate: "%{x}: <b>%{y:,.0f}đ</b> payout<extra></extra>",
  }], {
    margin: { l: 44, r: 8, t: 8, b: 26 },
    font: { family: "Be Vietnam Pro, sans-serif", size: 10.5, color: "#52514e" },
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    yaxis: { gridcolor: "#e1e0d9", tickformat: "~s", zeroline: false },
    xaxis: { showgrid: false },
    bargap: 0.35,
  }, { displayModeBar: false, responsive: true });

  $("income-rows").innerHTML = days.slice().reverse().map((d) => `
    <div class="row-item">
      <div><b>${d.date}</b><br>
        <span style="color:var(--text-muted);font-size:11px">
          ${d.trips} cuốc · ${d.online_h}h online · nhận ${(d.acceptance_rate * 100).toFixed(0)}%</span></div>
      <div style="text-align:right">
        <div class="amt">${fmtVnd(d.payout_vnd)}</div>
        <div style="font-size:10px;color:var(--text-muted)">gộp ${fmtVnd(d.gross_vnd)}</div></div>
    </div>`).join("");
}

/* ================= XE & PIN ================= */
function renderEv() {
  $("ev-soc").textContent = `${S.state.soc_percent}%`;
  $("ev-range").textContent = `${S.state.vehicle_range_km} km`;
  $("ev-plate").textContent = `Hồ sơ mô phỏng · ${S.driverId}`;
  $("station-rows").innerHTML = S.mapCtx.charging_stations.slice(0, 6).map((st) => `
    <div class="row-item"><div>🔋 <b>${st.name}</b><br>
      <span style="font-size:10.5px;color:var(--text-muted)">${st.lat.toFixed(4)}, ${st.lng.toFixed(4)} · OSM</span></div>
    </div>`).join("");
}

/* ================= CÀI ĐẶT ================= */
function renderSettings() {
  const r = S.state.rating || {};
  $("set-rating").textContent = r.n
    ? `★ ${r.avg} (${r.n} lượt · ${(r.five_rate * 100).toFixed(0)}% 5★)` : "chưa có lượt chấm";
  const ms = S.state.missions || [];
  $("mission-rows").innerHTML = ms.length ? ms.map((m) => `
    <div style="padding:7px 0;border-top:1px solid var(--border-hairline)">
      <b>${m.title}</b> — ${m.progress}/${m.target}
      ${m.done ? `<span style="color:var(--status-good);font-weight:700"> ✓ ${fmtVnd(m.reward_vnd)}</span>` : ""}
      <div class="confidence-track"><div class="confidence-fill"
        style="width:${Math.min(100, (m.progress / Math.max(1, m.target)) * 100)}%"></div></div>
    </div>`).join("")
    : `<span style="color:var(--text-muted)">chưa có nhiệm vụ</span>`;
}

async function fillCatalog() {
  S.catalog = await api.catalog();
  $("prov-line").textContent =
    `data/mock/realdata-v1 · engine ${S.catalog.engine_commit} · nhãn ${S.catalog.label}`;
  $("sel-driver").innerHTML = S.catalog.drivers.map((d) =>
    `<option value="${d.driver_id}" ${d.driver_id === S.driverId ? "selected" : ""}>
       ${d.driver_id} (${d.fleet})</option>`).join("");
  $("sel-date").innerHTML = S.catalog.dates.map((d) =>
    `<option ${d === S.date ? "selected" : ""}>${d}</option>`).join("");
}

/* ================= TRỢ LÝ XANH ================= */
async function showAdvice(nowMin) {
  const body = $("advice-body");
  body.innerHTML = `<div class="silent-box">Đang hỏi trợ lý…</div>`;
  try {
    const a = await api.advice(S.driverId, S.date, nowMin);
    if (a.silent.is_silent) {
      body.innerHTML = `<div class="silent-box"><span class="big-ico">✅</span>
        ${a.silent.message}<br><small style="color:var(--text-muted)">mã: ${a.silent.reason_code}</small></div>`;
      return;
    }
    body.innerHTML = a.items.map((it) => `
      <div class="advice-item ${it.kind === "info" ? "info" : ""}">
        <b>${it.title}</b>
        <p>${it.message}</p>
        <table class="num-table">${(it.numbers || []).map((n) => `
          <tr><td>${n.name.replaceAll("_", " ")}</td>
              <td>${n.unit === "vnd" ? fmtVnd(n.value) : n.value + " " + (n.unit || "")}</td>
              <td>${n.source}</td></tr>`).join("")}
        </table>
        <div class="confidence-track"><div class="confidence-fill" style="width:${it.confidence * 100}%"></div></div>
        <div class="meta">độ tin ${(it.confidence * 100).toFixed(0)}% · solver ${it.solver} · mã ${it.reason_code}
          ${it.caveat ? `<br>⚠ ${it.caveat}` : ""}</div>
      </div>`).join("");
  } catch (e) {
    body.innerHTML = `<div class="silent-box">Không gọi được trợ lý (${e.message})</div>`;
  }
}

/* ================= TRIP LIFECYCLE DEMO (port từ demo Khánh) ================= */
const WP_COLORS = ["#00AFB9", "#F59E0B", "#8B5CF6", "#F43F5E"];

function clearRoute() {
  routeLayers.forEach((l) => map.removeLayer(l));
  routeLayers = [];
  if (moveTimer) clearInterval(moveTimer);
}

async function startIncomingTrip() {
  const t = await api.tripStep(S.demoTrips.length, "INCOMING");
  const wps = [
    { lat: t.pickup_lat, lng: t.pickup_lng, name: `Đón: ${t.pickup_address}` },
    { lat: t.dropoff_lat, lng: t.dropoff_lng, name: `Trả: ${t.dropoff_address}` },
  ];
  const route = await api.route(wps);
  S.activeRoute = { ...route, wps, trip: t };
  clearRoute();
  // polyline 2 lớp theo brand Khánh
  routeLayers.push(L.polyline(route.coords, { color: "#0f172a", weight: 10, opacity: 0.9 }).addTo(map));
  routeLayers.push(L.polyline(route.coords, { color: "#00AFB9", weight: 6 }).addTo(map));
  wps.forEach((w, i) => routeLayers.push(L.marker([w.lat, w.lng], {
    icon: L.divIcon({
      html: `<div style="width:24px;height:24px;border-radius:50%;background:${WP_COLORS[i % 4]};
        color:#fff;border:2px solid #fff;display:flex;align-items:center;justify-content:center;
        font-size:11px;font-weight:700;box-shadow:0 2px 6px rgba(0,0,0,.3)">${String.fromCharCode(65 + i)}</div>`,
      iconSize: [24, 24], iconAnchor: [12, 12],
    }),
  }).addTo(map)));
  map.fitBounds(routeLayers[1].getBounds(), { padding: [60, 60] });

  $("inc-km").textContent = `${route.total_dist_km} km · ${route.total_duration_min} phút`;
  $("inc-fare").textContent = fmtVnd(route.fare_vnd);
  $("inc-stops").innerHTML = wps.map((w, i) => `
    <div class="trip-row"><div class="wp" style="background:${WP_COLORS[i % 4]}">${String.fromCharCode(65 + i)}</div>
      <div>${w.name}</div></div>`).join("");
  $("trip-incoming").classList.remove("hidden");
  $("cta-area").classList.add("hidden");
  S.tripStep = 1;
}

function animateAlong(coords, ms) {
  if (moveTimer) clearInterval(moveTimer);
  let i = 0;
  const dt = Math.max(25, Math.floor(ms / coords.length));
  moveTimer = setInterval(() => {
    if (i < coords.length) { driverMarker.setLatLng(coords[i]); i++; }
    else clearInterval(moveTimer);
  }, dt);
}

function acceptTrip() {
  const r = S.activeRoute;
  $("trip-incoming").classList.add("hidden");
  $("trip-active").classList.remove("hidden");
  $("nav-state").textContent = "ĐANG ĐẾN ĐIỂM ĐÓN (OSRM)";
  $("nav-cust").textContent = r.trip.customer_name;
  $("nav-route").textContent = r.wps.map((w) => w.name.split(":")[1]).join(" ➔ ");
  $("nav-fare").textContent = fmtVnd(r.fare_vnd);
  $("nav-km").textContent = `${r.total_dist_km} km`;
  $("btn-nav-next").textContent = "ĐÃ ĐẾN NƠI ĐÓN KHÁCH";
  animateAlong(r.coords, 3200);
  S.tripStep = 2;
}

function navNext() {
  if (S.tripStep === 2) {
    $("nav-state").textContent = "ĐANG CHỞ KHÁCH";
    $("btn-nav-next").textContent = "HOÀN THÀNH CUỐC (DEMO)";
    animateAlong(S.activeRoute.coords, 4200);
    S.tripStep = 3;
  } else if (S.tripStep === 3) {
    const r = S.activeRoute;
    S.demoTrips.unshift({
      name: r.trip.customer_name, km: r.total_dist_km,
      fare: r.fare_vnd, src: r.source,
    });
    $("trip-history").innerHTML = S.demoTrips.map((t) => `
      <div class="row-item"><div><b>${t.name}</b><br>
        <span style="font-size:10.5px;color:var(--text-muted)">${t.km} km · nguồn ${t.src} · DEMO — không cộng vào payout</span></div>
        <div class="amt">${fmtVnd(t.fare)}</div></div>`).join("");
    $("trip-active").classList.add("hidden");
    $("cta-area").classList.remove("hidden");
    $("cta-text").textContent = "Tìm cuốc demo tiếp";
    clearRoute();
    S.tripStep = 0;
  }
}

/* ================= NAV + EVENTS ================= */
function switchScreen(id) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.add("hidden"));
  $(id).classList.remove("hidden");
  document.querySelectorAll(".nav-btn").forEach((b) =>
    b.classList.toggle("active", b.dataset.screen === id));
  if (id === "screen-now") setTimeout(() => map.invalidateSize(), 150);
}

function bindEvents() {
  document.querySelectorAll(".nav-btn").forEach((b) =>
    b.addEventListener("click", () => switchScreen(b.dataset.screen)));
  $("btn-menu").addEventListener("click", () => switchScreen("screen-settings"));
  $("bot-fab").addEventListener("click", () => {
    $("bot-sheet").classList.remove("hidden");
    $("bot-dot").classList.add("hidden");
    const h = document.querySelector("#advice-hours .chip.active");
    showAdvice(parseInt(h.dataset.h, 10));
  });
  $("btn-bot-close").addEventListener("click", () => $("bot-sheet").classList.add("hidden"));
  $("bot-sheet").addEventListener("click", (e) => {
    if (e.target === $("bot-sheet")) $("bot-sheet").classList.add("hidden");
  });
  document.querySelectorAll("#advice-hours .chip").forEach((c) =>
    c.addEventListener("click", () => {
      document.querySelectorAll("#advice-hours .chip").forEach((x) => x.classList.remove("active"));
      c.classList.add("active");
      showAdvice(parseInt(c.dataset.h, 10));
    }));
  $("btn-cta").addEventListener("click", () => {
    if (S.tripStep === 0) startIncomingTrip();
  });
  $("btn-decline").addEventListener("click", () => {
    $("trip-incoming").classList.add("hidden");
    $("cta-area").classList.remove("hidden");
    clearRoute(); S.tripStep = 0;
  });
  $("btn-accept").addEventListener("click", acceptTrip);
  $("btn-nav-next").addEventListener("click", navNext);
  $("btn-apply-profile").addEventListener("click", async () => {
    await loadProfile($("sel-driver").value, $("sel-date").value);
    switchScreen("screen-now");
  });
}

/* ================= INIT ================= */
(async function init() {
  initMap();
  bindEvents();
  const dv = await api.defaultView();
  await loadProfile(dv.driver_id, dv.date);
  await fillCatalog();
})();
