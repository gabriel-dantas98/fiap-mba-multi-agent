/* ===== Group One — G-One animated robot =====
   A hand-vectorized version of the brand mascot that idles and fluidly cycles
   between emotions. Requires GSAP (brand/vendor/gsap.min.js) loaded first.

   Usage:
     <div data-g1-robot></div>
     <script src="brand/vendor/gsap.min.js"></script>
     <script src="brand/robot.js"></script>
   Every element with [data-g1-robot] gets a robot mounted + animated.
   Honors prefers-reduced-motion (renders a static happy face). */
(function () {
  'use strict';

  var GOLD = '#F4C020', GOLD_D = '#E0A81C',
      NAVY = '#0A0F1E', VISOR = '#121A30',
      WHITE = '#FFFFFF', SHADE = '#C9DEF2', SHADE_D = '#A9C6E4';

  // Static markup (also mirrored in brand/svg/robot.svg). Eyes are drawn by JS.
  var SVG =
    '<svg class="g1r" viewBox="0 0 200 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mascote G-One">' +
      '<g class="g1r-all">' +
        // antennae
        '<g class="g1r-ant g1r-ant-l">' +
          '<path d="M70 56 L46 30" stroke="' + NAVY + '" stroke-width="6" stroke-linecap="round" fill="none"/>' +
          '<circle cx="44" cy="27" r="8" fill="' + GOLD + '" stroke="' + NAVY + '" stroke-width="4"/>' +
        '</g>' +
        '<g class="g1r-ant g1r-ant-r">' +
          '<path d="M130 56 L154 30" stroke="' + NAVY + '" stroke-width="6" stroke-linecap="round" fill="none"/>' +
          '<circle cx="156" cy="27" r="8" fill="' + GOLD + '" stroke="' + NAVY + '" stroke-width="4"/>' +
        '</g>' +
        // top dome
        '<path d="M82 50 A18 18 0 0 1 118 50 Z" fill="' + GOLD + '" stroke="' + NAVY + '" stroke-width="4" stroke-linejoin="round"/>' +
        // side ears
        '<rect x="40" y="92" width="16" height="34" rx="8" fill="' + SHADE + '" stroke="' + NAVY + '" stroke-width="4"/>' +
        '<rect x="144" y="92" width="16" height="34" rx="8" fill="' + SHADE + '" stroke="' + NAVY + '" stroke-width="4"/>' +
        // head
        '<rect x="50" y="50" width="100" height="86" rx="34" fill="' + WHITE + '" stroke="' + NAVY + '" stroke-width="5"/>' +
        '<path d="M133 64 a30 30 0 0 1 5 18 v22 a30 30 0 0 1 -10 22 q22 -30 5 -62 Z" fill="' + SHADE + '" opacity=".55"/>' +
        // visor
        '<rect class="g1r-visor" x="62" y="64" width="76" height="58" rx="26" fill="' + VISOR + '" stroke="' + NAVY + '" stroke-width="4"/>' +
        // eyes (filled by JS)
        '<g class="g1r-eyes"></g>' +
        // body
        '<g class="g1r-body">' +
          '<path d="M78 134 q22 12 44 0 l4 40 q-26 22 -52 0 Z" fill="' + WHITE + '" stroke="' + NAVY + '" stroke-width="5" stroke-linejoin="round"/>' +
          // wings
          '<path d="M80 150 q-34 2 -42 26 q24 6 44 -8 Z" fill="' + SHADE + '" stroke="' + NAVY + '" stroke-width="4.5" stroke-linejoin="round"/>' +
          '<path d="M120 150 q34 2 42 26 q-24 6 -44 -8 Z" fill="' + SHADE + '" stroke="' + NAVY + '" stroke-width="4.5" stroke-linejoin="round"/>' +
          // lower body taper
          '<path d="M82 176 q18 16 36 0 l-6 34 q-12 12 -24 0 Z" fill="' + WHITE + '" stroke="' + NAVY + '" stroke-width="5" stroke-linejoin="round"/>' +
          '<line x1="100" y1="182" x2="100" y2="206" stroke="' + SHADE_D + '" stroke-width="3" stroke-linecap="round"/>' +
          // chest button
          '<circle cx="100" cy="150" r="11" fill="' + GOLD + '" stroke="' + NAVY + '" stroke-width="4"/>' +
          '<circle cx="100" cy="150" r="3.5" fill="' + GOLD_D + '"/>' +
        '</g>' +
      '</g>' +
    '</svg>';

  // eye geometry — parametric so emotions tween smoothly (no MorphSVG needed)
  var EYE_X = { l: 84, r: 116 }, EYE_Y = 92, EYE_W = 13;

  // emotion = {curve, openY, round, glow}
  //  curve: +up = happy smile, 0 = flat, -down = sad/sleepy (in SVG y-down, smile arcs upward => negative q)
  var EMOTIONS = {
    happy:    { curve: -13, openY: 1,   round: 0,  dx: 0 },
    content:  { curve: -7,  openY: 1,   round: 0,  dx: 0 },
    neutral:  { curve: 0,   openY: 1,   round: 0,  dx: 0 },
    focus:    { curve: -4,  openY: 0.4, round: 0,  dx: 0 },
    surprise: { curve: 0,   openY: 1.5, round: 1,  dx: 0 },
    curious:  { curve: -9,  openY: 1.1, round: 0,  dx: 3 },
    sleepy:   { curve: 7,   openY: 0.5, round: 0,  dx: 0 },
  };
  var ORDER = ['happy', 'curious', 'surprise', 'focus', 'content', 'neutral', 'sleepy'];

  function eyePath(cx, curve) {
    // quadratic arc: smile when curve negative
    var x1 = cx - EYE_W, x2 = cx + EYE_W, qy = EYE_Y + curve;
    return 'M' + x1 + ' ' + EYE_Y + ' Q' + cx + ' ' + qy + ' ' + x2 + ' ' + EYE_Y;
  }

  function buildEyes(eyesEl) {
    eyesEl.innerHTML =
      '<path class="g1r-eye g1r-eye-l" fill="none" stroke="' + GOLD + '" stroke-width="7" stroke-linecap="round"/>' +
      '<path class="g1r-eye g1r-eye-r" fill="none" stroke="' + GOLD + '" stroke-width="7" stroke-linecap="round"/>' +
      '<circle class="g1r-pupil g1r-pupil-l" cx="' + EYE_X.l + '" cy="' + EYE_Y + '" r="0" fill="' + GOLD + '"/>' +
      '<circle class="g1r-pupil g1r-pupil-r" cx="' + EYE_X.r + '" cy="' + EYE_Y + '" r="0" fill="' + GOLD + '"/>';
  }

  function applyEmotion(ctx, e, immediate) {
    var dur = immediate ? 0 : 0.55;
    var state = ctx.state;
    // tween shared params then redraw on each frame
    ctx.gsap.to(state, {
      curve: e.curve, openY: e.openY, round: e.round, dx: e.dx,
      duration: dur, ease: 'power2.inOut', overwrite: 'auto',
      onUpdate: function () { drawEyes(ctx); }
    });
  }

  function drawEyes(ctx) {
    var s = ctx.state;
    var arcOpacity = 1 - s.round;          // arcs fade as we go round-eyed
    var pupilR = s.round * 7;
    ctx.eyeL.setAttribute('d', eyePath(EYE_X.l + s.dx, s.curve));
    ctx.eyeR.setAttribute('d', eyePath(EYE_X.r + s.dx, s.curve));
    ctx.eyeL.style.opacity = arcOpacity;
    ctx.eyeR.style.opacity = arcOpacity;
    // openY squashes the arcs vertically about the eye line (blink + focus + surprise)
    var sy = s.openY * s.blink;
    ctx.eyeL.setAttribute('transform', 'translate(' + (EYE_X.l + s.dx) + ' ' + EYE_Y + ') scale(1 ' + sy + ') translate(' + (-(EYE_X.l + s.dx)) + ' ' + (-EYE_Y) + ')');
    ctx.eyeR.setAttribute('transform', 'translate(' + (EYE_X.r + s.dx) + ' ' + EYE_Y + ') scale(1 ' + sy + ') translate(' + (-(EYE_X.r + s.dx)) + ' ' + (-EYE_Y) + ')');
    ctx.pupL.setAttribute('cx', EYE_X.l + s.dx); ctx.pupL.setAttribute('r', pupilR * s.blink);
    ctx.pupR.setAttribute('cx', EYE_X.r + s.dx); ctx.pupR.setAttribute('r', pupilR * s.blink);
  }

  function mount(host, gsap) {
    host.innerHTML = SVG;
    var svg = host.querySelector('svg');
    var eyesEl = svg.querySelector('.g1r-eyes');
    buildEyes(eyesEl);

    var ctx = {
      gsap: gsap,
      svg: svg,
      eyeL: svg.querySelector('.g1r-eye-l'),
      eyeR: svg.querySelector('.g1r-eye-r'),
      pupL: svg.querySelector('.g1r-pupil-l'),
      pupR: svg.querySelector('.g1r-pupil-r'),
      state: { curve: -13, openY: 1, round: 0, dx: 0, blink: 1 }
    };
    drawEyes(ctx);

    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce || !gsap) { return; }

    var all = svg.querySelector('.g1r-all');
    var antL = svg.querySelector('.g1r-ant-l');
    var antR = svg.querySelector('.g1r-ant-r');
    gsap.set([antL, antR], { transformOrigin: 'bottom center', svgOrigin: '' });

    // idle: gentle float + subtle tilt
    gsap.to(all, { y: -8, duration: 2.4, ease: 'sine.inOut', yoyo: true, repeat: -1, transformOrigin: '50% 50%' });
    gsap.to(all, { rotation: 2, duration: 5.5, ease: 'sine.inOut', yoyo: true, repeat: -1, transformOrigin: '50% 60%' });
    // antennae sway (opposed)
    gsap.fromTo(antL, { rotation: -6 }, { rotation: 6, duration: 1.9, ease: 'sine.inOut', yoyo: true, repeat: -1, transformOrigin: '70px 56px' });
    gsap.fromTo(antR, { rotation: 6 }, { rotation: -6, duration: 1.9, ease: 'sine.inOut', yoyo: true, repeat: -1, transformOrigin: '130px 56px' });
    // antenna tips pulse
    gsap.to(svg.querySelectorAll('.g1r-ant circle'), { scale: 1.18, opacity: .8, duration: .9, ease: 'sine.inOut', yoyo: true, repeat: -1, transformOrigin: '50% 50%' });

    // blink loop (independent of emotion)
    function blink() {
      gsap.to(ctx.state, {
        blink: 0.08, duration: 0.09, ease: 'power1.in',
        onUpdate: function () { drawEyes(ctx); },
        onComplete: function () {
          gsap.to(ctx.state, {
            blink: 1, duration: 0.12, ease: 'power1.out',
            onUpdate: function () { drawEyes(ctx); }
          });
        }
      });
      gsap.delayedCall(2 + Math.random() * 3.5, blink);
    }
    gsap.delayedCall(2 + Math.random() * 2, blink);

    // random emotion scheduler — fluid transitions
    var i = 0;
    function nextEmotion() {
      // weighted-ish wander through ORDER with occasional jumps
      if (Math.random() < 0.5) i = (i + 1) % ORDER.length;
      else i = Math.floor(Math.random() * ORDER.length);
      applyEmotion(ctx, EMOTIONS[ORDER[i]]);
      gsap.delayedCall(1.6 + Math.random() * 2.6, nextEmotion);
    }
    applyEmotion(ctx, EMOTIONS.happy, true);
    gsap.delayedCall(1.8, nextEmotion);
  }

  function init() {
    var gsap = window.gsap || null;
    var hosts = document.querySelectorAll('[data-g1-robot]');
    hosts.forEach(function (h) { mount(h, gsap); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  window.G1Robot = { mount: function (el) { mount(el, window.gsap || null); } };
})();
