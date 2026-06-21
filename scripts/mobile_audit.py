"""
Mobile rendering audit using Playwright/Chromium.
iPhone-style viewport: 390x844, deviceScaleFactor=2, isMobile=True
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

AUDIT_JS = """
() => {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const results = {
        viewport: { width: vw, height: vh },
        scrollWidth: document.documentElement.scrollWidth,
        horizontalOverflow: null,
        overflowingElements: [],
        images: [],
        smallText: [],
        tapTargets: [],
        misc: []
    };

    // 1. HORIZONTAL OVERFLOW
    const scrollW = document.documentElement.scrollWidth;
    if (scrollW > vw) {
        results.horizontalOverflow = { scrollWidth: scrollW, innerWidth: vw, diff: scrollW - vw };
        // Find offending elements
        const all = document.querySelectorAll('*');
        const offenders = [];
        all.forEach(el => {
            try {
                const r = el.getBoundingClientRect();
                if (r.right > vw + 1) {
                    const text = (el.textContent || '').trim().slice(0, 60);
                    const src = el.src || el.href || '';
                    offenders.push({
                        tag: el.tagName,
                        id: el.id || '',
                        classes: (el.className && typeof el.className === 'string') ? el.className.slice(0, 80) : '',
                        right: Math.round(r.right),
                        width: Math.round(r.width),
                        text: text,
                        src: src.slice(0, 80)
                    });
                }
            } catch(e) {}
        });
        // Deduplicate by keeping the most specific (deepest) offenders
        results.overflowingElements = offenders.slice(0, 20);
    }

    // 2. IMAGES
    const imgs = document.querySelectorAll('img');
    imgs.forEach(img => {
        const r = img.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;
        const nat = { w: img.naturalWidth, h: img.naturalHeight };
        const ren = { w: Math.round(r.width), h: Math.round(r.height) };
        const issues = [];
        // Taller than viewport
        if (ren.h > vh) {
            issues.push(`taller than viewport (rendered ${ren.h}px, vh=${vh})`);
        }
        // Distorted: ratio diff > 20%
        if (nat.w > 0 && nat.h > 0) {
            const natRatio = nat.w / nat.h;
            const renRatio = ren.w / ren.h;
            if (Math.abs(natRatio - renRatio) / natRatio > 0.2) {
                issues.push(`distorted: natural ${nat.w}x${nat.h} (ratio ${natRatio.toFixed(2)}) rendered ${ren.w}x${ren.h} (ratio ${renRatio.toFixed(2)})`);
            }
        }
        // Cut off: right edge beyond viewport
        if (r.right > vw + 2) {
            issues.push(`cut off: right edge at ${Math.round(r.right)}px, viewport ${vw}px`);
        }
        if (issues.length > 0) {
            results.images.push({
                src: (img.src || '').slice(-60),
                alt: img.alt || '',
                classes: (img.className && typeof img.className === 'string') ? img.className.slice(0,60) : '',
                rendered: ren,
                natural: nat,
                issues: issues
            });
        }
    });

    // 3. SMALL TEXT (sample visible text nodes)
    const textEls = document.querySelectorAll('p, span, a, li, td, th, label, h1, h2, h3, h4, h5, h6, button');
    textEls.forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        const style = window.getComputedStyle(el);
        const fs = parseFloat(style.fontSize);
        if (fs < 12 && fs > 0) {
            results.smallText.push({
                tag: el.tagName,
                classes: (el.className && typeof el.className === 'string') ? el.className.slice(0,60) : '',
                fontSize: fs,
                text: (el.textContent || '').trim().slice(0, 60)
            });
        }
    });

    // 4. TAP TARGETS
    const interactives = document.querySelectorAll('a, button, input, select, textarea, [role="button"], [onclick]');
    const targetList = [];
    interactives.forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        const w = Math.round(r.width);
        const h = Math.round(r.height);
        if (w < 40 || h < 40) {
            targetList.push({
                tag: el.tagName,
                classes: (el.className && typeof el.className === 'string') ? el.className.slice(0,60) : '',
                text: (el.textContent || el.value || el.placeholder || '').trim().slice(0, 50),
                href: (el.href || '').slice(0, 60),
                size: { w, h },
                top: Math.round(r.top),
                left: Math.round(r.left)
            });
        }
    });
    // Check proximity between targets
    const proxIssues = [];
    for (let i = 0; i < targetList.length; i++) {
        // just report small ones
        results.tapTargets.push(targetList[i]);
    }

    // 5. MISC: fixed/sticky elements that might overlap content
    const fixedEls = document.querySelectorAll('*');
    fixedEls.forEach(el => {
        try {
            const style = window.getComputedStyle(el);
            if (style.position === 'fixed' || style.position === 'sticky') {
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {
                    results.misc.push({
                        type: 'fixed/sticky',
                        position: style.position,
                        tag: el.tagName,
                        classes: (el.className && typeof el.className === 'string') ? el.className.slice(0,80) : '',
                        rect: { top: Math.round(r.top), bottom: Math.round(r.bottom), height: Math.round(r.height), width: Math.round(r.width) }
                    });
                }
            }
        } catch(e) {}
    });

    return results;
}
"""

def run_audit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )

        all_results = {}
        import os
        screenshot_dir = "C:/Users/Taylor/Desktop/DINKCLUB/redesign/prototype/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)

        for slug, url in PAGES:
            print(f"\n=== Auditing: {slug} ({url}) ===")
            page = context.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(500)
                data = page.evaluate(AUDIT_JS)
                data["url"] = url
                data["slug"] = slug
                all_results[slug] = data
                # screenshot
                page.screenshot(path=f"{screenshot_dir}/mobile_{slug}.png", full_page=True)
                print(f"  scrollWidth={data['scrollWidth']}, innerWidth={data['viewport']['width']}")
                if data["horizontalOverflow"]:
                    print(f"  OVERFLOW: +{data['horizontalOverflow']['diff']}px")
                print(f"  images with issues: {len(data['images'])}")
                print(f"  small text: {len(data['smallText'])}")
                print(f"  small tap targets: {len(data['tapTargets'])}")
            except Exception as e:
                print(f"  ERROR: {e}")
                all_results[slug] = {"url": url, "slug": slug, "error": str(e)}
            finally:
                page.close()

        browser.close()

        # Save JSON
        out_path = "C:/Users/Taylor/Desktop/DINKCLUB/redesign/prototype/scripts/audit_results.json"
        with open(out_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults saved to {out_path}")
        return all_results

if __name__ == "__main__":
    run_audit()
