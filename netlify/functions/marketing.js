// Dink Club — Marketing Studio AI (secure serverless function).
// Holds the Anthropic API key server-side (never sent to the browser) and only
// responds to a logged-in Netlify Identity user, so it can't be abused publicly.
//
// Admin setup (one time): in Netlify -> Site configuration -> Environment variables,
// add  ANTHROPIC_API_KEY = <your Anthropic key>.  Then redeploy.

const MODEL = "claude-sonnet-4-6"; // strong + cost-effective for caption/calendar generation

const SYSTEM = `You are an elite Instagram marketing strategist for "Dink Club", an outdoor pickleball club in Miami, Florida.
You write high-performing, on-brand Instagram content and content calendars.

Brand voice: energetic, fun, community-first, a little competitive. Pickleball culture. Local Miami flavor.
Audience: local players (beginners to 5.0), social/competitive adults, people looking for something active and social.

Best practices you always apply:
- Strong scroll-stopping hook in the first line of every caption.
- One clear call-to-action per post (register, DM, tag a partner, save, share to stories, come play).
- Mix content pillars: events/tournaments, community & people, quick tips/drills, behind-the-scenes, user-generated content, promos/last-call.
- Use a "countdown campaign" when an event has a date: build from awareness -> details/lineup -> social proof -> last call -> day-of hype -> recap.
- Recommend ideal posting windows for a local audience (mornings ~7-9am, lunch ~11:30-1, evenings ~6-8pm; weekends late morning). Vary times.
- Use a focused set of relevant hashtags (mix of broad pickleball tags + local Miami tags + a couple branded). Never spammy walls of 30 identical tags.
- Captions can use tasteful emojis and line breaks.

Output rules: respond with ONLY valid minified-or-pretty JSON, no markdown fences, no commentary, matching exactly this shape:
{
  "strategy": "1-3 sentence summary of the plan",
  "posts": [
    {
      "date": "YYYY-MM-DD",
      "time": "e.g. 6:30 PM",
      "type": "Reel | Carousel | Single image | Story",
      "hook": "the first line / hook",
      "caption": "full ready-to-post caption with line breaks and emojis",
      "hashtags": ["#tag1", "#tag2"],
      "visual": "short description of what to film/show for this post"
    }
  ]
}`;

exports.handler = async (event, context) => {
  if (event.httpMethod !== "POST") {
    return resp(405, { error: "Method not allowed" });
  }

  // Require a logged-in Netlify Identity user (protects the API key from abuse).
  const user = context.clientContext && context.clientContext.user;
  if (!user) {
    return resp(401, { error: "Please log in to use the Marketing Studio." });
  }

  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    return resp(500, {
      error: "The AI isn't connected yet. (Admin: add ANTHROPIC_API_KEY in Netlify environment variables, then redeploy.)",
    });
  }

  let p = {};
  try { p = JSON.parse(event.body || "{}"); } catch (e) {}

  const today = (p.today || "").trim();
  const goal = (p.goal || "Grow awareness and drive event signups").trim();
  const tone = (p.tone || "energetic and fun").trim();
  const count = Math.min(Math.max(parseInt(p.count, 10) || 6, 1), 14);
  const ev = p.event || null;

  let task;
  if (ev && ev.name) {
    task = `Build an Instagram content calendar of ${count} posts leading up to this event.
Today's date is ${today || "unknown"}.
Event name: ${ev.name}
Event date: ${ev.date || ev.label || "TBA"}
Event details: ${ev.blurb || "(none provided)"}
Registration link: ${ev.link || "(none)"}
Campaign goal: ${goal}
Tone: ${tone}
Spread the posts sensibly between today and the event date (or over the next ~2 weeks if no firm date), following a countdown campaign arc.`;
  } else {
    task = `Build an Instagram content calendar of ${count} posts for the Dink Club over roughly the next two weeks starting ${today || "today"}.
No single event — focus on community, open play, tips, behind-the-scenes, and general awareness.
Campaign goal: ${goal}
Tone: ${tone}`;
  }

  let data;
  try {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 4000,
        system: SYSTEM,
        messages: [{ role: "user", content: task }],
      }),
    });
    data = await r.json();
    if (!r.ok) {
      return resp(502, { error: (data && data.error && data.error.message) || "The AI request failed." });
    }
  } catch (e) {
    return resp(502, { error: "Could not reach the AI service: " + e.message });
  }

  const text = (data.content || []).map((c) => c.text || "").join("").trim();
  const parsed = extractJson(text);
  if (!parsed) {
    return resp(200, { strategy: "", posts: [], raw: text });
  }
  return resp(200, parsed);
};

function extractJson(text) {
  if (!text) return null;
  // Strip accidental code fences, then grab the outermost { ... }.
  const cleaned = text.replace(/```json/gi, "").replace(/```/g, "");
  const start = cleaned.indexOf("{");
  const end = cleaned.lastIndexOf("}");
  if (start === -1 || end === -1 || end < start) return null;
  try { return JSON.parse(cleaned.slice(start, end + 1)); } catch (e) { return null; }
}

function resp(statusCode, obj) {
  return {
    statusCode,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(obj),
  };
}
