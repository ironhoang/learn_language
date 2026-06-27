# txt → HTML + Audio

Hướng dẫn dùng script `scripts/txt_to_html_audio.py` để chuyển file txt hội thoại (ChatGPT) thành trang HTML có nút 🔊 nghe audio từng câu, và tự động thêm card vào trang chủ.

---

## Tổng quan

Script đọc file txt trong `chatgpt-data/`, giữ nguyên thứ tự hội thoại, rồi tạo ra HTML trong `episoden/` với:

- **PM card** (xanh) — lời Project Manager
- **You card** (xám) — câu trả lời của bạn
- **Correction card** (trắng) — câu gốc bị sai → câu đúng + nút 🔊 + giải thích
- **Expression card** (vàng) — các mẫu câu hữu ích + nút 🔊
- **Play bar** cố định bên dưới: `▶ Play All` và `▶ From here`

Sau khi generate xong, script tự cập nhật:
- `index.html` — thêm card vào section "English Corrections"
- `react-app/src/pages/HomePage.jsx` — thêm entry vào `CHATGPT_ENGLISH`
- `chatgpt-data/registry.json` — lưu metadata để tránh duplicate

Audio được generate bằng **edge-tts** (miễn phí), upload lên **Cloudflare R2**, nhúng vào HTML dưới dạng URL công khai.

---

## Workflow thêm file mới

```
1. Đặt file txt vào chatgpt-data/
2. Chạy script → chọn file theo số
3. Xem xác nhận, nhập y hoặc Enter
4. Script generate audio + HTML
5. index.html và HomePage.jsx tự được cập nhật
```

---

## Cách chạy

### Bước 1 — Chạy và chọn file

```bash
python scripts/txt_to_html_audio.py
```

Script hiện danh sách file txt trong `chatgpt-data/`. File nào đã có HTML thì đánh dấu `✓`:

```
📂  Chọn file để convert:

  1.  english-project.txt ✓
  2.  english-session2.txt
  0.  Thoát

Nhập số:
```

Nhập số tương ứng, `0` để thoát không làm gì.

### Bước 2 — Xem trước trước khi generate audio

Dùng `--dry-run` để kiểm tra parse + cấu trúc HTML trước, không tốn TTS:

```bash
python scripts/txt_to_html_audio.py --dry-run
# → chọn file theo menu
```

Output sẽ cho biết số PM/User/Correction/Expression blocks và số nhóm:

```
📖  Parsing english-session2.txt …
    PM=4  User=2  Corrections=12  Expressions=2
    → 2 groups
      Group 1: 18 blocks, ~255 audio words (~2 min)
      Group 2: 6 blocks,  ~110 audio words (~1 min)
```

### Bước 3 — Generate audio + HTML

```bash
python scripts/txt_to_html_audio.py
# → chọn file
```

Script sẽ:
1. Parse file txt, giữ nguyên thứ tự hội thoại
2. Sinh audio cho từng câu Better + Expression bằng edge-tts
3. Upload MP3 lên Cloudflare R2
4. Ghi URL vào nút 🔊 trong HTML
5. Lưu `episoden/<ten-file>.html`
6. Cập nhật `index.html`, `HomePage.jsx`, `registry.json`

Idempotent: câu đã có audio trên R2 → bỏ qua, không generate lại.

> **Tại sao chạy chậm?** Sau mỗi câu, script tạm dừng **ngẫu nhiên 0.5–1.5 giây** trước khi gọi tiếp edge-tts. Đây là rate-limit protection — gọi liên tục quá nhanh có thể bị từ chối. Bình thường với ~20 câu thì mất khoảng 30–45 giây.

### Generate lại audio (ghi đè)

```bash
python scripts/txt_to_html_audio.py --overwrite
```

Dùng khi muốn re-generate audio (đổi giọng đọc, fix lỗi phát âm...).

### Truyền file thẳng (bỏ qua menu)

```bash
python scripts/txt_to_html_audio.py ten-file.txt
python scripts/txt_to_html_audio.py ten-file.txt --dry-run
python scripts/txt_to_html_audio.py ten-file.txt --overwrite
```

---

## Cài đặt

### 1. Cài dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` cần có:
```
python-dotenv>=1.0.0
boto3
edge-tts
```

### 2. Cấu hình R2 (Cloudflare)

Tạo file `.env` ở root (copy từ `.env.example`):

```bash
cp .env.example .env
```

Điền vào `.env`:
```
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY=your_r2_access_key_id
R2_SECRET_KEY=your_r2_secret_access_key
R2_BUCKET=learn-en-ch-assets
R2_PUBLIC_URL=https://pub-xxxx.r2.dev
```

> Lấy thông tin tại: **Cloudflare Dashboard → R2 → Manage R2 API Tokens**

---

## Cấu trúc file txt

Script nhận dạng 4 loại khối theo marker cố định:

### 1. Project Manager block
```
Project Manager

Nội dung PM viết...
```

### 2. User reply (không có marker, nằm giữa 2 PM block)
```
Project Manager

Câu hỏi của PM...

Ok về ý tưởng của tôi...    ← User reply, không có header
1. Ý tưởng 1...

Project Manager

Trả lời của PM...
```

> Script tự phát hiện: nếu một PM block ngay sau là PM block khác (không qua "English Corrections"), đoạn cuối = User reply.

### 3. English Corrections block

Format cũ (`Better version`):
```
English Corrections
Your sentence

câu sai của bạn

Better version

Câu đúng hơn.

Why

Giải thích lý do.
```

Format mới (`✅ Better:`):
```
English Corrections
Your sentence

câu sai của bạn

✅ Better:

Câu đúng 1.

or

Câu đúng 2 (alternative).

Why

Giải thích.
```

> Có thể có nhiều `Your sentence` liên tiếp trong 1 `English Corrections` section.
> Nếu có `⭐` inline giữa các corrections, script xử lý được, không bị bỏ sót.

### 4. Expression block
```
⭐ Useful expressions for meetings

We should implement...
We could add...
I'd like to include...
```

> Dòng `⭐` phải đứng đầu dòng. Các câu phía sau được collect làm mẫu câu có audio.

---

## Quy tắc chia nhóm (~2 phút mỗi nhóm)

Script đếm số từ của phần audio (câu Better + câu Expression). Khi tổng vượt **260 từ** (~2 phút ở 130 từ/phút), nó tách nhóm mới. PM/User block luôn thuộc nhóm hiện tại, không bao giờ bị tách giữa chừng.

---

## Output

| File | Mô tả |
|------|--------|
| `episoden/<ten-file>.html` | HTML hoàn chỉnh, tên khớp với tên txt |
| `chatgpt-data/registry.json` | Metadata của tất cả file đã convert |
| `index.html` | Tự được cập nhật, section "English Corrections" |
| `react-app/src/pages/HomePage.jsx` | Tự được cập nhật, const `CHATGPT_ENGLISH` |
| `audio/en_*.mp3` | Cache audio local (không cần commit) |

---

## Troubleshooting

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| `Missing R2 env vars` | Thiếu `.env` hoặc biến chưa điền | Kiểm tra `.env`, chạy `--dry-run` để test trước |
| Thiếu corrections trong HTML | Sai format `Better version` / `✅ Better:` | Chạy `--dry-run`, kiểm tra số Corrections in output |
| Audio không phát | URL R2 sai hoặc bucket chưa public | Kiểm tra `R2_PUBLIC_URL` và public access trên R2 |
| `edge-tts` lỗi | Chưa cài hoặc không có internet | `pip install edge-tts`, kiểm tra kết nối mạng |
| Card bị duplicate | `registry.json` bị xóa | Script dùng registry để dedupe — không xóa file này |
