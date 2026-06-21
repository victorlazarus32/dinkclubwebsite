/* Dink Club — Events module.
   Renders event cards from events.json into #upcoming-events, then date-proofs:
   passed events move to Past Events, "tba" events show as Coming Soon, and the
   soonest upcoming event is flagged NEXT UP. Edit events via /admin (no code). */
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
    if (!up) return; // page has no events module
    var past = document.getElementById('past-events');
    var wrap = document.getElementById('past-wrap');

    fetch('events.json', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var events = (data && data.events) || [];
        var today = new Date(); today.setHours(0, 0, 0, 0);

        events.forEach(function (ev) {
          var tba = ev.status === 'tba' || !ev.date;
          var link = ev.link || '';
          var hasLink = link && link !== '#';
          var attrs = hasLink ? ' href="' + esc(link) + '" target="_blank" rel="noopener"' : '';
          var img = hasLink
            ? '<a class="evimg contain"' + attrs + ' style="background-image:url(\'' + esc(ev.image) + '\')" aria-label="' + esc(ev.name) + ' flyer"></a>'
            : '<div class="evimg contain" style="background-image:url(\'' + esc(ev.image) + '\')" role="img" aria-label="' + esc(ev.name) + '"></div>';
          var btnClass = tba ? 'btn-dark' : 'btn-volt';
          var btn = '<a class="btn ' + btnClass + '"' + (hasLink ? attrs : ' href="#"') + '>' + esc(ev.cta || (tba ? 'Details' : 'Register →')) + '</a>';
          var el = document.createElement('div');
          el.className = 'ev';
          if (!tba) { el.setAttribute('data-end', ev.date); el.setAttribute('data-label', ev.label || ''); }
          else { el.setAttribute('data-tba', ''); }
          el.innerHTML = img +
            '<div class="evbody">' +
              '<div class="evdate">' + esc(ev.label || (tba ? 'COMING SOON' : '')) + '</div>' +
              '<div class="evname">' + esc(ev.name) + '</div>' +
              '<p>' + esc(ev.blurb) + '</p>' + btn +
            '</div>';
          up.appendChild(el);
        });

        // date-proof: move passed events to Past
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
        // sort upcoming soonest-first; tba last
        var upcoming = Array.prototype.slice.call(up.querySelectorAll('.ev[data-end]'));
        upcoming.sort(function (a, b) { return new Date(a.getAttribute('data-end')) - new Date(b.getAttribute('data-end')); });
        upcoming.forEach(function (e) { up.appendChild(e); });
        Array.prototype.forEach.call(up.querySelectorAll('.ev[data-tba]'), function (e) { up.appendChild(e); });
        // flag soonest as NEXT UP
        if (upcoming.length) {
          var f = upcoming[0].querySelector('.evdate');
          if (f) f.textContent = '★ NEXT UP · ' + (upcoming[0].getAttribute('data-label') || '');
        }
        if (past && wrap && past.children.length) wrap.style.display = '';
      })
      .catch(function () { /* leave grid empty if events.json fails to load */ });
  });
})();
