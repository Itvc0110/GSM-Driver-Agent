import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

import {api} from "../js/api.js";

const requests = [];
globalThis.fetch = async (url, options = {}) => {
  requests.push({url: String(url), options});
  return {ok: true, status: 200, json: async () => ({session_id: "s-1", step_version: 0})};
};

await api.demoCreate(1001);
await api.demoSelect("s-1", 7);
await api.demoState("s-1");
await api.demoStep("s-1", {client_step_id: "step-0", expected_step_version: 0});
await api.demoAdviceDisplay("s-1", "ckpt-1", {
  display_id: "display-1", client_event_id: "mount-1", mounted_at: "2026-08-04T10:00:00Z",
});
await api.demoAdviceResponse("s-1", "ckpt-1", {
  display_id: "display-1", client_event_id: "accept-1", response: "accepted",
  occurred_at: "2026-08-04T10:00:01Z",
});
await api.demoAdviceWhy("s-1", "ckpt-1", {
  display_id: "display-1", client_request_id: "why-1", expected_step_version: 1,
});

assert.equal(requests[0].options.method, "POST");
assert.match(requests[1].url, /\/driver$/);
assert.equal(requests[1].options.method, "PUT");
assert.match(requests[2].url, /\/state$/);
assert.match(requests[3].url, /\/steps$/);
assert.match(requests[4].url, /\/advice\/ckpt-1\/display$/);
assert.match(requests[5].url, /\/advice\/ckpt-1\/response$/);
assert.match(requests[6].url, /\/advice\/ckpt-1\/why$/);

const app = await readFile(new URL("../js/app.js", import.meta.url), "utf8");
assert.doesNotMatch(app, /tripStep|demoTrips|api\.tripStep|\/api\/v1\/trip\/step/);
assert.doesNotMatch(app, /innerHTML/);
assert.match(app, /requestDemoWhy/);
assert.doesNotMatch(app, /addText\(why, [^,]+, item\.why/);

const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
for (const id of ["demo-actor", "btn-demo-next", "demo-session-status", "demo-advice"]) {
  assert.match(html, new RegExp(`id="${id}"`));
}
