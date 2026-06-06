export const installState = $state({ prompt: null, iosHintOpen: false });

export function isIOS() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
}

export function isInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches
    || navigator.standalone === true;
}

export function hasPlayedGame() {
  return !!localStorage.getItem('ludus_has_played');
}

export function markGamePlayed() {
  localStorage.setItem('ludus_has_played', '1');
}

export async function triggerInstall() {
  if (!installState.prompt) return;
  installState.prompt.prompt();
  const { outcome } = await installState.prompt.userChoice;
  if (outcome === 'accepted') installState.prompt = null;
}
