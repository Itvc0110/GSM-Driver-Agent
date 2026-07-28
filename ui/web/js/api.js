// api.js — lớp gọi backend DUY NHẤT của web UI.
// UI không tính số nào: mọi con số đến từ các endpoint này (contract ui/contracts/*.json).

const BASE = "";  // cùng origin (FastAPI mount /app)

async function get(url) {
  const r = await fetch(BASE + url);
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
  advice: (driverId, date, nowMin) =>
    get(`/api/v1/advice?driver_id=${driverId}&date=${date}&now_min=${nowMin}`),
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
