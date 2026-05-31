/* Group One brandbook — interactions */
(function () {
  // copy hex
  function toast(msg) {
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.classList.remove('show'); }, 1600);
  }
  document.querySelectorAll('[data-copy]').forEach(function (el) {
    el.addEventListener('click', function () {
      var v = el.getAttribute('data-copy');
      navigator.clipboard && navigator.clipboard.writeText(v);
      toast(v + ' copiado');
    });
  });

  // download inline SVG
  window.downloadSvg = function (id, name) {
    var el = document.getElementById(id);
    if (!el) return;
    var clone = el.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    var s = new XMLSerializer().serializeToString(clone);
    var blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>\n' + s], { type: 'image/svg+xml' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 800);
    toast(name + ' baixado');
  };

  // scroll spy
  var links = [].slice.call(document.querySelectorAll('.nav-links a'));
  var secs = links.map(function (l) { return document.querySelector(l.getAttribute('href')); });
  function spy() {
    var y = window.scrollY + 120;
    var idx = 0;
    secs.forEach(function (s, i) { if (s && s.offsetTop <= y) idx = i; });
    links.forEach(function (l, i) { l.style.color = i === idx ? '#fff' : ''; });
  }
  window.addEventListener('scroll', spy, { passive: true });
  spy();
})();
