/* Group One — Componentes (interações) */
(function () {
  function toast(m){var t=document.getElementById('toast');t.textContent=m;t.classList.add('show');clearTimeout(toast._t);toast._t=setTimeout(function(){t.classList.remove('show');},1500);}
  window.gToast = toast;

  // tabs
  document.querySelectorAll('.tabs').forEach(function(tabs){
    var btns=tabs.querySelectorAll('.tab'), panes=tabs.querySelectorAll('.tabpane');
    btns.forEach(function(b,i){b.addEventListener('click',function(){
      btns.forEach(function(x){x.classList.remove('active');});
      panes.forEach(function(x){x.classList.remove('active');});
      b.classList.add('active'); if(panes[i]) panes[i].classList.add('active');
    });});
  });

  // alert dismiss
  document.querySelectorAll('.alert .x').forEach(function(x){
    x.addEventListener('click',function(){var a=x.closest('.alert');a.style.transition='.2s';a.style.opacity='0';setTimeout(function(){a.style.display='none';},200);toast('Alerta dispensado');});
  });

  // modal
  window.openModal=function(){document.getElementById('demoModal').classList.add('open');};
  window.closeModal=function(){document.getElementById('demoModal').classList.remove('open');};
  var bk=document.getElementById('demoModal');
  if(bk) bk.addEventListener('click',function(e){if(e.target===bk)closeModal();});

  // demo buttons toast
  document.querySelectorAll('[data-demo]').forEach(function(b){
    b.addEventListener('click',function(){if(!b.disabled)toast(b.getAttribute('data-demo'));});
  });

  // scrollspy
  var links=[].slice.call(document.querySelectorAll('.side-nav a'));
  var secs=links.map(function(l){return document.querySelector(l.getAttribute('href'));});
  function spy(){var y=(document.querySelector('.main').scrollTop||window.scrollY)+140;var idx=0;
    secs.forEach(function(s,i){if(s&&s.offsetTop<=y)idx=i;});
    links.forEach(function(l,i){l.classList.toggle('active',i===idx);});}
  window.addEventListener('scroll',spy,{passive:true});
  spy();
})();
