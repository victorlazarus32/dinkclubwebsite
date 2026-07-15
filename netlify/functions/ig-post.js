// Dink Club — Post to Instagram (secure serverless function).
// Publishes to the connected Instagram Business account via Meta's Graph API.
// Supports three photo post types, chosen by the dashboard via the "type" field:
//   - "feed"     : one photo to the main grid (default)
//   - "story"    : one photo to the 24-hour Story
//   - "carousel" : 2–10 photos as a swipeable carousel post
// Token stays server-side; only a logged-in user can call it.
//
// Admin setup (one time): Netlify -> Site configuration -> Environment variables:
//   IG_USER_ID        = the Instagram account's numeric ID (optional; "me" works)
//   IG_ACCESS_TOKEN   = a long-lived access token with content-publish permission
//                       (this is now auto-renewed weekly by ig-refresh.js)
//   IG_GRAPH_BASE     = (optional) API base. Default https://graph.instagram.com/v21.0
//
// Note: Instagram requires each image to be a public JPEG URL. Our site images
// are public; the dashboard uploads Instagram-ready JPGs before posting.

const GRAPH = process.env.IG_GRAPH_BASE || "https://graph.instagram.com/v21.0";

exports.handler = async (event, context) => {
  if (event.httpMethod !== "POST") return resp(405, { error: "Method not allowed" });

  const user = context.clientContext && context.clientContext.user;
  if (!user) return resp(401, { error: "Please log in." });

  // Prefer the auto-refreshed token stored in Blobs by the weekly ig-refresh
  // function; fall back to the env var (used before the first refresh runs, or
  // if Blobs is ever unavailable). This keeps posting working no matter what.
  const token = (await storedToken()) || process.env.IG_ACCESS_TOKEN;
  if (!token) {
    return resp(500, { error: "Instagram isn't connected yet. (Admin: add IG_ACCESS_TOKEN in Netlify, then redeploy.)" });
  }
  // With the Instagram Login token, "me" resolves to the connected account, so an
  // explicit IG_USER_ID is optional.
  const igId = process.env.IG_USER_ID || "me";

  let p = {};
  try { p = JSON.parse(event.body || "{}"); } catch (e) {}
  const type = (p.type || "feed").toString().toLowerCase();
  const caption = (p.caption || "").toString();

  try {
    // ---- Carousel: 2–10 photos ----
    if (type === "carousel") {
      const urls = Array.isArray(p.image_urls) ? p.image_urls.filter((u) => /^https?:\/\//.test(u)) : [];
      if (urls.length < 2) return resp(400, { error: "A carousel needs at least 2 published pictures." });
      if (urls.length > 10) return resp(400, { error: "Instagram allows at most 10 pictures in a carousel." });

      // 1) Create a child container per image (in parallel to stay fast).
      const children = await Promise.all(
        urls.map((u) => createContainer(igId, token, { image_url: u, is_carousel_item: "true" }))
      );
      const badChild = children.find((c) => !c.ok);
      if (badChild) return resp(502, { error: badChild.error || "Could not prepare a carousel picture." });

      // 2) Create the parent carousel container.
      const parent = await createContainer(igId, token, {
        media_type: "CAROUSEL",
        children: children.map((c) => c.id).join(","),
        caption,
      });
      if (!parent.ok) return resp(502, { error: parent.error || "Could not prepare the carousel." });

      // 3) Wait for processing, then publish.
      const ready = await waitReady(parent.id, token);
      if (!ready.ok) return resp(502, { error: ready.error });
      const pub = await publishContainer(igId, token, parent.id);
      if (!pub.ok) return resp(502, { error: pub.error || "Instagram couldn't publish the carousel." });
      return resp(200, { id: pub.id });
    }

    // ---- Single photo: feed or story ----
    const imageUrl = (p.image_url || "").trim();
    if (!/^https?:\/\//.test(imageUrl)) {
      return resp(400, { error: "This post needs a picture that's published on the site first." });
    }
    // Stories don't show captions, so we omit it for that type.
    const params = type === "story"
      ? { image_url: imageUrl, media_type: "STORIES" }
      : { image_url: imageUrl, caption };

    const c = await createContainer(igId, token, params);
    if (!c.ok) return resp(502, { error: c.error || "Could not prepare the post for Instagram." });
    const ready = await waitReady(c.id, token);
    if (!ready.ok) return resp(502, { error: ready.error });
    const pub = await publishContainer(igId, token, c.id);
    if (!pub.ok) return resp(502, { error: pub.error || "Instagram couldn't publish the post." });
    return resp(200, { id: pub.id });
  } catch (e) {
    return resp(502, { error: "Instagram request failed: " + e.message });
  }
};

// Create a media container. `params` are the Graph API fields (image_url,
// media_type, children, caption, is_carousel_item…). Returns {ok,id} or {ok:false,error}.
async function createContainer(igId, token, params) {
  const qs = new URLSearchParams(params);
  qs.set("access_token", token);
  try {
    const r = await fetch(`${GRAPH}/${igId}/media?${qs.toString()}`, { method: "POST" });
    const j = await r.json();
    if (!r.ok || !j.id) return { ok: false, error: igErr(j) };
    return { ok: true, id: j.id };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

// Poll a container until Instagram finishes processing it (photos are usually
// ready almost instantly). Kept short to stay under the function time limit.
async function waitReady(containerId, token) {
  for (let i = 0; i < 4; i++) {
    await sleep(1500);
    try {
      const s = await fetch(`${GRAPH}/${containerId}?fields=status_code&access_token=${encodeURIComponent(token)}`);
      const sj = await s.json();
      if (sj.status_code === "FINISHED") return { ok: true };
      if (sj.status_code === "ERROR" || sj.status_code === "EXPIRED") {
        return { ok: false, error: "Instagram couldn't process this media. Please try a different photo." };
      }
    } catch (e) {}
  }
  return { ok: false, error: "Instagram is still preparing the media — wait ~15 seconds and tap Post again." };
}

async function publishContainer(igId, token, creationId) {
  try {
    const r = await fetch(
      `${GRAPH}/${igId}/media_publish?creation_id=${encodeURIComponent(creationId)}&access_token=${encodeURIComponent(token)}`,
      { method: "POST" }
    );
    const j = await r.json();
    if (!r.ok || !j.id) return { ok: false, error: igErr(j) };
    return { ok: true, id: j.id };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

// Read the auto-refreshed token that ig-refresh.js keeps current in Blobs.
// Any failure (Blobs empty, module missing) returns null so the caller falls
// back to the IG_ACCESS_TOKEN env var — posting behaves exactly as before.
async function storedToken() {
  try {
    const { getStore } = require("@netlify/blobs");
    const saved = await getStore("instagram").get("access_token", { type: "json" });
    return (saved && saved.token) || null;
  } catch (e) {
    return null;
  }
}
function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
function igErr(j) {
  return (j && j.error && (j.error.error_user_msg || j.error.message)) || null;
}
function resp(statusCode, obj) {
  return { statusCode, headers: { "Content-Type": "application/json" }, body: JSON.stringify(obj) };
}
