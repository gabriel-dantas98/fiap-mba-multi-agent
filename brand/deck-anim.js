/* ===== Group One — fluid slide transitions for <deck-stage> =====
   Non-invasive enhancement: <deck-stage> swaps slides instantly and fires a
   bubbling/composed `slidechange` CustomEvent. We listen for it and play an
   organic, staggered entrance on the incoming slide's content with GSAP.
   Requires brand/vendor/gsap.min.js before this file. No-op without GSAP or
   under prefers-reduced-motion. */
(function () {
  'use strict';
  var gsap = window.gsap;
  if (!gsap) return;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return;

  // Meaningful content blocks to stagger in (document order, de-duplicated by querySelectorAll).
  var SEL = [
    '.kicker', '.stitle', 'h1', 'h2', '.lead', '.badge-pill', '.cover-logo',
    '.bullets li', '.agenda li', '.pcard', '.member',
    '.stat .big', '.stat .cap', '.quote .mark', '.quote .q', '.quote .by',
    '.two > *', '.diagram', '.cover-logo + *', '.mascot-sm'
  ].join(',');

  function targets(slide) {
    var nodes = Array.prototype.slice.call(slide.querySelectorAll(SEL));
    // keep only the outermost matches (drop a node if an ancestor is also selected)
    return nodes.filter(function (n) {
      return !nodes.some(function (m) { return m !== n && m.contains(n); });
    });
  }

  function animateIn(slide, dir) {
    var els = targets(slide);
    if (!els.length) els = Array.prototype.slice.call(slide.children);

    // whole-slide breath
    gsap.fromTo(slide,
      { opacity: 0.35 },
      { opacity: 1, duration: 0.5, ease: 'power2.out', overwrite: 'auto' });

    gsap.killTweensOf(els);
    gsap.fromTo(els,
      { opacity: 0, y: 26 * (dir >= 0 ? 1 : -1), filter: 'blur(7px)' },
      {
        opacity: 1, y: 0, filter: 'blur(0px)',
        duration: 0.72, ease: 'power3.out', stagger: 0.065,
        overwrite: 'auto',
        onComplete: function () { els.forEach(function (e) { e.style.filter = ''; }); }
      });
  }

  var lastIndex = 0;
  function onChange(e) {
    var d = e.detail || {};
    var slide = d.slide;
    if (!slide) return;
    var dir = (typeof d.index === 'number' && typeof d.previousIndex === 'number')
      ? Math.sign(d.index - d.previousIndex) || 1 : 1;
    lastIndex = d.index;
    // run on the next frame so it lands after deck-stage flips data-deck-active
    requestAnimationFrame(function () { animateIn(slide, dir); });
  }

  document.addEventListener('slidechange', onChange);
})();
