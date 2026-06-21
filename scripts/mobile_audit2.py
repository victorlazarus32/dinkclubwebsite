"""
Supplemental audit: check viewport meta, image CSS, mobilebar height,
breadcrumb tap targets, and footer link proximity.
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

SUPPLEMENTAL_JS = """
() => {
    const results = {};

    // 1. Viewport meta
    const vmeta = document.querySelector('meta[name="viewport"]');
    results.viewportMeta = vmeta ? vmeta.getAttribute('content') : 'MISSING';

    // 2. Actual window.innerWidth (layout viewport)
    results.layoutViewportWidth = window.innerWidth;
    results.layoutViewportHeight = window.innerHeight;

    // 3. Device pixel ratio
    results.devicePixelRatio = window.devicePixelRatio;

    // 4. Image CSS rules for hero images (first img on page)
    const imgs = Array.from(document.querySelectorAll('img'));
    results.heroImage = null;
    if (imgs.length > 0) {
        const img = imgs[0];
        const cs = window.getComputedStyle(img);
        const r = img.getBoundingClientRect();
        results.heroImage = {
            src: img.src.slice(-60),
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            renderedW: Math.round(r.width),
            renderedH: Math.round(r.height),
            objectFit: cs.objectFit,
            maxWidth: cs.maxWidth,
            width: cs.width,
            height: cs.height,
            display: cs.display
        };
    }

    // 5. All images with their CSS
    results.allImages = imgs.map(img => {
        const cs = window.getComputedStyle(img);
        const r = img.getBoundingClientRect();
        return {
            src: img.src.slice(-60),
            nat: { w: img.naturalWidth, h: img.naturalHeight },
            ren: { w: Math.round(r.width), h: Math.round(r.height) },
            objectFit: cs.objectFit,
            objectPosition: cs.objectPosition,
            maxWidth: cs.maxWidth,
            width: cs.width,
            height: cs.height,
            overflow: cs.overflow
        };
    });

    // 6. Mobile bar height and bottom padding check
    const mobilebar = document.querySelector('.mobilebar');
    results.mobilebar = null;
    if (mobilebar) {
        const r = mobilebar.getBoundingClientRect();
        const cs = window.getComputedStyle(mobilebar);
        results.mobilebar = {
            height: Math.round(r.height),
            width: Math.round(r.width),
            position: cs.position,
            bottom: cs.bottom,
            zIndex: cs.zIndex
        };
    }

    // 7. Check what's just above the mobilebar (potential content obscured)
    // Check the last visible section's bottom relative to mobilebar top
    const mobilebarRect = mobilebar ? mobilebar.getBoundingClientRect() : null;

    // 8. Burger button details
    const burger = document.querySelector('.burger, button.burger, [class*="burger"], [class*="hamburger"], [aria-label*="menu"]');
    results.burger = null;
    if (burger) {
        const r = burger.getBoundingClientRect();
        const cs = window.getComputedStyle(burger);
        results.burger = {
            tag: burger.tagName,
            classes: burger.className,
            width: Math.round(r.width),
            height: Math.round(r.height),
            fontSize: cs.fontSize,
            padding: cs.padding,
            paddingTop: cs.paddingTop,
            paddingRight: cs.paddingRight,
            paddingBottom: cs.paddingBottom,
            paddingLeft: cs.paddingLeft,
            minWidth: cs.minWidth,
            minHeight: cs.minHeight,
            touchAction: cs.touchAction
        };
    }

    // 9. Header breadcrumb / nav links
    const breadcrumbs = document.querySelectorAll('nav a, header a, .breadcrumb a');
    results.headerLinks = Array.from(breadcrumbs).slice(0, 10).map(a => {
        const r = a.getBoundingClientRect();
        return {
            text: a.textContent.trim().slice(0,30),
            w: Math.round(r.width),
            h: Math.round(r.height),
            top: Math.round(r.top)
        };
    });

    // 10. Check for horizontal scroll by looking for elements wider than viewport
    const vw = window.innerWidth;
    const wideEls = [];
    document.querySelectorAll('*').forEach(el => {
        try {
            const r = el.getBoundingClientRect();
            if (r.width > vw + 2) {
                const cs = window.getComputedStyle(el);
                wideEls.push({
                    tag: el.tagName,
                    classes: (el.className && typeof el.className === 'string') ? el.className.slice(0,60) : '',
                    renderedW: Math.round(r.width),
                    computedWidth: cs.width,
                    maxWidth: cs.maxWidth,
                    right: Math.round(r.right)
                });
            }
        } catch(e) {}
    });
    results.elementWiderThanViewport = wideEls.slice(0, 10);

    // 11. Footer link grid - check if it extends off screen
    const footer = document.querySelector('footer');
    results.footer = null;
    if (footer) {
        const r = footer.getBoundingClientRect();
        const cs = window.getComputedStyle(footer);
        results.footer = {
            width: Math.round(r.width),
            right: Math.round(r.right),
            display: cs.display,
            gridTemplateColumns: cs.gridTemplateColumns,
            flexWrap: cs.flexWrap
        };
        // Check footer's children widths
        const children = Array.from(footer.children).slice(0, 5);
        results.footerChildren = children.map(c => {
            const cr = c.getBoundingClientRect();
            const ccs = window.getComputedStyle(c);
            return {
                tag: c.tagName,
                classes: (c.className && typeof c.className === 'string') ? c.className.slice(0,60) : '',
                w: Math.round(cr.width),
                right: Math.round(cr.right),
                display: ccs.display
            };
        });
    }

    return results;
}
"""

def run_supplemental():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )

        all_results = {}
        for slug, url in PAGES:
            print(f"\n=== {slug} ===")
            page = context.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(500)
                data = page.evaluate(SUPPLEMENTAL_JS)
                data["url"] = url
                all_results[slug] = data
                print(f"  viewport meta: {data.get('viewportMeta')}")
                print(f"  layoutViewport: {data.get('layoutViewportWidth')}x{data.get('layoutViewportHeight')}")
                print(f"  devicePixelRatio: {data.get('devicePixelRatio')}")
                if data.get('heroImage'):
                    h = data['heroImage']
                    print(f"  hero img: nat={h['naturalWidth']}x{h['naturalHeight']} ren={h['renderedW']}x{h['renderedH']} object-fit={h['objectFit']} width={h['width']} height={h['height']}")
                if data.get('burger'):
                    b = data['burger']
                    print(f"  burger: {b['width']}x{b['height']}px, padding={b['padding']}")
                if data.get('mobilebar'):
                    m = data['mobilebar']
                    print(f"  mobilebar: {m['width']}x{m['height']}px, z={m['zIndex']}")
                if data.get('elementWiderThanViewport'):
                    print(f"  wide elements: {data['elementWiderThanViewport']}")
            except Exception as e:
                print(f"  ERROR: {e}")
                all_results[slug] = {"error": str(e)}
            finally:
                page.close()

        browser.close()

        out_path = "C:/Users/Taylor/Desktop/DINKCLUB/redesign/prototype/scripts/audit2_results.json"
        with open(out_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved to {out_path}")
        return all_results

if __name__ == "__main__":
    run_supplemental()
