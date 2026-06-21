"""
Final mobile audit — use scale=1, emulate iPhone via UA only.
This gives true 390px layout viewport matching what a real iPhone browser delivers.
"""
import json
from playwright.sync_api import sync_playwright

PAGES = [
    ("home", "https://victorlazarus32.github.io/dinkclubwebsite/"),
    ("tournaments", "https://victorlazarus32.github.io/dinkclubwebsite/tournaments.html"),
    ("lessons", "https://victorlazarus32.github.io/dinkclubwebsite/lessons.html"),
    ("open-play", "https://victorlazarus32.github.io/dinkclubwebsite/open-play.html"),
    ("private-events", "https://victorlazarus32.github.io/dinkclubwebsite/private-events.html"),
    ("court-reservations", "https://victorlazarus32.github.io/dinkclubwebsite/court-reservations.html"),
]

FULL_AUDIT_JS = """
() => {
    const vw = window.innerWidth;   // layout viewport = 390
    const vh = window.innerHeight;  // 844

    const out = {
        layoutVW: vw,
        layoutVH: vh,
        scrollWidth: document.documentElement.scrollWidth,
        scrollHeight: document.documentElement.scrollHeight,
        horizontalOverflow: null,
        overflowingElements: [],
        images: [],
        tapTargets: [],
        mobilebarInfo: null,
        headerInfo: null,
        footerLinkLayout: null,
        breadcrumbs: [],
        miscFixed: []
    };

    // ── 1. HORIZONTAL OVERFLOW ──────────────────────────────────────────────
    if (document.documentElement.scrollWidth > vw + 1) {
        out.horizontalOverflow = {
            scrollWidth: document.documentElement.scrollWidth,
            innerWidth: vw,
            excess: document.documentElement.scrollWidth - vw
        };
        const all = Array.from(document.querySelectorAll('*'));
        const seen = new Set();
        all.forEach(el => {
            try {
                const r = el.getBoundingClientRect();
                if (r.right > vw + 1) {
                    const key = el.tagName + (el.className||'') + Math.round(r.right);
                    if (!seen.has(key)) {
                        seen.add(key);
                        out.overflowingElements.push({
                            tag: el.tagName,
                            cls: (typeof el.className === 'string') ? el.className.slice(0,60) : '',
                            right: Math.round(r.right),
                            left: Math.round(r.left),
                            w: Math.round(r.width),
                            text: (el.innerText||'').trim().slice(0,40)
                        });
                    }
                }
            } catch(e){}
        });
        out.overflowingElements = out.overflowingElements.slice(0,20);
    }

    // ── 2. IMAGES ───────────────────────────────────────────────────────────
    Array.from(document.querySelectorAll('img')).forEach(img => {
        const r = img.getBoundingClientRect();
        if (r.width < 1 && r.height < 1) return;
        const cs = window.getComputedStyle(img);
        const nat = {w: img.naturalWidth, h: img.naturalHeight};
        const ren = {w: Math.round(r.width), h: Math.round(r.height)};
        const issues = [];

        // Taller than viewport
        if (ren.h > vh) {
            issues.push(`excessively_tall: ${ren.h}px > vh ${vh}`);
        }

        // Distortion: check only if object-fit is NOT cover/contain (those are intentional crops)
        const of = cs.objectFit;
        if (nat.w > 0 && nat.h > 0 && of !== 'cover' && of !== 'contain') {
            const natR = nat.w / nat.h;
            const renR = ren.w / (ren.h || 1);
            if (Math.abs(natR - renR) / natR > 0.25) {
                issues.push(`distorted (${of}): nat ${nat.w}x${nat.h} ratio=${natR.toFixed(2)} vs ren ${ren.w}x${ren.h} ratio=${renR.toFixed(2)}`);
            }
        }

        // Cut off (right > viewport)
        if (r.right > vw + 2) {
            issues.push(`cut_off_right: right=${Math.round(r.right)}, vw=${vw}`);
        }

        // Zero width (broken)
        if (ren.w === 0 && ren.h > 0) {
            issues.push(`zero_width: rendered 0x${ren.h} — likely broken carousel`);
        }

        if (issues.length) {
            out.images.push({
                src: img.src.slice(-70),
                alt: img.alt.slice(0,60),
                cls: (typeof img.className === 'string') ? img.className.slice(0,40) : '',
                nat, ren,
                objectFit: of,
                issues
            });
        }
    });

    // ── 3. TAP TARGETS ──────────────────────────────────────────────────────
    const interactives = Array.from(document.querySelectorAll('a[href], button, input, select, [role="button"]'));
    interactives.forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width < 1 && r.height < 1) return; // hidden
        // Skip off-screen elements (footer link grid etc.)
        // Actually include all visible ones
        const w = Math.round(r.width);
        const h = Math.round(r.height);
        if (w < 40 || h < 40) {
            out.tapTargets.push({
                tag: el.tagName,
                cls: (typeof el.className === 'string') ? el.className.slice(0,60) : '',
                text: (el.textContent||el.value||'').trim().slice(0,50),
                href: (el.href||'').slice(0,70),
                w, h,
                top: Math.round(r.top),
                left: Math.round(r.left)
            });
        }
    });

    // ── 4. MOBILEBAR ────────────────────────────────────────────────────────
    const mb = document.querySelector('.mobilebar');
    if (mb) {
        const r = mb.getBoundingClientRect();
        const cs = window.getComputedStyle(mb);
        out.mobilebarInfo = {
            h: Math.round(r.height),
            w: Math.round(r.width),
            top: Math.round(r.top),
            bottom: Math.round(r.bottom),
            position: cs.position,
            zIndex: cs.zIndex,
            display: cs.display,
            buttons: Array.from(mb.querySelectorAll('a, button')).map(b => {
                const br = b.getBoundingClientRect();
                return {
                    text: b.textContent.trim().slice(0,30),
                    w: Math.round(br.width),
                    h: Math.round(br.height)
                };
            })
        };
    }

    // ── 5. HEADER / NAV ─────────────────────────────────────────────────────
    const header = document.querySelector('header, nav, [class*="header"], [class*="nav"]');
    if (header) {
        const r = header.getBoundingClientRect();
        const cs = window.getComputedStyle(header);
        out.headerInfo = {
            tag: header.tagName,
            cls: (typeof header.className === 'string') ? header.className.slice(0,60) : '',
            h: Math.round(r.height),
            w: Math.round(r.width),
            position: cs.position
        };
    }

    // ── 6. BREADCRUMBS / inline nav ─────────────────────────────────────────
    const bcLinks = document.querySelectorAll('nav a:not(footer nav a), .breadcrumb a, header a');
    out.breadcrumbs = Array.from(bcLinks).slice(0,10).map(a => {
        const r = a.getBoundingClientRect();
        return {
            text: a.textContent.trim().slice(0,30),
            w: Math.round(r.width), h: Math.round(r.height),
            top: Math.round(r.top), left: Math.round(r.left)
        };
    });

    // ── 7. FOOTER LINK GRID ANALYSIS ─────────────────────────────────────────
    const footer = document.querySelector('footer');
    if (footer) {
        const r = footer.getBoundingClientRect();
        const cs = window.getComputedStyle(footer);
        // Are footer links laid out in a multi-column grid?
        const footLinks = Array.from(footer.querySelectorAll('a')).map(a => {
            const ar = a.getBoundingClientRect();
            return { text: a.textContent.trim().slice(0,30), left: Math.round(ar.left), top: Math.round(ar.top), w: Math.round(ar.width), h: Math.round(ar.height) };
        });
        // Are any footer links rendered to the right of the viewport?
        const offscreen = footLinks.filter(l => l.left + l.w > vw + 2);
        out.footerLinkLayout = {
            footerWidth: Math.round(r.width),
            footerRight: Math.round(r.right),
            display: cs.display,
            gridTemplateColumns: cs.gridTemplateColumns,
            linksOffscreen: offscreen,
            totalLinks: footLinks.length
        };
    }

    // ── 8. FIXED/STICKY elements ─────────────────────────────────────────────
    const seen2 = new Set();
    Array.from(document.querySelectorAll('*')).forEach(el => {
        try {
            const cs = window.getComputedStyle(el);
            if ((cs.position === 'fixed' || cs.position === 'sticky') && !seen2.has(el.tagName + (el.className||''))) {
                seen2.add(el.tagName + (el.className||''));
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {
                    out.miscFixed.push({
                        position: cs.position,
                        tag: el.tagName,
                        cls: (typeof el.className === 'string') ? el.className.slice(0,60) : '',
                        top: Math.round(r.top), bottom: Math.round(r.bottom),
                        w: Math.round(r.width), h: Math.round(r.height),
                        zIndex: cs.zIndex
                    });
                }
            }
        } catch(e){}
    });

    return out;
}
"""

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use scale=1, isMobile=True — this gives true 390px layout viewport
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=1,
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )

        all_results = {}
        import os
        ss_dir = "C:/Users/Taylor/Desktop/DINKCLUB/redesign/prototype/screenshots"
        os.makedirs(ss_dir, exist_ok=True)

        for slug, url in PAGES:
            print(f"\n=== {slug} ===")
            page = context.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(600)
                data = page.evaluate(FULL_AUDIT_JS)
                data["url"] = url
                all_results[slug] = data

                print(f"  vw={data['layoutVW']} vh={data['layoutVH']} scrollW={data['scrollWidth']}")
                if data['horizontalOverflow']:
                    print(f"  OVERFLOW +{data['horizontalOverflow']['excess']}px")
                    for el in data['overflowingElements'][:5]:
                        print(f"    {el['tag']}.{el['cls'][:30]} right={el['right']} w={el['w']}")
                print(f"  images with issues: {len(data['images'])}")
                for im in data['images']:
                    print(f"    {im['src'][-40:]} -> {im['issues']}")
                print(f"  small tap targets: {len(data['tapTargets'])}")
                for t in data['tapTargets'][:5]:
                    print(f"    {t['tag']} '{t['text'][:25]}' {t['w']}x{t['h']}px @top={t['top']}")
                if data.get('mobilebarInfo'):
                    m = data['mobilebarInfo']
                    print(f"  mobilebar: {m['w']}x{m['h']}px pos={m['position']} z={m['zIndex']} top={m['top']}")
                if data.get('footerLinkLayout'):
                    fl = data['footerLinkLayout']
                    print(f"  footer: w={fl['footerWidth']} right={fl['footerRight']} links_offscreen={len(fl['linksOffscreen'])}/{fl['totalLinks']}")

                # Screenshot
                page.screenshot(path=f"{ss_dir}/mobile3_{slug}.png", full_page=True)
            except Exception as e:
                print(f"  ERROR: {e}")
                all_results[slug] = {"url": url, "error": str(e)}
            finally:
                page.close()

        browser.close()

        out_path = "C:/Users/Taylor/Desktop/DINKCLUB/redesign/prototype/scripts/audit3_results.json"
        with open(out_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved: {out_path}")
        return all_results

if __name__ == "__main__":
    run()
