# Deploy lên Serverless Stack

Project này là **static HTML thuần** (không cần server). Stack gồm:

- **Vercel** — host toàn bộ HTML/CSS/JS
- **Cloudflare R2** — lưu assets tĩnh (audio, ảnh) khi cần
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

## Tóm tắt thứ tự làm

```
1. vercel --prod          ← deploy ngay hôm nay (5 phút)
2. R2 bucket              ← khi cần thêm audio/ảnh
3. Supabase               ← khi muốn lưu tiến trình học
```

---

## Cấu trúc file hiện tại

```
learn-en-ch/
├── index.html              ← trang chủ
├── episoden/
│   ├── ask.html            ← câu hỏi set 1
│   ├── ask2.html           ← câu hỏi set 2
│   ├── introduce.html      ← câu trả lời set 1
│   └── introduce2.html     ← câu trả lời set 2
└── docs/
    └── deploy.md           ← file này
```

Vercel sẽ serve `index.html` làm root, các đường dẫn tương đối giữa các file hoạt động bình thường.
