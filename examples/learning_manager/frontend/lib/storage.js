(function () {
  const STORAGE_KEY = "openkeri.frontend.v4";
  const { createDefaultState } = window.OpenKeriPlanner;

  function loadState() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return createDefaultState();
    try {
      const state = JSON.parse(raw);
      if (state.version !== 4 || !Array.isArray(state.projects)) {
        return createDefaultState();
      }
      return state;
    } catch {
      return createDefaultState();
    }
  }

  function saveState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  window.OpenKeriStorage = { loadState, saveState, STORAGE_KEY };
})();
