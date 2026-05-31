/* ===== Group One — loading screen controller =====
   Self-injecting. Include after <body> opens, in this order:
     <link rel="stylesheet" href="brand/loader.css">
     <script src="brand/vendor/gsap.min.js"></script>   (optional but recommended)
     <script src="brand/loader.js"></script>
   It builds the overlay (animated G1 logo), shows it for at least MIN ms, then fades out. */
(function () {
  'use strict';

  var MIN = 1700;
  var start = Date.now();
  var gsap = window.gsap || null;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // The vectorized G1 logo (mirror of brand/svg/g1-logo.svg), split into G and 1.
  var LOGO =
    '<svg viewBox="0 0 120 130" xmlns="http://www.w3.org/2000/svg" fill="currentColor" aria-hidden="true">' +
      '<path class="g1l-g" d="M60 10 L12.4 37.5 L12.4 92.5 L60 120 L60 95 L34 80 L34 50 L60 35 Z"/>' +
      '<path class="g1l-one" d="M100 26 L100 120 L78 120 L78 52 L60 52 Z"/>' +
    '</svg>';

  var overlay = document.createElement('div');
  overlay.className = 'g1-loader' + (gsap ? '' : ' no-gsap');
  overlay.id = 'g1-loader';
  overlay.setAttribute('aria-hidden', 'true');
  overlay.innerHTML =
    '<div class="g1-loader-grid"></div>' +
    '<div class="g1-loader-stage">' +
      '<svg class="g1-loader-ring" viewBox="0 0 168 168"><circle cx="84" cy="84" r="75"></circle></svg>' +
      '<div class="g1-loader-logo">' + LOGO + '</div>' +
    '</div>' +
    '<div class="g1-loader-word">Group&nbsp;One</div>' +
    '<div class="g1-loader-track"><div class="g1-loader-bar"></div></div>';

  function inject() {
    if (!document.body) { document.addEventListener('DOMContentLoaded', inject); return; }
    document.body.insertBefore(overlay, document.body.firstChild);
    document.body.classList.add('g1-loading');
    animate();
  }

  function animate() {
    if (!gsap || reduce) return;
    var g = overlay.querySelector('.g1l-g');
    var one = overlay.querySelector('.g1l-one');
    var ring = overlay.querySelector('.g1-loader-ring circle');
    var word = overlay.querySelector('.g1-loader-word');
    var bar = overlay.querySelector('.g1-loader-bar');

    gsap.set([g, one], { transformOrigin: '50% 50%' });
    var tl = gsap.timeline();
    tl.from(g,   { x: -34, opacity: 0, rotation: -12, duration: .6, ease: 'back.out(1.6)' })
      .from(one, { x: 34, opacity: 0, rotation: 12, duration: .6, ease: 'back.out(1.6)' }, '-=.42')
      .to(ring,  { strokeDashoffset: 120, duration: 1.1, ease: 'power2.inOut' }, 0)
      .from(word, { opacity: 0, y: 8, duration: .5, ease: 'power2.out' }, '-=.5')
      .fromTo(bar, { width: '0%' }, { width: '100%', duration: 1.1, ease: 'power1.inOut' }, '-=.7')
      // tiny "alive" breath on the assembled logo
      .to([g, one], { scale: 1.05, duration: .5, ease: 'sine.inOut', yoyo: true, repeat: 1, transformOrigin: '50% 50%' }, '-=.2');
  }

  function dismiss() {
    overlay.classList.add('done');
    document.body.classList.remove('g1-loading');
    setTimeout(function () { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); }, 650);
  }
  function finish() {
    var wait = reduce ? 0 : Math.max(0, MIN - (Date.now() - start));
    setTimeout(dismiss, wait);
  }

  inject();
  if (document.readyState === 'complete') finish();
  else window.addEventListener('load', finish);
  setTimeout(dismiss, 6500); // safety net
})();
