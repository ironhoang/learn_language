# Sinh bài đọc tiếng Trung theo chủ đề + HSK level

Hướng dẫn dùng `scripts/generate_zh_lesson.py` để tạo 1 bài đọc tiếng Trung ngắn theo chủ đề tự do
(tiếng Việt) + cấp độ HSK, chia đoạn tối đa 6 câu, mỗi câu tách riêng để nghe-lặp lại (shadowing).
Mỗi câu còn được chia nhỏ thành **phrases** (cụm 2-5 chữ) — câu tiếng Trung đầy đủ thường quá dài
để người mới đọc/nghe trọn vẹn ngay, nên tách cụm nhỏ để tập từng phần trước. Audio (cả câu lẫn
từng cụm) đọc ở tốc độ **0.75x** cho dễ nghe hơn tốc độ chuẩn.

Spec gốc: [spec/todo-generate-zh-lesson.md](../spec/todo-generate-zh-lesson.md)

Module này **tách biệt** với `content-pipeline/` (sinh video ngắn để đăng TikTok) và `workflows/`
(dạy hội thoại công việc tiếng Anh) — đây là bài đọc tương tác trên web, xem trực tiếp trong
`react-app`.

---

## Tổng quan pipeline

```
scripts/generate_zh_lesson.py "<chủ đề tiếng Việt>" <hsk-level>
        │
        ▼ Bước 1 — gọi DeepSeek, validate, retry, sinh pinyin + tách phrases mỗi câu
react-app/public/data/zh-lesson-<slug>.json     (paragraphs/sentences/phrases, audio="" hết)
react-app/public/data/zh-lessons-index.json     (danh mục, tự cập nhật)
scripts/_generated/<slug>-<timestamp>.json      (cache raw response DeepSeek)
        │
   [in bài đọc ra terminal (kèm cụm phrases) — review tay TRƯỚC khi tốn TTS nếu cần sửa]
        │
        ▼ Bước 2 — TTS cả câu lẫn từng phrase (edge-tts, tốc độ 0.75x) + upload R2
react-app/public/data/zh-lesson-<slug>.json     (đã điền audio = URL R2, cả câu lẫn phrase)
        │
        ▼ Xem trong react-app
/#/zh-lessons              → danh sách bài đã tạo
/#/zh-lesson/<slug>        → học từng đoạn, nghe lặp lại từng câu
```

2 bước chạy **tuần tự trong cùng 1 lệnh** — không cần gọi 2 script riêng.

---

## Cách chạy

```bash
cd /Users/nexusfrontiertech/projects/tools/learn-en-ch

# Cài dependency (1 lần) — chạy bằng python3 hệ thống, không cần venv riêng
pip3 install -r scripts/requirements.txt

# Sinh bài học đầy đủ (nội dung + audio)
python3 scripts/generate_zh_lesson.py "truyện ngụ ngôn" hsk1

# Tuỳ chỉnh số đoạn / giọng đọc
python3 scripts/generate_zh_lesson.py "gọi món ăn" hsk2 --paragraphs 5 --voice male

# Chỉ sinh nội dung, chưa tốn TTS — để đọc lại/sửa câu trước
python3 scripts/generate_zh_lesson.py "truyện ngụ ngôn" hsk1 --no-audio

# Chạy lại KHÔNG kèm --no-audio → tự phát hiện nội dung đã có, chỉ chạy tiếp bước audio
python3 scripts/generate_zh_lesson.py "truyện ngụ ngôn" hsk1

# Ghi đè nội dung đã tồn tại (sinh lại từ đầu, kể cả khi đã có audio thật)
python3 scripts/generate_zh_lesson.py "truyện ngụ ngôn" hsk1 --force

# Build lại nội dung từ 1 cache đã lưu, không gọi API lần nữa
python3 scripts/generate_zh_lesson.py "truyện ngụ ngôn" hsk1 --from-cache scripts/_generated/hsk1-truyen-ngu-ngon-20260711-063059.json

# Liệt kê các bài đã tạo
python3 scripts/generate_zh_lesson.py --list
```

### Các cờ

| Cờ | Mặc định | Ý nghĩa |
|---|---|---|
| `--paragraphs` | `4` | Số đoạn trong bài đọc |
| `--voice` | `female` | Giọng đọc: `female` (`zh-CN-XiaoxiaoNeural`) hoặc `male` (`zh-CN-YunxiNeural`) |
| `--no-audio` | tắt | Chỉ chạy Bước 1 (nội dung), không TTS |
| `--force` | tắt | Ghi đè nội dung đã tồn tại |
| `--max-retries` | `2` | Số lần DeepSeek tự sửa nếu validate fail |
| `--from-cache <path>` | — | Dùng lại 1 raw response đã cache thay vì gọi API |
| `--list` | — | Liệt kê bài đã tạo rồi thoát |

---

## Xem bài học

```bash
cd react-app
npm run dev
```

Mở `http://localhost:5199/#/zh-lessons` → chọn bài → mỗi câu có nút 🔊 phát riêng (nghe-lặp lại),
bên dưới là các "cụm" (phrase chip) nhỏ — mỗi cụm cũng có nút 🔊 riêng để tập đọc từng phần trước
khi ghép lại cả câu. Nút "Đoạn trước / Đoạn tiếp" để đi từng bước, thanh phát-tất-cả dưới cùng (chế
độ "中文") phát tuần tự các CÂU (không gồm phrase) trong đoạn đang xem.

---

## Output

| File | Mô tả |
|---|---|
| `react-app/public/data/zh-lesson-<slug>.json` | Bài học hoàn chỉnh — nguồn duy nhất react-app fetch để render |
| `react-app/public/data/zh-lessons-index.json` | Danh mục các bài đã tạo (script tự cập nhật mỗi lần chạy) |
| `scripts/_generated/<slug>-<timestamp>.json` | Cache raw response DeepSeek — không mất lần gọi API nào kể cả khi validate fail |
| `audio/zh_<hash>.mp3` | Cache audio local trước khi upload R2 (1 file/câu + 1 file/phrase, tốc độ 0.75x) |
| R2 bucket `audio/zh_<hash>.mp3` | Audio thật được serve cho react-app (URL public ghi vào `lesson.json`) |

`<slug>` = `<hsk-level>-<chủ đề đã bỏ dấu, kebab-case>`, vd `"truyện ngụ ngôn"` + `hsk1` →
`hsk1-truyen-ngu-ngon`.

---

## Cấu hình cần thiết

`.env` ở root cần có (dùng chung với các script khác trong `scripts/`, không cần thêm mới nếu đã
chạy `generate_lesson_deepseek.py` / `generate_audio_han.py` trước đó):

```
DEEPSEEK_API_KEY=...
R2_ACCOUNT_ID=...
R2_ACCESS_KEY=...
R2_SECRET_KEY=...
R2_PUBLIC_URL=...
```

Thiếu biến R2 → script vẫn ghi xong nội dung (Bước 1), chỉ bỏ qua Bước 2 kèm cảnh báo rõ ràng,
không crash.

---

## Troubleshooting

| Lỗi | Nguyên nhân | Cách fix |
|---|---|---|
| `Thiếu DEEPSEEK_API_KEY trong .env` | Chưa cấu hình `.env` | Thêm `DEEPSEEK_API_KEY=...` vào `.env` ở root |
| `Vẫn còn N lỗi sau K lần thử — KHÔNG ghi lesson.json` | DeepSeek liên tục lệch schema (sai số đoạn/câu, lẫn tiếng Latin trong `zh`) | Sửa tay file cache trong `scripts/_generated/`, chạy lại với `--from-cache <path>` |
| `<file> đã tồn tại — bỏ qua bước sinh nội dung` | Bình thường — script đang bảo vệ không ghi đè bài đã có | Dùng `--force` nếu thực sự muốn sinh lại nội dung |
| `Thiếu biến môi trường R2 (...) — bỏ qua bước audio` | Chưa cấu hình R2 trong `.env` | Điền đủ 4 biến `R2_*`, chạy lại lệnh (không cờ `--no-audio`) để tiếp tục audio |
| Bài đọc dùng từ vượt cấp độ HSK đã chọn | LLM ưu tiên mạch truyện tự nhiên hơn giới hạn từ vựng chặt — nhất là chủ đề cần từ kể chuyện (truyện ngụ ngôn, phiêu lưu...) | Chọn chủ đề đơn giản hơn phù hợp cấp độ (vd HSK1: "chào hỏi", "gia đình", "số đếm"), hoặc đọc lại + sửa tay trước khi chạy audio (`--no-audio`) |
| Trang `/zh-lessons` trống dù đã chạy script | `react-app/public/data/zh-lessons-index.json` chưa được tạo/ghi đúng chỗ | Kiểm tra script có in ra dòng `✅ Đã ghi react-app/public/data/zh-lesson-...json` không; nếu không, xem lỗi validate ở trên |
| `⚠️ Phrases không khớp câu ... dùng fallback chia theo dấu câu` | DeepSeek tách cụm nhưng nối lại không khớp nguyên câu (hiếm — validate+retry ở Bước 1 thường đã bắt lỗi này trước) | Không chặn pipeline — script tự chia theo dấu câu thay thế. Có thể bỏ qua, hoặc sửa tay `phrases` trong `lesson.json` rồi xoá `audio` liên quan để TTS lại đúng cụm mong muốn |
