/*
 * workflows/shared/hub.js
 * Chạy trên workflows/index.html — thêm % hoàn thành vào mỗi card thật (có data-lesson)
 * và render "Recently Learned" gom từ mọi lesson.
 *
 * % hoàn thành chỉ hiện nếu người dùng đã từng tương tác với lesson đó (có progress trong
 * localStorage) — cố ý không hiện "0%" cho lesson chưa mở lần nào, tránh gây hiểu nhầm.
 */
(async function () {
  const P = window.EWProgress;
  if (!P) return;

  const cards = Array.from(document.querySelectorAll('.card[data-lesson]'));
  if (!cards.length) return;

  const progressAll = P.loadProgress();

  const lessons = await Promise.all(
    cards.map(async (card) => {
      const id = card.dataset.lesson;
      try {
        const res = await fetch(`./${id}/lesson.json`);
        if (!res.ok) return null;
        const data = await res.json();
        return { id, card, data };
      } catch {
        return null;
      }
    })
  );

  const recent = [];

  lessons.filter(Boolean).forEach(({ id, card, data }) => {
    const lp = progressAll[id];
    if (lp) {
      const total = data.chunks.length;
      const mastered = data.chunks.filter((c) => P.isMastered(lp.chunks[c.id])).length;
      const pct = total ? Math.round((mastered / total) * 100) : 0;
      injectProgressBadge(card, pct);

      for (const c of data.chunks) {
        const cp = lp.chunks[c.id];
        if (cp && cp.lastAt) {
          recent.push({ lessonId: id, lessonTitle: data.meta.title, chunkId: c.id, example: c.example, lastAt: cp.lastAt });
        }
      }
    }
  });

  renderRecentlyLearned(recent);

  function injectProgressBadge(card, pct) {
    const meta = card.querySelector('.card-meta');
    if (!meta) return;
    const span = document.createElement('span');
    span.className = 'badge badge-progress';
    span.textContent = `${pct}% hoàn thành`;
    meta.appendChild(span);
  }

  function renderRecentlyLearned(items) {
    const section = document.getElementById('recently-learned');
    const list = section ? section.querySelector('.recent-list') : null;
    if (!section || !list || !items.length) return;

    items.sort((a, b) => b.lastAt - a.lastAt);
    const top = items.slice(0, 5);

    list.innerHTML = top
      .map(
        (it) => `
        <a class="recent-item" href="${esc(it.lessonId)}/index.html#chunk-${esc(it.chunkId)}">
          <span class="recent-item-text">${esc(it.example)}</span>
          <span class="recent-item-meta">${esc(it.lessonTitle)} · ${timeAgo(it.lastAt)}</span>
        </a>`
      )
      .join('');

    section.style.display = 'block';
  }

  function timeAgo(ms) {
    const diffMin = Math.floor((Date.now() - ms) / 60000);
    if (diffMin < 1) return 'vừa xong';
    if (diffMin < 60) return `${diffMin} phút trước`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr} giờ trước`;
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay} ngày trước`;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]);
  }
})();
