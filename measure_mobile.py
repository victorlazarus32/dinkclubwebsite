import json
from playwright.sync_api import sync_playwright

URLS = [
    "https://victorlazarus32.github.io/dinkclubwebsite/",
    "https://victorlazarus32.github.io/dinkclubwebsite/tournaments.html",
    "https://victorlazarus32.github.io/dinkclubwebsite/lessons.html",
    "https://victorlazarus32.github.io/dinkclubwebsite/open-play.html",
    "https://victorlazarus32.github.io/dinkclubwebsite/private-events.html",
    "https://victorlazarus32.github.io/dinkclubwebsite/court-reservations.html",
]

EVAL_JS = """
() => {
    const w = window.innerWidth;
    const h = window.innerHeight;
    const scrollW = document.documentElement.scrollWidth;
    const overflow = scrollW - w;

    let overflowElems = [];
    if (overflow > 0) {
        const all = document.querySelectorAll('*');
        let count = 0;
        for (const el of all) {
            if (count >= 5) break;
            try {
                const r = el.getBoundingClientRect();
                if (r.right > w + 1) {
                    overflowElems.push({
                        tag: el.tagName,
                        className: (el.className || '').toString().substring(0, 60),
                        text: (el.textContent || '').trim().substring(0, 40),
                        right: Math.round(r.right)
                    });
                    count++;
                }
            } catch(e) {}
        }
    }

    const imgs = document.querySelectorAll('img');
    let oversizedImages = [];
    let distortedImages = [];
    for (const img of imgs) {
        try {
            const r = img.getBoundingClientRect();
            const rW = Math.round(r.width);
            const rH = Math.round(r.height);
            const src = img.src.split('/').pop().substring(0, 50);
            if (rH > h) {
                oversizedImages.push({ src, renderedW: rW, renderedH: rH });
            }
            const nW = img.naturalWidth;
            const nH = img.naturalHeight;
            if (nW > 0 && nH > 0 && rW > 0 && rH > 0) {
                const nRatio = nW / nH;
                const rRatio = rW / rH;
                const diff = Math.abs(nRatio - rRatio) / nRatio;
                const fit = window.getComputedStyle(img).objectFit;
                if (diff > 0.15 && fit !== 'cover' && fit !== 'contain') {
                    distortedImages.push({ src, diff: Math.round(diff * 100) + '%', objectFit: fit });
                }
            }
        } catch(e) {}
    }

    let tinyText = 0;
    const allEls = document.querySelectorAll('*');
    for (const el of allEls) {
        try {
            const cs = window.getComputedStyle(el);
            const fs = parseFloat(cs.fontSize);
            if (fs < 12) {
                const txt = (el.textContent || '').trim();
                if (txt.length > 0) {
                    const vis = cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0';
                    if (vis) tinyText++;
                }
            }
        } catch(e) {}
    }

    return { overflow, overflowElems, oversizedImages, distortedImages, tinyText };
}
"""

results = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    for url in URLS:
        page = browser.new_page(
            viewport={'width': 390, 'height': 844},
            device_scale_factor=2,
            is_mobile=True
        )
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            data = page.evaluate(EVAL_JS)
            data['url'] = url
            results.append(data)
        except Exception as e:
            results.append({'url': url, 'error': str(e)})
        finally:
            page.close()
    browser.close()

print(json.dumps(results, indent=2))
