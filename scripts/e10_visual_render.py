"""Template HTML của visual gate E10 — tách khỏi `e10_visual.py` để dễ sửa riêng phần trình bày.

Palette/typography KẾ THỪA design system của dự án (`src/gsm_sim/dashboard_theme.py`):
accent Xanh SM `#199e70` là accent DUY NHẤT; semantic good/warning/critical tách riêng cho
chip kết luận; mono cho mọi số (tabular-nums). Hai theme đều được định nghĩa bằng token,
`data-theme` của viewer thắng `prefers-color-scheme` theo cả hai chiều.
"""
from __future__ import annotations


def _chip(lop: str) -> str:
    kind = ("good" if "GIỮ" in lop else
            "warn" if "MỘT-PHẦN" in lop else
            "crit" if ("SỤP" in lop or "ÂM" in lop) else "neutral")
    return f'<span class="chip {kind}">{lop.split("(")[0].strip()}</span>'


def _card(title: str, sub: str, svg: str) -> str:
    return (f'<figure><figcaption><span class="t">{title}</span>'
            f'<span class="s">{sub}</span></figcaption>{svg}</figure>')


CSS = """
 :root {
   --bg:#f7faf8; --elev:#ffffff; --dim:#eef3f0; --line:#d5e0da;
   --tx:#12181c; --tx2:#5c6f6a; --accent:#127754;
   --good:#199e70; --warn:#a86f00; --crit:#c4413f; --cool:#2f6fc4;
 }
 @media (prefers-color-scheme: dark) {
   :root { --bg:#12181c; --elev:#1a2126; --dim:#242d33; --line:#263036;
           --tx:#f2f5f4; --tx2:#9fb0ac; --accent:#2ecf95;
           --good:#199e70; --warn:#c98500; --crit:#e66767; --cool:#3987e5; }
 }
 :root[data-theme="dark"] { --bg:#12181c; --elev:#1a2126; --dim:#242d33; --line:#263036;
   --tx:#f2f5f4; --tx2:#9fb0ac; --accent:#2ecf95; --warn:#c98500; --crit:#e66767;
   --cool:#3987e5; }
 :root[data-theme="light"] { --bg:#f7faf8; --elev:#ffffff; --dim:#eef3f0; --line:#d5e0da;
   --tx:#12181c; --tx2:#5c6f6a; --accent:#127754; --warn:#a86f00; --crit:#c4413f;
   --cool:#2f6fc4; }
 * { box-sizing: border-box; }
 body { margin:0; padding:30px 20px 60px; background:var(--bg); color:var(--tx);
   font:400 16px/1.6 ui-sans-serif, system-ui, "Segoe UI", sans-serif;
   -webkit-font-smoothing:antialiased; }
 .wrap { max-width:1080px; margin:0 auto; display:flex; flex-direction:column; gap:32px; }
 header { display:flex; flex-direction:column; gap:8px; }
 .eyebrow { font:600 .74rem/1.6 ui-monospace, "Cascadia Code", Consolas, monospace;
   letter-spacing:.14em; text-transform:uppercase; color:var(--accent);
   display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
 h1 { font-size:1.62rem; font-weight:650; margin:0; letter-spacing:-.012em;
   text-wrap:balance; max-width:26ch; }
 .answer { display:flex; flex-wrap:wrap; align-items:baseline; gap:16px; margin-top:4px; }
 .big { font:700 3.3rem/1 ui-monospace, "Cascadia Code", Consolas, monospace;
   color:var(--accent); font-variant-numeric:tabular-nums; letter-spacing:-.03em; }
 .answer p { margin:0; color:var(--tx2); max-width:44ch; }
 .answer b { color:var(--tx); font-weight:600; }
 .mock { padding:2px 9px; border-radius:99px; font-weight:600; letter-spacing:.08em;
   background:var(--dim); color:var(--tx2); border:1px solid var(--line); }
 .lede { color:var(--tx2); margin:0; max-width:70ch; }
 .lede b, .note b { color:var(--tx); font-weight:600; }
 code { font-family:ui-monospace, "Cascadia Code", Consolas, monospace; font-size:.9em;
   background:var(--dim); padding:1px 5px; border-radius:4px; }
 .grid { display:grid; gap:16px; grid-template-columns:repeat(auto-fit, minmax(266px, 1fr));
   margin-top:16px; }
 figure { margin:0; padding:14px; background:var(--elev); border:1px solid var(--line);
   border-radius:12px; display:flex; flex-direction:column; gap:10px; }
 figcaption { display:flex; flex-direction:column; gap:4px; }
 figcaption .t { font-weight:600; font-size:.97rem; }
 figcaption .s { font:.79rem/1.5 ui-monospace, "Cascadia Code", Consolas, monospace;
   color:var(--tx2); font-variant-numeric:tabular-nums; }
 .tablewrap { overflow-x:auto; border:1px solid var(--line); border-radius:12px;
   background:var(--elev); }
 table { border-collapse:collapse; width:100%; min-width:560px; }
 th, td { text-align:left; padding:11px 14px; border-bottom:1px solid var(--line);
   white-space:nowrap; }
 tbody tr:last-child td { border-bottom:0; }
 th { font:600 .71rem/1.5 ui-monospace, monospace; letter-spacing:.1em;
   text-transform:uppercase; color:var(--tx2); background:var(--dim); }
 td.num { font-family:ui-monospace, "Cascadia Code", Consolas, monospace;
   font-variant-numeric:tabular-nums; }
 .ci { color:var(--tx2); font-size:.86em; }
 .chip { display:inline-block; padding:2px 10px; border-radius:99px; font-size:.78rem;
   font-weight:600; border:1px solid currentColor; }
 .chip.good { color:var(--good); } .chip.warn { color:var(--warn); }
 .chip.crit { color:var(--crit); } .chip.neutral { color:var(--tx2); }
 .note { border-left:3px solid var(--warn); padding:3px 0 3px 16px; color:var(--tx2);
   max-width:70ch; margin:0; }
 .notes { display:flex; flex-direction:column; gap:16px; }
 .sw { display:inline-block; width:.7em; height:.7em; border-radius:2px; vertical-align:-1px; }
 :focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
"""


def render(*, seed, k, svg_a, svg_o, svg_r, svg_diff, tot_a, tot_o, tot_r,
           hhi_a, hhi_o, hhi_r, moved, diff_art) -> str:
    st = diff_art["stop1_delta_oracle"]
    ar = diff_art["arms"]
    r_hist = ar["hist"]["delta_vs_A"]["mean"] / st["mean"]
    r_real = ar["real"]["delta_vs_A"]["mean"] / st["mean"]
    r_wait = ar["wait"]["delta_vs_A"]["mean"] / st["mean"]

    def row(label, hint, rec, ratio, chip_html):
        lo, hi = rec["ci"]
        return (f'<tr><td>{label}'
                + (f' <span class="ci">{hint}</span>' if hint else "")
                + f'</td><td class="num">{rec["mean"]:+,.0f}đ '
                  f'<span class="ci">[{lo:,.0f}, {hi:,.0f}]</span></td>'
                  f'<td class="num">{ratio:.0%}</td><td>{chip_html}</td></tr>')

    return f"""<title>E10 — advisor mất λ thì tài xế đứng đâu? (MOCK, seed {seed})</title>
<style>{CSS}</style>
<div class="wrap">
<header>
 <div class="eyebrow">E10 · advisor cũng nhiễu <span class="mock">MOCK</span></div>
 <h1>Advisor mất λ thì tài xế đứng đâu — và mất bao nhiêu tiền?</h1>
 <div class="answer">
  <span class="big">{r_real:.0%}</span>
  <p>của <b>{st['mean']:+,.0f}đ</b>/người/ngày còn lại khi advisor chỉ được thấy
  <b>cuốc đã đón</b> thay vì λ thật của thế giới. Suy giảm có ý nghĩa thống kê,
  nhưng <b>không sụp</b>.</p>
 </div>
</header>

<section>
 <p class="lede">Màu = <b>tài xế-phút đứng chờ</b> trong ô (mật độ cung), seed {seed}, phủ toàn
 đội, kênh vị trí <code>wait_only</code>. Cầu do thế giới sinh ra và <b>giống nhau từng bit</b>
 ở cả ba bản đồ (cùng seed) — mọi khác biệt bên dưới đều do lời khuyên.</p>
 <div class="grid">
  {_card("World A — không có advisor", f"{tot_a:,.0f} tài xế-phút · HHI {hhi_a:.4f}", svg_a)}
  {_card("B_oracle — advisor biết λ", f"{tot_o:,.0f} · HHI {hhi_o:.4f}", svg_o)}
  {_card("B_real — chỉ thấy cuốc đã đón", f"{tot_r:,.0f} · HHI {hhi_r:.4f}", svg_r)}
  {_card("Hiệu: B_real − B_oracle",
         '<span class="sw" style="background:var(--crit)"></span> realized dồn nhiều hơn · '
         '<span class="sw" style="background:var(--cool)"></span> ít hơn · '
         f'{moved:,.0f} tài xế-phút dịch chỗ', svg_diff)}
 </div>
</section>

<section>
 <div class="tablewrap"><table>
  <thead><tr><th>Nguồn tin của advisor</th><th>Δ thu nhập vs không-advisor</th>
   <th>Còn lại</th><th>Kết luận</th></tr></thead>
  <tbody>
   {row("λ của thế giới", "(trần hiện tại)", st, 1.0,
        '<span class="chip neutral">tái lập trần +6.016</span>')}
   {row("30 ngày cuốc lịch sử", "", ar["hist"]["delta_vs_A"], r_hist, _chip(ar["hist"]["lop"]))}
   {row(f"Cuốc đã đón trong ngày (k={k})", "", ar["real"]["delta_vs_A"], r_real,
        _chip(ar["real"]["lop"]))}
   {row("Thời gian chờ của ô", "(thay λ)", ar["wait"]["delta_vs_A"], r_wait,
        _chip(ar["wait"]["lop"]))}
  </tbody>
 </table></div>
 <p class="lede" style="margin-top:12px">Δ là hiệu ghép cặp trên <b>100 seed tươi</b>
 (5000–5099), khoảng tin cậy bootstrap 95%. Bản đồ phía trên chỉ là <b>một seed</b>, để thấy
 cơ chế chứ không phải để đọc độ lớn.</p>
</section>

<section class="notes">
 <p class="note"><b>Không tìm thấy dấu hiệu dồn cục.</b> Khi mất λ, cung <b>phân tán hơn</b> chứ
 không tụ lại: HHI {hhi_o:.4f} → {hhi_r:.4f}. Tương quan giữa phần dư cầu và mật độ cung ≈ 0 ở
 cả ba thế giới. Đây là <i>không tìm thấy bằng chứng</i>, không phải <i>đã bác bỏ</i> — thế giới
 mô phỏng có thứ hạng ô đứng yên cả ngày, tức nơi dồn cục khó xảy ra nhất.</p>
 <p class="note"><b>{r_real:.0%} là chặn TRÊN.</b> Trong mô phỏng, thứ hạng ô không đổi theo giờ
 nên "cuốc giờ trước" đoán được "cuốc giờ này" (đo được: sai lệch so với λ hiện tại và so với λ
 trễ bằng nhau, 0,249). Ngoài đời nhu cầu dịch chuyển sáng/tối, nên phần giữ lại được sẽ
 <b>thấp hơn</b>.</p>
 <p class="note"><b>Thời gian chờ không thay được λ.</b> Trigger theo chờ-lâu bắn đúng nhưng quá
 hiếm — 3,6 ứng viên/ngày so với 248 của bản realized — nên giá trị không phân biệt được với 0
 trên toàn dải ngưỡng đã quét (15–35 phút).</p>
</section>
</div>"""
