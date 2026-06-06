self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  if (!event.data) return;

  let payload;
  try {
    payload = event.data.json();
  } catch {
    payload = { title: "Ludus", body: event.data.text(), url: "/" };
  }

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      // If any app window is visible, the user is already looking at it — skip the notification.
      const appVisible = clients.some((c) => c.visibilityState === "visible");
      if (appVisible) return;

      return self.registration.showNotification(payload.title ?? "Ludus", {
        body: payload.body,
        icon: "/icon-192.png",
        badge: "/icon-192.png",
        data: { url: payload.url ?? "/" },
        tag: payload.url, // collapse multiple notifications for the same game
        renotify: false,
      });
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url ?? "/";
  event.waitUntil(
    clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((windowClients) => {
        // Focus existing tab if already open
        for (const client of windowClients) {
          if (client.url.endsWith(url) && "focus" in client) {
            return client.focus();
          }
        }
        return clients.openWindow(url);
      })
  );
});
