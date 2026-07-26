// mo-phong.js — Khu Mô phỏng (Track UI U3).
// UI chỉ ĐỌC JSON engine (replay/journey/ab/sweep) — không tính lại số nào.
// Màu series theo entity (design-tokens dataviz.categorical_light — validated).

const KIND_COLORS = {
  on_trip: "#1baf7a", enroute: "#2a78d6", charge: "#eda100",
  rest: "#4a3aa7", relocate: "#e87ba4", idle: "#9aa4ab",
};
const KIND_VI = {
  on_trip: "Chở khách", enroute: "Đi đón", charge: "Đổi pin/sạc",
  rest: "Nghỉ", relocate: "Dịch chuyển", idle: "Chờ đơn",
};
const PLOTLY_BASE = {
  font: { family: "Be Vietnam Pro, sans-serif", size: 11, color: "#52514e" },
  paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
};
const fmtVnd = (v) => (v == null ? "—" : Math.round(v).toLocaleString("vi-VN") + "đ");
const hhmm = (m) => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(Math.floor(m % 60)).padStart(2, "0")}`;
const $ = (id) => document.getElementById(id);
const get = async (url) => {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
};

const S = {
  seed: 1000, replay: null, runInfo: null, playTimer: null,
  speed: 1,                 // ×1/×4/×16 — (step phút, interval ms) trong SPEEDS
  events: [],               // events gộp từ top-6 tài xế bận nhất (đã sort theo t)
  feedIdx: 0,               // con trỏ feed: đã đẩy tới event thứ mấy
};
const SPEEDS = { 1: { step: 1, ms: 150 }, 4: { step: 4, ms: 120 }, 16: { step: 16, ms: 90 } };
const EV_COLORS = { advice: "#7fd4db", mission_completed: "#eda100",
                    day_bonus: "#58c977", newbie_bonus: "#9085e9", trip_rated: "#9fb3bd" };
const EV_VI = { advice: "advice", mission_completed: "mission", day_bonus: "thưởng ngày",
                newbie_bonus: "tân binh", trip_rated: "chấm sao" };

/* ================= REPLAY ================= */
let map, actorLayer, stationLayer;

function initMap() {
  map = L.map("replay-map").setView([21.013, 105.822], 13.5);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 19, subdomains: "abcd", attribution: "© OSM · © CARTO" }).addTo(map);
  actorLayer = L.layerGroup().addTo(map);
  stationLayer = L.layerGroup().addTo(map);
}

function drawStations(stations) {
  stationLayer.clearLayers();
  for (const st of stations) {
    L.circleMarker([st.lat, st.lng], {
      radius: 6, color: "#fff", weight: 2, fillColor: "#eda100", fillOpacity: 1,
    }).bindTooltip(st.name).addTo(stationLayer);
  }
}

// vị trí actor tại phút t: nội suy tuyến tính trong leg chứa t
function posAt(legs, t) {
  let lo = 0, hi = legs.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1, g = legs[mid];
    if (t < g.t0_min) hi = mid - 1;
    else if (t > g.t1_min) lo = mid + 1;
    else {
      const f = g.t1_min > g.t0_min ? (t - g.t0_min) / (g.t1_min - g.t0_min) : 0;
      return {
        lat: g.from[0] + (g.to[0] - g.from[0]) * f,
        lng: g.from[1] + (g.to[1] - g.from[1]) * f,
        kind: g.kind,
      };
    }
  }
  return null; // ngoài mọi leg (offline)
}

let flashActor = null;      // actor vừa có sự kiện → vẽ ring nổi

function renderFrame(t) {
  $("clock").textContent = hhmm(t);
  if (!S.replay) return;
  actorLayer.clearLayers();
  let active = 0;
  for (const a of S.replay.actors) {
    const p = posAt(a.legs, t);
    if (!p) continue;
    active++;
    const hot = flashActor === a.actor_id;
    L.circleMarker([p.lat, p.lng], {
      radius: hot ? 9 : 5, weight: hot ? 3 : 1.5,
      color: hot ? "#00AFB9" : "#ffffff",
      fillColor: KIND_COLORS[p.kind] || "#9aa4ab", fillOpacity: 0.95,
    }).bindTooltip(`d-${a.actor_id} · ${a.archetype} · ${KIND_VI[p.kind] || p.kind}`)
      .addTo(actorLayer);
  }
  $("active-count").textContent = `${active}/${S.replay.actors.length} tài xế trên đường`;
}

// feed CrewAI-terminal: đẩy dòng cho mọi event trong (tPrev, tNow]
function pumpFeed(tPrev, tNow) {
  const feed = $("event-feed");
  while (S.feedIdx < S.events.length && S.events[S.feedIdx].t_min <= tNow) {
    const e = S.events[S.feedIdx++];
    if (e.t_min <= tPrev) continue;
    const line = document.createElement("div");
    line.className = "fl";
    line.innerHTML = `<span class="t">[${hhmm(e.t_min)}]</span>
      <span class="who">d-${e.actor_id}</span>
      <span style="color:${EV_COLORS[e.kind] || "#d7e2e8"}">${EV_VI[e.kind] || e.kind}</span>
      · ${e.label}`;
    feed.appendChild(line);
    while (feed.children.length > 40) feed.firstChild.remove();
    feed.scrollTop = feed.scrollHeight;
    flashActor = e.actor_id;
    setTimeout(() => { if (flashActor === e.actor_id) flashActor = null; }, 1800);
  }
}

function seekFeed(t) {
  // slider kéo tay / nhảy: đặt lại con trỏ feed về vị trí t (không dội lại cả quá khứ)
  S.feedIdx = S.events.findIndex((e) => e.t_min > t);
  if (S.feedIdx < 0) S.feedIdx = S.events.length;
}

function togglePlay() {
  if (S.playTimer) {
    clearInterval(S.playTimer); S.playTimer = null;
    $("btn-play").textContent = "▶ Chạy";
    return;
  }
  $("btn-play").textContent = "⏸ Dừng";
  startTimer();
}

function startTimer() {
  if (S.playTimer) clearInterval(S.playTimer);
  const { step, ms } = SPEEDS[S.speed];
  S.playTimer = setInterval(() => {
    const sl = $("time-slider");
    const prev = parseInt(sl.value, 10);
    let t = prev + step;
    if (t > parseInt(sl.max, 10)) { t = parseInt(sl.min, 10); seekFeed(t); }
    sl.value = t;
    renderFrame(t);
    pumpFeed(prev, t);
  }, ms);
}

function jumpNextEvent() {
  const sl = $("time-slider");
  const t = parseInt(sl.value, 10);
  const nxt = S.events.find((e) => e.t_min > t);
  if (!nxt) return;
  sl.value = nxt.t_min;
  seekFeed(nxt.t_min - 1);
  renderFrame(nxt.t_min);
  pumpFeed(nxt.t_min - 1, nxt.t_min);
}

async function loadEvents() {
  // gộp events của top-6 tài xế bận nhất (endpoint journey sẵn có; run đã cache nên rẻ)
  const top = (S.runInfo?.actors || []).slice(0, 6);
  const js = await Promise.all(top.map((a) =>
    get(`/api/v1/sim/journey?seed=${S.seed}&actor_id=${a.actor_id}`).catch(() => null)));
  S.events = js.filter(Boolean)
    .flatMap((j) => j.events.map((e) => ({ ...e, actor_id: j.actor_id })))
    .sort((a, b) => a.t_min - b.t_min);
  S.feedIdx = 0;
  $("event-feed").innerHTML =
    `<div class="fl"><span class="t">[--:--]</span> nạp ${S.events.length} sự kiện từ 6 tài xế bận nhất — bấm ▶</div>`;
}

/* ================= JOURNEY ================= */
async function loadJourney(actorId) {
  const j = await get(`/api/v1/sim/journey?seed=${S.seed}&actor_id=${actorId}`);
  const m = j.metrics;
  $("j-kpis").innerHTML = [
    ["Payout (4 nguồn)", fmtVnd(m.payout_vnd)],
    ["Cuốc", fmtVnd(m.trip_payout_vnd)],
    ["Thưởng ngày", fmtVnd(m.day_bonus_vnd)],
    ["Mission", fmtVnd(m.mission_reward_vnd)],
    ["Tân binh", fmtVnd(m.newbie_vnd)],
    ["Cuốc xong / offer", `${m.trips_completed ?? "–"} / ${m.offers ?? "–"}`],
  ].map(([k, v]) => `<div class="card" style="box-shadow:none;border:1px solid var(--border-hairline)">
      <h3>${k}</h3><div class="big" style="font-size:16px">${v}</div></div>`).join("");

  // Gantt: mỗi kind một trace bar ngang (base=t0, x=duration) — đúng cách dashboard làm
  const kinds = Object.keys(KIND_COLORS);
  const traces = kinds.map((k) => {
    const segs = j.segments.filter((s) => s.kind === k);
    return {
      type: "bar", orientation: "h", name: KIND_VI[k],
      y: segs.map(() => ""), base: segs.map((s) => s.t0_min),
      x: segs.map((s) => s.t1_min - s.t0_min),
      marker: { color: KIND_COLORS[k] },
      hovertemplate: segs.map((s) =>
        `${KIND_VI[k]}: ${hhmm(s.t0_min)}–${hhmm(s.t1_min)}<extra></extra>`),
      showlegend: segs.length > 0,
    };
  });
  Plotly.newPlot("chart-gantt", traces, {
    ...PLOTLY_BASE, barmode: "stack", bargap: 0,
    margin: { l: 8, r: 8, t: 8, b: 28 },
    xaxis: { range: [280, 1440], tickvals: [360, 600, 840, 1080, 1320],
             ticktext: ["6h", "10h", "14h", "18h", "22h"], showgrid: false },
    yaxis: { visible: false },
    legend: { orientation: "h", y: -0.25 },
  }, { displayModeBar: false, responsive: true });

  // Income curve (step) + event markers
  const xs = j.income_curve.map((p) => p[0]), ys = j.income_curve.map((p) => p[1]);
  const evColors = { advice: "#00AFB9", mission_completed: "#eda100",
                     day_bonus: "#0ca30c", newbie_bonus: "#4a3aa7" };
  const shapes = j.events.map((e) => ({
    type: "line", x0: e.t_min, x1: e.t_min, y0: 0, y1: 1, yref: "paper",
    line: { color: evColors[e.kind] || "#9aa4ab", width: 1, dash: "dot" },
  }));
  Plotly.newPlot("chart-income", [{
    x: xs, y: ys, mode: "lines", line: { shape: "hv", color: "#068c96", width: 2 },
    hovertemplate: "phút %{x:.0f} — <b>%{y:,.0f}đ</b><extra></extra>",
    name: "payout cộng dồn",
  }, {
    x: j.events.map((e) => e.t_min), y: j.events.map(() => Math.max(...ys, 1) * 0.05),
    mode: "markers", marker: { size: 8, symbol: "diamond",
      color: j.events.map((e) => evColors[e.kind] || "#9aa4ab") },
    text: j.events.map((e) => e.label), hovertemplate: "%{text}<extra></extra>",
    name: "sự kiện", showlegend: false,
  }], {
    ...PLOTLY_BASE, shapes,
    margin: { l: 56, r: 8, t: 8, b: 28 },
    xaxis: { range: [280, 1440], tickvals: [360, 600, 840, 1080, 1320],
             ticktext: ["6h", "10h", "14h", "18h", "22h"], showgrid: false },
    yaxis: { gridcolor: "#e1e0d9", tickformat: "~s", zeroline: false },
    showlegend: false,
  }, { displayModeBar: false, responsive: true });

  $("tbl-offers").innerHTML = `
    <tr><th>Giờ</th><th>Quyết định</th><th>Lý do</th><th>Kết cục</th><th>Giá (gross)</th></tr>`
    + j.offers.map((o) => `
    <tr><td>${hhmm(o.t_min)}</td>
        <td>${o.accepted ? "✅ nhận" : "✖ từ chối"}</td>
        <td>${o.reason}</td>
        <td>${o.completed == null ? "–" : o.completed ? "hoàn thành" : "huỷ sau nhận"}</td>
        <td>${fmtVnd(o.fare_vnd)}</td></tr>`).join("");
}

/* ================= A/B ================= */
async function runAB() {
  const body = $("ab-body");
  $("btn-ab").disabled = true;
  body.innerHTML = `<div class="silent-box">Đang chạy 2 thế giới cùng seed ${S.seed}… (~30-60s)</div>`;
  try {
    const ab = await get(`/api/v1/sim/ab?seed=${S.seed}`);
    $("ab-warning").textContent = ab.warning_text;
    const t = ab.target_actors[0];
    const g = ab.guardrail;
    body.innerHTML = `
      <div class="kpi-row">
        <div class="card" style="box-shadow:none;border:1px solid var(--border-hairline)">
          <h3>Δ payout (B − A)</h3>
          <div class="big" style="color:${t.delta_vnd >= 0 ? "var(--status-good)" : "var(--status-critical)"}">
            ${t.delta_vnd >= 0 ? "+" : ""}${fmtVnd(t.delta_vnd)}</div>
          <div class="note">d-${t.actor_id} · ${t.archetype} · seed ${ab.seed}</div></div>
        <div class="card" style="box-shadow:none;border:1px solid var(--border-hairline)">
          <h3>A (tự làm)</h3><div class="big">${fmtVnd(t.payout_a_vnd)}</div></div>
        <div class="card" style="box-shadow:none;border:1px solid var(--border-hairline)">
          <h3>B (theo trợ lý)</h3><div class="big">${fmtVnd(t.payout_b_vnd)}</div>
          <div class="note">${ab.delta.advice_events} sự kiện advice</div></div>
        <div class="card" style="box-shadow:none;border:1px solid var(--border-hairline)">
          <h3>Guardrail hệ thống (quan sát)</h3>
          <div class="big">${g.ok === null ? "— (1 seed)" : g.ok ? "✅ ổn" : "⚠ xấu đi"}</div>
          <div class="note">worst-cell Δ served: ${g.worst_cell_delta_served}
            · cell bị soi: ${g.flagged_cells.length}
            · phán quyết thật: tab Độ nhạy (30 seed)</div></div>
      </div>
      <div class="note" style="font-size:11px;color:var(--text-muted);margin-top:8px">
        Kênh: ${ab.channel} · CRN cùng seed — khác biệt duy nhất là advice.</div>`;
    Plotly.newPlot("chart-ab", [
      { x: ab.income_curves.a.map((p) => p[0]), y: ab.income_curves.a.map((p) => p[1]),
        mode: "lines", name: "A — tự làm", line: { shape: "hv", color: "#9aa4ab", width: 2 } },
      { x: ab.income_curves.b.map((p) => p[0]), y: ab.income_curves.b.map((p) => p[1]),
        mode: "lines", name: "B — theo trợ lý", line: { shape: "hv", color: "#068c96", width: 2.5 } },
    ], {
      ...PLOTLY_BASE,
      margin: { l: 56, r: 8, t: 8, b: 28 },
      xaxis: { tickvals: [360, 600, 840, 1080, 1320],
               ticktext: ["6h", "10h", "14h", "18h", "22h"], showgrid: false },
      yaxis: { gridcolor: "#e1e0d9", tickformat: "~s" },
      legend: { orientation: "h", y: 1.12 },
    }, { displayModeBar: false, responsive: true });
  } catch (e) {
    body.innerHTML = `<div class="silent-box">Lỗi chạy A/B: ${e.message}</div>`;
  } finally {
    $("btn-ab").disabled = false;
  }
}

/* ================= SWEEP ================= */
async function loadSweep() {
  const panel = $("sweep-panels");
  try {
    const sw = await get("/api/v1/sim/sweep");
    panel.innerHTML = "";
    if (sw._meta?.STALE) {
      panel.insertAdjacentHTML("beforeend",
        `<div class="warn-strip">⚠ Artifact sweep này STALE — ${sw._meta.note}</div>`);
    }
    for (const [arch, data] of Object.entries(sw)) {
      if (arch.startsWith("_")) continue;
      if (!data.cells) {
        panel.insertAdjacentHTML("beforeend", `<div class="section-label">${arch}</div>
          <div class="note" style="font-size:12px">${JSON.stringify(data)}</div>`);
        continue;
      }
      const adhs = [...new Set(Object.keys(data.cells).map((k) => k.match(/adh=([\d.]+)/)[1]))].sort();
      const lifts = [...new Set(Object.keys(data.cells).map((k) => k.match(/lift=([\d.]+)/)[1]))].sort();
      const z = adhs.map((a) => lifts.map((l) => data.cells[`adh=${a}|lift=${l}`]?.delta_mean ?? null));
      const txt = adhs.map((a) => lifts.map((l) => {
        const c = data.cells[`adh=${a}|lift=${l}`];
        return c ? `${Math.round(c.delta_mean / 1000)}k${c.significant ? " ✳" : ""}` : "";
      }));
      const zmax = Math.max(...z.flat().map((v) => Math.abs(v ?? 0)), 1);
      const div = document.createElement("div");
      div.innerHTML = `<div class="section-label">${arch} — Δ payout TB (VND, 30 seed/ô); tài xế đích d-${data.target_actor ?? "?"}</div>
        <div id="hm-${arch}" style="height:${90 + adhs.length * 52}px"></div>`;
      panel.appendChild(div);
      // diverging đỏ↔cyan, midpoint XÁM trung tính tại 0 (dataviz: không hue ở 0)
      Plotly.newPlot(`hm-${arch}`, [{
        type: "heatmap", z, x: lifts.map((l) => `lift ${l}`), y: adhs.map((a) => `adh ${a}`),
        zmin: -zmax, zmax, text: txt, texttemplate: "%{text}",
        colorscale: [[0, "#c73a3a"], [0.5, "#eef0f1"], [1, "#046e77"]],
        colorbar: { thickness: 10, tickformat: "~s" },
        hovertemplate: "%{y} · %{x}: <b>%{z:,.0f}đ</b><extra></extra>",
      }], {
        ...PLOTLY_BASE, margin: { l: 76, r: 8, t: 4, b: 30 },
      }, { displayModeBar: false, responsive: true });
    }
  } catch (e) {
    panel.innerHTML = `<div class="silent-box">Chưa có file sweep (${e.message})</div>`;
  }
}

/* ================= LOAD + NAV ================= */
async function loadSeedDay() {
  const seed = parseInt($("seed").value, 10);
  S.seed = seed;
  $("btn-load").textContent = "Đang chạy engine…";
  $("btn-load").disabled = true;
  try {
    const [replay, runInfo] = await Promise.all([
      get(`/api/v1/sim/replay?seed=${seed}`),
      get(`/api/v1/sim/run?seed=${seed}`),
    ]);
    S.replay = replay; S.runInfo = runInfo;
    drawStations(replay.stations);
    const sl = $("time-slider");
    sl.min = replay.t_min_range[0]; sl.max = replay.t_min_range[1];
    renderFrame(parseInt(sl.value, 10));
    $("sel-actor").innerHTML = runInfo.actors.slice(0, 40).map((a) =>
      `<option value="${a.actor_id}">d-${a.actor_id} · ${a.archetype} · ${a.trips} cuốc · ${fmtVnd(a.payout_vnd)}</option>`).join("");
    await loadEvents();
    await loadJourney(runInfo.actors[0].actor_id);
  } finally {
    $("btn-load").textContent = "Nạp ngày sim";
    $("btn-load").disabled = false;
  }
}

document.querySelectorAll(".tabs .chip").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".tabs .chip").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    b.classList.add("active");
    $(b.dataset.tab).classList.add("active");
    if (b.dataset.tab === "tab-replay") setTimeout(() => map.invalidateSize(), 120);
  }));

$("btn-play").addEventListener("click", togglePlay);
$("btn-next-event").addEventListener("click", jumpNextEvent);
document.querySelectorAll(".speed-chip").forEach((c) =>
  c.addEventListener("click", () => {
    document.querySelectorAll(".speed-chip").forEach((x) => x.classList.remove("active"));
    c.classList.add("active");
    S.speed = parseInt(c.dataset.speed, 10);
    if (S.playTimer) startTimer();   // đang chạy thì đổi nhịp ngay
  }));
$("time-slider").addEventListener("input", (e) => {
  const t = parseInt(e.target.value, 10);
  seekFeed(t);
  renderFrame(t);
});
$("btn-load").addEventListener("click", loadSeedDay);
$("btn-ab").addEventListener("click", runAB);
$("sel-actor").addEventListener("change", (e) => loadJourney(parseInt(e.target.value, 10)));

initMap();
loadSweep();
loadSeedDay();
