/*
 * workflows/shared/favorites.js
 * Trang "Favorite Expressions" — gom các chunk đã ⭐ từ mọi workflow.
 * Đọc ew_favorites (key "<lessonId>:<chunkId>"), fetch lesson.json tương ứng, render lại thành chunk-card.
 */
(async function () {
  const root = document.getElementById('favorites');
  if (!root) return;
  const P = window.EWProgress;

  const favs = P.loadFavorites();
  const keys = Object.keys(favs).filter((k) => favs[k]);

  if (!keys.length) {
    renderEmpty();
    return;
  }

  const byLesson = {};
  for (const key of keys) {
    const [lessonId, chunkId] = key.split(':');
    (byLesson[lessonId] = byLesson[lessonId] || []).push(chunkId);
  }

  const lessonIds = Object.keys(byLesson);
  const lessons = await Promise.all(
    lessonIds.map(async (id) => {
      try {
        const res = await fetch(`./${id}/lesson.json`);
        if (!res.ok) return null;
        return { id, data: await res.json() };
      } catch {
        return null;
      }
    })
  );

  const sections = lessons
    .filter(Boolean)
    .map(({ id, data }) => {
      const chunkIds = new Set(byLesson[id]);
      const chunks = data.chunks.filter((c) => chunkIds.has(c.id));
      if (!chunks.length) return '';
      const cards = chunks.map((c) => renderFavCard(id, c)).join('');
      return `
        <div class="fav-lesson-group">
          <div class="fav-lesson-title"><a href="${esc(id)}/index.html">${esc(data.meta.title)}</a></div>
          ${cards}
        </div>`;
    })
    .join('');

  if (!sections.trim()) {
    renderEmpty();
    return;
  }

  root.innerHTML =
    renderHeader() +
    `
    <section class="section">
      <h2 class="section-title">Favorite Expressions</h2>
      ${sections}
    </section>`;

  wirePlayButtons();
  wireUnfavorite();

  // ── Render ──────────────────────────────────────────────────────────────

  function renderHeader() {
    return `
      <header class="lesson-header">
        <div class="header-links">
          <a class="back" href="./index.html">← English Workflow</a>
        </div>
        <h1>⭐ Favorite Expressions</h1>
        <p class="desc">Các câu bạn đã đánh dấu yêu thích, gom từ mọi workflow.</p>
      </header>`;
  }

  function renderEmpty() {
    root.innerHTML =
      renderHeader() +
      `
      <section class="section">
        <p class="empty-state">Chưa có câu nào được đánh dấu ⭐. Vào 1 lesson, tap ngôi sao ở mỗi chunk để lưu vào đây.</p>
      </section>`;
  }

  function renderFavCard(lessonId, c) {
    const favKey = `${lessonId}:${c.id}`;
    const chips = (c.phrases || [])
      .map((p) => `<button class="phrase-chip" data-url="${esc(p.audio)}">${esc(p.text)}</button>`)
      .join('');
    return `
      <div class="chunk-card" data-fav-card="${esc(favKey)}">
        <div class="chunk-card-top">
          <div class="chunk-text">${esc(c.text)}</div>
          <button class="fav-btn active" data-fav="${esc(favKey)}" title="Bỏ yêu thích">★</button>
        </div>
        <div class="chunk-phrases">${chips}</div>
        <div class="chunk-example">${esc(c.example)}</div>
        <div class="chunk-vi">${esc(c.translation_vi)}</div>
        <div class="example-audio-row">
          <button class="audio-btn" data-url="${esc(c.audio)}" title="Nghe nguyên câu">🔊</button>
          <button class="audio-btn slow" data-url="${esc(c.audio_slow)}" title="Nghe chậm">🐢</button>
        </div>
      </div>`;
  }

  // ── Audio (single-shot player — không cần sequence trên trang này) ───────

  let audio = null;
  let activeEl = null;

  function playOneShot(url, el) {
    const wasThisPlaying = activeEl === el && audio;
    if (audio) audio.pause();
    if (activeEl) activeEl.classList.remove('playing');
    audio = null;
    activeEl = null;
    if (wasThisPlaying || !url) return;
    audio = new Audio(url);
    activeEl = el;
    el.classList.add('playing');
    audio.play().catch(() => {});
    audio.onended = () => {
      el.classList.remove('playing');
      activeEl = null;
      audio = null;
    };
  }

  function wirePlayButtons() {
    root.querySelectorAll('.audio-btn, .phrase-chip').forEach((btn) => {
      btn.addEventListener('click', () => playOneShot(btn.dataset.url, btn));
    });
  }

  function wireUnfavorite() {
    root.querySelectorAll('.fav-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.fav;
        const current = P.loadFavorites();
        delete current[key];
        P.saveFavorites(current);
        const card = btn.closest('[data-fav-card]');
        const group = card ? card.closest('.fav-lesson-group') : null;
        if (card) card.remove();
        if (group && !group.querySelector('.chunk-card')) group.remove();
        if (!root.querySelector('.chunk-card')) renderEmpty();
      });
    });
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]);
  }
})();
