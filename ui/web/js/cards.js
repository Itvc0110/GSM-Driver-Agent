// cards.js — Proactive Cards (DIRECTIVES §12): advisor KHÔNG phải chatbot.
// 3 loại card: brief (trước ca, F1) · nudge (trong ca — CHỈ khi không chở khách, NHTSA) ·
// recap (sau ca, F3). Mỗi card: Làm theo / Bỏ qua / Vì sao → POST /api/v1/advice/action.
// Nguyên tắc giữ nguyên: card chỉ TRÌNH BÀY số từ backend; advisor im lặng = KHÔNG card;
// không nudge kiểu ép-chạy khi solver bảo infeasible (bài học đạo đức nudge Uber).

import { api, fmtVnd } from "./api.js";

const KIND_HOURS = { brief: 9 * 60, nudge: 14 * 60, recap: 21 * 60 + 30 };
// ĐA-04/F3: chủ đề nhịp gửi kèm mọi request. TẠM ánh xạ theo LOẠI CARD vì item của backend
// hôm nay chưa mang chủ đề thật (ĐA-06 `AdviceEnvelopeV2 = list[card]` mới có trường đó —
// duyệt rồi, chưa implement). Ánh xạ này là PLACEHOLDER có nhãn, KHÔNG phải taxonomy chốt:
// nó chỉ bảo đảm ba loại card không dùng chung một cooldown, chứ chưa phân biệt "nhắc thưởng"
// với "nhắc nghỉ" trong cùng một loại card.
const KIND_TOPIC = { brief: "brief", nudge: "nudge", recap: "recap" };
const KIND_LABEL = { brief: "Trước ca", nudge: "Trong ca", recap: "Tổng kết ca" };
const KIND_ICON = { brief: "🌅", nudge: "⚡", recap: "🌙" };

const eventId = () => globalThis.crypto?.randomUUID?.()
  || `client-${Date.now()}-${Math.random().toString(16).slice(2)}`;

export const mountEventId = (displayId) => `mount-${displayId}`;

// Dynamic advice, provenance and route text must never be interpreted as markup.
// Keep the legacy card renderer on the same safe DOM path as the demo renderer.
const node = (tag, className, value) => {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (value !== undefined && value !== null) el.textContent = String(value);
  return el;
};

const append = (parent, ...children) => {
  children.filter(Boolean).forEach((child) => parent.appendChild(child));
  return parent;
};

const numberValue = (number) => number?.unit === "vnd"
  ? fmtVnd(number.value)
  : `${number?.value ?? ""}${number?.unit ? ` ${number.unit}` : ""}`;

const numberTable = (numbers, {useName = false} = {}) => {
  const table = node("table", "num-table");
  const body = node("tbody");
  (numbers || []).forEach((number) => {
    const row = node("tr");
    append(row,
      node("td", null, useName
        ? String(number.name || number.id || "").replaceAll("_", " ")
        : number.id),
      node("td", null, numberValue(number)),
      node("td", null, number.source));
    body.appendChild(row);
  });
  table.appendChild(body);
  return table;
};

export function v2CardView(item) {
  return {
    title: item.title,
    summary: item.summary,
    why: item.why,
    action: item.canonical_action,
    actionWindow: item.action_window,
    futurePlan: item.future_plan,
    numbers: item.numbers,
    provenance: item.provenance,
    confidenceBand: item.confidence_band,
    caveatIds: item.caveat_ids,
  };
}

export const Cards = {
  mount: null,
  ctx: null,          // { profile: () => ({driverId, date}), state: () => driverState }
  history: [],        // card đã hiện trong phiên (cho hub)

  init(mountEl, ctx) {
    this.mount = mountEl;
    this.ctx = ctx;
  },

  async logAction(adviceId, action, kind) {
    const { driverId, date } = this.ctx.profile();
    try {
      await api.adviceAction({
        advice_id: adviceId, driver_id: driverId, date,
        action, card_kind: kind, at_min: KIND_HOURS[kind],
        topic: KIND_TOPIC[kind] || kind,
      });
    } catch (e) { console.warn("log action fail", e); }
  },

  async _v2(kind, isDriving = false) {
    const { driverId, date } = this.ctx.profile();
    return api.adviceV2({
      surface: kind, driverId, date, nowMin: KIND_HOURS[kind],
      shiftStartMin: 6 * 60, shiftEndMin: 22 * 60, isDriving,
    });
  },

  _renderV2(item) {
    const view = v2CardView(item);
    const el = node("div", "adv-card enter");
    const head = node("div", "adv-head");
    const kind = node("span", "adv-kind",
      `${KIND_ICON[item.surface] || ""} ${KIND_LABEL[item.surface] || item.surface} · Trợ Lý Xanh`);
    append(head, kind);
    const mock = view.provenance?.is_mock === true;
    if (mock) head.appendChild(node("span", "mock-badge", "mô phỏng"));
    const why = node("div", "adv-why hidden");
    append(why, node("p", null, view.why), numberTable(view.numbers));
    const provenance = view.provenance || {};
    why.appendChild(node("div", "meta",
      `${view.confidenceBand || ""} · ${provenance.data_mode || ""} · ${provenance.policy_version || ""}`));
    const actions = node("div", "adv-actions");
    append(actions,
      node("button", "adv-btn follow", "✅ Làm theo"),
      node("button", "adv-btn dismiss", "✖ Bỏ qua"),
      node("button", "adv-btn why", "？Vì sao"));
    const action = view.action?.code || "NO_ACTION";
    append(el, head, node("b", "adv-title", view.title),
      node("p", "adv-msg", `Hành động hiện tại: ${action}`),
      node("p", "adv-msg", view.summary), why, actions);
    while (this.mount.children.length >= 2) this.mount.firstChild.remove();
    this.mount.appendChild(el);

    // Mounted ACK happens only after the card is present in the DOM.
    api.adviceV2Display(item.checkpoint_id, {
      display_id: item.display_id, client_event_id: mountEventId(item.display_id),
      mounted_at: new Date().toISOString(),
    }).catch((e) => console.warn("v2 display ack fail", e));

    const respond = (response) => api.adviceV2Response(item.checkpoint_id, {
      display_id: item.display_id, client_event_id: eventId(), response,
      occurred_at: new Date().toISOString(),
    }).catch((e) => console.warn("v2 response fail", e));
    el.querySelector(".follow").addEventListener("click", () => {
      respond("accepted"); el.classList.add("followed");
      setTimeout(() => el.remove(), 650);
    });
    el.querySelector(".dismiss").addEventListener("click", () => {
      respond("dismissed"); el.classList.add("dismissed");
      setTimeout(() => el.remove(), 650);
    });
    el.querySelector(".why").addEventListener("click", () => {
      el.querySelector(".adv-why").classList.toggle("hidden");
      respond("expanded");
    });
    this.history.push({kind: item.surface, title: view.title,
                       at: new Date().toLocaleTimeString("vi-VN")});
    return el;
  },

  // L4-07 (2026-07-31): card IM LẶNG không có quyết định thật để hành động lên. Trước đây
  // nó vẫn vẽ "Làm theo"/"Bỏ qua" với advice_id BỊA (`brief-{date}`) ⇒ một cú bấm tạo
  // decision+followed cho lời khuyên advisor CHƯA TỪNG ĐƯA ⇒ adherence sản phẩm 100% giả.
  // Backend nay cũng từ chối (422) — hai tầng, vì client cũ/curl vẫn gọi được.
  _render(kind, adviceId, title, message, extraContent, confidence, actionable = true) {
    const el = node("div", "adv-card enter");
    const head = node("div", "adv-head");
    append(head,
      node("span", "adv-kind", `${KIND_ICON[kind] || ""} ${KIND_LABEL[kind] || kind} · Trợ Lý Xanh`),
      node("span", "mock-badge", "mô phỏng"));
    const why = node("div", "adv-why hidden");
    if (extraContent) why.appendChild(extraContent);
    const actions = node("div", "adv-actions");
    if (actionable) {
      append(actions,
        node("button", "adv-btn follow", "✅ Làm theo"),
        node("button", "adv-btn dismiss", "✖ Bỏ qua"));
    }
    if (extraContent) actions.appendChild(node("button", "adv-btn why", "？Vì sao"));
    if (!actionable) actions.appendChild(node("button", "adv-btn close", "Đã hiểu"));
    append(el, head, node("b", "adv-title", title), node("p", "adv-msg", message));
    if (confidence != null) {
      const track = node("div", "confidence-track");
      const fill = node("div", "confidence-fill");
      const width = Math.max(0, Math.min(100, Number(confidence) * 100));
      fill.style.width = `${Number.isFinite(width) ? width : 0}%`;
      track.appendChild(fill);
      el.appendChild(track);
    }
    append(el, why, actions);
    const close = (cls, act) => {
      this.logAction(adviceId, act, kind);
      el.classList.add(cls);
      setTimeout(() => el.remove(), 650);
    };
    if (actionable) {
      el.querySelector(".follow").addEventListener("click", () => close("followed", "followed"));
      el.querySelector(".dismiss").addEventListener("click", () => close("dismissed", "dismissed"));
    } else {
      // im lặng: đóng thẻ KHÔNG ghi event nào (không có quyết định để ghi nhận)
      el.querySelector(".close").addEventListener("click", () => {
        el.classList.add("dismissed");
        setTimeout(() => el.remove(), 650);
      });
    }
    const whyBtn = el.querySelector(".why");
    if (whyBtn) whyBtn.addEventListener("click", () => {
      el.querySelector(".adv-why").classList.toggle("hidden");
      this.logAction(adviceId, "expanded", kind);
    });
    // chỉ giữ tối đa 2 card trên màn — card cũ nhất tự rời
    while (this.mount.children.length >= 2) this.mount.firstChild.remove();
    this.mount.appendChild(el);
    this.history.push({ kind, title, at: new Date().toLocaleTimeString("vi-VN") });
    return el;
  },

  _whyHtml(item) {
    const fragment = document.createDocumentFragment();
    fragment.appendChild(numberTable(item.numbers, {useName: true}));
    const meta = node("div", "meta",
      `solver ${item.solver || ""} · mã ${item.reason_code || ""} · độ tin ${
        (Number(item.confidence || 0) * 100).toFixed(0)}%`);
    meta.style.fontSize = "10.5px";
    meta.style.color = "var(--text-muted)";
    meta.style.marginTop = "6px";
    if (item.caveat) meta.appendChild(node("div", null, `⚠ ${item.caveat}`));
    fragment.appendChild(meta);
    return fragment;
  },

  // -------- BRIEF (F1): mốc hôm nay + advice S1 đầu ca --------
  async brief() {
    const { driverId, date } = this.ctx.profile();
    const v2 = await this._v2("brief");
    if (v2.status !== "disabled") {
      return v2.status === "ready" ? this._renderV2(v2.items[0]) : null;
    }
    const a = await api.advice(driverId, date, KIND_HOURS.brief, KIND_TOPIC.brief);
    if (a.silent.is_silent) {
      return this._render("brief", `brief-${date}`, "Bạn đang đúng nhịp",
        a.silent.message, null, null, false);   // L4-07: im lặng ⇒ không nút hành động
    }
    const it = a.items[0];
    return this._render("brief", it.advice_id, it.title, it.message,
      this._whyHtml(it), it.confidence);
  },

  // -------- NUDGE (F2): NGẮN, chỉ khi KHÔNG chở khách --------
  async nudge({ isDriving }) {
    // ĐA-04/R-12: BÁO trạng thái cho luật chung quyết, KHÔNG tự chặn ở client.
    // Bản cũ `if (isDriving) return null` giữ đúng NHTSA nhưng có hai cái sai:
    //   (a) backend không bao giờ thấy `is_driving` ⇒ nhánh QUEUE trong `cadence.evaluate`
    //       CHẾT ở sản phẩm — cùng họ "code tự quảng cáo nhánh không chạy" đã trả giá ở
    //       `topic_cooldown`; ở SIM thuộc tính này được bảo đảm bằng cấu trúc (vòng idle bỏ
    //       ENROUTE/ON_TRIP) ⇒ thuộc tính có ở sim mà không có ở sản phẩm;
    //   (b) lời khuyên bị VỨT thay vì HOÃN — QUEUE nghĩa là "nhắc khi bạn dừng", đúng thứ
    //       tài xế cần; return null làm mất luôn.
    // An toàn KHÔNG giảm: backend trả QUEUE ⇒ `silent` ⇒ không card nào được vẽ.
    const { driverId, date } = this.ctx.profile();
    const v2 = await this._v2("nudge", isDriving);
    if (v2.status !== "disabled") {
      return v2.status === "ready" ? this._renderV2(v2.items[0]) : null;
    }
    const a = await api.advice(driverId, date, KIND_HOURS.nudge, KIND_TOPIC.nudge, isDriving);
    if (a.silent.is_silent) return null;   // im lặng = KHÔNG card, không bịa
    const it = a.items[0];
    // nudge rút gọn: title + 1 số chính; chi tiết nằm ở "Vì sao"
    const firstNum = (it.numbers || [])[0];
    const shortMsg = firstNum
      ? `${firstNum.name.replaceAll("_", " ")}: ${firstNum.unit === "vnd" ? fmtVnd(firstNum.value) : firstNum.value + " " + (firstNum.unit || "")}`
      : it.message.split(".")[0] + ".";
    return this._render("nudge", it.advice_id, it.title, shortMsg,
      this._whyHtml(it), it.confidence);
  },

  // -------- RECAP (F3): payout thật + lời khuyên cuối ngày --------
  async recap() {
    const { driverId, date } = this.ctx.profile();
    const v2 = await this._v2("recap");
    if (v2.status !== "disabled") {
      return v2.status === "ready" ? this._renderV2(v2.items[0]) : null;
    }
    const st = this.ctx.state();
    if (!st) return null;   // R5 double-check: bấm recap trước khi hồ sơ tải xong
    const m = st.money;
    const bd = m.payout_breakdown || {};
    const a = await api.advice(driverId, date, KIND_HOURS.recap, KIND_TOPIC.recap);
    const tail = a.silent.is_silent
      ? a.silent.message
      : `${a.items[0].title} — mở "Vì sao" để xem chi tiết.`;
    const msg = `Payout hôm nay ${fmtVnd(m.payout_vnd)} (cuốc ${fmtVnd(bd.trip_payout_vnd)}`
      + `${bd.mission_reward_vnd ? ` · mission ${fmtVnd(bd.mission_reward_vnd)}` : ""}) · `
      + `${st.payout_summary.trips_count} cuốc. ${tail}`;
    const it = a.items[0];
    return this._render("recap", it ? it.advice_id : `recap-${date}`,
      "Tổng kết ca hôm nay", msg, it ? this._whyHtml(it) : null,
      it ? it.confidence : null, Boolean(it));   // L4-07: không item ⇒ id bịa ⇒ không nút
  },
};
