// Theme preference: 'auto' (follow OS), 'light' or 'dark'.
// Stored in localStorage only — never sent to the server.
const KEY = 'ludus_theme';
const ORDER = ['auto', 'light', 'dark'];
const media = window.matchMedia('(prefers-color-scheme: dark)');

function load() {
  try {
    const v = localStorage.getItem(KEY);
    return ORDER.includes(v) ? v : 'auto';
  } catch {
    return 'auto';
  }
}

export const themeState = $state({ mode: load() });

function apply() {
  const dark = themeState.mode === 'dark' || (themeState.mode === 'auto' && media.matches);
  document.documentElement.classList.toggle('dark', dark);
}

media.addEventListener('change', () => {
  if (themeState.mode === 'auto') apply();
});

export function cycleTheme() {
  themeState.mode = ORDER[(ORDER.indexOf(themeState.mode) + 1) % ORDER.length];
  try {
    if (themeState.mode === 'auto') localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, themeState.mode);
  } catch {}
  apply();
}

apply();
