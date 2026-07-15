// Dink Club — keeps the Instagram access token alive automatically.
//
// Instagram "Instagram Login" tokens are valid for 60 days, but they can be
// renewed at any time (once the token is 24h+ old and still valid), and each
// renewal buys another 60 days. This scheduled function runs weekly, renews the
// token, and saves the fresh one to Netlify Blobs so the posting function
// (ig-post.js) always reads a live token.
//
// Weekly runs + 60-day tokens = large safety margin: several failed runs in a
// row still wouldn't let the token expire. Set up once, never touch it again.
//
// The schedule is configured in netlify.toml -> [functions."ig-refresh"].

const { getStore } = require("@netlify/blobs");

const STORE = "instagram";
const KEY = "access_token";

exports.handler = async () => {
  let store;
  try {
    store = getStore(STORE);
  } catch (e) {
    console.error("[ig-refresh] Blobs unavailable:", e.message);
    return { statusCode: 500, body: "Blobs unavailable" };
  }

  // Current token: prefer the rotating one in Blobs; on the very first run fall
  // back to the token the admin pasted into the IG_ACCESS_TOKEN env var.
  let token = "";
  try {
    const saved = await store.get(KEY, { type: "json" });
    if (saved && saved.token) token = saved.token;
  } catch (e) {}
  if (!token) token = process.env.IG_ACCESS_TOKEN || "";
  if (!token) {
    console.error("[ig-refresh] No token to refresh (Blobs empty and IG_ACCESS_TOKEN unset).");
    return { statusCode: 400, body: "No token" };
  }

  // Renew for another ~60 days.
  const url =
    "https://graph.instagram.com/refresh_access_token" +
    "?grant_type=ig_refresh_token&access_token=" +
    encodeURIComponent(token);

  let j;
  try {
    const r = await fetch(url);
    j = await r.json();
    if (!r.ok || !j.access_token) {
      const msg =
        (j && j.error && (j.error.message || j.error.error_user_msg)) ||
        "unknown error";
      console.error("[ig-refresh] Refresh rejected:", msg);
      return { statusCode: 502, body: "Refresh failed: " + msg };
    }
  } catch (e) {
    console.error("[ig-refresh] Request failed:", e.message);
    return { statusCode: 502, body: "Request failed" };
  }

  // Save the fresh token for ig-post.js to use.
  try {
    await store.setJSON(KEY, {
      token: j.access_token,
      expires_in: j.expires_in || null,
      refreshed_at: new Date().toISOString(),
    });
  } catch (e) {
    console.error("[ig-refresh] Could not save new token:", e.message);
    return { statusCode: 500, body: "Save failed" };
  }

  const days = j.expires_in ? Math.round(j.expires_in / 86400) : "?";
  console.log("[ig-refresh] Token renewed — valid ~" + days + " more days.");
  return { statusCode: 200, body: "Renewed (~" + days + " days)" };
};
