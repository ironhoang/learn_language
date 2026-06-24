// Module-level singleton — one audio plays at a time across all components
let currentAudio = null;
let currentSrc = null;
let lastManualSrc = null; // last src the user clicked manually
let subscribers = [];

export function getLastManualSrc() { return lastManualSrc; }

function notify() {
  subscribers.forEach(fn => fn(currentSrc));
}

export function stopCurrent() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.onended = null;
    currentAudio = null;
    currentSrc = null;
    notify();
  }
}

export function playSrc(src, onEnded) {
  stopCurrent();
  if (!src) return;
  const audio = new Audio(src);
  currentAudio = audio;
  currentSrc = src;
  notify();
  audio.play().catch(() => {
    if (currentAudio === audio) {
      currentAudio = null;
      currentSrc = null;
      notify();
    }
    onEnded && onEnded();
  });
  audio.onended = () => {
    if (currentAudio === audio) {
      currentAudio = null;
      currentSrc = null;
      notify();
    }
    onEnded && onEnded();
  };
}

import { useState, useEffect } from 'react';

export function useAudioPlayer() {
  const [activeSrc, setActiveSrc] = useState(currentSrc);

  useEffect(() => {
    const cb = src => setActiveSrc(src);
    subscribers.push(cb);
    return () => {
      subscribers = subscribers.filter(fn => fn !== cb);
    };
  }, []);

  function toggle(src) {
    lastManualSrc = src; // remember where the user was
    if (currentSrc === src) stopCurrent();
    else playSrc(src);
  }

  return { activeSrc, toggle };
}
