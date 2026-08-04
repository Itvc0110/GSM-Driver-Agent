import assert from "node:assert/strict";
import {beginDisplayAck, completeDisplayAck, isStaleStep} from "../js/demo_guards.js";

assert.equal(isStaleStep(3, 2), true);
assert.equal(isStaleStep(3, 3), false);
assert.equal(isStaleStep(3, 4), false);

const state = {acked: new Set(), pending: new Set()};
assert.equal(beginDisplayAck(state, "display-1"), true);
assert.equal(beginDisplayAck(state, "display-1"), false);
completeDisplayAck(state, "display-1", false);
assert.equal(beginDisplayAck(state, "display-1"), true);
completeDisplayAck(state, "display-1", true);
assert.equal(beginDisplayAck(state, "display-1"), false);
