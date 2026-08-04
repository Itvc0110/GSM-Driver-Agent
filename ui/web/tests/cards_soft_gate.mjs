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

// 🔀 Viết lại 2026-08-04 sau khi rebase lên PR #5. Bản đầu kiểm bằng regex trên chuỗi `innerHTML`;
// Khánh đã chuyển `_render` sang **dựng DOM node** (`node()` đặt `textContent`) nên không còn chuỗi
// nào để regex — cổng sẽ **xanh rỗng** nếu không sửa. Đây là mini-DOM thật: `createElement` ·
// `appendChild` · `textContent` · `className` · `querySelector` **đi theo CÂY**.
//
// Kiểm trên CÂY mạnh hơn kiểm trên chuỗi: một nút `follow` nhét vào bằng đường khác vẫn có thể lọt
// regex, nhưng không lọt phép duyệt cây.
class ElGia {
  constructor(tag) {
    this.tag = tag;
    this.className = "";
    this.textContent = "";
    this.style = {};
    this.children = [];
    this.listeners = [];
    this.classes = new Set();
    this.classList = {
      add: (c) => this.classes.add(c),
      toggle: (c) => (this.classes.has(c) ? this.classes.delete(c) : this.classes.add(c)),
      contains: (c) => this.classes.has(c),
    };
  }
  get firstChild() { return this.children[0]; }
  appendChild(el) { this.children.push(el); return el; }
  replaceChildren(...c) { this.children = c; }
  remove() { }
  addEventListener(_ev, fn) { this.listeners.push(fn); }

  /** Duyệt CẢ CÂY kể cả chính nút này, theo thứ tự tài liệu.
   *  Phòng thủ với child KHÔNG phải `ElGia` (chuỗi, fragment thật) — `_whyHtml` của Khánh trả
   *  `DocumentFragment`, và một `walk()` giả định mọi child đều là node sẽ **nổ** thay vì báo sai.
   *  Cổng phải hỏng ở chỗ ranh giới hở, không hỏng ở chỗ stub thiếu. */
  *walk() {
    yield this;
    for (const c of this.children) {
      if (c && typeof c.walk === "function") yield* c.walk();
    }
  }

  /** Toàn bộ text của cây — thay cho `innerHTML` trong các phép kiểm. */
  get text() { return [...this.walk()].map((n) => n.textContent || "").join(" "); }

  // Trả `null` khi không có — điều QUAN TRỌNG NHẤT của stub này. `_render` gọi
  // `el.querySelector(".follow").addEventListener(...)` KHÔNG guard, nên nếu trả bừa một object
  // cho mọi selector thì bug "thẻ mềm vẫn có nút follow" sẽ không bao giờ lộ ra.
  querySelector(sel) {
    const cls = sel.replace(/^\./, "");
    for (const n of this.walk()) {
      if (n !== this && String(n.className || "").split(/\s+/).includes(cls)) return n;
    }
    return null;
  }
  click(cls) {
    const el = this.querySelector("." + cls);
    if (!el) throw new Error(`không có nút '.${cls}' trong cây — thẻ này không vẽ nút đó`);
    el.listeners.forEach((f) => f());
  }
}

globalThis.document = {
  createElement: (t) => new ElGia(t),
  createDocumentFragment: () => new ElGia("#fragment"),
};
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

/** `extraContent` nay là một NODE (Khánh đổi từ chuỗi HTML sang DocumentFragment ở PR #5) —
 *  truyền chuỗi vào sẽ làm `why.appendChild()` nhận sai kiểu và cổng hỏng vì lý do không phải
 *  ranh giới. */
const noiDungViSao = () => {
  const f = document.createDocumentFragment();
  f.appendChild(Object.assign(new ElGia("i"), { textContent: "vì sao" }));
  return f;
};

const ve = (opts) => {
  Cards.mount = new ElGia("div");
  apiCalls = []; warns = [];
  return Cards._render("nudge", "adv-1", "Tiêu đề", "Nội dung", noiDungViSao(), 0.8,
    opts.actionable ?? true, opts.topic ?? null, opts.isSoft ?? false);
};

console.log("CỔNG cards.js — KHUYÊN MỀM không có nút 'Làm theo'\n");

// --- 1. thẻ MỀM: không có nút Làm theo -------------------------------------------------
{
  const el = ve({ isSoft: true, topic: "rest_nudge" });
  kiem("thẻ mềm KHÔNG có nút 'Làm theo'",
    !el.text.includes("Làm theo") && el.querySelector(".follow") === null,
    "thẻ khuyên mềm vẫn vẽ nút 'Làm theo' ⇒ tài xế bị hỏi 'anh có nghe lời khuyên nghỉ không' — "
    + "đúng câu QĐ-1 cấm hỏi. Xem tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md");
  kiem("thẻ mềm CÓ nút 'Ẩn'", el.querySelector(".hide") !== null,
    "mất nút Ẩn ⇒ tài xế không tắt được thẻ phiền. Cường chốt: 'giữ nút ẩn, bỏ nút Làm theo'");
  kiem("thẻ mềm mang class `adv-soft`", el.className.includes("adv-soft"),
    "thiếu hook CSS để style thẻ mềm khác thẻ kinh tế");
}

// --- 2. ĐỐI CHỨNG: thẻ kinh tế VẪN có nút Làm theo ------------------------------------
// Không có bước này thì một `_render` không vẽ nút nào cũng làm cổng trên xanh.
{
  const el = ve({ isSoft: false, topic: "nudge" });
  kiem("ĐỐI CHỨNG — thẻ kinh tế VẪN có 'Làm theo'", el.querySelector(".follow") !== null,
    "cổng đang xanh vì thẻ nào cũng không có nút, không phải vì ranh giới chạy đúng");
  kiem("ĐỐI CHỨNG — thẻ kinh tế KHÔNG có nút 'Ẩn'", el.querySelector(".hide") === null,
    "hai chế độ lẫn vào nhau");
}

// --- 3. thẻ IM LẶNG: không nút nào ghi event ------------------------------------------
{
  const el = ve({ actionable: false });
  kiem("thẻ im lặng chỉ có 'Đã hiểu'",
    el.querySelector(".close") !== null && el.querySelector(".follow") === null,
    "L4-07: thẻ im lặng không có quyết định thật, bấm nút sẽ tạo adherence giả");
}

// --- 3b. 🔀 SAU REBASE PR #5: text KHÔNG được đi qua innerHTML -------------------------
// Khánh chuyển `_render` sang `node()` (đặt `textContent`) đúng lúc bản của tôi còn nội suy
// `${title}` vào `innerHTML`. Giữ nền của anh ấy là quyết định BẢO MẬT, nên phải có cổng canh —
// nếu không, lần refactor sau rất dễ quay lại innerHTML cho "gọn".
{
  const doc = "<img src=x onerror=alert(1)>";
  Cards.mount = new ElGia("div"); apiCalls = [];
  const el = Cards._render("nudge", "adv-x", doc, doc, null, 0.5, true, "nudge", false);
  const co_the_la_markup = [...el.walk()].some((n) => n.tag === "img");
  kiem("tiêu đề/nội dung KHÔNG bị diễn giải thành markup",
    !co_the_la_markup && el.text.includes(doc),
    "text từ server/LLM đang được đưa vào DOM dưới dạng markup — đường XSS ngay chỗ hiển thị "
    + "lời khuyên. Dùng `node()`/`textContent`, đừng quay lại `innerHTML`.");
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
