# Learn EN + 中文 — React App

SPA học tiếng Anh và tiếng Trung, đọc data từ JSON, deploy dưới dạng static site.

---

## Cấu trúc quan trọng

```
react-app/
├── public/data/          ← 15 file JSON (generate từ Python script)
├── src/
│   ├── pages/            ← HomePage, AskPage, IntroducePage, WithKidPage
│   ├── components/       ← AudioBtn, PlayerBar, HomeBtn
│   └── hooks/            ← useAudioPlayer.js
└── ...

scripts/
└── extract-to-json.py    ← Script extract data từ HTML → JSON
```

---

## Chạy local

```bash
# 1. Cài dependencies (chỉ cần lần đầu)
cd react-app
npm install

# 2. Nếu JSON chưa có hoặc HTML vừa thay đổi — regenerate data
cd ..
python3 scripts/extract-to-json.py

# 3. Chạy dev server
cd react-app
npm run dev
# → http://localhost:5173
```

---

## Deploy lên Vercel

### Cách 1 — Vercel CLI (nhanh nhất)

```bash
# Cài Vercel CLI (nếu chưa có)
npm i -g vercel

cd react-app

# Build production trước
npm run build

# Deploy (Vercel tự đọc thư mục dist/)
vercel --prebuilt
```

Hoặc để Vercel tự build:

```bash
cd react-app
vercel
# Vercel sẽ tự chạy npm run build → tạo dist/ → upload
```

Khi Vercel hỏi:
- **Framework Preset** → `Vite`
- **Build Command** → `npm run build` *(default)*
- **Output Directory** → `dist` *(default)*
- **Root Directory** → để trống (đang ở trong `react-app/`)

### Cách 2 — Kết nối GitHub (tự động deploy)

1. Push repo lên GitHub
2. Vào [vercel.com](https://vercel.com) → **New Project** → Import repo
3. Cài đặt:
   - **Root Directory**: `react-app`
   - **Framework**: `Vite`
   - Build & Output giữ nguyên default
4. Click **Deploy**

Mỗi lần push lên `main` → Vercel tự build lại.

### Lưu ý quan trọng: JSON data phải có trong `public/data/`

File JSON trong `public/data/` **phải được commit vào git** vì Vercel cần chúng lúc build.

```bash
# Sau khi chạy extract script, commit JSON vào git
git add react-app/public/data/
git commit -m "chore: update lesson data JSON"
git push
```

Nếu **không muốn commit JSON** (vì nặng / tự động generate), có thể thêm bước trong Vercel build command:

```
# Vercel Build Command (cài bs4 rồi chạy script trước khi build)
pip install beautifulsoup4 && python3 ../scripts/extract-to-json.py && npm run build
```

---

## Cập nhật data khi thêm bài mới

```bash
# 1. Sửa / thêm file HTML trong episoden/, jobs/, han/
# 2. Regenerate JSON
python3 scripts/extract-to-json.py
# 3. Commit và push
git add react-app/public/data/
git commit -m "feat: thêm bài mới"
git push
```

---

## Build production

```bash
cd react-app
npm run build
# Output → react-app/dist/
```

Folder `dist/` là static site, có thể serve bằng bất kỳ web server nào.
