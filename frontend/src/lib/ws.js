import { getToken } from "./token.js";

export function createGameSocket(sessionId, { onState, onError, onCancelled }) {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const url = `${protocol}://${location.host}/ws/${sessionId}?token=${encodeURIComponent(getToken())}`;
  let ws;
  let dead = false;
  let paused = false;
  let reconnectTimer = null;

  function connect() {
    ws = new WebSocket(url);

    ws.onopen = () => {};

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "state") onState(msg.session);
      if (msg.type === "error") onError?.(msg.message);
      if (msg.type === "cancelled") onCancelled?.();
    };

    ws.onclose = () => {
      if (!dead && !paused) reconnectTimer = setTimeout(connect, 2000);
    };

    ws.onerror = () => ws.close();
  }

  // Disconnect when the page is hidden (screen locked, tab backgrounded) so the
  // server unregisters presence and sends a push notification on the next turn.
  // Reconnect when the page becomes visible again to resume live updates.
  function handleVisibility() {
    if (document.hidden) {
      paused = true;
      clearTimeout(reconnectTimer);
      ws.close();
    } else {
      paused = false;
      connect();
    }
  }

  document.addEventListener("visibilitychange", handleVisibility);
  connect();

  return {
    sendAction(action) {
      const msg = JSON.stringify({ type: "action", action });
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(msg);
      } else if (ws.readyState === WebSocket.CONNECTING) {
        ws.addEventListener("open", () => ws.send(msg), { once: true });
      }
      // CLOSING / CLOSED: drop — the reconnect loop restores the connection
    },
    close() {
      dead = true;
      clearTimeout(reconnectTimer);
      document.removeEventListener("visibilitychange", handleVisibility);
      ws.close();
    },
  };
}
