import { useState, useRef } from 'react';
import { playSrc, stopCurrent, getLastManualSrc } from '../hooks/useAudioPlayer';

const MODES = {
  all: {
    idle: '▶ Tất cả',
    running: '⏸ Tất cả',
    selector: '.audio-btn[data-src]',
  },
  zh: {
    idle: '▶ 中文',
    running: '⏸ 中文',
    selector: '.zh .audio-btn[data-src], .vocab-chip > .audio-btn[data-src], .fq-zh .audio-btn[data-src]',
  },
  en: {
    idle: '▶ EN',
    running: '⏸ EN',
    selector: '.en .audio-btn[data-src], .ve .audio-btn[data-src], .fq-en .audio-btn[data-src]',
  },
};

export default function PlayerBar({ extraModes, onPlay }) {
  const [activeMode, setActiveMode] = useState(null);
  const [progress, setProgress] = useState({ idx: 0, total: 0 });
  const playlistRef = useRef(null); // ref so closure stays fresh

  const modes = extraModes ? { ...MODES, ...extraModes } : MODES;

  function collectSrcs(selector) {
    return Array.from(document.querySelectorAll(selector))
      .map(b => b.dataset.src)
      .filter(Boolean);
  }

  function advance(srcs, idx) {
    if (!playlistRef.current || playlistRef.current !== srcs) return; // stopped
    if (idx >= srcs.length) {
      stopAll();
      return;
    }
    setProgress({ idx: idx + 1, total: srcs.length });
    onPlay && onPlay(srcs[idx]);
    playSrc(srcs[idx], () => advance(srcs, idx + 1));
  }

  function startMode(key) {
    const srcs = collectSrcs(modes[key].selector);
    if (!srcs.length) return;

    // Start from the audio the user last clicked manually (if it's in this playlist)
    const lastSrc = getLastManualSrc();
    const startIdx = lastSrc ? Math.max(srcs.indexOf(lastSrc), 0) : 0;

    stopCurrent();
    playlistRef.current = srcs;
    setActiveMode(key);
    advance(srcs, startIdx);
  }

  function stopAll() {
    playlistRef.current = null;
    stopCurrent();
    setActiveMode(null);
    setProgress({ idx: 0, total: 0 });
  }

  function toggle(key) {
    if (activeMode === key) stopAll();
    else startMode(key);
  }

  return (
    <div id="play-all-bar">
      {Object.entries(modes).map(([key, cfg]) => (
        <button
          key={key}
          className={`pa-btn${activeMode === key ? ' active' : ''}`}
          onClick={() => toggle(key)}
        >
          {activeMode === key ? cfg.running : cfg.idle}
        </button>
      ))}
      <span id="pa-status">
        {activeMode && progress.total > 0 ? `${progress.idx} / ${progress.total}` : ''}
      </span>
      <div id="pa-divider" />
      <button id="pa-stop" onClick={stopAll}>■ Dừng</button>
    </div>
  );
}
