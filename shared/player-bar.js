/* player-bar.js — Play All / ZH / EN / Stop bar, shared across episode & job pages */
(function () {
  'use strict';

  /* ── CSS ──────────────────────────────────────────────────────── */
  var css = document.createElement('style');
  css.textContent =
    '#play-all-bar{' +
    'position:fixed;bottom:0;left:0;right:0;height:54px;' +
    'background:#0a0e19;border-top:1px solid #1e293b;' +
    'display:flex;align-items:center;justify-content:center;gap:7px;' +
    'z-index:500;padding:0 12px;}' +

    '.pa-btn{' +
    'display:inline-flex;align-items:center;' +
    'background:#1e293b;border:1px solid #334155;color:#94a3b8;' +
    'font-size:0.78rem;font-weight:600;padding:6px 13px;' +
    'border-radius:8px;cursor:pointer;transition:all 0.15s;' +
    'font-family:inherit;white-space:nowrap;}' +
    '.pa-btn:hover{border-color:#475569;color:#cbd5e1;}' +
    '.pa-btn.active{border-color:#f97316;color:#f97316;}' +

    '#pa-divider{width:1px;height:22px;background:#1e293b;flex-shrink:0;margin:0 2px;}' +

    '#pa-stop{' +
    'background:transparent;border:1px solid #334155;color:#64748b;' +
    'font-size:0.78rem;padding:6px 10px;border-radius:8px;' +
    'cursor:pointer;transition:all 0.15s;font-family:inherit;}' +
    '#pa-stop:hover{border-color:#475569;color:#94a3b8;}' +

    '#pa-status{' +
    'font-size:0.7rem;color:#475569;min-width:36px;text-align:center;' +
    'font-variant-numeric:tabular-nums;}' +

    '@media(max-width:420px){' +
    '.pa-btn{padding:6px 9px;font-size:0.72rem;}' +
    '#pa-stop{padding:6px 8px;font-size:0.72rem;}' +
    '#pa-status{min-width:28px;}' +
    '}';
  document.head.appendChild(css);

  /* ── Bar HTML ─────────────────────────────────────────────────── */
  var bar = document.createElement('div');
  bar.id = 'play-all-bar';
  bar.innerHTML =
    '<button class="pa-btn" id="pa-all">▶ Tất cả</button>' +
    '<button class="pa-btn" id="pa-zh">▶ 中文</button>'  +
    '<button class="pa-btn" id="pa-en">▶ EN</button>'    +
    '<span id="pa-status"></span>'                        +
    '<div id="pa-divider"></div>'                         +
    '<button id="pa-stop">■ Dừng</button>';
  document.body.appendChild(bar);

  document.body.style.paddingBottom = '70px';

  /* ── Modes ────────────────────────────────────────────────────── */
  var MODES = {
    all: {
      btn: document.getElementById('pa-all'),
      idle: '▶ Tất cả', running: '⏸ Tất cả',
      src: function () { return document.querySelectorAll('.audio-btn[data-src]'); }
    },
    zh: {
      btn: document.getElementById('pa-zh'),
      idle: '▶ 中文', running: '⏸ 中文',
      src: function () { return document.querySelectorAll('.zh .audio-btn[data-src]'); }
    },
    en: {
      btn: document.getElementById('pa-en'),
      idle: '▶ EN', running: '⏸ EN',
      src: function () { return document.querySelectorAll('.en .audio-btn[data-src]'); }
    }
  };

  /* ── State ────────────────────────────────────────────────────── */
  var pa = { list: [], idx: 0, audio: null, on: false, mode: null };

  var statusEl = document.getElementById('pa-status');

  /* ── Helpers ──────────────────────────────────────────────────── */
  function clearCurrent() {
    if (pa.audio) { pa.audio.pause(); pa.audio = null; }
    pa.list.forEach(function (b) { b.classList.remove('playing'); });
  }

  function stopManualIfAny() {
    var btn = document.querySelector('.audio-btn.playing');
    if (btn && window.playAudio) window.playAudio(btn);
  }

  function resetBtns() {
    Object.keys(MODES).forEach(function (k) {
      MODES[k].btn.textContent = MODES[k].idle;
      MODES[k].btn.classList.remove('active');
    });
  }

  function updateStatus() {
    statusEl.textContent = pa.on ? (pa.idx + 1) + ' / ' + pa.list.length : '';
  }

  /* ── Advance playlist ─────────────────────────────────────────── */
  function step() {
    if (!pa.on) return;
    if (pa.idx >= pa.list.length) { pa.idx = 0; } /* loop */

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
  function startMode(mode) {
    stopManualIfAny();
    clearCurrent();
    pa.list = Array.from(mode.src());
    if (!pa.list.length) return;
    pa.idx  = 0;
    pa.on   = true;
    pa.mode = mode;
    resetBtns();
    mode.btn.textContent = mode.running;
    mode.btn.classList.add('active');
    step();
  }

  function stopAll() {
    pa.on   = false;
    pa.mode = null;
    clearCurrent();
    resetBtns();
    updateStatus();
  }

  /* ── Wire buttons ─────────────────────────────────────────────── */
  Object.keys(MODES).forEach(function (k) {
    var m = MODES[k];
    m.btn.addEventListener('click', function () {
      if (pa.on && pa.mode === m) stopAll(); else startMode(m);
    });
  });

  document.getElementById('pa-stop').addEventListener('click', stopAll);

  /* ── Stop play-all when user manually clicks an audio button ──── */
  document.addEventListener('click', function (e) {
    var t   = e.target;
    var btn = t.closest
      ? t.closest('.audio-btn')
      : (t.classList && t.classList.contains('audio-btn') ? t : null);
    if (btn && pa.on) stopAll();
  }, true /* capture: fires before inline onclick */);

})();
