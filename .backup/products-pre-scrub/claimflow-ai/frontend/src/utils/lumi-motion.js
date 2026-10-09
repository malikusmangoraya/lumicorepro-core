// lumi-motion — scroll-reveal + stagger + hover micro-motion (dependency-free).
(function () {
  'use strict';
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var shownAt = null;
  var all = [];
  var doomed = 0;

  function targetEls() {
    var root = document.getElementById('root') || document.body;
    return Array.prototype.slice
      .call(root.querySelectorAll('[data-reveal], section, article, h1:not(:first-child), h2, h3'))
      .filter(function (el) {
        if (el.querySelectorAll('h2, h3').length) return /section|article/i.test(el.tagName);
        return true;
      })
      .filter(function (el) {
        var cs = getComputedStyle(el);
        return cs.display !== 'none' && cs.visibility !== 'hidden';
      });
  }

  function collect() {
    all = targetEls();
    all.forEach(function (el, i) {
      if (el.dataset.reveal === '' && el.classList.contains('lumi-reveal')) return;
      el.classList.add('lumi-reveal');
      el.style.setProperty('--lumi-d', (i % 24) * 55 + 'ms');
    });
    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          el.classList.add('lumi-in');
          obs.unobserve(el);
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -36px 0px' }
    );
    all.forEach(function (el) {
      obs.observe(el);
    });
  }

  window.addEventListener('lumi-motion:activate', collect);
  var t = window.setTimeout(collect, 120);
  if (document.readyState === 'complete') {
    window.clearTimeout(t);
    collect();
  }
})();
