/* Dink Club — Events module.
   Reads events.json and renders:
   (1) the event cards into #upcoming-events (sorts by date, flags NEXT UP,
       moves passed events to Past Events, shows "tba" as Coming Soon), and
   (2) the featured-event banner into #featured-event (auto-hides after its date).
   Everything here is editable by the client via /admin — no code needed. */
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  ready(function () {
    var up = document.getElementById('upcoming-events');
    var feat = document.getElementById('featured-event');
    if (!up && !feat) return; // nothing on this page to render

    fetch('events.json', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var today = new Date(); today.setHours(0, 0, 0, 0);

        /* ---------- event cards ---------- */
        if (up) {
          var past = document.getElementById('past-events');
          var wrap = document.getElementById('past-wrap');
          (data.events || []).forEach(function (ev) {
            var tba = ev.status === 'tba' || !ev.date;
            var link = ev.link || '';
            var hasLink = link && link !== '#';
            var attrs = hasLink ? ' href="' + esc(link) + '" target="_blank" rel="noopener"' : '';
            var img = hasLink
              ? '<a class="evimg contain"' + attrs + ' style="background-image:url(\'' + esc(ev.image) + '\')" aria-label="' + esc(ev.name) + ' flyer"></a>'
              : '<div class="evimg contain" style="background-image:url(\'' + esc(ev.image) + '\')" role="img" aria-label="' + esc(ev.name) + '"></div>';
            var btn = '<a class="btn ' + (tba ? 'btn-dark' : 'btn-volt') + '"' + (hasLink ? attrs : ' href="#"') + '>' + esc(ev.cta || (tba ? 'Details' : 'Register →')) + '</a>';
            var el = document.createElement('div');
            el.className = 'ev';
            if (!tba) { el.setAttribute('data-end', ev.date); el.setAttribute('data-label', ev.label || ''); }
            else { el.setAttribute('data-tba', ''); }
            el.innerHTML = img +
              '<div class="evbody"><div class="evdate">' + esc(ev.label || (tba ? 'COMING SOON' : '')) + '</div>' +
              '<div class="evname">' + esc(ev.name) + '</div><p>' + esc(ev.blurb) + '</p>' + btn + '</div>';
            up.appendChild(el);
          });
          if (past) {
            Array.prototype.forEach.call(up.querySelectorAll('.ev[data-end]'), function (ev) {
              var d = new Date(ev.getAttribute('data-end') + 'T23:59:59');
              var label = ev.getAttribute('data-label') || '';
              var b = ev.querySelector('.evdate');
              if (d < today) {
                ev.classList.add('is-past');
                if (b) { b.textContent = 'PAST · ' + label; b.style.color = '#8a929b'; }
                var btn = ev.querySelector('.btn'); if (btn) btn.textContent = 'View Results →';
                past.appendChild(ev);
              } else if (b) { b.textContent = label; }
            });
          }
          var upcoming = Array.prototype.slice.call(up.querySelectorAll('.ev[data-end]'));
          upcoming.sort(function (a, b) { return new Date(a.getAttribute('data-end')) - new Date(b.getAttribute('data-end')); });
          upcoming.forEach(function (e) { up.appendChild(e); });
          Array.prototype.forEach.call(up.querySelectorAll('.ev[data-tba]'), function (e) { up.appendChild(e); });
          if (upcoming.length) {
            var f0 = upcoming[0].querySelector('.evdate');
            if (f0) f0.textContent = '★ NEXT UP · ' + (upcoming[0].getAttribute('data-label') || '');
          }
          if (past && wrap && past.children.length) wrap.style.display = '';
        }

        /* ---------- featured banner ---------- */
        if (feat) {
          var f = data.featured;
          var hidden = !f || f.enabled === false ||
            (f.hideAfter && new Date() > new Date(f.hideAfter + 'T23:59:59'));
          if (hidden) { feat.style.display = 'none'; return; }
          var dets = (f.details || []).map(function (d) { return '<li>' + esc(d) + '</li>'; }).join('');
          var tagline = f.tagline ? ' <b style="color:#fff">' + esc(f.tagline) + '</b>' : '';
          feat.innerHTML =
            '<div class="wrap split" style="align-items:center">' +
              '<img src="' + esc(f.image) + '" alt="' + esc(f.title) + ' event flyer" loading="lazy" style="width:100%;max-width:380px;height:auto;border-radius:12px;display:block;margin:0 auto">' +
              '<div>' +
                '<p class="eyebrow" style="color:var(--volt)">' + esc(f.eyebrow) + '</p>' +
                '<h2 style="color:#fff;font-size:clamp(1.9rem,4vw,2.8rem);font-weight:900;margin-bottom:12px">' + esc(f.title) + '</h2>' +
                '<p style="color:#cfd6dd;margin-bottom:16px">' + esc(f.body) + tagline + '</p>' +
                '<ul style="list-style:none;padding:0;margin:0 0 20px;display:grid;gap:8px;color:#cfd6dd;font-size:.95rem">' + dets + '</ul>' +
                '<div style="display:flex;gap:12px;flex-wrap:wrap">' +
                  '<a class="btn btn-volt" href="' + esc(f.ctaLink || '#') + '">' + esc(f.ctaText || 'Sign Up →') + '</a>' +
                  '<a class="btn btn-ghost light call" href="tel:+13058134238">Call 305-813-4238</a>' +
                '</div>' +
              '</div>' +
            '</div>';
        }
      })
      .catch(function () { if (feat) feat.style.display = 'none'; });
  });
})();
