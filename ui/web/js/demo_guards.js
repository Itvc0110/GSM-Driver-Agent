// Pure replay guards shared by the demo renderer and Node smoke tests.

export function isStaleStep(currentVersion, responseVersion) {
  return Number(responseVersion) < Number(currentVersion);
}

export function beginDisplayAck(state, displayId) {
  if (!displayId || state.acked.has(displayId) || state.pending.has(displayId)) return false;
  state.pending.add(displayId);
  return true;
}

export function completeDisplayAck(state, displayId, succeeded) {
  state.pending.delete(displayId);
  if (succeeded) state.acked.add(displayId);
}
