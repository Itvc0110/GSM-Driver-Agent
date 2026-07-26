// app.js — GSM Driver web app (Track UI U2 + UX-CARDS UPDATE-067).
// Nguyên tắc: UI CHỈ RENDER số từ backend (contract-first). Cuốc "demo" là mô phỏng
// interaction — cước demo KHÔNG được cộng vào payout (payout đến từ data mock).
// UX-CARDS (DIRECTIVES §12): advisor là PROACTIVE CARDS, không phải chatbot.

import { api, fmtVnd } from "./api.js";
import { Cards } from "./cards.js";

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
  const pill = $("pill-payout");
  // countup nhẹ cho stakeholder demo — số cuối luôn là số THẬT từ data
  const target = m.payout_vnd;
  const start = performance.now();
  const dur = 650;
  const tick = (t) => {
    const f = Math.min(1, (t - start) / dur);
    const v = Math.round(target * (0.4 + 0.6 * f));
    pill.innerHTML = `${fmtVnd(f >= 1 ? target : v)}
      <span class="sub">Thu nhập tài xế (payout) · ${S.date} · mô phỏng</span>`;
    if (f < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
  pill.classList.remove("bump"); void pill.offsetWidth; pill.classList.add("bump");
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

/* ================= HUB TRỢ LÝ (không chat — cards ở cards.js) ================= */
function renderCardHistory() {
  $("card-history").innerHTML = Cards.history.length
    ? Cards.history.map((h) => `<div style="padding:4px 0;border-top:1px solid var(--border-hairline)">
        ${h.at} · <b>${h.kind}</b> — ${h.title}</div>`).join("")
    : "chưa có";
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function runDayDemo() {
  // "Một ngày của tài xế" ~90s: brief → nhận cuốc demo → nudge (sau khi trả khách) → recap
  $("bot-sheet").classList.add("hidden");
  switchScreen("screen-now");
  await Cards.brief();
  await wait(7000);
  if (S.tripStep === 0) await startIncomingTrip();
  await wait(3000);
  if (S.tripStep === 1) acceptTrip();
  await wait(6000);
  if (S.tripStep === 2) navNext();          // đã đến điểm đón
  await wait(6000);
  if (S.tripStep === 3) navNext();          // hoàn thành → tự bắn nudge (xem navNext)
  await wait(8000);
  await Cards.recap();
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
    // UX-CARDS: nudge CHỈ sau khi trả khách xong (đang dừng — NHTSA); im lặng = không card
    Cards.nudge({ isDriving: false });
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
    renderCardHistory();
  });
  $("btn-bot-close").addEventListener("click", () => $("bot-sheet").classList.add("hidden"));
  $("bot-sheet").addEventListener("click", (e) => {
    if (e.target === $("bot-sheet")) $("bot-sheet").classList.add("hidden");
  });
  $("btn-day-demo").addEventListener("click", runDayDemo);
  $("btn-show-brief").addEventListener("click", () => { $("bot-sheet").classList.add("hidden"); Cards.brief(); });
  $("btn-show-nudge").addEventListener("click", () => { $("bot-sheet").classList.add("hidden"); Cards.nudge({ isDriving: S.tripStep >= 2 }); });
  $("btn-show-recap").addEventListener("click", () => { $("bot-sheet").classList.add("hidden"); Cards.recap(); });
  $("btn-adherence-refresh").addEventListener("click", refreshAdherence);
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

/* ================= ADHERENCE LOG (Cài đặt) ================= */
async function refreshAdherence() {
  try {
    const r = await api.adviceActions(S.driverId);
    $("adherence-rows").innerHTML = r.actions.length
      ? r.actions.slice(0, 12).map((a) => `
        <div style="padding:5px 0;border-top:1px solid var(--border-hairline)">
          <b>${{ followed: "✅ Làm theo", dismissed: "✖ Bỏ qua", expanded: "？Vì sao" }[a.action] || a.action}</b>
          · ${a.card_kind} · ${a.date}
          <span style="color:var(--text-muted);font-size:10.5px">· ${a.advice_id}</span></div>`).join("")
      : "chưa có bản ghi";
  } catch (e) {
    $("adherence-rows").textContent = `không đọc được nhật ký (${e.message})`;
  }
}

/* ================= INIT ================= */
(async function init() {
  initMap();
  bindEvents();
  const dv = await api.defaultView();
  Cards.init($("card-stack"), {
    profile: () => ({ driverId: S.driverId, date: S.date }),
    state: () => S.state,
  });
  await loadProfile(dv.driver_id, dv.date);
  await fillCatalog();
  await refreshAdherence();
  Cards.brief();   // F1: brief tự hiện khi mở app (không cần bấm)
})();
