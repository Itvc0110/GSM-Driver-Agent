// api.js — lớp gọi backend DUY NHẤT của web UI.
// UI không tính số nào: mọi con số đến từ các endpoint này (contract ui/contracts/*.json).

const BASE = "";  // cùng origin (FastAPI mount /app)

async function get(url) {
  const r = await fetch(BASE + url);
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}

async function post(url, body) {
  const r = await fetch(BASE + url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}

async function put(url, body) {
  const r = await fetch(BASE + url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}

export const api = {
  defaultView: () => get("/api/v1/driver/default-view"),
  catalog: () => get("/api/v1/driver/catalog"),
  state: (driverId, date) =>
    get(`/api/v1/driver/state?driver_id=${driverId}&date=${date}`),
  history: (driverId, date, days = 14) =>
    get(`/api/v1/driver/history?driver_id=${driverId}&date=${date}&days=${days}`),
  // ĐA-04/F3: `topic` PHẢI được gửi. Không gửi thì backend rơi về default 'bonus' và
  // cooldown/dismiss "theo chủ đề" gộp hết thành một chủ đề — bỏ qua nhắc buổi sáng sẽ
  // khoá miệng cả tổng kết ca. Đây là nửa client của "một luật".
  advice: (driverId, date, nowMin, topic, isDriving) =>
    get(`/api/v1/advice?driver_id=${driverId}&date=${date}&now_min=${nowMin}`
        + (topic ? `&topic=${encodeURIComponent(topic)}` : "")
        + (isDriving ? "&is_driving=true" : "")),
  adviceV2: async ({surface, driverId, date, nowMin, shiftStartMin, shiftEndMin, isDriving}) => {
    const query = new URLSearchParams({
      surface, driver_id: driverId, date, now_min: String(nowMin),
      shift_start_min: String(shiftStartMin), shift_end_min: String(shiftEndMin),
      is_driving: String(Boolean(isDriving)),
    });
    const r = await fetch(`${BASE}/api/v2/advice?${query}`);
    if (r.status === 503) return {status: "disabled", fallback: "v1"};
    if (!r.ok) throw new Error(`/api/v2/advice -> ${r.status}`);
    return r.json();
  },
  adviceV2Display: (checkpointId, body) =>
    post(`/api/v2/advice/${encodeURIComponent(checkpointId)}/display`, body),
  adviceV2Response: (checkpointId, body) =>
    post(`/api/v2/advice/${encodeURIComponent(checkpointId)}/response`, body),
  // Unified observer replay: the server owns actor selection, cursor and canonical state.
  demoCreate: (seed = 1000) => post("/api/v1/demo/sessions", {seed}),
  demoSelect: (sessionId, actorId) =>
    put(`/api/v1/demo/sessions/${encodeURIComponent(sessionId)}/driver`, {actor_id: actorId}),
  demoState: (sessionId) =>
    get(`/api/v1/demo/sessions/${encodeURIComponent(sessionId)}/state`),
  demoStep: (sessionId, body) =>
    post(`/api/v1/demo/sessions/${encodeURIComponent(sessionId)}/steps`, body),
  demoAdviceDisplay: (sessionId, checkpointId, body) =>
    post(`/api/v1/demo/sessions/${encodeURIComponent(sessionId)}/advice/${encodeURIComponent(checkpointId)}/display`, body),
  demoAdviceResponse: (sessionId, checkpointId, body) =>
    post(`/api/v1/demo/sessions/${encodeURIComponent(sessionId)}/advice/${encodeURIComponent(checkpointId)}/response`, body),
  mapContext: (date, hour, driverId) =>
    get(`/api/v1/map-context?date=${date}&hour=${hour}${driverId ? `&driver_id=${driverId}` : ""}`),
  tripStep: (idx, step) => get(`/api/v1/trip/step?trip_index=${idx}&step=${step}`),
  route: (waypoints) =>
    fetch(BASE + "/api/v1/routing/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ waypoints }),
    }).then((r) => r.json()),
  // UX-CARDS: đo adherence explicit
  adviceAction: (body) =>
    fetch(BASE + "/api/v1/advice/action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => r.json()),
  adviceActions: (driverId) =>
    get(`/api/v1/advice/actions${driverId ? `?driver_id=${driverId}` : ""}`),
};

export const fmtVnd = (v) =>
  v == null ? "—" : Math.round(v).toLocaleString("vi-VN") + "đ";

export function demoQuote(route) {
  if (route?.is_mock !== true || route?.data_mode !== "synthetic") {
    throw new Error("Cuốc demo chỉ được render từ quote MOCK synthetic");
  }
  return {
    grossText: fmtVnd(route.fare_vnd),
    payoutText: fmtVnd(route.driver_payout_vnd),
    shareText: `${Math.round(route.driver_share * 100)}%`,
    provenanceText: `${route.fare_policy_version} · MOCK`,
  };
}
