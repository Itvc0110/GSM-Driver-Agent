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

  _render(kind, adviceId, title, message, extraHtml, confidence) {
    const el = document.createElement("div");
    el.className = "adv-card enter";
    el.innerHTML = `
      <div class="adv-head">
        <span class="adv-kind">${KIND_ICON[kind]} ${KIND_LABEL[kind]} · Trợ Lý Xanh</span>
        <span class="mock-badge">mô phỏng</span>
      </div>
      <b class="adv-title">${title}</b>
      <p class="adv-msg">${message}</p>
      ${confidence != null ? `<div class="confidence-track"><div class="confidence-fill" style="width:${confidence * 100}%"></div></div>` : ""}
      <div class="adv-why hidden">${extraHtml || ""}</div>
      <div class="adv-actions">
        <button class="adv-btn follow">✅ Làm theo</button>
        <button class="adv-btn dismiss">✖ Bỏ qua</button>
        ${extraHtml ? `<button class="adv-btn why">？Vì sao</button>` : ""}
      </div>`;
    const close = (cls, act) => {
      this.logAction(adviceId, act, kind);
      el.classList.add(cls);
      setTimeout(() => el.remove(), 650);
    };
    el.querySelector(".follow").addEventListener("click", () => close("followed", "followed"));
    el.querySelector(".dismiss").addEventListener("click", () => close("dismissed", "dismissed"));
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
    const rows = (item.numbers || []).map((n) => `
      <tr><td>${n.name.replaceAll("_", " ")}</td>
          <td>${n.unit === "vnd" ? fmtVnd(n.value) : n.value + " " + (n.unit || "")}</td>
          <td>${n.source}</td></tr>`).join("");
    return `<table class="num-table">${rows}</table>
      <div class="meta" style="font-size:10.5px;color:var(--text-muted);margin-top:6px">
        solver ${item.solver} · mã ${item.reason_code} · độ tin ${(item.confidence * 100).toFixed(0)}%
        ${item.caveat ? `<br>⚠ ${item.caveat}` : ""}</div>`;
  },

  // -------- BRIEF (F1): mốc hôm nay + advice S1 đầu ca --------
  async brief() {
    const { driverId, date } = this.ctx.profile();
    const a = await api.advice(driverId, date, KIND_HOURS.brief, KIND_TOPIC.brief);
    if (a.silent.is_silent) {
      return this._render("brief", `brief-${date}`, "Bạn đang đúng nhịp",
        a.silent.message, null, null);
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
      it ? it.confidence : null);
  },
};
