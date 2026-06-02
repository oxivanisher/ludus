const TOKEN_KEY = "ludus_player_token";

function generateToken() {
  return crypto.randomUUID();
}

export function getToken() {
  let token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    token = generateToken();
    localStorage.setItem(TOKEN_KEY, token);
  }
  return token;
}

export function importToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
  // Reload so all reactive state re-initialises with the new token
  window.location.reload();
}

export function exportToken() {
  return localStorage.getItem(TOKEN_KEY) ?? getToken();
}

/**
 * Build a URL the user can share to import their token on another device.
 * Scanning the QR of this URL opens the site and triggers auto-import.
 */
export function buildImportUrl(token) {
  const url = new URL(window.location.href);
  url.pathname = "/";
  url.search = "";
  url.hash = "";
  url.searchParams.set("import_token", token);
  return url.toString();
}

/**
 * Call on app startup. If `?import_token=...` is in the URL, prompt the user
 * to confirm before overwriting their local token.
 * Returns the token to use for this session.
 */
export function handleImportFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const incoming = params.get("import_token");
  if (!incoming) return null;

  // Strip the param from the URL without reloading
  params.delete("import_token");
  const clean =
    window.location.pathname + (params.toString() ? "?" + params : "");
  window.history.replaceState({}, "", clean);

  return incoming; // caller shows confirmation dialog
}
