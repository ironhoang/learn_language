# So sánh TTS tiếng Việt: edge-tts vs Gemini

Công cụ nhỏ để nghe thử 1 câu tiếng Việt qua 2 giọng đọc khác nhau, phục vụ việc
chọn provider TTS cho nội dung tiếng Việt sau này. Đây là script độc lập, không
đi qua toàn bộ pipeline story→chunks→audio→... vì tiếng Việt chưa được cấu hình
như một `--language` đầy đủ (chưa có `languages/vietnamese/levels.yaml`).

## Cài đặt (một lần)

Dùng chung venv của `content-pipeline` — không cần cài thêm gì nếu bạn đã chạy
setup trong `content-pipeline/README.md`:

```bash
cd content-pipeline
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env   # rồi điền GEMINI_API_KEY (edge-tts không cần key)
```

## Chạy

```bash
cd content-pipeline
./.venv/bin/python compare_tts.py "Hãy kiểm tra lại campaign này và bố trí lịch quảng cáo facebook và google tuần tới?"
```

Mặc định dùng giọng nữ. Đổi sang giọng nam:

```bash
./.venv/bin/python compare_tts.py "Xin chào, hôm nay bạn có khỏe không?" --voice male
```

Kết quả nằm ở:
- `content-pipeline/output/tts_compare/edge.mp3` — edge-tts (`vi-VN-HoaiMyNeural` / `vi-VN-NamMinhNeural`)
- `content-pipeline/output/tts_compare/gemini.wav` — Gemini TTS (`gemini-2.5-flash-preview-tts`, giọng `Kore` / `Puck`)

Mỗi lần chạy sẽ ghi đè 2 file này — nghe xong đổi tên nếu muốn giữ lại để so sánh nhiều câu.

## Khác biệt giữa 2 provider

| | edge-tts | Gemini TTS |
|---|---|---|
| Cần API key | Không | Có (`GEMINI_API_KEY`) |
| Chi phí | Miễn phí | Tính theo token qua Gemini API |
| Timestamp từng từ | Có (dùng cho subtitle) | Không |
| Điều chỉnh tốc độ (`rate`) | Có (`+0%`, `-25%`...) | Không hỗ trợ |
| Định dạng file | mp3 | wav (PCM 24kHz mono, script tự đóng gói) |

## Dùng trong code

Cả hai provider đều implement chung interface `TTSProvider`
(`generator/providers/tts.py`), nên có thể lấy qua `get_tts_provider("edge")`
hoặc `get_tts_provider("gemini")` giống hệt cách `audio/generate.py` dùng.
Voice tiếng Việt cho edge-tts đã được thêm vào `_VOICE_MAP` trong
`generator/providers/tts_edge.py`; nếu sau này muốn đưa tiếng Việt vào pipeline
đầy đủ (`--language vietnamese`), bước còn thiếu là tạo
`languages/vietnamese/levels.yaml` giống thư mục `english/` và `chinese/`.
