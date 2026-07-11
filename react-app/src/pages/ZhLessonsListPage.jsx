import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import HomeBtn from '../components/HomeBtn';

export default function ZhLessonsListPage() {
  const [lessons, setLessons] = useState(null);

  useEffect(() => {
    fetch('/data/zh-lessons-index.json')
      .then(r => (r.ok ? r.json() : []))
      .then(setLessons)
      .catch(() => setLessons([]));
  }, []);

  if (!lessons) return <div className="loading">Đang tải…</div>;

  return (
    <div className="inner-page">
      <HomeBtn />
      <header>
        <h1>Bài đọc tiếng Trung / HSK</h1>
        <div className="timer-badge">{lessons.length} bài</div>
      </header>

      {lessons.length === 0 ? (
        <div className="loading">
          Chưa có bài nào. Chạy <code>scripts/generate_zh_lesson.py "&lt;chủ đề&gt;" &lt;hsk-level&gt;</code> để tạo.
        </div>
      ) : (
        <div className="set-cards" style={{ maxWidth: 640, margin: '0 auto' }}>
          {lessons.map(l => (
            <Link key={l.id} className="nav-card" to={`/zh-lesson/${l.id}`}>
              <div className="card-icon">📖</div>
              <div className="card-type" style={{ color: '#34d399' }}>{l.level}</div>
              <div className="card-title">{l.title_vi} · {l.title_zh}</div>
              <div className="card-desc">
                Chủ đề: {l.topic_vi} · {l.paragraph_count} đoạn / {l.sentence_count} câu
              </div>
              <div className="card-arrow">Học →</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
