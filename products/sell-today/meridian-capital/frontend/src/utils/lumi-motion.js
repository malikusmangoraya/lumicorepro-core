/**
 * lumi-motion - the animation layer.
 *
 * One rAF loop drives every scroll-linked effect, scroll work is passive, and
 * finished elements are unobserved, so a long landing page does not accumulate
 * handlers as you scroll. Only transform and opacity animate, which keeps the
 * work on the compositor and off the main thread's layout path.
 *
 * Nothing runs under prefers-reduced-motion.
 */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduced.matches) return;

  var parallaxEls = [];
  var watchArmed = false;
  var pending = [];
  var progressEl = null;
  var ticking = false;

  function root() {
    return document.getElementById('root') || document.body;
  }

  function reveal(el) {
    el.style.willChange = 'opacity, transform';
    el.classList.add('lumi-in');
    window.setTimeout(function () { el.style.willChange = ''; }, 900);
  }

  function onFrame() {
    ticking = false;
    var vh = window.innerHeight || 1;
    var scrolled = window.scrollY || 0;

    if (progressEl) {
      var max = document.documentElement.scrollHeight - vh;
      var p = max > 0 ? Math.min(1, Math.max(0, scrolled / max)) : 0;
      progressEl.style.setProperty('--lumi-progress', p.toFixed(4));
    }

    for (var i = 0; i < parallaxEls.length; i++) {
      var el = parallaxEls[i];
      var box = el.getBoundingClientRect();
      if (box.bottom < -200 || box.top > vh + 200) continue;
      var strength = parseFloat(el.dataset.parallax || '0.12');
      // Offset from viewport centre, so the layer drifts as it passes through.
      var offset = (box.top + box.height / 2 - vh / 2) * -strength;
      el.style.transform = 'translate3d(0,' + offset.toFixed(2) + 'px,0)';
    }

    // Safety net for the reveal layer. The observer above is the fast path, but a
    // callback is not guaranteed to arrive, and an armed element whose intersection
    // is never reported stays invisible for the whole session. This loop already
    // walks rects for parallax, so it also releases anything already on screen.
    if (pending.length) {
      for (var j = pending.length - 1; j >= 0; j--) {
        var item = pending[j];
        if (item.classList.contains('lumi-in') || !item.isConnected) {
          pending.splice(j, 1);
          continue;
        }
        var rect = item.getBoundingClientRect();
        if (rect.top < vh - 24 && rect.bottom > 24) {
          reveal(item);
          pending.splice(j, 1);
        }
      }
    }
  }

  function request() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(onFrame);
  }

  /* ---------------------------------------------------------------- reveal */

  function reveals() {
    var nodes = root().querySelectorAll(
      '[data-reveal], section, article, h1:not(:first-child), h2, h3'
    );
    var targets = [];
    Array.prototype.forEach.call(nodes, function (el) {
      // A wrapper that already contains headings animates as one block,
      // otherwise every heading inside it animates again.
      if (el.querySelector('h2, h3') && !/^(SECTION|ARTICLE)$/.test(el.tagName)) return;
      var cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      targets.push(el);
    });

    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          reveal(entry.target);
          obs.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -36px 0px' }
    );

    targets.forEach(function (el, i) {
      if (el.classList.contains('lumi-in')) return;
      // Already armed by an earlier pass: do not re-stagger it or observe it twice.
      if (el.dataset.lumiArmed === '1') return;
      el.dataset.lumiArmed = '1';
      el.classList.add('lumi-reveal');
      el.style.setProperty('--lumi-d', (i % 24) * 55 + 'ms');
      obs.observe(el);
      pending.push(el);
    });
  }

  /* -------------------------------------------------------------- counters */

  function animateCount(el) {
    var target = parseFloat(el.dataset.count);
    if (isNaN(target)) return;
    var decimals = (el.dataset.count.split('.')[1] || '').length;
    var prefix = el.dataset.countPrefix || '';
    var suffix = el.dataset.countSuffix || '';
    var start = performance.now();
    var dur = 1400;

    function tick(now) {
      var t = Math.min(1, (now - start) / dur);
      // easeOutExpo - fast start, long settle, reads as "counting up".
      var eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      el.textContent = prefix + (target * eased).toFixed(decimals) + suffix;
      if (t < 1) window.requestAnimationFrame(tick);
      else el.textContent = el.dataset.countFinal || el.textContent;
    }
    window.requestAnimationFrame(tick);
  }

  function counters() {
    var els = root().querySelectorAll('[data-count]');
    if (!els.length) return;
    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          animateCount(entry.target);
          obs.unobserve(entry.target);
        });
      },
      { threshold: 0.4 }
    );
    Array.prototype.forEach.call(els, function (el) {
      el.classList.add('lumi-count');
      obs.observe(el);
    });
  }

  /* -------------------------------------------------------------- magnetic */

  function magnetic() {
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    var els = root().querySelectorAll('.btn-primary, [data-magnetic]');
    Array.prototype.forEach.call(els, function (el) {
      if (el.dataset.lumiMagnetic === '1') return;
      el.dataset.lumiMagnetic = '1';
      var strength = parseFloat(el.dataset.magnetic || '0.22');

      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var dx = (e.clientX - (r.left + r.width / 2)) * strength;
        var dy = (e.clientY - (r.top + r.height / 2)) * strength;
        el.style.transform = 'translate3d(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px,0)';
      });
      el.addEventListener('pointerleave', function () {
        el.style.transform = '';
      });
    });
  }

  /* ------------------------------------------------------------------ tilt */

  function tilt() {
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    var els = root().querySelectorAll('.card-panel');
    Array.prototype.forEach.call(els, function (el) {
      if (el.dataset.lumiTilt === '1') return;
      el.dataset.lumiTilt = '1';
      el.classList.add('lumi-card');
      var max = parseFloat(el.dataset.tilt || '6');

      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5;
        var py = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform =
          'perspective(900px) rotateX(' + (-py * max).toFixed(2) +
          'deg) rotateY(' + (px * max).toFixed(2) + 'deg) translate3d(0,-4px,0)';
      });
      el.addEventListener('pointerleave', function () {
        el.style.transform = '';
      });
    });
  }

  /* ------------------------------------------------------------------ init */

  /* Pages mount lazily and route changes replace the whole tree, so the nodes
     present when setup() ran are not the nodes that exist a moment later. Without
     re-arming, a newly mounted [data-reveal] keeps whatever hidden state the motion
     layer gave it and only appears after a reload. */
  var authoredTimer = null;
  function rearm() {
    window.clearTimeout(authoredTimer);
    authoredTimer = window.setTimeout(function () {
      reveals();
      counters();
      magnetic();
      tilt();
      request();
    }, 60);
  }

  function watch() {
    if (typeof MutationObserver !== 'function') return;
    var obs = new MutationObserver(rearm);
    obs.observe(root(), { childList: true, subtree: true });
  }

  function setup() {
    if (!progressEl) {
      progressEl = document.createElement('div');
      progressEl.className = 'lumi-progress';
      progressEl.setAttribute('aria-hidden', 'true');
      document.body.appendChild(progressEl);
    }
    parallaxEls = Array.prototype.slice.call(
      root().querySelectorAll('[data-parallax], .hero-aurora')
    );
    parallaxEls.forEach(function (el) {
      if (!el.dataset.parallax) el.dataset.parallax = '0.08';
      el.classList.add('lumi-parallax');
    });
    reveals();
    counters();
    magnetic();
    tilt();
    if (!watchArmed) {
      watchArmed = true;
      watch();
    }
    window.addEventListener('scroll', request, { passive: true });
    window.addEventListener('resize', request, { passive: true });
    request();
  }

  window.addEventListener('lumi-motion:activate', setup);
  var t = window.setTimeout(setup, 120);
  if (document.readyState === 'complete') {
    window.clearTimeout(t);
    setup();
  }
})();
