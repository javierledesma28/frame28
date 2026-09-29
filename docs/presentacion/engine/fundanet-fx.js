/* =============================================================================
   FUNDANET DECK · EFECTOS
   Se carga después de fundanet-deck.js. Es puramente aditivo: si este fichero
   no está, o falla, el deck funciona igual. No toca el motor ni su estado.
   ============================================================================= */
(function () {
  'use strict';

  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------- 1 · orden dentro del paso
     --i escalona la entrada de los elementos que comparten data-step, para que
     no aparezcan todos a la vez. Se calcula una vez: no cambia nunca. */
  function stagger() {
    $$('.slide').forEach(function (sl) {
      var porPaso = {};
      $$('[data-motion-item]', sl).forEach(function (el) {
        var s = el.getAttribute('data-step') || '1';
        porPaso[s] = (porPaso[s] || 0);
        el.style.setProperty('--i', porPaso[s]);
        porPaso[s]++;
      });
      // Líneas de texto que se revelan una tras otra
      $$('.fx-lines', sl).forEach(function (host) {
        $$('.fx-line', host).forEach(function (l, j) { l.style.setProperty('--l', j); });
      });
    });
    $$('.ov-item').forEach(function (el, j) { el.style.setProperty('--i', j); });
  }

  /* ------------------------------------------------------ 2 · anillos de KPI
     data-ring="0..100" dibuja un arco de progreso alrededor de la cifra.
     pathLength no aplica a <circle>, así que se calcula la circunferencia. */
  function rings() {
    $$('[data-ring]').forEach(function (kpi) {
      if (kpi.querySelector('.kpi-ring')) return;
      var pct = Math.max(0, Math.min(100, parseFloat(kpi.getAttribute('data-ring')) || 0));
      var r = 26, c = 2 * Math.PI * r;
      var ns = 'http://www.w3.org/2000/svg';
      var svg = document.createElementNS(ns, 'svg');
      svg.setAttribute('class', 'kpi-ring');
      svg.setAttribute('viewBox', '0 0 62 62');
      svg.setAttribute('aria-hidden', 'true');
      ['r-bg', 'r-fg'].forEach(function (cls) {
        var ci = document.createElementNS(ns, 'circle');
        ci.setAttribute('cx', 31); ci.setAttribute('cy', 31); ci.setAttribute('r', r);
        ci.setAttribute('class', cls);
        if (cls === 'r-fg') {
          ci.style.strokeDasharray = c;
          ci.style.strokeDashoffset = c;
          // --ring es el desplazamiento final: cuánto arco queda sin pintar
          kpi.style.setProperty('--ring', (c * (1 - pct / 100)).toFixed(2));
        }
        svg.appendChild(ci);
      });
      kpi.appendChild(svg);
    });
  }

  /* --------------------------------------------------------- 3 · tilt 3D
     Sólo con ratón fino: en táctil no aporta y estorba. */
  function tilt() {
    if (reduced) return;
    if (window.matchMedia && !window.matchMedia('(pointer: fine)').matches) return;
    $$('.fx-tilt').forEach(function (el) {
      el.addEventListener('mousemove', function (e) {
        var b = el.getBoundingClientRect();
        var x = (e.clientX - b.left) / b.width - .5;
        var y = (e.clientY - b.top) / b.height - .5;
        el.style.setProperty('--ry', (x * 9).toFixed(2) + 'deg');
        el.style.setProperty('--rx', (-y * 9).toFixed(2) + 'deg');
      });
      el.addEventListener('mouseleave', function () {
        el.style.setProperty('--ry', '0deg');
        el.style.setProperty('--rx', '0deg');
      });
    });
  }

  /* -------------------------------------------------- 4 · fondo de red viva
     data-bg="net" en una slide dibuja nodos que derivan y se enlazan cuando
     se acercan. Un solo rAF para todas: sólo pinta la slide activa, así que
     el coste es constante aunque el deck tenga cincuenta slides. */
  function net() {
    if (reduced) return;
    var hosts = $$('.slide[data-bg="net"]');
    if (!hosts.length) return;

    var W = 1920, H = 1080;
    var capas = hosts.map(function (sl) {
      var cv = document.createElement('canvas');
      cv.className = 'fx-canvas';
      cv.width = W; cv.height = H;
      cv.setAttribute('aria-hidden', 'true');
      sl.insertBefore(cv, sl.firstChild);

      var n = parseInt(sl.getAttribute('data-net-nodes') || '46', 10);
      var pts = [];
      for (var i = 0; i < n; i++) {
        pts.push({
          x: Math.random() * W, y: Math.random() * H,
          vx: (Math.random() - .5) * .22, vy: (Math.random() - .5) * .22,
          r: 1.6 + Math.random() * 2.2
        });
      }
      return { sl: sl, ctx: cv.getContext('2d'), pts: pts };
    });

    // Colores de marca leídos del tema, no escritos a mano
    function color(v, fb) {
      var c = getComputedStyle(document.documentElement).getPropertyValue(v).trim();
      return c || fb;
    }

    var DIST = 190, DIST2 = DIST * DIST;
    function frame() {
      var pri = color('--fn-primary', '#F5C500');
      var sec = color('--fn-secondary', '#8a6f00');
      capas.forEach(function (c) {
        if (!c.sl.classList.contains('is-active')) return;   // sólo la visible
        var g = c.ctx;
        g.clearRect(0, 0, W, H);

        for (var i = 0; i < c.pts.length; i++) {
          var p = c.pts[i];
          p.x += p.vx; p.y += p.vy;
          if (p.x < 0 || p.x > W) p.vx *= -1;
          if (p.y < 0 || p.y > H) p.vy *= -1;
        }
        g.lineWidth = 1;
        for (var a = 0; a < c.pts.length; a++) {
          for (var b = a + 1; b < c.pts.length; b++) {
            var dx = c.pts[a].x - c.pts[b].x, dy = c.pts[a].y - c.pts[b].y;
            var d2 = dx * dx + dy * dy;
            if (d2 > DIST2) continue;
            g.globalAlpha = (1 - d2 / DIST2) * 0.16;
            g.strokeStyle = pri;
            g.beginPath();
            g.moveTo(c.pts[a].x, c.pts[a].y);
            g.lineTo(c.pts[b].x, c.pts[b].y);
            g.stroke();
          }
        }
        for (var k = 0; k < c.pts.length; k++) {
          g.globalAlpha = .30;
          g.fillStyle = k % 4 === 0 ? sec : pri;
          g.beginPath();
          g.arc(c.pts[k].x, c.pts[k].y, c.pts[k].r, 0, 6.2832);
          g.fill();
        }
        g.globalAlpha = 1;
      });
      raf = requestAnimationFrame(frame);
    }

    var raf = requestAnimationFrame(frame);
    // No gastar batería con la pestaña oculta
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { cancelAnimationFrame(raf); raf = 0; }
      else if (!raf) raf = requestAnimationFrame(frame);
    });
  }

  /* --------------------------------------- 5 · líneas sueltas fuera de .fx-lines */
  function loseLines() {
    $$('.fx-line').forEach(function (l) {
      if (l.style.getPropertyValue('--l')) return;
      var hermanos = Array.prototype.filter.call(l.parentNode.children, function (c) {
        return c.classList && c.classList.contains('fx-line');
      });
      l.style.setProperty('--l', hermanos.indexOf(l));
    });
  }

  /* ------------------------------------------------- 6 · puntero de foco
     Tecla L: el cursor se convierte en un foco que atenúa el resto de la slide.
     Sustituye al ratón perdido en el proyector. Es una capa fija sobre todo,
     sin eventos: no interfiere con clics ni con el motor. */
  function pointer() {
    var layer = document.createElement('div');
    layer.className = 'fx-pointer'; layer.setAttribute('aria-hidden', 'true');
    document.body.appendChild(layer);
    var on = false, raf = 0, x = innerWidth / 2, y = innerHeight / 2;
    function paint() { raf = 0; layer.style.setProperty('--px', x + 'px'); layer.style.setProperty('--py', y + 'px'); }
    document.addEventListener('mousemove', function (e) {
      if (!on) return; x = e.clientX; y = e.clientY;
      if (!raf) raf = requestAnimationFrame(paint);
    });
    document.addEventListener('keydown', function (e) {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName || '')) return;
      if (e.key.toLowerCase() === 'l') { on = !on; document.body.classList.toggle('is-pointer', on); paint(); }
      if (e.key === 'Escape' && on) { on = false; document.body.classList.remove('is-pointer'); }
    });
  }

  /* --------------------------------------------- 7 · comparador antes/después
     Arrastrar el tirador (o el propio panel) mueve --pos; ← → con el tirador
     enfocado lo mueve un 5 %. El estado vive en el elemento: rebobinar la
     slide no lo toca, y eso es lo esperado en una comparación manual. */
  function compare() {
    $$('.compare').forEach(function (c) {
      var h = c.querySelector('.cmp-handle');
      if (!h) { h = document.createElement('div'); h.className = 'cmp-handle'; c.appendChild(h); }
      h.setAttribute('tabindex', '0'); h.setAttribute('role', 'slider');
      h.setAttribute('aria-label', 'Comparar antes y después'); h.setAttribute('aria-valuemin', '0'); h.setAttribute('aria-valuemax', '100');
      var set = function (pct) {
        pct = Math.max(2, Math.min(98, pct));
        c.style.setProperty('--pos', pct.toFixed(1) + '%');
        h.setAttribute('aria-valuenow', String(Math.round(pct)));
      };
      var fromEvent = function (e) {
        var r = c.getBoundingClientRect();
        set(100 * (e.clientX - r.left) / r.width);
      };
      var drag = false;
      c.addEventListener('pointerdown', function (e) { drag = true; c.setPointerCapture && c.setPointerCapture(e.pointerId); fromEvent(e); e.preventDefault(); });
      c.addEventListener('pointermove', function (e) { if (drag) fromEvent(e); });
      c.addEventListener('pointerup', function () { drag = false; });
      c.addEventListener('pointercancel', function () { drag = false; });
      h.addEventListener('keydown', function (e) {
        var cur = parseFloat(getComputedStyle(c).getPropertyValue('--pos')) || 50;
        if (e.key === 'ArrowLeft') { set(cur - 5); e.preventDefault(); e.stopPropagation(); }
        if (e.key === 'ArrowRight') { set(cur + 5); e.preventDefault(); e.stopPropagation(); }
      });
      set(parseFloat(getComputedStyle(c).getPropertyValue('--pos')) || 50);
    });
  }

  /* -------------------------------------------- 8 · reproductor de terminal
     Las líneas están en el HTML (estático primero: sin JS se ve el resultado
     final). Con JS se ocultan y se reproducen en orden: las .cmd se teclean,
     las demás aparecen; data-wait="ms" espera antes de una línea y una línea
     .pause detiene hasta que el ponente pulsa. Arranca cuando su paso entra
     y se reinicia por completo si la slide se rebobina. */
  function termplay() {
    $$('.termplay').forEach(function (tp) {
      var screen = tp.querySelector('.tp-screen'); if (!screen) return;
      var lines = $$('.ln', screen);
      var speed = parseFloat(tp.getAttribute('data-speed') || '1') || 1;
      var bar = tp.querySelector('.tp-bar');
      if (!bar) {
        bar = document.createElement('div'); bar.className = 'tp-bar';
        bar.innerHTML = '<span class="tp-dot"></span><span class="tp-dot"></span><span class="tp-dot"></span>' +
          '<span class="tp-title">' + (tp.getAttribute('data-title') || 'terminal') + '</span>' +
          '<span class="tp-state"></span>' +
          '<button type="button" class="tp-btn" data-tp="toggle" aria-label="Reproducir o pausar">⏯</button>' +
          '<button type="button" class="tp-btn" data-tp="restart" aria-label="Reiniciar">↺</button>';
        tp.insertBefore(bar, screen);
      }
      var st = bar.querySelector('.tp-state');
      var i = 0, t = 0, paused = false, started = false, done = false;
      function status(s) { if (st) st.textContent = s || ''; }
      function reset() {
        clearTimeout(t); i = 0; paused = false; started = false; done = false;
        lines.forEach(function (l) { l.classList.remove('tp-on', 'tp-typing'); l.style.removeProperty('--dur'); });
        tp.classList.remove('is-paused', 'is-done'); status('');
      }
      function finish() { done = true; tp.classList.add('is-done'); status('fin'); }
      function step() {
        if (paused) return;
        if (i >= lines.length) { finish(); return; }
        var l = lines[i++];
        if (l.classList.contains('pause')) { l.classList.add('tp-on'); paused = true; tp.classList.add('is-paused'); status('en pausa · pulsa ⏯'); return; }
        var wait = (parseInt(l.getAttribute('data-wait') || '0', 10) || 0) / speed;
        var typing = l.classList.contains('cmd');
        var dur = typing ? Math.min(2800, 26 * l.textContent.length) / speed : 0;
        t = setTimeout(function () {
          l.style.setProperty('--dur', Math.round(dur) + 'ms');
          l.classList.add('tp-on'); if (typing) l.classList.add('tp-typing');
          screen.scrollTop = screen.scrollHeight;
          t = setTimeout(function () { l.classList.remove('tp-typing'); step(); }, dur + (typing ? 240 : 110) / speed);
        }, wait);
      }
      function play() {
        if (reduced) { lines.forEach(function (l) { l.classList.add('tp-on'); }); finish(); return; }
        started = true; paused = false; tp.classList.remove('is-paused'); status('');
        step();
      }
      function pause() { paused = true; clearTimeout(t); tp.classList.add('is-paused'); status('en pausa · pulsa ⏯'); }
      tp.classList.add('is-live');
      bar.addEventListener('click', function (e) {
        var b = e.target.closest('[data-tp]'); if (!b) return;
        var a = b.getAttribute('data-tp');
        if (a === 'restart') { reset(); play(); }
        else if (done) { reset(); play(); }
        else if (paused || !started) { play(); }
        else { pause(); }
      });
      // Arranque ligado al paso del motor: cuando el item entra, se reproduce;
      // si el ponente rebobina y el item sale, se reinicia del todo.
      var host = tp.closest('[data-motion-item]') || tp;
      var obs = new MutationObserver(function () {
        var inn = host.classList.contains('is-in');
        if (inn && !started && !done) play();
        if (!inn && (started || done)) reset();
      });
      obs.observe(host, { attributes: true, attributeFilter: ['class'] });
      if (host.classList.contains('is-in')) play();
    });
  }

  function init() {
    try {
      stagger();
      rings();
      loseLines();
      tilt();
      net();
      pointer();
      compare();
      termplay();
    } catch (e) {
      // Los efectos nunca deben tumbar el deck
      console.warn('[Think28 FX] efecto omitido:', e && e.message);
    }
  }

  // Después del motor, que es quien construye el índice y pone .motion-ready
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(init, 0); });
  else setTimeout(init, 0);
})();
