import { getToken } from "./token.js";

export function createGameSocket(sessionId, { onState, onError, onCancelled }) {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const url = `${protocol}://${location.host}/ws/${sessionId}?token=${encodeURIComponent(getToken())}`;
  let ws;
  let dead = false;
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
      if (!dead) reconnectTimer = setTimeout(connect, 2000);
    };

    ws.onerror = () => ws.close();
  }

  connect();

  return {
    sendAction(action) {
      ws.send(JSON.stringify({ type: "action", action }));
    },
    close() {
      dead = true;
      clearTimeout(reconnectTimer);
      ws.close();
    },
  };
}
