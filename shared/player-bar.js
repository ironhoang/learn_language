/* player-bar.js — Play All / Stop bar, shared across all episode & job pages */
(function () {
  'use strict';

  /* ── CSS ──────────────────────────────────────────────────────── */
  var css = document.createElement('style');
  css.textContent =
    '#play-all-bar{' +
    'position:fixed;bottom:0;left:0;right:0;height:54px;' +
    'background:#0a0e19;border-top:1px solid #1e293b;' +
    'display:flex;align-items:center;justify-content:center;gap:10px;' +
    'z-index:500;padding:0 16px;}' +

    '#pa-play{' +
    'display:inline-flex;align-items:center;gap:6px;' +
    'background:#1e293b;border:1px solid #334155;color:#94a3b8;' +
    'font-size:0.8rem;font-weight:600;padding:7px 16px;' +
    'border-radius:8px;cursor:pointer;transition:all 0.15s;font-family:inherit;}' +
    '#pa-play:hover{border-color:#475569;color:#cbd5e1;}' +
    '#pa-play.active{border-color:#f97316;color:#f97316;}' +

    '#pa-stop{' +
    'display:inline-flex;align-items:center;gap:4px;' +
    'background:transparent;border:1px solid #334155;color:#64748b;' +
    'font-size:0.78rem;padding:7px 12px;border-radius:8px;' +
    'cursor:pointer;transition:all 0.15s;font-family:inherit;}' +
    '#pa-stop:hover{border-color:#475569;color:#94a3b8;}' +

    '#pa-status{' +
    'font-size:0.72rem;color:#475569;min-width:44px;text-align:center;' +
    'font-variant-numeric:tabular-nums;}';
  document.head.appendChild(css);

  /* ── Bar HTML ─────────────────────────────────────────────────── */
  var bar = document.createElement('div');
  bar.id = 'play-all-bar';
  bar.innerHTML =
    '<button id="pa-play">▶ Phát tất cả</button>' +
    '<span id="pa-status"></span>' +
    '<button id="pa-stop">■ Dừng</button>';
  document.body.appendChild(bar);

  /* Bottom padding so the bar doesn't cover the last card */
  document.body.style.paddingBottom = '70px';

  /* ── State ────────────────────────────────────────────────────── */
  var pa = { list: [], idx: 0, audio: null, on: false };

  var playBtn  = document.getElementById('pa-play');
  var stopBtn  = document.getElementById('pa-stop');
  var statusEl = document.getElementById('pa-status');

  /* ── Helpers ──────────────────────────────────────────────────── */
  function getList() {
    return Array.from(document.querySelectorAll('.audio-btn[data-src]'));
  }

  function clearCurrent() {
    if (pa.audio) { pa.audio.pause(); pa.audio = null; }
    pa.list.forEach(function (b) { b.classList.remove('playing'); });
  }

  function stopManualIfAny() {
    /* The inline playAudio() uses a private `active` var; the only safe
       way to stop it externally is to re-click the active button. */
    var btn = document.querySelector('.audio-btn.playing');
    if (btn && window.playAudio) window.playAudio(btn);
  }

  function updateStatus() {
    statusEl.textContent = pa.on
      ? (pa.idx + 1) + ' / ' + pa.list.length
      : '';
  }

  /* ── Advance playlist ─────────────────────────────────────────── */
  function step() {
    if (!pa.on) return;
    if (pa.idx >= pa.list.length) { pa.idx = 0; } /* loop back to start */

    var btn = pa.list[pa.idx];
    if (!btn || !btn.dataset.src) { pa.idx++; step(); return; }

    pa.list.forEach(function (b) { b.classList.remove('playing'); });
    btn.classList.add('playing');
    updateStatus();

    pa.audio = new Audio(btn.dataset.src);
    pa.audio.play().catch(function () { pa.idx++; step(); });
    pa.audio.onended = function () {
      btn.classList.remove('playing');
      pa.idx++;
      step();
    };
  }

  /* ── Start / Stop ─────────────────────────────────────────────── */
  function startAll() {
    stopManualIfAny();
    clearCurrent();
    pa.list = getList();
    if (!pa.list.length) return;
    pa.idx = 0;
    pa.on  = true;
    playBtn.textContent = '⏸ Đang phát';
    playBtn.classList.add('active');
    step();
  }

  function stopAll() {
    pa.on = false;
    clearCurrent();
    playBtn.textContent = '▶ Phát tất cả';
    playBtn.classList.remove('active');
    updateStatus();
  }

  /* ── Button listeners ─────────────────────────────────────────── */
  playBtn.addEventListener('click', function () {
    if (pa.on) stopAll(); else startAll();
  });
  stopBtn.addEventListener('click', stopAll);

  /* ── Stop play-all when user manually clicks an audio button ──── */
  document.addEventListener('click', function (e) {
    var t   = e.target;
    var btn = t.closest
      ? t.closest('.audio-btn')
      : (t.classList && t.classList.contains('audio-btn') ? t : null);
    if (btn && pa.on) stopAll();
  }, true /* capture phase: fires before inline onclick */);

})();
