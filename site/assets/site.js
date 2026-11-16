(function () {
  var d = document;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  // Without this class every panel stays visible and the tabs stay hidden.
  d.documentElement.classList.add('ready');

  // Sticky nav shrinks once the page scrolls.
  var onScroll = function () { d.body.classList.toggle('scrolled', window.scrollY > 8); };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Tabs switch between pre-rendered panels.
  d.querySelectorAll('[data-tabs]').forEach(function (group) {
    var panels = d.querySelectorAll('[data-panel="' + group.getAttribute('data-tabs') + '"]');
    var buttons = group.querySelectorAll('button');
    buttons.forEach(function (btn, i) {
      btn.addEventListener('click', function () {
        buttons.forEach(function (b, j) { b.setAttribute('aria-pressed', String(i === j)); });
        panels.forEach(function (p, j) { p.classList.toggle('cur', i === j); });
      });
    });
  });

  // Copy the install command.
  var status = d.querySelector('[data-status]');
  if (navigator.clipboard) {
    d.querySelectorAll('[data-copy]').forEach(function (btn) {
      var label = btn.textContent;
      btn.hidden = false;
      btn.addEventListener('click', function () {
        navigator.clipboard.writeText(btn.getAttribute('data-copy')).then(function () {
          btn.textContent = btn.getAttribute('data-done');
          if (status) status.textContent = status.getAttribute('data-msg');
          setTimeout(function () {
            btn.textContent = label;
            if (status) status.textContent = '';
          }, 1600);
        }, function () {});
      });
    });
  }

  // Reveal each block once it scrolls into view (visible from the start without JS).
  var blocks = d.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window) || reduce) {
    blocks.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      var shown = 0;
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target;
        setTimeout(function () { el.classList.add('in'); }, shown * 90);
        shown += 1;
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });
    blocks.forEach(function (el) { io.observe(el); });
  }

  // GitHub stars; the counter stays hidden if the API fails or there are none yet.
  fetch('https://api.github.com/repos/aledepaoligampel/pcdd')
    .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
    .then(function (j) {
      var n = j.stargazers_count;
      if (typeof n !== 'number' || n < 1) return;
      var t = n >= 1000 ? (Math.round(n / 100) / 10) + 'k' : String(n);
      d.querySelectorAll('[data-stars]').forEach(function (el) { el.textContent = t; el.hidden = false; });
    })
    .catch(function () {});

  // Play the terminal session once; the full transcript is already in the HTML.
  var screen = d.querySelector('[data-term]');
  if (!screen || reduce) return;
  var lines = Array.prototype.slice.call(screen.children).filter(function (n) { return n.tagName === 'DIV'; });
  var caret = screen.querySelector('.caret');
  var step = 0;
  var tick = function () {
    if (step >= lines.length) return;
    screen.insertBefore(lines[step], caret);
    step += 1;
    var next = lines[step];
    if (!next) return;
    var delay = next.className === 'l-cmd' ? 900 : next.className === 'l-gap' ? 250 : 170;
    setTimeout(tick, delay);
  };
  lines.forEach(function (l) { l.remove(); });
  setTimeout(tick, 600);
})();
