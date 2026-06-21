# Dink Club — Events Module (no-code event manager)

A reusable, no-backend module that lets a non-technical client **add, edit, remove, and
reorder events** (weekly / biweekly / monthly) without touching code. Built as the
template for future client sites.

## How it works (3 pieces)

1. **`events.json`** — the single source of truth. One entry per event
   (name, status, date, label, image, link, button text, blurb).
2. **`assets/events.js`** — reads `events.json` and renders the event cards into any page
   that has an `#upcoming-events` container. It auto-sorts by date, flags the soonest as
   **★ NEXT UP**, moves passed events to **Past Events**, and shows status `tba` events as
   **Coming Soon**. Currently powers the **homepage** and **Tournaments** page from the
   same file — edit once, both update.
3. **`/admin`** — the no-code editor (Decap CMS). A friendly form-based dashboard where the
   client manages the event list and clicks **Publish**.

To change events by hand (developer): just edit `events.json`. To let the **client** do it:
finish the one-time auth setup below.

## One-time setup so the client can self-edit (`/admin`)

The editor needs a login. Recommended path for a non-technical client (no GitHub account):

**Netlify Identity + Git Gateway**
1. Connect this repo to **Netlify** (free): New site → import from GitHub → deploy. (Netlify
   serves the same files; you can keep GitHub Pages too or switch the domain to Netlify.)
2. In Netlify: **Identity → Enable Identity**; set **Registration = Invite only**.
3. **Identity → Services → Enable Git Gateway**.
4. **Identity → Invite users** → enter the client's email. They get an email, set a password,
   and log in at `yoursite/admin/` — no GitHub account required.
5. Done. The client edits events and hits **Publish**; the site redeploys automatically.

**Alternative (no Netlify): GitHub backend.** In `admin/config.yml` replace the `backend`
block with:
```yaml
backend:
  name: github
  repo: victorlazarus32/dinkclubwebsite
  branch: main
```
This requires a small OAuth helper (e.g., a free Cloudflare Worker / Vercel function) and the
client needs a GitHub account — fine for technical clients, more friction for others.

## Reusing this per client (the package)
For each new client site, copy: `events.json`, `assets/events.js`, the `/admin` folder, and
add an `#upcoming-events` + `#past-wrap`/`#past-events` container to any page that should show
events. Adjust `admin/config.yml` `repo`/branch, then do the Identity setup. Same module,
new site.

## Notes
- Works on static hosting (GitHub Pages/Netlify) — no server or database.
- Images uploaded through `/admin` land in `assets/img/uploads/` (relative paths, subpath-safe).
- The date logic runs in the visitor's browser, so the site always reflects "today" with no
  manual upkeep.
