/*
 * workflows/shared/progress.js
 * Lưu trữ progress + favorites (localStorage). Dùng chung bởi lesson.js, hub.js, favorites.js.
 * Không có backend — mọi thứ nằm trên máy người học.
 *
 * ew_favorites: { "<lessonId>:<chunkId>": true, ... }
 * ew_progress : {
 *   "<lessonId>": {
 *     chunks: { "<chunkId>": { listen: n, shadow: n, lastAt: epochMs } },
 *     recall: { "<recallId>": true },
 *     conversations: { "<convId>": true }
 *   }
 * }
 *
 * Mastery: 1 chunk được coi là "đã thành thạo" khi nghe (listen) ≥ 3 lần
 * VÀ shadow (đọc theo) ≥ 3 lần. Đây là công thức đơn giản hoá — schema không
 * gắn recall với từng chunk cụ thể nên không thể cộng thêm điều kiện "recall pass"
 * như phác thảo ban đầu trong spec.
 */
(function (global) {
  const FAV_KEY = 'ew_favorites';
  const PROGRESS_KEY = 'ew_progress';
  const MASTERY_LISTEN = 3;
  const MASTERY_SHADOW = 3;

  function loadFavorites() {
    try {
      return JSON.parse(localStorage.getItem(FAV_KEY) || '{}');
    } catch {
      return {};
    }
  }
  function saveFavorites(obj) {
    localStorage.setItem(FAV_KEY, JSON.stringify(obj));
  }

  function loadProgress() {
    try {
      return JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}');
    } catch {
      return {};
    }
  }
  function saveProgress(obj) {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(obj));
  }

  /** Đọc progress của 1 lesson, không ghi vào storage (dùng khi chỉ cần render). */
  function lessonProgress(all, lessonId) {
    return all[lessonId] || { chunks: {}, recall: {}, conversations: {} };
  }

  /** Đọc + đảm bảo tồn tại trong `all` (dùng khi sắp ghi thêm dữ liệu). */
  function ensureLessonProgress(all, lessonId) {
    if (!all[lessonId]) all[lessonId] = { chunks: {}, recall: {}, conversations: {} };
    return all[lessonId];
  }

  function isMastered(chunkProgress) {
    return !!chunkProgress && chunkProgress.listen >= MASTERY_LISTEN && chunkProgress.shadow >= MASTERY_SHADOW;
  }

  global.EWProgress = {
    FAV_KEY,
    PROGRESS_KEY,
    MASTERY_LISTEN,
    MASTERY_SHADOW,
    loadFavorites,
    saveFavorites,
    loadProgress,
    saveProgress,
    lessonProgress,
    ensureLessonProgress,
    isMastered,
  };
})(window);
