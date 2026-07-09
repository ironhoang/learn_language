/*
 * workflows/shared/lesson.js
 * Render lesson.json → UI + audio interactivity + progress tracking. Dùng chung cho mọi workflow.
 *
 * Trang shell cần: workflows/shared/progress.js load TRƯỚC file này, rồi
 * <div id="lesson"></div> + <script src="../shared/lesson.js"></script>
 * Script tự fetch ./lesson.json cạnh trang.
 *
 * Audio-first learning flow:
 *   - Chunk card: transcript (nguyên câu + nghĩa) bị blur, tap để hiện. Phrase chip luôn hiện, tap để nghe từng cụm.
 *   - Shadow mode / node: phát lần lượt từng phrase (có pause để nhắc lại) rồi phát nguyên câu, qua chunk kế.
 *   - Active recall: phát câu hỏi, tap "Show answers" mới hiện đáp án gợi ý.
 *   - Conversation: Play all (phát tuần tự) hoặc Role-play (đóng vai Engineer — hệ thống dừng ở lượt của bạn,
 *     bạn tự nói rồi tap để tiếp tục).
 *   - Favorite (⭐) và progress (nghe/shadow/mastery) lưu vào localStorage qua shared/progress.js
 *     (`ew_favorites`, `ew_progress`) — dùng chung cho hub và trang Favorites.
 */

(async function () {
  const root = document.getElementById('lesson');
  if (!root) return;
  const P = window.EWProgress;

  let lesson;
  try {
    const res = await fetch('./lesson.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    lesson = await res.json();
  } catch (err) {
    root.innerHTML = `<p class="error">Không tải được lesson.json — ${esc(String(err))}</p>`;
    return;
  }

  const progressAll = P.loadProgress();
  const lp = P.lessonProgress(progressAll, lesson.meta.id);

  document.title = `${lesson.meta.title} · English Workflow`;
  root.innerHTML = [
    renderMeta(lesson.meta),
    renderGraph(lesson.nodes),
    renderChunks(lesson.nodes, lesson.chunks, lp),
    renderRecall(lesson.recall),
    renderConversations(lesson.conversations, lp),
  ].join('');

  wireGraph();
  wireFavorites();
  wireReveal();
  wireSinglePlayButtons();
  wireRecallToggle();
  wireShadowButtons();
  wireConversationButtons();
  scrollToHashChunk();

  // ── Render ──────────────────────────────────────────────────────────────

  function renderMeta(meta) {
    return `
      <header class="lesson-header">
        <div class="header-links">
          <a class="back" href="../index.html">← English Workflow</a>
          <a class="fav-link" href="../favorites.html">⭐ Favorites</a>
        </div>
        <h1>${esc(meta.title)}</h1>
        <p class="title-vi">${esc(meta.title_vi)}</p>
        <p class="desc">${esc(meta.description)}</p>
        <div class="meta-badges">
          <span class="badge badge-${esc(meta.difficulty)}">${esc(meta.difficulty)}</span>
          <span class="badge">⏱ ${meta.duration_minutes} phút</span>
          <span class="badge">${esc(meta.category)}</span>
        </div>
      </header>`;
  }

  function renderGraph(nodes) {
    const items = nodes
      .map(
        (n) => `
        <div class="graph-node" data-node="${esc(n.id)}">
          <span class="graph-label">${esc(n.label)}</span>
          <span class="graph-label-vi">${esc(n.label_vi)}</span>
        </div>`
      )
      .join('<div class="graph-arrow">↓</div>');
    return `
      <section class="section">
        <h2 class="section-title">Workflow</h2>
        <div class="graph">${items}</div>
      </section>`;
  }

  function renderChunks(nodes, chunks, lp) {
    const byNode = nodes
      .map((n) => {
        const list = chunks.filter((c) => c.node_id === n.id);
        if (!list.length) return '';
        const cards = list.map((c) => renderChunkCard(c, lp)).join('');
        return `
          <div class="node-group" id="node-${esc(n.id)}">
            <div class="node-header">
              <h3 class="node-title">${esc(n.label)} <span class="node-title-vi">· ${esc(n.label_vi)}</span></h3>
              <button class="ctl-btn shadow-btn" data-idle-label="▶ Shadow" data-node="${esc(n.id)}">▶ Shadow</button>
            </div>
            ${cards}
          </div>`;
      })
      .join('');
    return `
      <section class="section">
        <h2 class="section-title">Chunks</h2>
        ${byNode}
      </section>`;
  }

  function renderChunkCard(c, lp) {
    const favKey = `${lesson.meta.id}:${c.id}`;
    const prog = lp.chunks[c.id] || { listen: 0, shadow: 0 };
    const mastered = P.isMastered(prog);
    return `
      <div class="chunk-card" id="chunk-${esc(c.id)}">
        <div class="chunk-card-top">
          <div class="chunk-text">${esc(c.text)}</div>
          <div class="chunk-card-actions">
            <span class="mastery-badge${mastered ? ' earned' : ''}" title="Đã thành thạo (nghe ≥3, shadow ≥3)">✓</span>
            <button class="fav-btn" data-fav="${esc(favKey)}" title="Yêu thích">☆</button>
          </div>
        </div>
        ${renderPhrases(c.phrases, c.id)}
        <div class="chunk-reveal blurred">
          <div class="reveal-hint">👁 Chạm để xem transcript</div>
          <div class="chunk-example">${esc(c.example)}</div>
          <div class="chunk-vi">${esc(c.translation_vi)}</div>
        </div>
        <div class="example-audio-row">
          <button class="audio-btn" data-url="${esc(c.audio)}" data-chunk="${esc(c.id)}" title="Nghe nguyên câu">🔊</button>
          <button class="audio-btn slow" data-url="${esc(c.audio_slow)}" data-chunk="${esc(c.id)}" title="Nghe chậm">🐢</button>
          <span class="chunk-stats">👂 ${prog.listen}&nbsp;&nbsp;🔁 ${prog.shadow}</span>
        </div>
      </div>`;
  }

  function renderRecall(recall) {
    if (!recall || !recall.length) return '';
    const items = recall
      .map(
        (r) => `
        <div class="recall-card">
          <div class="recall-top">
            <div class="recall-prompt">${esc(r.prompt)}</div>
            <button class="audio-btn" data-url="${esc(r.prompt_audio)}" title="Nghe câu hỏi">🔊</button>
          </div>
          ${r.hint_vi ? `<div class="recall-hint">${esc(r.hint_vi)}</div>` : ''}
          <button class="ctl-btn recall-toggle-btn" data-idle-label="Show answers" data-recall="${esc(r.id)}">Show answers</button>
          <div class="recall-answers hidden">${r.accepted_patterns.map((p) => `<span class="pattern">${esc(p)}...</span>`).join('')}</div>
        </div>`
      )
      .join('');
    return `
      <section class="section">
        <h2 class="section-title">Active Recall</h2>
        ${items}
      </section>`;
  }

  function renderConversations(convs, lp) {
    if (!convs || !convs.length) return '';
    const blocks = convs
      .map((c) => {
        const turns = c.turns.map(renderTurn).join('');
        const done = lp.conversations && lp.conversations[c.id];
        return `
          <div class="conversation">
            <div class="conv-header">
              <h3 class="conv-title">
                ${esc(c.title)}${c.title_vi ? ` <span class="node-title-vi">· ${esc(c.title_vi)}</span>` : ''}
                ${done ? '<span class="done-badge" title="Đã hoàn thành">✓</span>' : ''}
              </h3>
              <div class="conv-controls">
                <button class="ctl-btn playall-btn" data-idle-label="▶ Play all" data-conv="${esc(c.id)}">▶ Play all</button>
                <button class="ctl-btn roleplay-btn" data-idle-label="🎭 Role-play as Engineer" data-conv="${esc(c.id)}">🎭 Role-play as Engineer</button>
              </div>
            </div>
            <div class="turns" id="conv-${esc(c.id)}">${turns}</div>
          </div>`;
      })
      .join('');
    return `
      <section class="section">
        <h2 class="section-title">Mini Conversation</h2>
        ${blocks}
      </section>`;
  }

  function renderTurn(t) {
    const isEngineer = t.role === 'Engineer';
    return `
      <div class="turn turn-${isEngineer ? 'you' : 'other'}" data-url="${esc(t.audio)}" data-role="${esc(t.role)}">
        <div class="turn-head">
          <span class="turn-role">${esc(t.role)}</span>
          <button class="audio-btn small" data-url="${esc(t.audio)}" title="Nghe lượt này">🔊</button>
        </div>
        <span class="turn-text">${esc(t.text)}</span>
        ${renderPhrases(t.phrases)}
        ${t.translation_vi ? `<span class="turn-vi">${esc(t.translation_vi)}</span>` : ''}
      </div>`;
  }

  function renderPhrases(phrases, chunkId) {
    if (!phrases || !phrases.length) return '';
    const chunkAttr = chunkId ? ` data-chunk="${esc(chunkId)}"` : '';
    const chips = phrases.map((p) => `<button class="phrase-chip" data-url="${esc(p.audio)}"${chunkAttr}>${esc(p.text)}</button>`).join('');
    return `<div class="chunk-phrases">${chips}</div>`;
  }

  // ── Audio player (single shared instance, cancellable sequences) ─────────

  let audio = null;
  let activeEl = null;
  let pendingResolve = null;
  let seqToken = 0;
  let activeCtlBtn = null;

  function stopActive() {
    if (pendingResolve) {
      const r = pendingResolve;
      pendingResolve = null;
      r(0);
    }
    if (audio) {
      audio.onended = null;
      audio.onerror = null;
      audio.pause();
    }
    if (activeEl) activeEl.classList.remove('playing');
    audio = null;
    activeEl = null;
  }

  /** Phát 1 file, trả Promise resolve khi phát xong (duration giây) hoặc khi bị ngắt (0). */
  function playAwait(url, el) {
    return new Promise((resolve) => {
      stopActive();
      if (!url) {
        resolve(0);
        return;
      }
      audio = new Audio(url);
      activeEl = el || null;
      pendingResolve = resolve;
      if (activeEl) activeEl.classList.add('playing');
      audio.play().catch(() => {});
      audio.onended = () => {
        const dur = audio ? audio.duration || 1 : 1;
        pendingResolve = null;
        if (activeEl) activeEl.classList.remove('playing');
        audio = null;
        activeEl = null;
        resolve(dur);
      };
      audio.onerror = () => {
        pendingResolve = null;
        if (activeEl) activeEl.classList.remove('playing');
        audio = null;
        activeEl = null;
        resolve(1);
      };
    });
  }

  function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  /** Click nghe 1 clip đơn lẻ — hủy mọi sequence đang chạy, toggle nếu bấm lại chính nó. */
  function playOneShot(url, el) {
    const wasThisPlaying = activeEl === el && audio;
    seqToken++;
    resetActiveCtlBtn();
    stopActive();
    if (wasThisPlaying) return;
    playAwait(url, el);
  }

  function resetActiveCtlBtn() {
    if (activeCtlBtn) {
      activeCtlBtn.textContent = activeCtlBtn.dataset.idleLabel;
      activeCtlBtn.classList.remove('running');
      activeCtlBtn = null;
    }
  }

  function setCtlBtnRunning(btn, runningLabel) {
    resetActiveCtlBtn();
    btn.textContent = runningLabel;
    btn.classList.add('running');
    activeCtlBtn = btn;
  }

  function clearCtlBtn(btn) {
    btn.textContent = btn.dataset.idleLabel;
    btn.classList.remove('running');
    if (activeCtlBtn === btn) activeCtlBtn = null;
  }

  /** Gắn hành vi start/stop-toggle cho 1 nút điều khiển sequence (Shadow / Play all / Role-play). */
  function bindSequenceButton(btn, runningLabel, taskFn) {
    btn.addEventListener('click', async () => {
      if (btn.classList.contains('running')) {
        seqToken++;
        stopActive();
        clearCtlBtn(btn);
        return;
      }
      seqToken++;
      stopActive();
      const myToken = seqToken;
      setCtlBtnRunning(btn, runningLabel);
      await taskFn(myToken);
      if (myToken === seqToken) clearCtlBtn(btn);
    });
  }

  // ── Wiring: static single-play buttons ────────────────────────────────────

  function wireSinglePlayButtons() {
    root.querySelectorAll('.audio-btn, .phrase-chip').forEach((btn) => {
      btn.addEventListener('click', () => {
        playOneShot(btn.dataset.url, btn);
        if (btn.dataset.chunk) recordChunkEvent(btn.dataset.chunk, 'listen');
      });
    });
  }

  function wireGraph() {
    root.querySelectorAll('.graph-node').forEach((el) => {
      el.addEventListener('click', () => {
        const target = document.getElementById(`node-${el.dataset.node}`);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  function wireReveal() {
    root.querySelectorAll('.chunk-reveal.blurred').forEach((el) => {
      el.addEventListener('click', () => el.classList.remove('blurred'), { once: true });
    });
  }

  function wireRecallToggle() {
    root.querySelectorAll('.recall-toggle-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const answers = btn.nextElementSibling;
        const hidden = answers.classList.toggle('hidden');
        btn.textContent = hidden ? 'Show answers' : 'Hide answers';
        if (!hidden && btn.dataset.recall) recordRecallDone(btn.dataset.recall);
      });
    });
  }

  function scrollToHashChunk() {
    if (!location.hash.startsWith('#chunk-')) return;
    const target = document.getElementById(location.hash.slice(1));
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.classList.add('highlight');
    setTimeout(() => target.classList.remove('highlight'), 2000);
  }

  // ── Favorites (localStorage, via shared/progress.js) ──────────────────────

  function wireFavorites() {
    const favs = P.loadFavorites();
    root.querySelectorAll('.fav-btn').forEach((btn) => {
      const key = btn.dataset.fav;
      if (favs[key]) {
        btn.textContent = '★';
        btn.classList.add('active');
      }
      btn.addEventListener('click', () => {
        const current = P.loadFavorites();
        const isFav = !current[key];
        if (isFav) current[key] = true;
        else delete current[key];
        P.saveFavorites(current);
        btn.textContent = isFav ? '★' : '☆';
        btn.classList.toggle('active', isFav);
      });
    });
  }

  // ── Progress tracking (localStorage, via shared/progress.js) ──────────────

  function recordChunkEvent(chunkId, type) {
    const all = P.loadProgress();
    const lp2 = P.ensureLessonProgress(all, lesson.meta.id);
    const c = lp2.chunks[chunkId] || (lp2.chunks[chunkId] = { listen: 0, shadow: 0, lastAt: 0 });
    c[type] = (c[type] || 0) + 1;
    c.lastAt = Date.now();
    P.saveProgress(all);
    updateChunkStatsUI(chunkId, c);
  }

  function recordRecallDone(recallId) {
    const all = P.loadProgress();
    const lp2 = P.ensureLessonProgress(all, lesson.meta.id);
    if (lp2.recall[recallId]) return;
    lp2.recall[recallId] = true;
    P.saveProgress(all);
  }

  function recordConversationDone(convId) {
    const all = P.loadProgress();
    const lp2 = P.ensureLessonProgress(all, lesson.meta.id);
    if (lp2.conversations[convId]) return;
    lp2.conversations[convId] = true;
    P.saveProgress(all);
  }

  function updateChunkStatsUI(chunkId, c) {
    const card = document.getElementById(`chunk-${chunkId}`);
    if (!card) return;
    const statsEl = card.querySelector('.chunk-stats');
    if (statsEl) statsEl.innerHTML = `👂 ${c.listen}&nbsp;&nbsp;🔁 ${c.shadow}`;
    const badge = card.querySelector('.mastery-badge');
    if (badge) badge.classList.toggle('earned', P.isMastered(c));
  }

  // ── Shadowing mode ─────────────────────────────────────────────────────────

  function wireShadowButtons() {
    root.querySelectorAll('.shadow-btn').forEach((btn) => {
      bindSequenceButton(btn, '⏹ Stop', (token) => runShadow(btn.dataset.node, token));
    });
  }

  async function runShadow(nodeId, token) {
    const chunkEls = root.querySelectorAll(`#node-${cssEscape(nodeId)} .chunk-card`);
    for (const chunkEl of chunkEls) {
      if (token !== seqToken) return;
      const chunkId = chunkEl.id.replace('chunk-', '');
      const phraseBtns = chunkEl.querySelectorAll('.phrase-chip');
      for (const pBtn of phraseBtns) {
        if (token !== seqToken) return;
        const dur = await playAwait(pBtn.dataset.url, pBtn);
        if (token !== seqToken) return;
        const pause = Math.min(Math.max(dur, 0.8), 4) * 1000;
        await sleep(pause);
      }
      if (token !== seqToken) return;
      const fullBtn = chunkEl.querySelector('.example-audio-row .audio-btn:not(.slow)');
      await playAwait(fullBtn.dataset.url, chunkEl);
      if (token !== seqToken) return;
      recordChunkEvent(chunkId, 'shadow');
      await sleep(500);
    }
  }

  // ── Conversation: Play all + Role-play ──────────────────────────────────────

  function wireConversationButtons() {
    root.querySelectorAll('.playall-btn').forEach((btn) => {
      bindSequenceButton(btn, '⏹ Stop', (token) => runPlayAll(btn.dataset.conv, token));
    });
    root.querySelectorAll('.roleplay-btn').forEach((btn) => {
      bindSequenceButton(btn, '⏹ Stop', (token) => runRolePlay(btn.dataset.conv, token));
    });
  }

  async function runPlayAll(convId, token) {
    const turnEls = root.querySelectorAll(`#conv-${cssEscape(convId)} .turn`);
    for (const el of turnEls) {
      if (token !== seqToken) return;
      await playAwait(el.dataset.url, el);
      if (token !== seqToken) return;
      await sleep(300);
    }
    if (token === seqToken) recordConversationDone(convId);
  }

  async function runRolePlay(convId, token) {
    const turnEls = root.querySelectorAll(`#conv-${cssEscape(convId)} .turn`);
    for (const el of turnEls) {
      if (token !== seqToken) return;
      if (el.dataset.role === 'Engineer') {
        el.classList.add('your-turn');
        const proceed = await waitForContinue(el, token);
        el.classList.remove('your-turn');
        if (!proceed || token !== seqToken) return;
      } else {
        await playAwait(el.dataset.url, el);
        if (token !== seqToken) return;
        await sleep(300);
      }
    }
    if (token === seqToken) recordConversationDone(convId);
  }

  /** Hiện nút "Đã nói xong, tiếp tục" trên 1 turn, resolve(true) khi bấm, resolve(false) nếu sequence bị hủy. */
  function waitForContinue(turnEl, token) {
    return new Promise((resolve) => {
      const btn = document.createElement('button');
      btn.className = 'continue-btn';
      btn.textContent = '▶ Đã nói xong, tiếp tục';
      btn.addEventListener('click', () => {
        btn.remove();
        resolve(token === seqToken);
      });
      turnEl.appendChild(btn);

      const check = setInterval(() => {
        if (token !== seqToken) {
          clearInterval(check);
          btn.remove();
          resolve(false);
        }
      }, 200);
      btn.addEventListener('click', () => clearInterval(check));
    });
  }

  // ── Utils ──────────────────────────────────────────────────────────────────

  function cssEscape(s) {
    return String(s).replace(/[^a-zA-Z0-9_-]/g, '\\$&');
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]);
  }
})();
