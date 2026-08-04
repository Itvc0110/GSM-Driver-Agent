// 🔴 CỔNG: `cards.js` không được vẽ nút "Làm theo" cho KHUYÊN MỀM (QĐ-1, Cường 2026-08-03).
//
// ## Vì sao cổng này tồn tại — và vì sao nó KHÔNG cần jsdom
//
// `Nợ 7` được ghi là *"cổng cards.js cần jsdom/node — quyết định hạ tầng, hỏi Cường riêng"*, và nó
// treo nhiều ngày vì tiền đề đó. Đo lại 2026-08-04: **cả hai vế đều sai**.
//   · node CÓ SẴN (`C:\Program Files\nodejs`), và `cards.js` đã là ES module có `export`;
//   · `_render` chỉ chạm SÁU API DOM — `createElement` · `className` · `innerHTML` · `classList` ·
//     `querySelector` · `appendChild`/`remove`. Stub hết bằng ~40 dòng dưới đây.
// ⇒ Không `package.json`, không `npm install`, không `node_modules` trong repo. Không có quyết
//   định hạ tầng nào phải hỏi.
//
// Bài học đáng ghi hơn cả cổng: **một việc bị treo vì tiền đề chưa ai đo.** Chi phí đo tiền đề ở
// đây là hai lệnh `Get-Command`.
//
// ## Cổng này canh cái gì
//
// Ranh giới QĐ-1 hiện có ba lan can ở BACKEND (registry · `adherence_view` · 422 tại boundary).
// Nhưng thứ tài xế nhìn thấy là **cái nút**. Nếu client vẫn vẽ "✅ Làm theo" trên thẻ nghỉ thì:
//   · tài xế vẫn bị hỏi *"anh có làm theo lời khuyên nghỉ không"* — đúng câu QĐ-1 cấm hỏi;
//   · cú bấm ăn 422, tức lỗi hiện ra ở đúng chỗ tệ nhất: màn hình người dùng.
// Backend chặn được DỮ LIỆU, không chặn được CÂU HỎI. Nút là câu hỏi.
//
// ## Chạy
//   node ui/web/tests/cards_soft_gate.mjs      → exit 0 = xanh, exit 1 = đỏ
// Bọc trong pytest: `tests/test_cards_js_soft_gate.py` (để nó nằm trong "suite xanh" chung).

// ----------------------------------------------------------------- stub DOM tối thiểu

let apiCalls = [];
let warns = [];

class ElGia {
  constructor(tag) {
    this.tag = tag;
    this.className = "";
    this._html = "";
    this.children = [];
    this.listeners = {};      // selector -> [handler]
    this.classes = new Set();
    this.classList = {
      add: (c) => this.classes.add(c),
      toggle: (c) => (this.classes.has(c) ? this.classes.delete(c) : this.classes.add(c)),
      contains: (c) => this.classes.has(c),
    };
  }
  set innerHTML(v) { this._html = v; }
  get innerHTML() { return this._html; }
  get firstChild() { return this.children[0]; }
  appendChild(el) { this.children.push(el); return el; }
  remove() { }
  // `querySelector` chỉ cần đủ để `_render` gắn listener: trả một handle nếu class có trong HTML,
  // `null` nếu không. Trả `null` đúng lúc là điều QUAN TRỌNG NHẤT — `_render` gọi
  // `el.querySelector(".follow").addEventListener(...)` không guard, nên nếu ta trả bừa một object
  // cho mọi selector thì bug "thẻ mềm vẫn có nút follow" sẽ KHÔNG bao giờ lộ ra.
  querySelector(sel) {
    const cls = sel.replace(/^\./, "");
    if (!new RegExp(`class="[^"]*\\b${cls}\\b`).test(this._html)) return null;
    const self = this;
    return {
      addEventListener(_ev, fn) { (self.listeners[cls] ||= []).push(fn); },
      classList: { toggle() { }, add() { }, contains: () => false },
    };
  }
  click(cls) {
    const fns = this.listeners[cls];
    if (!fns) throw new Error(`không có listener cho '.${cls}' — thẻ này không có nút đó`);
    fns.forEach((f) => f());
  }
}

globalThis.document = { createElement: (t) => new ElGia(t) };
globalThis.setTimeout = () => 0;                     // `_render` dùng để gỡ thẻ; không cần chạy
globalThis.console = { ...console, warn: (...a) => warns.push(a.join(" ")) };

// ----------------------------------------------------------------- nạp module thật

const { Cards } = await import("../js/cards.js");
const apiMod = await import("../js/api.js");

// Chặn `api.adviceAction` để ĐẾM request thật sự rời client. Đây là điểm đo đúng: cổng phải hỏi
// *"có request nào được gửi không"*, không phải *"hàm có return sớm không"* — cái sau là kiểm cách
// viết code, cái trước là kiểm hành vi.
apiMod.api.adviceAction = async (body) => { apiCalls.push(body); return { ok: true }; };

Cards.init(new ElGia("div"), {
  profile: () => ({ driverId: "d-1", date: "2026-08-04" }),
  state: () => ({}),
});

// ----------------------------------------------------------------- khung kiểm

let fail = 0;
const kiem = (ten, dieu_kien, thong_diep) => {
  if (dieu_kien) { console.log(`  ✓ ${ten}`); return; }
  fail += 1;
  console.log(`  ✗ ${ten}\n      ${thong_diep}`);
};

const ve = (opts) => {
  Cards.mount = new ElGia("div");
  apiCalls = []; warns = [];
  return Cards._render("nudge", "adv-1", "Tiêu đề", "Nội dung", "<i>vì sao</i>", 0.8,
    opts.actionable ?? true, opts.topic ?? null, opts.isSoft ?? false);
};

console.log("CỔNG cards.js — KHUYÊN MỀM không có nút 'Làm theo'\n");

// --- 1. thẻ MỀM: không có nút Làm theo -------------------------------------------------
{
  const el = ve({ isSoft: true, topic: "rest_nudge" });
  kiem("thẻ mềm KHÔNG có nút 'Làm theo'",
    !el.innerHTML.includes("Làm theo") && !/class="[^"]*\bfollow\b/.test(el.innerHTML),
    "thẻ khuyên mềm vẫn vẽ nút 'Làm theo' ⇒ tài xế bị hỏi 'anh có nghe lời khuyên nghỉ không' — "
    + "đúng câu QĐ-1 cấm hỏi. Xem tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md");
  kiem("thẻ mềm CÓ nút 'Ẩn'", el.innerHTML.includes(">Ẩn<"),
    "mất nút Ẩn ⇒ tài xế không tắt được thẻ phiền. Cường chốt: 'giữ nút ẩn, bỏ nút Làm theo'");
  kiem("thẻ mềm mang class `adv-soft`", el.className.includes("adv-soft"),
    "thiếu hook CSS để style thẻ mềm khác thẻ kinh tế");
}

// --- 2. ĐỐI CHỨNG: thẻ kinh tế VẪN có nút Làm theo ------------------------------------
// Không có bước này thì một `_render` trả chuỗi rỗng cũng làm cổng trên xanh.
{
  const el = ve({ isSoft: false, topic: "nudge" });
  kiem("ĐỐI CHỨNG — thẻ kinh tế VẪN có 'Làm theo'", el.innerHTML.includes("Làm theo"),
    "cổng đang xanh vì thẻ nào cũng không có nút, không phải vì ranh giới chạy đúng");
  kiem("ĐỐI CHỨNG — thẻ kinh tế KHÔNG có nút 'Ẩn'", !el.innerHTML.includes(">Ẩn<"),
    "hai chế độ lẫn vào nhau");
}

// --- 3. thẻ IM LẶNG: không nút nào ghi event ------------------------------------------
{
  const el = ve({ actionable: false });
  kiem("thẻ im lặng chỉ có 'Đã hiểu'",
    el.innerHTML.includes("Đã hiểu") && !el.innerHTML.includes("Làm theo"),
    "L4-07: thẻ im lặng không có quyết định thật, bấm nút sẽ tạo adherence giả");
}

// --- 4. HÀNH VI: bấm Ẩn gửi `dismissed`, KHÔNG phải `followed` ------------------------
{
  const el = ve({ isSoft: true, topic: "weather" });
  el.click("hide");
  await new Promise((r) => queueMicrotask(r));
  kiem("bấm 'Ẩn' gửi đúng `dismissed`",
    apiCalls.length === 1 && apiCalls[0].action === "dismissed",
    `mong 1 request 'dismissed', nhận: ${JSON.stringify(apiCalls)}`);
  kiem("request mang topic THẬT (không phải KIND_TOPIC placeholder)",
    apiCalls[0]?.topic === "weather",
    `topic gửi đi là ${apiCalls[0]?.topic} — backend sẽ phân loại nhầm chủ đề`);
}

// --- 5. HÀNH VI: `followed` trên topic mềm KHÔNG rời client ---------------------------
// Đây là lan can thứ hai (nếu ai đó gọi logAction trực tiếp, không qua nút).
{
  Cards.mount = new ElGia("div"); apiCalls = []; warns = [];
  await Cards.logAction("adv-2", "followed", "nudge", "rest_nudge", true);
  kiem("`logAction('followed', isSoft=true)` KHÔNG gửi request",
    apiCalls.length === 0,
    `đã gửi ${apiCalls.length} request cho một trace bị cấm: ${JSON.stringify(apiCalls)}`);
  kiem("…và có cảnh báo để dev thấy", warns.some((w) => w.includes("khuyên mềm")),
    "chặn IM LẶNG ⇒ dev sẽ tưởng request đã gửi và đi tìm bug ở backend");

  apiCalls = [];
  await Cards.logAction("adv-3", "followed", "nudge", "nudge", false);
  kiem("ĐỐI CHỨNG — `followed` trên topic kinh tế VẪN gửi", apiCalls.length === 1,
    "lan can chặn nhầm cả kênh kinh tế ⇒ mất phép đo adherence của sản phẩm");

  apiCalls = [];
  await Cards.logAction("adv-4", "dismissed", "nudge", "rest_nudge", true);
  kiem("ĐỐI CHỨNG — `dismissed` trên topic mềm VẪN gửi", apiCalls.length === 1,
    "chặn `dismissed` ⇒ nhịp nói ĐA-04 chết, thẻ mềm không bao giờ im");
}

console.log(fail === 0 ? "\nXANH — ranh giới khuyên mềm kín ở tầng CLIENT"
  : `\nĐỎ — ${fail} kiểm không đạt`);
process.exit(fail === 0 ? 0 : 1);
