# Deploy lên Serverless Stack

Project này là **static HTML thuần** (không cần server). Stack gồm:

- **Vercel** — host toàn bộ HTML/CSS/JS
- **Cloudflare R2** — lưu file audio MP3 (generate bằng `scripts/generate_audio.py`)
- **Supabase** — database/auth nếu thêm tính năng sau

---

## 1. Vercel (bắt buộc — host chính)

### Chuẩn bị

```bash
npm i -g vercel
```

### Deploy từ folder local (không cần GitHub)

```bash
cd /Users/nexusfrontiertech/projects/tools/learn-en-ch
vercel
```

Vercel sẽ hỏi vài câu:
- **Set up and deploy?** → `Y`
- **Which scope?** → chọn account của bạn
- **Link to existing project?** → `N` (lần đầu)
- **Project name?** → `learn-en-ch` (hoặc tên bạn muốn)
- **In which directory?** → `.` (Enter)
- **Override settings?** → `N`

Sau khi xong, Vercel in ra URL dạng `https://learn-en-ch-xxx.vercel.app`.

### Deploy lần tiếp theo

```bash
vercel --prod
```

### Deploy qua GitHub (khuyến nghị)

1. Tạo repo trên GitHub, push code lên
2. Vào [vercel.com](https://vercel.com) → **Add New Project** → Import repo
3. Vercel tự detect static site, không cần config gì thêm
4. Mỗi lần `git push` → Vercel tự build + deploy

### Custom domain (tuỳ chọn)

```bash
vercel domains add your-domain.com
```

Hoặc vào **Vercel Dashboard → Project → Settings → Domains**.

---

## 2. Cloudflare R2 (khi cần lưu audio/ảnh)

Hiện tại project chưa cần R2 vì chỉ có HTML. Dùng R2 khi bạn thêm file audio (phát âm), ảnh minh hoạ, v.v.

### Tạo bucket

```bash
# Cài Wrangler CLI
npm i -g wrangler
wrangler login

# Tạo bucket
wrangler r2 bucket create learn-en-ch-assets
```

### Upload file

```bash
# Upload 1 file
wrangler r2 object put learn-en-ch-assets/audio/hello.mp3 --file ./audio/hello.mp3

# Upload cả folder (dùng script)
for f in ./assets/*; do
  wrangler r2 object put "learn-en-ch-assets/$(basename $f)" --file "$f"
done
```

### Bật public access

Vào [dash.cloudflare.com](https://dash.cloudflare.com) → R2 → bucket `learn-en-ch-assets` → **Settings** → bật **Public Access**.

URL asset sẽ có dạng:
```
https://pub-xxxx.r2.dev/audio/hello.mp3
```

Dùng URL này trong HTML:
```html
<audio src="https://pub-xxxx.r2.dev/audio/hello.mp3"></audio>
```

### Giá

- **10 GB free** / tháng storage
- **1 triệu request free** / tháng
- Phù hợp hoàn toàn cho project nhỏ

---

## 3. Supabase (khi cần backend)

Dùng Supabase khi bạn muốn thêm:
- Lưu tiến trình học (đã học từ nào rồi)
- Tài khoản người dùng
- Danh sách từ vựng cá nhân

### Tạo project

1. Vào [supabase.com](https://supabase.com) → **New Project**
2. Đặt tên: `learn-en-ch`, chọn region gần nhất (Singapore)
3. Lưu lại **Project URL** và **anon key**

### Ví dụ: lưu từ vựng đã ôn

Tạo table trong Supabase SQL Editor:

```sql
create table vocab_progress (
  id uuid default gen_random_uuid() primary key,
  word text not null,
  pinyin text,
  review_count integer default 0,
  last_reviewed_at timestamptz default now()
);
```

Thêm vào HTML:

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
  const { createClient } = supabase;
  const sb = createClient('YOUR_URL', 'YOUR_ANON_KEY');

  async function markReviewed(word) {
    await sb.from('vocab_progress').upsert({ word, review_count: 1 });
  }
</script>
```

### Giá Supabase Free tier

| Tính năng | Free |
|---|---|
| Database | 500 MB |
| Auth users | 50,000 |
| Storage | 1 GB |
| Edge Functions | 500k invocations/tháng |

---

## 4. Audio Generation (scripts/generate_audio.py)

Script tự động:
- Đọc tất cả text tiếng Trung + tiếng Anh trong 4 file episoden
- Generate MP3 qua **edge-tts** (Microsoft TTS, miễn phí, không cần API key)
- Upload lên Cloudflare R2
- Inject nút 🔊 vào đúng vị trí trong HTML

### Giọng TTS

| Ngôn ngữ | Voice | Chất lượng |
|---|---|---|
| Tiếng Trung | `zh-CN-XiaoxiaoNeural` | Nữ, tự nhiên, chuẩn Phổ thông |
| Tiếng Anh | `en-US-AriaNeural` | Nữ, tự nhiên, giọng Mỹ |

### Bước 1 — Cài Python dependencies

```bash
cd /Users/nexusfrontiertech/projects/tools/learn-en-ch

# Tạo virtual environment (khuyến nghị)
python3 -m venv .venv
source .venv/bin/activate

# Cài packages
pip install -r scripts/requirements.txt
```

### Bước 2 — Tạo R2 API Token

1. Vào [dash.cloudflare.com](https://dash.cloudflare.com) → **R2** → **Manage R2 API Tokens**
2. Click **Create API Token**
3. Permission: **Object Read & Write** → chọn bucket `learn-en-ch-assets`
4. Copy **Access Key ID** và **Secret Access Key**

Bật public access cho bucket:
- R2 → `learn-en-ch-assets` → **Settings** → **Public Access** → Enable

### Bước 3 — Tạo file .env

```bash
cp .env.example .env
# Mở .env và điền thông tin R2 vào
```

Nội dung `.env`:
```
R2_ACCOUNT_ID=abc123def456          # Cloudflare Account ID (góc phải trên dashboard)
R2_ACCESS_KEY=your_access_key
R2_SECRET_KEY=your_secret_key
R2_BUCKET=learn-en-ch-assets
R2_PUBLIC_URL=https://pub-xxxx.r2.dev   # lấy từ Settings của bucket
```

### Bước 4 — Chạy script

```bash
python scripts/generate_audio.py
```

Output mẫu:
```
📄  ask.html
    🎙   TTS: '你叫什么名字？'
    ☁️   upload → r2://learn-en-ch-assets/audio/zh_a1b2c3d4e5f6.mp3
    🎙   TTS: "What's your name?"
    ☁️   upload → r2://learn-en-ch-assets/audio/en_9f8e7d6c5b4a.mp3
    ...
  ✅  Đã lưu ask.html

🎉  Hoàn tất!
```

Script **idempotent** — chạy lại an toàn:
- File MP3 đã có local → không generate lại
- Element đã có nút 🔊 → skip
- Chỉ generate + upload những gì còn thiếu

### Bước 5 — Deploy lại lên Vercel

```bash
vercel --prod
```

Vercel sẽ serve HTML đã được inject nút 🔊. File MP3 nằm trên R2 (không trong git).

### Giá edge-tts + R2

| | Chi phí |
|---|---|
| edge-tts (Microsoft) | **Miễn phí** hoàn toàn |
| R2 storage (10 GB) | **Miễn phí** |
| R2 egress | **Miễn phí** (không tính băng thông như S3) |

---

## Tóm tắt thứ tự làm

```
1. vercel --prod                      ← deploy HTML (5 phút)
2. Tạo R2 bucket + bật public access  ← 10 phút
3. cp .env.example .env               ← điền R2 credentials
4. pip install -r scripts/requirements.txt
5. python scripts/generate_audio.py   ← generate + upload audio
6. vercel --prod                      ← redeploy HTML có nút 🔊
7. Supabase                           ← khi muốn lưu tiến trình học
```

---

## Cấu trúc file

```
learn-en-ch/
├── index.html
├── .env                    ← KHÔNG commit (trong .gitignore)
├── .env.example            ← template
├── .gitignore
├── audio/                  ← cache MP3 local (trong .gitignore)
├── episoden/
│   ├── ask.html
│   ├── ask2.html
│   ├── introduce.html
│   └── introduce2.html
├── scripts/
│   ├── generate_audio.py   ← script chính
│   └── requirements.txt
└── docs/
    └── deploy.md
```


python3 -m venv .venv


python3 -m venv .venv
```

### Kích hoạt venv

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

> Khi active thành công, terminal sẽ hiện `(.venv)` ở đầu dòng.

### Cài packages

```bash
pip install -r requirements.txt
```
