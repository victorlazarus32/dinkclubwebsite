# -*- coding: utf-8 -*-
"""
Mobile audit v4 — force 390px by setting viewport meta via JS injection,
capture screenshots, and run all checks.
"""
import json
import sys
from playwright.sync_api import sync_playwright

# Ensure stdout handles unicode
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PAGES = [
    ("home", "https://victorlazarus32.github.io/dinkclubwebsite/"),
    ("tournaments", "https://victorlazarus32.github.io/dinkclubwebsite/tournaments.html"),
    ("lessons", "https://victorlazarus32.github.io/dinkclubwebsite/lessons.html"),
    ("open-play", "https://victorlazarus32.github.io/dinkclubwebsite/open-play.html"),
    ("private-events", "https://victorlazarus32.github.io/dinkclubwebsite/private-events.html"),
    ("court-reservations", "https://victorlazarus32.github.io/dinkclubwebsite/court-reservations.html"),
]

AUDIT_JS = r"""
() => {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const sw = document.documentElement.scrollWidth;

    const out = {
        vw, vh, sw,
        hOverflow: sw > vw + 1 ? {excess: sw - vw, sw, vw} : null,
        overflowEls: [],
        images: [],
        tapTargets: [],
        mobilebar: null,
        fixedEls: [],
        footerLinks: [],
        burgerBtn: null
    };

    // 1. Overflow elements
    if (out.hOverflow) {
        Array.from(document.querySelectorAll('*')).forEach(el => {
            try {
                const r = el.getBoundingClientRect();
                if (r.right > vw + 1) {
                    out.overflowEls.push({
                        tag: el.tagName,
                        cls: String(el.className||'').slice(0,50),
                        right: Math.round(r.right),
                        w: Math.round(r.width),
                        snippet: String(el.innerText||'').trim().slice(0,30)
                    });
                }
            } catch(e){}
        });
        out.overflowEls = out.overflowEls.slice(0, 20);
    }

    // 2. Images
    Array.from(document.querySelectorAll('img')).forEach(img => {
        const r = img.getBoundingClientRect();
        const cs = window.getComputedStyle(img);
        const nat = {w: img.naturalWidth, h: img.naturalHeight};
        const ren = {w: Math.round(r.width), h: Math.round(r.height)};
        const issues = [];

        if (ren.h > vh) issues.push('tall:' + ren.h + 'px');
        if (ren.w === 0 && ren.h > 10) issues.push('zero_width_carousel');
        if (r.right > vw + 2) issues.push('cutoff_right:' + Math.round(r.right));

        // Distortion (only for object-fit:fill which is default/unexpected)
        const of = cs.objectFit;
        if (nat.w > 0 && nat.h > 0 && of !== 'cover' && of !== 'contain') {
            const nr = nat.w / nat.h;
            const rr = ren.w / (ren.h || 1);
            if (Math.abs(nr - rr) / nr > 0.2) {
                issues.push('distorted('+of+'):nat_' + nat.w + 'x' + nat.h + '_ren_' + ren.w + 'x' + ren.h);
            }
        }

        if (issues.length) {
            out.images.push({
                src: img.src.slice(-60),
                nat, ren,
                objectFit: of,
                issues
            });
        }
    });

    // 3. Tap targets
    Array.from(document.querySelectorAll('a[href], button, [role="button"]')).forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width < 1 && r.height < 1) return;
        const w = Math.round(r.width);
        const h = Math.round(r.height);
        if (w < 40 || h < 40) {
            out.tapTargets.push({
                tag: el.tagName,
                cls: String(el.className||'').slice(0,50),
                text: String(el.textContent||'').trim().slice(0,40),
                href: String(el.href||'').slice(0,70),
                w, h,
                top: Math.round(r.top),
                left: Math.round(r.left)
            });
        }
    });

    // 4. Mobilebar
    const mb = document.querySelector('.mobilebar');
    if (mb) {
        const r = mb.getBoundingClientRect();
        const cs = window.getComputedStyle(mb);
        const btns = Array.from(mb.querySelectorAll('a, button')).map(b => {
            const br = b.getBoundingClientRect();
            return {text: String(b.textContent||'').trim().slice(0,20), w: Math.round(br.width), h: Math.round(br.height)};
        });
        out.mobilebar = {h: Math.round(r.height), w: Math.round(r.width), top: Math.round(r.top), position: cs.position, z: cs.zIndex, btns};
    }

    // 5. Fixed/sticky elements
    const seen = new Set();
    Array.from(document.querySelectorAll('*')).forEach(el => {
        try {
            const cs = window.getComputedStyle(el);
            if (cs.position === 'fixed' || cs.position === 'sticky') {
                const key = el.tagName + String(el.className||'');
                if (!seen.has(key)) {
                    seen.add(key);
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 && r.height > 0) {
                        out.fixedEls.push({
                            pos: cs.position, tag: el.tagName, cls: String(el.className||'').slice(0,50),
                            top: Math.round(r.top), bottom: Math.round(r.bottom),
                            w: Math.round(r.width), h: Math.round(r.height), z: cs.zIndex
                        });
                    }
                }
            }
        } catch(e){}
    });

    // 6. Footer links layout
    const footer = document.querySelector('footer');
    if (footer) {
        const fcs = window.getComputedStyle(footer);
        out.footerLinks = Array.from(footer.querySelectorAll('a')).map(a => {
            const ar = a.getBoundingClientRect();
            return {text: String(a.textContent||'').trim().slice(0,20), left: Math.round(ar.left), top: Math.round(ar.top), w: Math.round(ar.w||ar.width), h: Math.round(ar.height)};
        });
        out.footerDisplay = fcs.display;
        out.footerGrid = fcs.gridTemplateColumns;
        out.footerW = Math.round(footer.getBoundingClientRect().width);
    }

    // 7. Burger button
    const burger = document.querySelector('.burger, button[class*="burger"], button[class*="menu"], [aria-label*="menu"]');
    if (burger) {
        const r = burger.getBoundingClientRect();
        const cs = window.getComputedStyle(burger);
        out.burgerBtn = {
            w: Math.round(r.width), h: Math.round(r.height),
            padding: cs.padding, paddingBox: {
                t: cs.paddingTop, r: cs.paddingRight,
                b: cs.paddingBottom, l: cs.paddingLeft
            },
            minW: cs.minWidth, minH: cs.minHeight
        };
    }

    return out;
}
"""

def run():
    results = {}
    import os
    ss_dir = "C:/Users/Taylor/Desktop/DINKCLUB/redesign/prototype/screenshots"
    os.makedirs(ss_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            '--force-device-scale-factor=1',
            '--window-size=390,844',
            '--disable-lcd-text'
        ])

        for slug, url in PAGES:
            print(f"\n=== {slug} ===")
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=1,
                is_mobile=True,
                has_touch=True,
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/16.0 Mobile/15E148 Safari/604.1"
                )
            )
            page = context.new_page()
            try:
                # Inject viewport override before page loads
                page.add_init_script("""
                    Object.defineProperty(window, 'innerWidth', {get: () => 390, configurable: true});
                """)
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(800)

                # Force viewport meta via JS
                page.evaluate("""
                    () => {
                        let vm = document.querySelector('meta[name="viewport"]');
                        if (!vm) { vm = document.createElement('meta'); vm.name='viewport'; document.head.appendChild(vm); }
                        vm.content = 'width=390, initial-scale=1.0, maximum-scale=1.0';
                    }
                """)
                page.wait_for_timeout(300)

                data = page.evaluate(AUDIT_JS)
                data['url'] = url
                results[slug] = data

                print(f"  vw={data['vw']} vh={data['vh']} scrollW={data['sw']}")
                if data['hOverflow']:
                    print(f"  OVERFLOW +{data['hOverflow']['excess']}px")
                    for e in data['overflowEls'][:8]:
                        print(f"    {e['tag']}.{e['cls'][:25]} right={e['right']} w={e['w']} '{e['snippet'][:20]}'")
                else:
                    print("  No horizontal overflow")

                # Unique image issues
                seen_imgs = set()
                for im in data['images']:
                    key = str(im['issues'])
                    if key not in seen_imgs:
                        seen_imgs.add(key)
                        print(f"  IMG {im['src'][-40:]}: {im['issues']}")

                # Tap targets — deduplicate by issue type
                print(f"  Tap targets <40px: {len(data['tapTargets'])}")
                for t in data['tapTargets'][:8]:
                    print(f"    {t['tag']} '{t['text'][:25]}' {t['w']}x{t['h']}px top={t['top']}")

                if data.get('mobilebar'):
                    m = data['mobilebar']
                    print(f"  Mobilebar: {m['w']}x{m['h']}px pos={m['position']} z={m['z']} top={m['top']}")
                    for b in m.get('btns',[]):
                        print(f"    btn '{b['text']}' {b['w']}x{b['h']}px")

                if data.get('burgerBtn'):
                    b = data['burgerBtn']
                    print(f"  Burger: {b['w']}x{b['h']}px padding={b['padding']}")

                # Screenshot (above fold only)
                page.screenshot(path=f"{ss_dir}/m4_{slug}.png", full_page=False)
                page.screenshot(path=f"{ss_dir}/m4_{slug}_full.png", full_page=True)
                print(f"  Screenshots saved")

            except Exception as e:
                print(f"  ERROR: {e}")
                results[slug] = {"url": url, "error": str(e)}
            finally:
                page.close()
                context.close()

        browser.close()

    out_path = "C:/Users/Taylor/Desktop/DINKCLUB/redesign/prototype/scripts/audit4_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nDone. Results: {out_path}")
    return results

if __name__ == "__main__":
    run()
