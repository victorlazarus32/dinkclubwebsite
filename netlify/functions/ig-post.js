// Dink Club — Post to Instagram (secure serverless function).
// Publishes one image + caption to the connected Instagram Business account via
// Meta's Graph API. Token stays server-side; only a logged-in user can call it.
//
// Admin setup (one time): Netlify -> Site configuration -> Environment variables:
//   IG_USER_ID        = the Instagram account's numeric ID
//   IG_ACCESS_TOKEN   = a long-lived access token with content-publish permission
//   IG_GRAPH_BASE     = (optional) API base. Default https://graph.instagram.com/v21.0
//                       (the "Instagram Login" method, no Facebook Page needed).
//                       If you ever switch to the Facebook-Page method, set this to
//                       https://graph.facebook.com/v21.0
// Then redeploy.
//
// Note: Instagram requires the image to be a public JPEG URL. Our site images are
// public; use .jpg pictures for posting.

const GRAPH = process.env.IG_GRAPH_BASE || "https://graph.instagram.com/v21.0";

exports.handler = async (event, context) => {
  if (event.httpMethod !== "POST") return resp(405, { error: "Method not allowed" });

  const user = context.clientContext && context.clientContext.user;
  if (!user) return resp(401, { error: "Please log in." });

  const token = process.env.IG_ACCESS_TOKEN;
  if (!token) {
    return resp(500, { error: "Instagram isn't connected yet. (Admin: add IG_ACCESS_TOKEN in Netlify, then redeploy.)" });
  }
  // With the Instagram Login token, "me" resolves to the connected account, so an
  // explicit IG_USER_ID is optional.
  const igId = process.env.IG_USER_ID || "me";

  let p = {};
  try { p = JSON.parse(event.body || "{}"); } catch (e) {}
  const imageUrl = (p.image_url || "").trim();
  const caption = (p.caption || "").toString();
  if (!/^https?:\/\//.test(imageUrl)) {
    return resp(400, { error: "This post needs a picture that's published on the site first." });
  }

  try {
    // 1) Create a media container.
    const cUrl = `${GRAPH}/${igId}/media?image_url=${encodeURIComponent(imageUrl)}&caption=${encodeURIComponent(caption)}&access_token=${encodeURIComponent(token)}`;
    const c = await fetch(cUrl, { method: "POST" });
    const cj = await c.json();
    if (!c.ok || !cj.id) return resp(502, { error: igErr(cj) || "Could not prepare the post for Instagram." });

    // 2) Publish the container.
    const pUrl = `${GRAPH}/${igId}/media_publish?creation_id=${encodeURIComponent(cj.id)}&access_token=${encodeURIComponent(token)}`;
    const pub = await fetch(pUrl, { method: "POST" });
    const pj = await pub.json();
    if (!pub.ok || !pj.id) return resp(502, { error: igErr(pj) || "Instagram couldn't publish the post." });

    return resp(200, { id: pj.id });
  } catch (e) {
    return resp(502, { error: "Instagram request failed: " + e.message });
  }
};

function igErr(j) {
  return j && j.error && (j.error.error_user_msg || j.error.message);
}
function resp(statusCode, obj) {
  return { statusCode, headers: { "Content-Type": "application/json" }, body: JSON.stringify(obj) };
}
