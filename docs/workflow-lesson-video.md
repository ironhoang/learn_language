# Workflow: Sinh bài học (DeepSeek) → Sinh video

Hướng dẫn dùng 2 script để tạo nội dung cho module "English Workflow for AI Engineers":

- `scripts/generate_lesson_deepseek.py` — sinh `workflows/<id>/lesson.json` bằng DeepSeek API
- `scripts/generate_workflow_video.py` — sinh video dọc (9:16) từ `lesson.json` đã có audio

Hai script này là 2 bước trong cùng 1 pipeline: **catalog → lesson.json → audio → video**.

---

## Tổng quan pipeline

```
workflows/catalog.json (danh mục, chỉ có metadata)
        │
        ▼  scripts/generate_lesson_deepseek.py
workflows/<id>/lesson.json   (nodes, chunks, recall, conversations — audio fields rỗng)
        │
        ▼  scripts/generate_audio_workflow.py <id>   ← bước trung gian, không thuộc phạm vi doc này
workflows/<id>/lesson.json   (đã điền audio, audio_slow, prompt_audio — URL trên R2)
        │
        ▼  scripts/generate_workflow_video.py <id>
workflows/<id>/video/{nodes,chunks,recall,conversation-N}.mp4
```

`generate_workflow_video.py` **cần** `lesson.json` đã có audio thật (bước `generate_audio_workflow.py`) thì chunks/recall/conversation mới có giọng đọc để tải về ghép; nếu chưa có audio, script vẫn chạy được nhưng sẽ tự TTS tạm cho phần thiếu.

---

## Phần 1 — `generate_lesson_deepseek.py`

### Script này làm gì

Gọi DeepSeek API (OpenAI-compatible) để soạn một bài học hoàn chỉnh đúng schema (`workflows/lesson.schema.json`), dùng bài **Daily Standup** có sẵn làm few-shot mẫu (giọng văn, cách chia chunk, cách tách phrase).

### Các bước xử lý (step by step)

1. **Đọc danh mục** — `workflows/catalog.json` chứa `title`, `title_vi`, `category`, `tags`, `hint` (mô tả kịch bản) cho từng workflow id. Thêm workflow mới chỉ cần thêm 1 entry JSON vào đây, không cần sửa code.
2. **Chọn workflow** — truyền thẳng id (`sprint-planning`), hoặc để trống để hiện menu chọn tương tác (chỉ liệt kê workflow *chưa* có `lesson.json`).
3. **Build prompt** — ghép:
   - `MODULE_PHILOSOPHY`: triết lý nội dung (workflow-first, chunk-first, audio-first, hạn chế giải thích ngữ pháp)
   - toàn bộ JSON Schema (`lesson.schema.json`)
   - toàn bộ `daily-standup/lesson.json` làm ví dụ mẫu
   - `CRITICAL_RULES`: các ràng buộc output bắt buộc (xem bên dưới)
4. **Gọi DeepSeek** (`model=deepseek-chat`, `response_format=json_object`, `temperature=0.8`, `max_tokens=16000`) để ép trả JSON thuần.
5. **Cache RAW response** ngay lập tức vào `workflows/_generated/<id>-<timestamp>.json` — **không ghi đè**, để không mất lần gọi API nào (kể cả khi validate fail).
6. **Validate draft**, kiểm tra:
   - đúng JSON Schema (`jsonschema.validate`)
   - `meta.id` khớp đúng workflow id
   - mọi `chunks[].node_id` trỏ tới 1 node có thật
   - mỗi node có **4–6 chunk** (không hơn không kém)
   - mỗi conversation có **≥ 6 turn**
   - **quan trọng nhất**: nối `phrases[].text` bằng dấu cách phải khớp **chính xác từng ký tự** với `example` (không paraphrase, chỉ được tách câu)
7. **Tự động sửa nếu lỗi** — nếu validate fail, gửi lại lỗi cụ thể cho DeepSeek và yêu cầu trả JSON đầy đủ đã sửa (tối đa `--max-retries`, mặc định 2 lần).
8. **Ghi file** — nếu pass, ghi `workflows/<id>/lesson.json` (mọi field `audio`, `audio_slow`, `prompt_audio` để `""`, sẽ điền ở bước audio sau).
9. **In hướng dẫn bước tiếp theo** ra terminal.

### Cách chạy

```bash
# Xem trạng thái đã/chưa generate
python3 scripts/generate_lesson_deepseek.py --list

# Chọn workflow từ danh sách tương tác
python3 scripts/generate_lesson_deepseek.py

# Generate thẳng 1 id cụ thể
python3 scripts/generate_lesson_deepseek.py sprint-planning

# Tùy chỉnh độ khó / thời lượng
python3 scripts/generate_lesson_deepseek.py sprint-planning --difficulty advanced --duration 20

# Build lại từ 1 cache đã lưu (không gọi API lần nữa)
python3 scripts/generate_lesson_deepseek.py code-review --from-cache workflows/_generated/code-review-20260709-101500.json

# Ghi đè lesson.json đã tồn tại (kể cả đã có audio thật — cẩn thận!)
python3 scripts/generate_lesson_deepseek.py sprint-planning --force
```

### Sau khi có `lesson.json`

1. **Đọc lại bằng mắt người** — kiểm tra câu có tự nhiên không, TRƯỚC KHI chạy audio (sửa text sau khi đã có audio thật sẽ lãng phí, vì audio phải sinh lại).
2. Chạy `python3 scripts/generate_audio_workflow.py <id>` để điền audio.
3. Thêm shell HTML `workflows/<id>/index.html` (copy từ `daily-standup/index.html`, đổi title).
4. Bỏ class `"soon"` cho card tương ứng trong `workflows/index.html`.

### Cấu hình cần thiết

`.env` ở root cần có:
```
DEEPSEEK_API_KEY=your_deepseek_api_key
```

---

## Phần 2 — `generate_workflow_video.py`

### Script này làm gì

`scripts/generate_workflow_video.py` chỉ là **wrapper mỏng** — logic thật nằm ở `content-pipeline/workflow_video.py` và chạy dưới venv riêng của `content-pipeline` (vì cần `edge-tts`, `pypinyin`, `ffmpeg` mà môi trường `scripts/` ở root không cài).

Mục đích: dựng video dọc ngắn từ 1 `lesson.json` **đã có sẵn**, tái sử dụng máy render ASS subtitle + gradient background + ffmpeg có sẵn trong content-pipeline — vì chunk/recall/conversation đã có audio + text thật rồi, chỉ cần tải về, ghép, và render, không cần gọi LLM/TTS lại (trừ phần `nodes`).

### 4 loại video có thể sinh cho mỗi workflow

| kind | Nguồn text | Nguồn audio |
|------|-----------|-------------|
| `nodes` | `nodes[].label` (nhãn các bước trong sơ đồ workflow) | **TTS mới** (schema không có audio cho node) |
| `chunks` | `chunks[].example` | `chunks[].audio` (đã sinh sẵn) |
| `recall` | `recall[].prompt` | `recall[].prompt_audio` (đã sinh sẵn) |
| `conversation-<n>` | `conversations[n-1].turns[].text` | `conversations[n-1].turns[].audio` (đã sinh sẵn) |

### Các bước xử lý (step by step)

1. **Đọc `lesson.json`** của workflow id được truyền vào.
2. **Xác định danh sách "kind" cần sinh** — nếu có `--only`, chỉ sinh 1 loại; nếu không, sinh cả 4 loại (`nodes`, `chunks`, `recall`, và 1 `conversation-N` cho mỗi conversation có trong bài).
3. Với mỗi kind, gọi `generate_video(workflow_id, kind)`:
   a. **Lấy danh sách segment** `(text, audio_url)` tương ứng với kind (xem bảng trên).
   b. **Lấy audio cho từng segment**:
      - nếu đã có `audio_url` → tải về, cache tại `content-pipeline/cache/workflow_video/<md5>.mp3` (dùng header `User-Agent: Mozilla/5.0` vì Cloudflare R2 chặn user-agent mặc định của `urllib`).
      - nếu không có (chỉ xảy ra với `nodes`) → tự synthesize bằng **edge-tts** (giọng nam, resolve qua `resolve_voice("english", "male")`).
   c. **Đo duration** từng đoạn audio (`probe_duration`, dùng ffprobe), dựng timeline `subtitle.json` (mảng `{sentence, start, end}`) để khớp phụ đề với audio.
   d. **Ghép toàn bộ audio** thành 1 file `combined.mp3` bằng ffmpeg (`concat` demuxer + **re-encode** `libmp3lame 128k` — re-encode chứ không stream-copy để tránh lỗi khi ghép các file có codec khác nhau: file tải từ R2 vs file TTS mới sinh).
   e. **Render video** bằng `renderer_ffmpeg` (ASS subtitle cuộn/tĩnh + nền gradient), dùng cấu hình `content-pipeline/config/config.yaml` (`video:` section) cộng thêm `language=english`, `topic` và `level` lấy từ `lesson["meta"]`.
   f. **Ghi output** vào `workflows/<id>/video/<kind>.mp4`.
4. In đường dẫn từng file video đã sinh ra terminal.

### Cách chạy

```bash
# Sinh cả 4 loại video (nodes, chunks, recall, mọi conversation-N)
python3 scripts/generate_workflow_video.py architecture-discussion

# Chỉ sinh 1 loại
python3 scripts/generate_workflow_video.py architecture-discussion --only chunks
python3 scripts/generate_workflow_video.py architecture-discussion --only nodes
python3 scripts/generate_workflow_video.py architecture-discussion --only conversation-1
```

> Script tự chạy dưới `content-pipeline/.venv/bin/python` — không cần tự kích hoạt venv, nhưng venv đó phải đã được tạo và cài dependencies của `content-pipeline` (xem `content-pipeline/README.md`).

### Output

| File | Mô tả |
|------|--------|
| `workflows/<id>/video/nodes.mp4` | Video đọc tên các bước trong sơ đồ workflow |
| `workflows/<id>/video/chunks.mp4` | Video đọc lần lượt các câu ví dụ (chunks) |
| `workflows/<id>/video/recall.mp4` | Video đọc các câu hỏi ôn tập (recall) |
| `workflows/<id>/video/conversation-N.mp4` | Video hội thoại thứ N, đọc theo đúng thứ tự turn |
| `content-pipeline/cache/workflow_video/` | Cache audio tải về từ R2 (theo md5 của URL) + audio TTS tạm cho `nodes` |

---

## Sơ đồ toàn cảnh

```
1. workflows/catalog.json                      (metadata — viết tay)
        │
2. generate_lesson_deepseek.py <id>            (gọi DeepSeek, validate, retry)
        │  → workflows/_generated/<id>-<ts>.json   (cache raw response)
        │  → workflows/<id>/lesson.json             (audio fields rỗng)
        │
   [người review lại câu văn — TRƯỚC khi chạy audio]
        │
3. generate_audio_workflow.py <id>              (điền audio thật, upload R2)
        │  → workflows/<id>/lesson.json             (đã có URL audio)
        │
4. generate_workflow_video.py <id>              (wrapper → content-pipeline/workflow_video.py)
        │  → workflows/<id>/video/*.mp4
        │
5. Thêm workflows/<id>/index.html + bỏ class "soon" trong workflows/index.html
```

---

## Troubleshooting

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| `Thiếu DEEPSEEK_API_KEY trong .env` | Chưa cấu hình `.env` ở root | Thêm `DEEPSEEK_API_KEY=...` vào `.env` |
| `Validate fail ... phrases nối lại không khớp example` | DeepSeek paraphrase thay vì chỉ tách câu | Script tự retry; nếu vẫn fail sau `--max-retries`, sửa tay file cache rồi chạy lại với `--from-cache` |
| `lesson.json đã tồn tại` khi generate | Tránh ghi đè bài đã có audio thật | Chỉ dùng `--force` khi chắc chắn muốn generate lại từ đầu |
| `node 'x' có N chunk (yêu cầu 4-6)` | DeepSeek sinh thiếu/thừa chunk cho 1 node | Tự động retry kèm lỗi cụ thể; sửa tay nếu vẫn fail |
| Video thiếu giọng đọc cho chunk/recall | Chưa chạy `generate_audio_workflow.py` trước | Chạy bước điền audio trước khi sinh video |
| `403` khi tải audio từ R2 | Cloudflare chặn User-Agent mặc định | Đã xử lý sẵn trong code (header giả lập trình duyệt) — nếu vẫn lỗi, kiểm tra URL/bucket public |
| `ffmpeg: command not found` | Chưa cài ffmpeg trong môi trường content-pipeline | Cài ffmpeg (`brew install ffmpeg`) và đảm bảo chạy đúng venv của content-pipeline |
