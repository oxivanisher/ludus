import { getToken } from "./token.js";

async function request(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Player-Token": getToken(),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  stats: () => request("/api/stats"),

  games: () => request("/api/games"),

  mySessions: () => request("/api/sessions"),

  publicSessions: () => request("/api/sessions/public"),

  createSession: (game_slug, username, public_game = false, vs_computer = false) =>
    request("/api/sessions", {
      method: "POST",
      body: JSON.stringify({ game_slug, username, public: public_game, vs_computer }),
    }),

  getSession: (id) => request(`/api/sessions/${id}`),

  joinSession: (id, username) =>
    request(`/api/sessions/${id}/join`, {
      method: "POST",
      body: JSON.stringify({ username }),
    }),

  forfeitSession: (id) =>
    request(`/api/sessions/${id}/forfeit`, { method: "POST" }),

  rematch: (id) =>
    request(`/api/sessions/${id}/rematch`, { method: "POST" }),

  cancelSession: (id) =>
    request(`/api/sessions/${id}`, { method: "DELETE" }),
};
