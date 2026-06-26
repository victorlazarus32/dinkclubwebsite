// Dink Club — Marketing Studio AI (secure serverless function).
// Generates ONE Instagram post per call (fast, never times out). The dashboard
// fires several of these in parallel to build the full calendar.
//
// Holds the Anthropic API key server-side (never sent to the browser) and only
// responds to a logged-in Netlify Identity user, so it can't be abused publicly.
//
// Admin setup (one time): Netlify -> Site configuration -> Environment variables,
// add  ANTHROPIC_API_KEY = <your Anthropic key>.  Then redeploy.

const MODEL = "claude-sonnet-4-6"; // each call is tiny, so we can use a strong model and still be fast

const SYSTEM = `You are an elite Instagram marketing strategist for "Dink Club", an outdoor pickleball club in Miami, Florida.
You write ONE high-performing, on-brand Instagram post at a time.

Brand voice: energetic, fun, community-first, a little competitive. Pickleball culture, local Miami flavor.
Audience: local players (beginners to 5.0), social and competitive adults who want something active and social.

Always: open with a scroll-stopping hook; give ONE clear call-to-action; use tasteful emojis and line breaks;
use a focused set of relevant hashtags (mix broad pickleball + local Miami + a couple branded like #DinkClub). Never a spammy wall of tags.

Output rules: respond with ONLY one valid JSON object, no markdown fences, no commentary, exactly this shape:
{
  "type": "Reel | Carousel | Single image | Story",
  "hook": "the first line / hook",
  "caption": "full ready-to-post caption with line breaks and emojis",
  "hashtags": ["#tag1", "#tag2"],
  "visual": "one short sentence: what to film or show for this post"
}`;

const TIMES = ["7:30 AM", "12:00 PM", "6:30 PM", "8:00 AM", "5:30 PM", "11:30 AM", "1:00 PM", "7:00 PM"];
const MIDDLE_ROLES = [
  "Share the key details and what to expect (format, levels, prizes, vibe).",
  "Give a quick pickleball tip or drill to build interest and show expertise.",
  "Behind-the-scenes / community vibe — the people, the courts, the energy.",
  "Social proof — highlight a past event, a winner, or a happy regular.",
  "Engagement post — ask players to tag their doubles partner in the comments.",
  "Open play / drop-in reminder — easy low-commitment way to come check it out.",
];

exports.handler = async (event, context) => {
  if (event.httpMethod !== "POST") return resp(405, { error: "Method not allowed" });

  const user = context.clientContext && context.clientContext.user;
  if (!user) return resp(401, { error: "Please log in to use the Marketing Studio." });

  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    return resp(500, { error: "The AI isn't connected yet. (Admin: add ANTHROPIC_API_KEY in Netlify env vars, then redeploy.)" });
  }

  let p = {};
  try { p = JSON.parse(event.body || "{}"); } catch (e) {}

  const today = (p.today || "").trim();
  const goal = (p.goal || "Drive event signups").trim();
  const tone = (p.tone || "energetic and fun").trim();
  const total = Math.min(Math.max(parseInt(p.total, 10) || 6, 1), 12);
  const index = Math.min(Math.max(parseInt(p.index, 10) || 0, 0), total - 1);
  const ev = p.event && p.event.name ? p.event : null;

  const eventDate = ev ? cleanDate(ev.date) : "";
  const date = planDate(today, eventDate, index, total);
  const time = TIMES[index % TIMES.length];

  // Where this post sits in the countdown arc.
  let role;
  const frac = total > 1 ? index / (total - 1) : 0;
  if (index === 0) role = ev ? "KICKOFF — announce the event and create excitement." : "Set the tone — introduce Dink Club and invite people to come play.";
  else if (frac >= 0.85) role = ev ? "FINAL PUSH — last call / day-of hype. Urgency to register or show up." : "Strong call to action to come play this week.";
  else role = MIDDLE_ROLES[(index - 1) % MIDDLE_ROLES.length];

  let task = `Write Instagram post #${index + 1} of ${total} for Dink Club.
Goal of the campaign: ${goal}
Tone: ${tone}
This post will be published on ${date} at ${time}.
This post's job in the plan: ${role}`;
  if (ev) {
    task += `
It is part of a countdown leading up to this event:
- Event: ${ev.name}
- Event date: ${ev.date || ev.label || "TBA"}
- Details: ${ev.blurb || "(none provided)"}
- Registration link: ${ev.link || "(none)"}`;
  }
  task += `\nRemember: respond with ONLY the JSON object.`;

  let data;
  try {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: MODEL, max_tokens: 900, system: SYSTEM, messages: [{ role: "user", content: task }] }),
    });
    data = await r.json();
    if (!r.ok) return resp(502, { error: (data && data.error && data.error.message) || "The AI request failed." });
  } catch (e) {
    return resp(502, { error: "Could not reach the AI service: " + e.message });
  }

  const text = (data.content || []).map((c) => c.text || "").join("").trim();
  const post = extractJson(text) || { type: "Single image", hook: "", caption: text, hashtags: [], visual: "" };
  post.date = date;
  post.time = time;
  return resp(200, post);
};

function cleanDate(d) {
  if (!d) return "";
  const m = String(d).match(/\d{4}-\d{2}-\d{2}/);
  return m ? m[0] : "";
}
function planDate(today, eventDate, i, total) {
  let start = today && /^\d{4}-\d{2}-\d{2}$/.test(today) ? new Date(today + "T12:00:00Z") : new Date();
  let end;
  if (eventDate) end = new Date(eventDate + "T12:00:00Z");
  else { end = new Date(start.getTime()); end.setUTCDate(end.getUTCDate() + 14); }
  if (!(end > start)) { end = new Date(start.getTime()); end.setUTCDate(end.getUTCDate() + total + 1); }
  const t = total > 1 ? i / (total - 1) : 0;
  const d = new Date(start.getTime() + (end.getTime() - start.getTime()) * t);
  return d.toISOString().slice(0, 10);
}
function extractJson(text) {
  if (!text) return null;
  const cleaned = text.replace(/```json/gi, "").replace(/```/g, "");
  const start = cleaned.indexOf("{");
  const end = cleaned.lastIndexOf("}");
  if (start === -1 || end === -1 || end < start) return null;
  try { return JSON.parse(cleaned.slice(start, end + 1)); } catch (e) { return null; }
}
function resp(statusCode, obj) {
  return { statusCode, headers: { "Content-Type": "application/json" }, body: JSON.stringify(obj) };
}
