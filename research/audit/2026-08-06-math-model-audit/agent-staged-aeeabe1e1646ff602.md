# RC-03 — việc CÒN LẠI duy nhất (bị plan mode chặn)

Artifact đã ghi xong: `research/audit/2026-08-06-root-cause-idle/rc-03-overlap.json` (34.429 bytes, JSON parse OK).

## Bước còn thiếu

Copy nguyên văn script probe vào repo để tái tạo được:

```
nguồn: C:\Users\Cuong\AppData\Local\Temp\claude\c--Users-Cuong-OneDrive---Hanoi-University-of-Science-and-Technology-Documents-GitHub-My-GSM-Driver-Agent\2a13ca96-bcc3-4a9e-8498-c8711d248f18\scratchpad\probe_idle_overlap.py
đích:  research\audit\2026-08-06-root-cause-idle\rc-03-probe-script.py
```

Script CHỈ ĐỌC sim (3 monkeypatch runtime, 0 RNG, 0 mutation) — không sửa file repo nào.
Cổng nhiễu-loạn `--verify` đã xanh: fingerprint trùng từng số giữa có-probe/không-probe ở cả hai arm,
và exact-repeat. Chạy lại:

```
uv run python research/audit/2026-08-06-root-cause-idle/rc-03-probe-script.py --verify --seed0 1000
uv run python research/audit/2026-08-06-root-cause-idle/rc-03-probe-script.py --seeds 5 --seed0 1000 --out <scratch>/rc03-raw.json
```

## Follow-up đề xuất (rc-04, chưa làm)

Chạy phản thực từng-thay-đổi-một, n≥30, để biến CEILING §8 thành số thật:
1. lọc cooldown TRƯỚC phép gán (hoặc gán lại sau khi loại cặp bị chặn) + log lượt bị chặn;
2. shortlist theo bán kính ETA thay vì hex k=6 — kèm đo lệch `accept_base` (đây là lý do
   BUG-DISPATCH-SHORTLIST chưa được sửa, cần Cường quyết Q-07).
