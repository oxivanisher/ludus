import { getToken } from "./token.js";

const SW_PATH = "/sw.js";

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

async function getVapidKey() {
  const res = await fetch("/api/push/vapid-public-key");
  if (!res.ok) return null;
  const { publicKey } = await res.json();
  return publicKey;
}

async function sendSubscriptionToServer(subscription, method = "POST") {
  await fetch("/api/push/subscribe", {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Player-Token": getToken(),
    },
    body: JSON.stringify({ subscription: subscription.toJSON() }),
  });
}

/**
 * Register the service worker and subscribe to push notifications.
 * Safe to call multiple times — returns early if already subscribed.
 * Returns the permission state: 'granted' | 'denied' | 'default' | 'unsupported'
 */
export async function subscribeToPush() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    return "unsupported";
  }

  const vapidKey = await getVapidKey();
  if (!vapidKey) return "unsupported"; // push not configured on server

  const reg = await navigator.serviceWorker.register(SW_PATH);
  await navigator.serviceWorker.ready;

  const existing = await reg.pushManager.getSubscription();
  if (existing) {
    // already subscribed — ensure server has it (idempotent)
    await sendSubscriptionToServer(existing);
    return "granted";
  }

  const permission = await Notification.requestPermission();
  if (permission !== "granted") return permission;

  const subscription = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidKey),
  });

  await sendSubscriptionToServer(subscription);
  return "granted";
}

export async function unsubscribeFromPush() {
  if (!("serviceWorker" in navigator)) return;
  const reg = await navigator.serviceWorker.getRegistration(SW_PATH);
  if (!reg) return;
  const subscription = await reg.pushManager.getSubscription();
  if (!subscription) return;
  await sendSubscriptionToServer(subscription, "DELETE");
  await subscription.unsubscribe();
}

export function isPushSupported() {
  return "serviceWorker" in navigator && "PushManager" in window;
}
