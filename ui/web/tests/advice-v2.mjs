import assert from "node:assert/strict";

import {api} from "../js/api.js";
import {mountEventId, v2CardView} from "../js/cards.js";

let requested = "";
globalThis.fetch = async (url) => {
  requested = String(url);
  return {ok: true, status: 200, json: async () => ({status: "silent", items: []})};
};
await api.adviceV2({
  surface: "nudge", driverId: "d-1", date: "2026-08-03", nowMin: 540,
  shiftStartMin: 360, shiftEndMin: 1080, isDriving: false,
});
assert.match(requested, /surface=nudge/);
assert.doesNotMatch(requested, /topic|priority/);

const item = {
  title: "Server title", summary: "Server summary", why: "Server why",
  canonical_action: {code: "SWAP", label_id: "action.swap"},
  action_window: null, future_plan: [], numbers: [],
  provenance: {data_mode: "live", is_mock: false},
  confidence_band: "high", caveat_ids: [],
};
assert.deepEqual(v2CardView(item), {
  title: "Server title", summary: "Server summary", why: "Server why",
  action: item.canonical_action, actionWindow: null, futurePlan: [], numbers: [],
  provenance: item.provenance, confidenceBand: "high", caveatIds: [],
});
assert.equal(mountEventId("display-1"), "mount-display-1");
assert.equal(mountEventId("display-1"), "mount-display-1");

globalThis.fetch = async () => ({ok: false, status: 503, json: async () => ({})});
assert.deepEqual(await api.adviceV2({
  surface: "brief", driverId: "d-1", date: "2026-08-03", nowMin: 1,
  shiftStartMin: 0, shiftEndMin: 60, isDriving: false,
}), {status: "disabled", fallback: "v1"});
