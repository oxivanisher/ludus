const KEY = "ludus_username";

export function getSavedUsername() {
  return localStorage.getItem(KEY) ?? "";
}

export function saveUsername(name) {
  if (name) localStorage.setItem(KEY, name);
}
