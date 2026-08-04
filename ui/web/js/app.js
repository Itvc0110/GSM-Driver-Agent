// Unified GSM Driver Web demo.
// The browser renders server-owned snapshots from an immutable simulator replay.  It does
// not construct trips, advance a cursor, calculate SOC/payout or ask an agent for advice.

import { api, fmtVnd } from "./api.js";

const S = {
  driverId: null, date: null, state: null, history: null, mapCtx: null, catalog: null,
  demo: {
    sessionId: null, actorId: null, stepVersion: 0, busy: false,
    ackedDisplayIds: new Set(), lastResponse: null,
  },
};

const $ = (id) => document.getElementById(id);
let map, demandLayer, stationLayer, routeLayers = [], driverMarker;

/* ================= MAP ================= */
function initMap() {
  map = L.map("map", { zoomControl: false }).setView([21.013, 105.827], 13.5);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 19, subdomains: "abcd", attribution: "© OSM · © CARTO",
  }).addTo(map);
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
  const seq = ["#c3ebee", "#95dbe0", "#5ec4cc", "#22a9b4", "#068c96"];
  for (const z of mc.demand_zones || []) {
    const c = seq[Math.min(seq.length - 1, Math.floor(z.intensity * seq.length))];
    L.circle([z.lat, z.lng], {
      radius: 220 + z.intensity * 420, color: c, weight: 1,
      fillColor: c, fillOpacity: 0.42,
    }).bindPopup(`Số đơn đặt (mô phỏng): cường độ ${(z.intensity * 100).toFixed(0)}%<br>
      <small>hex ${z.h3_index} · không đảm bảo đơn về tay bạn</small>`).addTo(demandLayer);
  }
  for (const st of mc.charging_stations || []) {
    L.circleMarker([st.lat, st.lng], {
      radius: 7, color: "#fff", weight: 2, fillColor: "#eda100", fillOpacity: 1,
    }).bindPopup(`<b>${st.name}</b><br><small>tủ đổi pin (OSM — vị trí thật)</small>`)
      .addTo(stationLayer);
  }
  const alertSlot = $("alert-slot");
  alertSlot.replaceChildren();
  for (const alert of mc.alerts || []) {
    const card = document.createElement("div");
    card.className = "alert-card";
    const icon = document.createElement("div");
    icon.className = "ico";
    icon.textContent = "📈";
    card.appendChild(icon);
    const body = document.createElement("div");
    const title = document.createElement("b");
    title.textContent = alert.title;
    body.appendChild(title);
    const message = document.createElement("p");
    message.textContent = alert.message;
    body.appendChild(message);
    card.appendChild(body);
    alertSlot.appendChild(card);
  }
}

/* ================= PROFILE SCREENS (read-only context) ================= */
async function loadProfile(driverId, date) {
  S.driverId = driverId;
  S.date = date;
  const [state, history, mapContext] = await Promise.all([
    api.state(driverId, date),
    api.history(driverId, date, 14),
    api.mapContext(date, 18, driverId),
  ]);
  S.state = state;
  S.history = history;
  S.mapCtx = mapContext;
  renderHeader();
  renderIncome();
  renderEv();
  renderSettings();
  renderMapContext(mapContext);
}

function renderHeader() {
  const money = S.state.money;
  $("pill-payout").textContent = `${fmtVnd(money.payout_vnd)} · ${S.date} · mô phỏng`;
  $("pill-trips").textContent = `${S.state.payout_summary.trips_count} cuốc`;
  const soc = S.state.soc_percent;
  const socElement = $("pill-soc");
  socElement.firstChild.nodeValue = `⚡ ${soc}% `;
  $("pill-soc-tag").hidden = S.state.soc_source !== "MOCK";
  socElement.classList.toggle("low", soc < 25);
  socElement.classList.toggle("is-mock", S.state.soc_source === "MOCK");
}

function renderIncome() {
  const money = S.state.money;
  $("inc-date").textContent = S.date;
  $("inc-payout").textContent = fmtVnd(money.payout_vnd);
  const breakdown = money.payout_breakdown || {};
  $("inc-breakdown").textContent =
    `cuốc ${fmtVnd(breakdown.trip_payout_vnd)} · mission ${fmtVnd(breakdown.mission_reward_vnd || 0)} · mô phỏng`;
  $("inc-gross").textContent = fmtVnd(money.gross_vnd);
  $("inc-net").textContent = "—";
  const days = S.history.days;
  Plotly.newPlot("chart-income", [{
    x: days.map((day) => day.date.slice(5)), y: days.map((day) => day.payout_vnd),
    type: "bar", marker: { color: "#2a78d6", cornerradius: 4 },
    hovertemplate: "%{x}: <b>%{y:,.0f}đ</b> payout<extra></extra>",
  }], {
    margin: { l: 44, r: 8, t: 8, b: 26 },
    font: { family: "Be Vietnam Pro, sans-serif", size: 10.5, color: "#52514e" },
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    yaxis: { gridcolor: "#e1e0d9", tickformat: "~s", zeroline: false },
    xaxis: { showgrid: false }, bargap: 0.35,
  }, { displayModeBar: false, responsive: true });
  $("income-rows").replaceChildren();
  for (const day of days.slice().reverse()) {
    const row = document.createElement("div");
    row.className = "row-item";
    addText(row, "div", `${day.date} · ${day.trips} cuốc · ${day.online_h}h online · nhận ${(day.acceptance_rate * 100).toFixed(0)}%`);
    addText(row, "div", `${fmtVnd(day.payout_vnd)} · gross ${fmtVnd(day.gross_vnd)}`);
    $("income-rows").appendChild(row);
  }
}

function renderEv() {
  $("ev-soc").textContent = `${S.state.soc_percent}%`;
  const applicable = S.state.vehicle_range_km_applicable;
  const low = S.state.vehicle_range_km_low;
  const high = S.state.vehicle_range_km_high;
  $("ev-range").textContent = applicable === false ? "— chưa có cơ sở" :
    (low != null && high != null ? `${low}–${high} km` : `${S.state.vehicle_range_km} km`);
  $("ev-range").title = S.state.vehicle_range_km_basis || "";
  $("ev-range-note").textContent = applicable === false
    ? "Đội xe này chưa có tham số tiêu hao trong hệ thống nên không hiển thị số."
    : "Dải suy từ mức tiêu hao của engine — đầu thấp thận trọng; không phải số thật.";
  const fleet = (S.catalog?.drivers || []).find((driver) => driver.driver_id === S.driverId)?.fleet || "";
  const names = {
    "bike-sim": "VinFast (bike điện)", "bike-rto": "VinFast (bike điện · RTO)",
    "car-platform": "VinFast VF5 (ô tô)", "car-employee": "VinFast (ô tô · nhân viên)",
    "car-premium": "VinFast VF8 Luxury (ô tô)",
  };
  $("ev-name").textContent = names[fleet] || "Xe mô phỏng";
  $("ev-plate").textContent = `Hồ sơ mô phỏng · ${S.driverId}`;
  $("station-rows").replaceChildren();
  for (const station of (S.mapCtx?.charging_stations || []).slice(0, 6)) {
    const row = document.createElement("div");
    row.className = "row-item";
    addText(row, "div", `🔋 ${station.name} · ${station.lat.toFixed(4)}, ${station.lng.toFixed(4)} · OSM`);
    $("station-rows").appendChild(row);
  }
}

function renderSettings() {
  const rating = S.state.rating || {};
  $("set-rating").textContent = rating.n
    ? `★ ${rating.avg} (${rating.n} lượt · ${(rating.five_rate * 100).toFixed(0)}% 5★)`
    : "chưa có lượt chấm";
  const missions = S.state.missions || [];
  $("mission-rows").replaceChildren();
  if (!missions.length) {
    addText($("mission-rows"), "span", "chưa có nhiệm vụ");
    return;
  }
  for (const mission of missions) {
    const row = document.createElement("div");
    row.style.padding = "7px 0";
    row.style.borderTop = "1px solid var(--border-hairline)";
    addText(row, "b", `${mission.title} — ${mission.progress}/${mission.target}`);
    $("mission-rows").appendChild(row);
  }
}

async function fillCatalog() {
  S.catalog = await api.catalog();
  $("prov-line").textContent =
    `data/mock/realdata-v1 · engine ${S.catalog.engine_commit} · nhãn ${S.catalog.label}`;
  const driverSelect = $("sel-driver");
  driverSelect.replaceChildren();
  for (const driver of S.catalog.drivers) {
    const option = document.createElement("option");
    option.value = driver.driver_id;
    option.textContent = `${driver.driver_id} (${driver.fleet})`;
    option.selected = driver.driver_id === S.driverId;
    driverSelect.appendChild(option);
  }
  const dateSelect = $("sel-date");
  dateSelect.replaceChildren();
  for (const date of S.catalog.dates) {
    const option = document.createElement("option");
    option.value = date;
    option.textContent = date;
    option.selected = date === S.date;
    dateSelect.appendChild(option);
  }
}

/* ================= CANONICAL REPLAY RENDER ================= */
function clearRoutes() {
  routeLayers.forEach((layer) => map.removeLayer(layer));
  routeLayers = [];
}

function addText(parent, tag, text, className = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = text == null ? "" : String(text);
  parent.appendChild(node);
  return node;
}

function renderDemoRoutes(response) {
  clearRoutes();
  for (const route of response.routes || []) {
    if (!Array.isArray(route.coords) || route.coords.length < 2) continue;
    const real = route.route_is_real_road === true;
    routeLayers.push(L.polyline(route.coords, {
      color: "#0f172a", weight: 9, opacity: 0.86,
    }).addTo(map));
    routeLayers.push(L.polyline(route.coords, {
      color: real ? "#00AFB9" : "#F59E0B", weight: 5,
      dashArray: real ? null : "8 8",
    }).addTo(map));
  }
  const trip = response.trip;
  const markerData = trip ? [
    {label: "P", point: trip.pickup, color: "#00AFB9"},
    {label: "D", point: trip.destination, color: "#F59E0B"},
  ] : [];
  for (const markerDataItem of markerData) {
    const point = markerDataItem.point || {};
    const lng = point.lng ?? point.lon;
    if (point.lat == null || lng == null) continue;
    const marker = L.marker([point.lat, lng], {
      icon: L.divIcon({
        html: `<div style="width:24px;height:24px;border-radius:50%;background:${markerDataItem.color};
          color:#fff;border:2px solid #fff;display:flex;align-items:center;justify-content:center;
          font-size:11px;font-weight:700;box-shadow:0 2px 6px rgba(0,0,0,.3)">${markerDataItem.label}</div>`,
        iconSize: [24, 24], iconAnchor: [12, 12],
      }),
    }).addTo(map);
    routeLayers.push(marker);
  }
  const lines = routeLayers.filter((layer) => typeof layer.getBounds === "function");
  if (lines.length) map.fitBounds(lines[lines.length - 1].getBounds(), {padding: [60, 60]});
  const route = (response.routes || [])[0];
  $("demo-route-note").textContent = route
    ? `${route.leg} · ${route.distance_km} km · ${route.duration_min} phút · ${route.source}`
      + (route.route_is_real_road ? " · đường thật" : " · fallback hình học")
    : "Không có leg route ở transition này.";
}

function renderDemoTrip(trip) {
  if (!trip) {
    $("demo-trip").textContent = "Transition này không có cuốc đang hiển thị.";
    return;
  }
  const pickup = trip.pickup || {};
  const destination = trip.destination || {};
  $("demo-trip").textContent =
    `Cuốc ${trip.trip_id} · ${trip.state} · ${trip.dist_km} km · gross ${fmtVnd(trip.gross_vnd)} `
    + `· P (${pickup.lat}, ${pickup.lon ?? pickup.lng}) → D (${destination.lat}, ${destination.lon ?? destination.lng})`;
}

function sendDisplayAck(item) {
  if (!item || S.demo.ackedDisplayIds.has(item.display_id)) return;
  S.demo.ackedDisplayIds.add(item.display_id);
  requestAnimationFrame(() => api.demoAdviceDisplay(
    S.demo.sessionId, item.checkpoint_id, {
      display_id: item.display_id,
      client_event_id: `web-mount-${item.display_id}`,
      mounted_at: new Date().toISOString(),
    }).catch((error) => console.warn("display ACK failed", error)));
}

function sendAdviceResponse(item, response) {
  if (!item) return;
  api.demoAdviceResponse(S.demo.sessionId, item.checkpoint_id, {
    display_id: item.display_id,
    client_event_id: `web-${response}-${item.display_id}`,
    response,
    occurred_at: new Date().toISOString(),
  }).catch((error) => console.warn("advice response failed", error));
}

function renderDemoAdvice(advice) {
  const slot = $("demo-advice");
  slot.replaceChildren();
  if (!advice || advice.status !== "ready" || !advice.items?.length) {
    addText(slot, "span", `Advice: im lặng (${advice?.silent?.reason_code || advice?.reason_code || "no_checkpoint"})`, "note");
    return;
  }
  const item = advice.items[0];
  addText(slot, "div", item.title, "tag");
  addText(slot, "div", item.summary, "advice-summary");
  const source = item.provenance?.is_mock ? "MOCK" : "LIVE";
  addText(slot, "div", `Nguồn: ${source} · presentation: ${advice.presentation_source || "template"}`, "note");
  if (item.action_window?.start && item.action_window?.end) {
    addText(slot, "div", `Khung: ${item.action_window.start} → ${item.action_window.end}`, "note");
  }
  const numbers = item.numbers || [];
  if (numbers.length) {
    const list = document.createElement("ul");
    for (const number of numbers) {
      const value = [number.value, number.unit].filter((part) => part != null).join(" ");
      addText(list, "li", `${value} · ${number.source || "source unknown"}`);
    }
    slot.appendChild(list);
  }
  const why = document.createElement("div");
  why.hidden = true;
  addText(why, "div", item.why, "note");
  slot.appendChild(why);
  const actions = document.createElement("div");
  actions.style.display = "flex";
  actions.style.gap = "6px";
  actions.style.marginTop = "6px";
  for (const response of ["accepted", "dismissed", "expanded"]) {
    const button = document.createElement("button");
    button.className = "btn ghost";
    button.style.margin = "0";
    button.textContent = response === "accepted" ? "Làm theo" : response === "dismissed" ? "Bỏ qua" : "Vì sao";
    button.addEventListener("click", () => {
      sendAdviceResponse(item, response);
      if (response === "expanded") why.hidden = !why.hidden;
    });
    actions.appendChild(button);
  }
  slot.appendChild(actions);
  sendDisplayAck(item);
}

function renderDemoStep(response) {
  S.demo.lastResponse = response;
  const driver = response.driver || {};
  const position = driver.position || {};
  if (position.lat != null && position.lng != null) {
    driverMarker.setLatLng([position.lat, position.lng]);
    map.panTo([position.lat, position.lng], {animate: false});
  }
  $("pill-payout").textContent = `${fmtVnd(driver.payout_vnd)} · ${response.provenance?.data_mode || "sim-engine"}`;
  $("pill-trips").textContent = `${driver.trips_done ?? 0} cuốc`;
  $("pill-soc").firstChild.nodeValue = `⚡ ${driver.soc_pct ?? "—"}% `;
  $("pill-soc-tag").hidden = false;
  $("demo-step-meta").textContent =
    `t=${response.simulation_time_min} phút · bước ${response.step_version} · ${response.transition.kind}`;
  renderDemoTrip(response.trip);
  renderDemoRoutes(response);
  renderDemoAdvice(response.advice);
  const history = $("trip-history");
  history.replaceChildren();
  for (const event of (response.timeline || []).slice().reverse().slice(0, 8)) {
    const row = document.createElement("div");
    row.className = "row-item";
    addText(row, "span", `${event.sequence}. t=${event.t_min} · ${event.kind}`);
    history.appendChild(row);
  }
}

async function createDemoSession() {
  if (S.demo.sessionId) return;
  $("demo-session-status").textContent = "Đang chạy simulator replay…";
  try {
    const created = await api.demoCreate(1000);
    S.demo.sessionId = created.session_id;
    S.demo.stepVersion = created.step_version;
    const picker = $("demo-actor");
    picker.replaceChildren();
    for (const actor of created.actors || []) {
      const option = document.createElement("option");
      option.value = actor.actor_id;
      option.textContent = `Actor ${actor.actor_id} · ${actor.archetype} · ${actor.fleet}`;
      picker.appendChild(option);
    }
    picker.disabled = false;
    $("demo-session-status").textContent = `Session ${created.session_id.slice(0, 8)} · chọn actor`;
  } catch (error) {
    $("demo-session-status").textContent = `Không tạo được session: ${error.message}`;
  }
}

async function selectDemoActor() {
  if (!S.demo.sessionId || !$("demo-actor").value) return;
  try {
    const selected = await api.demoSelect(S.demo.sessionId, Number($("demo-actor").value));
    S.demo.actorId = selected.actor_id;
    S.demo.stepVersion = selected.step_version;
    $("btn-demo-next").disabled = false;
    $("demo-session-status").textContent = `Actor ${S.demo.actorId} · replay sẵn sàng`;
  } catch (error) {
    $("demo-session-status").textContent = `Không chọn được actor: ${error.message}`;
  }
}

async function nextDemoStep() {
  if (!S.demo.sessionId || S.demo.actorId == null || S.demo.busy) return;
  S.demo.busy = true;
  $("btn-demo-next").disabled = true;
  try {
    const response = await api.demoStep(S.demo.sessionId, {
      client_step_id: `web-${S.demo.sessionId}-${S.demo.stepVersion}`,
      expected_step_version: S.demo.stepVersion,
    });
    S.demo.stepVersion = response.step_version;
    renderDemoStep(response);
    $("demo-session-status").textContent = response.provenance?.is_mock
      ? `Actor ${response.actor_id} · MOCK simulator replay`
      : `Actor ${response.actor_id} · replay`;
  } catch (error) {
    $("demo-session-status").textContent = `Next Step lỗi: ${error.message}`;
  } finally {
    S.demo.busy = false;
    $("btn-demo-next").disabled = false;
  }
}

/* ================= NAV + EVENTS ================= */
function switchScreen(id) {
  document.querySelectorAll(".screen").forEach((screen) => screen.classList.add("hidden"));
  $(id).classList.remove("hidden");
  document.querySelectorAll(".nav-btn").forEach((button) =>
    button.classList.toggle("active", button.dataset.screen === id));
  if (id === "screen-now") setTimeout(() => map.invalidateSize(), 150);
}

async function refreshAdherence() {
  try {
    const result = await api.adviceActions(S.driverId);
    const slot = $("adherence-rows");
    slot.replaceChildren();
    if (!result.actions?.length) {
      addText(slot, "span", "chưa có bản ghi");
      return;
    }
    for (const action of result.actions.slice(0, 12)) {
      const row = document.createElement("div");
      row.style.padding = "5px 0";
      row.style.borderTop = "1px solid var(--border-hairline)";
      addText(row, "span", `${action.action} · ${action.card_kind} · ${action.date} · ${action.advice_id}`);
      slot.appendChild(row);
    }
  } catch (error) {
    $("adherence-rows").textContent = `không đọc được nhật ký (${error.message})`;
  }
}

function bindEvents() {
  document.querySelectorAll(".nav-btn").forEach((button) =>
    button.addEventListener("click", () => switchScreen(button.dataset.screen)));
  $("btn-menu").addEventListener("click", () => switchScreen("screen-settings"));
  $("bot-fab").addEventListener("click", () => $("bot-sheet").classList.remove("hidden"));
  $("btn-bot-close").addEventListener("click", () => $("bot-sheet").classList.add("hidden"));
  $("bot-sheet").addEventListener("click", (event) => {
    if (event.target === $("bot-sheet")) $("bot-sheet").classList.add("hidden");
  });
  $("btn-day-demo").addEventListener("click", async () => {
    $("bot-sheet").classList.add("hidden");
    switchScreen("screen-now");
    await createDemoSession();
  });
  $("demo-actor").addEventListener("change", selectDemoActor);
  $("btn-demo-next").addEventListener("click", nextDemoStep);
  $("btn-adherence-refresh").addEventListener("click", refreshAdherence);
  $("btn-apply-profile").addEventListener("click", async () => {
    await loadProfile($("sel-driver").value, $("sel-date").value);
    switchScreen("screen-now");
  });
}

/* ================= INIT ================= */
(async function init() {
  initMap();
  bindEvents();
  try {
    const defaultView = await api.defaultView();
    await loadProfile(defaultView.driver_id, defaultView.date);
    await fillCatalog();
    await refreshAdherence();
    await createDemoSession();
  } catch (error) {
    $("demo-session-status").textContent = `Không khởi tạo được demo: ${error.message}`;
  }
})();
