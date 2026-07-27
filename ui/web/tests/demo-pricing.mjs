import assert from "node:assert/strict";

import { demoQuote } from "../js/api.js";

const quote = demoQuote({
  fare_vnd: 19_450,
  driver_payout_vnd: 14_588,
  driver_share: 0.75,
  fare_policy_version: "sim-policy-v0",
  data_mode: "synthetic",
  is_mock: true,
});

assert.deepEqual(quote, {
  grossText: "19.450đ",
  payoutText: "14.588đ",
  shareText: "75%",
  provenanceText: "sim-policy-v0 · MOCK",
});

assert.throws(
  () => demoQuote({fare_vnd: 19_450, driver_payout_vnd: 14_588, is_mock: false}),
  /MOCK/,
);
