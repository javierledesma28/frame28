/* =============================================================================
   FUNDANET DECK ENGINE · motor
   -----------------------------------------------------------------------------
   Principio de diseño: el estado se APLICA POR ÍNDICE, nunca se encadena con
   temporizadores. Ir al paso 4 no es "ejecutar 1,2,3,4": es pintar el estado 4.
   Eso hace el rebobinado determinista por construcción — no hay forma de que
   avanzar y retroceder dejen la slide distinta.

   Contrato "estático primero": este script añade `.motion-ready` al documento
   sólo cuando ha terminado de inicializarse sin errores. Si algo falla antes,
   el CSS deja todo el contenido visible y el deck sigue siendo utilizable.
   ============================================================================= */
(function () {
  'use strict';

  var W = 1920, H = 1080;
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  var deck = {
    slides: [], i: 0, step: 0, steps: 0,
    playing: false, timer: null, audience: null, isAudience: false,
    t0: Date.now(), slideT0: Date.now()
  };

  /* ------------------------------------------------------------- 1 · escalado
     Se escala el escenario entero, no cada elemento. Todo se autora a 1920x1080
     y el deck se ve idéntico en cualquier pantalla o proyector. */
  function fit() {
    var vp = $('.deck-viewport'), st = $('.deck-stage');
    if (!vp || !st) return;
    var s = Math.min(vp.clientWidth / W, vp.clientHeight / H);
    var x = (vp.clientWidth - W * s) / 2, y = (vp.clientHeight - H * s) / 2;
    st.style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + s + ')';
  }

  /* ------------------------------------------------------- 2 · pasos de slide
     Un paso agrupa los [data-motion-item] con el mismo data-step (1..N).
     Estado 0 = nada revelado. Estado N = slide completa. */
  function stepsOf(sl) {
    var n = 0;
    $$('[data-motion-item]', sl).forEach(function (el) {
      n = Math.max(n, parseInt(el.getAttribute('data-step') || '1', 10) || 1);
    });
    return n;
  }

  function applyStep(sl, k) {
    var total = stepsOf(sl);
    $$('[data-motion-item]', sl).forEach(function (el) {
      var s = parseInt(el.getAttribute('data-step') || '1', 10) || 1;
      el.classList.toggle('is-in', s <= k);
      el.classList.toggle('is-now', s === k && k < total);
    });
    // Nodos de proceso y carriles: marcan hecho / en curso por su propio índice
    $$('[data-flow-step]', sl).forEach(function (el) {
      var s = parseInt(el.getAttribute('data-flow-step'), 10);
      el.classList.toggle('done', s < k);
      el.classList.toggle('is-now', s === k);
    });
    sl.setAttribute('data-frame', k >= total ? 'end' : (k === 0 ? 'static' : 'step'));
    sl.setAttribute('data-step-count', String(total));
    paintStepbar(sl, k, total);
    countUp(sl, k);
  }

  function paintStepbar(sl, k, total) {
    var bar = $('.stepbar', sl);
    if (!bar) return;
    var dots = $$('.sb-dot', bar);
    if (dots.length !== total) {
      bar.querySelectorAll('.sb-dot').forEach(function (d) { d.remove(); });
      var lab = $('.sb-lab', bar);
      for (var j = 1; j <= total; j++) {
        var d = document.createElement('span');
        d.className = 'sb-dot';
        bar.insertBefore(d, lab || null);
      }
      dots = $$('.sb-dot', bar);
    }
    dots.forEach(function (d, j) {
      d.classList.toggle('done', j + 1 < k);
      d.classList.toggle('now', j + 1 === k);
    });
    var lab = $('.sb-lab', bar);
    if (lab && lab.hasAttribute('data-auto')) {
      lab.innerHTML = 'Paso <b>' + Math.max(k, 1) + '</b> de <b>' + total + '</b>';
    }
  }

  /* Contadores: se animan una vez, cuando su paso entra. Idempotente. */
  function countUp(sl, k) {
    $$('[data-count-to]', sl).forEach(function (el) {
      var host = el.closest('[data-motion-item]');
      var s = host ? (parseInt(host.getAttribute('data-step') || '1', 10) || 1) : 1;
      var target = parseFloat(el.getAttribute('data-count-to'));
      var dec = parseInt(el.getAttribute('data-count-dec') || '0', 10);
      var pre = el.getAttribute('data-count-pre') || '';
      var suf = el.getAttribute('data-count-suf') || '';
      if (s > k) {
        el.textContent = pre + (0).toFixed(dec) + suf;
        el.removeAttribute('data-counted');
        el.removeAttribute('data-counting');
        return;
      }
      if (el.getAttribute('data-counted') === '1') return;
      el.setAttribute('data-counted', '1');
      if (reduced()) { el.textContent = pre + target.toFixed(dec) + suf; return; }
      var t0 = performance.now(), dur = 820;
      el.setAttribute('data-counting', '1');
      (function tick(now) {
        // Si la pestaña se oculta a mitad de la cuenta, el navegador deja de
        // llamar a rAF y este tick no vuelve: se cierra aquí mismo.
        if (document.hidden) { cierraContadores(); return; }
        var p = Math.min(1, (now - t0) / dur);
        var e = 1 - Math.pow(1 - p, 3);
        el.textContent = pre + (target * e).toFixed(dec) + suf;
        if (p < 1) { requestAnimationFrame(tick); return; }
        el.removeAttribute('data-counting');
      })(t0);
    });
  }

  /* Un contador a medias que se queda congelado para siempre
     ---------------------------------------------------------------------------
     `requestAnimationFrame` NO se ejecuta mientras la pestaña está oculta. Un
     contador al que le pillan a mitad se queda con el número que llevara —y
     como ya tiene `data-counted`, no vuelve a arrancar nunca—. El ponente que
     cambia de ventana durante una slide de KPIs vuelve y lee «3.334 €» donde
     su deck dice 4.118 €, sin ningún indicio de que eso esté mal.

     Se cierran todos en su valor final. La animación ya no se puede enseñar
     —ocurrió mientras nadie miraba— y al volver lo único que importa es que la
     cifra sea la de verdad.

     Se escucha en los DOS sentidos a propósito: al ocultarse, para cerrar lo
     que estuviera en vuelo; y al volver, porque si la cuenta arrancó con la
     pestaña ya oculta el tick no llegó a correr ni una vez y el número se
     habría quedado en cero. Medido el 18/09/2026 con el deck del CTO. */
  function cierraContadores() {
    $$('[data-count-to][data-counting="1"]').forEach(function (el) {
      el.removeAttribute('data-counting');
      var dec = parseInt(el.getAttribute('data-count-dec') || '0', 10);
      el.textContent = (el.getAttribute('data-count-pre') || '')
        + parseFloat(el.getAttribute('data-count-to')).toFixed(dec)
        + (el.getAttribute('data-count-suf') || '');
    });
  }
  document.addEventListener('visibilitychange', cierraContadores);

  function reduced() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /* Al imprimir (o exportar a PDF) los contadores deben mostrar su valor final
     en todas las slides, no el cero del estado inicial. */
  function printCounters() {
    $$('[data-count-to]').forEach(function (el) {
      var target = parseFloat(el.getAttribute('data-count-to'));
      var dec = parseInt(el.getAttribute('data-count-dec') || '0', 10);
      el.textContent = (el.getAttribute('data-count-pre') || '') + target.toFixed(dec) + (el.getAttribute('data-count-suf') || '');
      el.setAttribute('data-counted', '1');
    });
  }
  window.addEventListener('beforeprint', printCounters);
  if (window.matchMedia) {
    var mqPrint = window.matchMedia('print');
    if (mqPrint.addEventListener) mqPrint.addEventListener('change', function (e) { if (e.matches) printCounters(); });
    else if (mqPrint.addListener) mqPrint.addListener(function (e) { if (e.matches) printCounters(); });
  }

  /* ------------------------------------------------------- 3 · ir a una slide */
  function show(n, opts) {
    opts = opts || {};
    n = Math.max(0, Math.min(deck.slides.length - 1, n));
    var prevI = deck.i;
    var prev = deck.slides[deck.i], next = deck.slides[n];
    var back = n < deck.i;

    if (prev && prev !== next) {
      prev.classList.remove('is-active', 'is-enter');
      prev.classList.add('is-exit');
      (function (p) { setTimeout(function () { p.classList.remove('is-exit'); }, 700); })(prev);
    }

    deck.i = n;
    deck.steps = stepsOf(next);
    // Al entrar hacia delante la slide muestra ya su primer bloque: llegar y no
    // ver nada parece un fallo, y obliga al ponente a pulsar dos veces.
    // data-start-step="0" fuerza la entrada en vacío cuando eso es lo buscado.
    var inicio = next.getAttribute('data-start-step');
    inicio = (inicio == null) ? Math.min(1, deck.steps) : (parseInt(inicio, 10) || 0);
    deck.step = (opts.step != null) ? opts.step : (back ? deck.steps : inicio);

    next.classList.add('is-active');
    if (prev !== next) {
      next.classList.remove('is-enter');
      void next.offsetWidth;                 // reinicia la animación de entrada
      next.classList.add('is-enter');
      // Se retira al terminar: si se queda, los pseudo-elementos de la
      // transición (cortinas, máscaras) siguen montados sobre el contenido.
      clearTimeout(next._enterT);
      next._enterT = setTimeout(function () { next.classList.remove('is-enter'); }, 1100);
    }
    applyStep(next, deck.step);

    deck.slideT0 = Date.now();
    paintChrome();
    announce();
    sync();
    if (!opts.init && prev !== next) maybeIntro(prevI, n);
  }

  /* Barra de progreso por capítulos: un tramo por capítulo, proporcional a sus
     slides, con su relleno propio. El tramo actual muestra el nombre; el resto
     al pasar el ratón. Clic en un tramo salta a su primera slide. Sin capítulos
     declarados (ni eyebrows) la barra sigue siendo la línea continua de siempre. */
  function buildProgress() {
    var pr = $('.deck-progress'); if (!pr) return;
    var ch = chapters(), list = ch.list, N = deck.slides.length;
    if (!list.length) return;
    var seg = function (cls, slides, label) {
      return '<span class="dp-seg ' + cls + '" style="--w:' + (100 * slides.length / N).toFixed(3) + '%"' +
        ' data-first="' + slides[0] + '" data-last="' + slides[slides.length - 1] + '" data-go="' + slides[0] + '"' +
        (label ? ' title="' + esc(label) + '"' : '') + '><i></i>' + (label ? '<b>' + esc(label) + '</b>' : '') + '</span>';
    };
    var h = '';
    if (ch.start.length) h += seg('dp-end', ch.start, '');
    list.forEach(function (c) { h += seg('dp-ch', c.slides, c.name); });
    if (ch.end.length) h += seg('dp-end', ch.end, '');
    pr.innerHTML = h;
    pr.classList.add('has-chapters');
    pr.style.width = '';
    if (!deck.isAudience) {
      pr.addEventListener('click', function (e) {
        var s = e.target.closest('[data-go]');
        if (s) { stop(); show(parseInt(s.getAttribute('data-go'), 10)); }
      });
    }
  }
  function paintProgress() {
    var pr = $('.deck-progress'); if (!pr) return;
    var frac = deck.steps ? deck.step / deck.steps : 1;
    if (!pr.classList.contains('has-chapters')) {
      pr.style.width = (100 * (deck.i + frac) / deck.slides.length) + '%';
      return;
    }
    $$('.dp-seg', pr).forEach(function (s) {
      var a = parseInt(s.getAttribute('data-first'), 10), b = parseInt(s.getAttribute('data-last'), 10), n = b - a + 1;
      var f = deck.i > b ? 1 : (deck.i < a ? 0 : (deck.i - a + frac) / n);
      var fill = $('i', s); if (fill) fill.style.width = (100 * f).toFixed(2) + '%';
      s.classList.toggle('is-now', deck.i >= a && deck.i <= b);
      s.classList.toggle('done', deck.i > b);
    });
  }

  function paintChrome() {
    var pos = $('.dc-pos');
    if (pos) pos.textContent = (deck.i + 1) + ' / ' + deck.slides.length;
    paintProgress();
    var b = $('[data-deck-action="prev"]'), f = $('[data-deck-action="next"]');
    if (b) b.disabled = (deck.i === 0 && deck.step === 0);
    if (f) f.disabled = (deck.i === deck.slides.length - 1 && deck.step >= deck.steps);
    var pl = $('[data-deck-action="play"]');
    if (pl) pl.setAttribute('aria-pressed', deck.playing ? 'true' : 'false');
    if (overviewOpen() && !deck.introOpen) buildOverview(false);
    if (deck.presenterOn) paintPresenter();
  }

  function announce() {
    var st = $('.deck-status');
    if (!st) return;
    var sl = deck.slides[deck.i];
    var t = (sl.getAttribute('data-title') || ($('.s-title', sl) || {}).textContent || '').trim();
    st.textContent = 'Slide ' + (deck.i + 1) + ' de ' + deck.slides.length +
      (deck.steps ? ', paso ' + deck.step + ' de ' + deck.steps : '') + '. ' + t;
  }

  /* -------------------------------------------------------- 4 · avanzar/atrás */
  function next() {
    if (deck.step < deck.steps) { deck.step++; applyStep(deck.slides[deck.i], deck.step); paintChrome(); announce(); sync(); return true; }
    if (deck.i < deck.slides.length - 1) { show(deck.i + 1); return true; }
    stop(); return false;
  }
  function prev() {
    if (deck.step > 0) { deck.step--; applyStep(deck.slides[deck.i], deck.step); paintChrome(); announce(); sync(); return; }
    if (deck.i > 0) show(deck.i - 1);
  }

  /* ------------------------------------------------------------ 5 · autoplay */
  function play() {
    if (deck.playing) return;
    deck.playing = true; paintChrome();
    var hold = parseInt(getComputedStyle(document.documentElement)
      .getPropertyValue('--motion-hold'), 10) || 720;
    (function beat() {
      deck.timer = setTimeout(function () {
        if (!deck.playing) return;
        if (next()) beat(); else stop();
      }, Math.max(hold, 900));
    })();
  }
  function stop() {
    deck.playing = false;
    if (deck.timer) { clearTimeout(deck.timer); deck.timer = null; }
    paintChrome();
  }
  function toggle() { deck.playing ? stop() : play(); }

  /* ------------------------------------------------ 6 · recorrido por capítulos
     El índice no es una rejilla de slides: es el mapa de la historia. Cada slide
     declara su capítulo con data-chapter (si no, hereda el de la anterior; si
     ningún deck lo declara, se agrupa por el .s-eyebrow). Las portadas sin
     capítulo son los extremos del recorrido. El capítulo actual va iluminado,
     los pasados atenuados y los futuros perfilados. Al pasar el ratón por una
     slide se ve su miniatura real; al hacer clic se va a ella.
     El mismo mapa se abre solo, un par de segundos, al entrar en cada capítulo:
     hace de agenda sin gastar una slide. */
  function titleOf(sl, j) {
    return (sl.getAttribute('data-title') || ($('.s-title', sl) || {}).textContent || 'Slide ' + (j + 1)).trim();
  }
  function chapters() {
    if (deck._chapters) return deck._chapters;
    var chs = [], cur = null, start = [], end = [];
    var declared = deck.slides.some(function (s) { return s.hasAttribute('data-chapter'); });
    var last = deck.slides.length - 1;
    deck.slides.forEach(function (sl, j) {
      var name = sl.getAttribute('data-chapter');
      if (name == null && !declared) name = (($('.s-eyebrow', sl) || {}).textContent || '').trim() || null;
      var cover = sl.classList.contains('cover');
      if (name == null && cover) {
        if (!chs.length) { start.push(j); return; }
        if (j === last) { end.push(j); return; }
      }
      if (name != null && (!cur || cur.name !== name)) { cur = { name: name, slides: [], first: j, seconds: 0 }; chs.push(cur); }
      if (!cur) { cur = { name: 'Contenido', slides: [], first: j, seconds: 0 }; chs.push(cur); }
      cur.slides.push(j);
      cur.seconds += parseInt(sl.getAttribute('data-seconds') || '0', 10) || 0;
    });
    deck._chapters = { list: chs, start: start, end: end };
    return deck._chapters;
  }
  function chapterIndex(j) {
    var list = chapters().list;
    for (var c = 0; c < list.length; c++) if (list[c].slides.indexOf(j) >= 0) return c;
    return -1;
  }
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function mins(sec) { return sec ? '≈ ' + Math.max(1, Math.round(sec / 60)) + ' min' : ''; }

  function buildOverview(intro) {
    var ov = $('.deck-overview'); if (!ov) return;
    var ch = chapters(), list = ch.list, n = list.length;
    var ci = chapterIndex(deck.i);
    var title = (document.title || '').split('·')[0].trim();
    var pos = ci >= 0 ? 'Capítulo <b>' + (ci + 1) + '</b> de ' + n : '';
    var frac = ci < 0 ? (deck.i > (ch.start[0] || -1) ? 1 : 0)
                      : (ci + (list[ci].slides.indexOf(deck.i) + 1) / list[ci].slides.length) / n;

    var h = '<div class="ov-head">' +
      '<span class="fn-logo blanco sm" role="img" aria-label="Think28"></span>' +
      '<span class="ov-title">' + esc(title) + '</span>' +
      '<span class="ov-pos">' + pos + ' · slide <b>' + (deck.i + 1) + '</b> de ' + deck.slides.length + '</span>' +
      (intro ? '' : '<button type="button" class="ov-close" data-ov="close" aria-label="Cerrar índice">✕</button>') +
      '</div>';

    h += '<div class="ov-journey"><div class="ov-cols" style="--n:' + n + '">';
    h += '<div class="ov-line"><i style="width:' + (100 * frac).toFixed(1) + '%"></i></div>';

    var endpoint = function (j, cls) {
      return '<button type="button" class="ov-end ' + cls + (j === deck.i ? ' is-active' : (j < deck.i ? ' past' : '')) +
        '" data-go="' + j + '" data-preview="' + j + '"><span class="ov-dot"></span><span class="ov-end-t">' +
        esc(titleOf(deck.slides[j], j)) + '</span></button>';
    };
    h += ch.start.length ? endpoint(ch.start[0], 'start') : '<span class="ov-end start ghost"></span>';

    list.forEach(function (c, k) {
      var st = k < ci ? 'done' : (k === ci ? 'is-now' : 'todo');
      h += '<section class="ov-ch ' + st + '" style="--i:' + k + '">' +
        '<button type="button" class="ov-ch-head" data-go="' + c.first + '">' +
          '<span class="ov-ch-n">' + String(k + 1).padStart(2, '0') + '</span>' +
          '<span class="ov-ch-name">' + esc(c.name) + '</span>' +
          '<span class="ov-ch-meta">' + c.slides.length + (c.slides.length === 1 ? ' slide' : ' slides') +
            (c.seconds ? ' · ' + mins(c.seconds) : '') + '</span>' +
        '</button><ol class="ov-ch-list">';
      c.slides.forEach(function (j) {
        var cls = j === deck.i ? ' is-active' : (j < deck.i ? ' past' : '');
        h += '<li><button type="button" class="ov-s' + cls + '" data-go="' + j + '" data-preview="' + j + '">' +
          '<span class="ov-s-n">' + String(j + 1).padStart(2, '0') + '</span>' +
          '<span class="ov-s-t">' + esc(titleOf(deck.slides[j], j)) + '</span></button></li>';
      });
      h += '</ol></section>';
    });

    h += ch.end.length ? endpoint(ch.end[0], 'end') : '<span class="ov-end end ghost"></span>';
    h += '</div></div>';

    if (intro && ci >= 0) {
      h += '<div class="ov-intro-cap"><span class="ov-intro-k">Capítulo ' + (ci + 1) + ' de ' + n + '</span>' +
           '<span class="ov-intro-t">' + esc(list[ci].name) + '</span></div>';
    } else {
      h += '<div class="ov-preview" hidden><div class="ov-pv-screen"></div><div class="ov-pv-cap"></div></div>' +
           '<div class="ov-hint">Clic en una slide para ir · <b>O</b> o <b>Esc</b> cierra</div>';
    }
    ov.innerHTML = h;
    ov.classList.toggle('is-intro', !!intro);

    if (!intro) {
      $$('[data-preview]', ov).forEach(function (b) {
        b.addEventListener('mouseenter', function () { preview(parseInt(b.getAttribute('data-preview'), 10)); });
        b.addEventListener('focus', function () { preview(parseInt(b.getAttribute('data-preview'), 10)); });
      });
    }
  }
  function preview(j) {
    var pv = $('.ov-preview'); if (!pv) return;
    pv.hidden = false;
    thumb($('.ov-pv-screen', pv), deck.slides[j]);
    var cap = $('.ov-pv-cap', pv);
    if (cap) cap.innerHTML = '<b>' + String(j + 1).padStart(2, '0') + '</b> ' + esc(titleOf(deck.slides[j], j));
  }
  function openOverview(opts) {
    opts = opts || {};
    var ov = $('.deck-overview'); if (!ov) return;
    clearTimeout(deck.introT);
    buildOverview(!!opts.intro);
    deck.introOpen = !!opts.intro;
    ov.classList.add('is-open');
    if (opts.intro) {
      deck.introT = setTimeout(closeOverview, opts.ms || 2400);
    } else {
      var act = $('.ov-s.is-active, .ov-end.is-active', ov);
      if (act) preview(parseInt(act.getAttribute('data-go'), 10));
    }
  }
  function closeOverview() {
    var o = $('.deck-overview'); if (!o) return;
    clearTimeout(deck.introT);
    deck.introOpen = false;
    o.classList.remove('is-open', 'is-intro');
    var pv = $('.ov-pv-screen', o); if (pv && pv._ro) { pv._ro.disconnect(); pv._ro = null; }
  }
  function overviewOpen() { var o = $('.deck-overview'); return !!(o && o.classList.contains('is-open')); }
  function toggleOverview() { overviewOpen() ? closeOverview() : openOverview(); }

  /* El índice sólo aparece y desaparece cuando lo pide el ponente (tecla O,
     icono o FundanetDeck.overview()). Nunca se abre ni se cierra solo mientras
     se presenta. La única excepción es opt-in: con data-chapter-intro="on" en
     <html>, al cruzar hacia delante la frontera de un capítulo el recorrido se
     muestra 2,4 s con el capítulo nuevo encendido y se cierra solo. */
  function maybeIntro(fromI, toI) {
    if (document.documentElement.getAttribute('data-chapter-intro') !== 'on') return;
    if (reduced() || toI <= fromI) return;
    var a = chapterIndex(fromI), b = chapterIndex(toI);
    if (b < 0 || a === b || chapters().list.length < 2) return;
    if (chapters().list[b].first !== toI) return;        // sólo al entrar por la primera slide
    openOverview({ intro: true });
  }

  /* ------------------------------------------------------ 7 · modo presentador
     Dos ventanas reales sincronizadas por postMessage directo entre opener y
     popup. Se eligió postMessage y no BroadcastChannel/localStorage porque son
     los únicos que funcionan con file:// (origen opaco), que es como se abre
     un deck que mandas por correo. */
  function openPresenter() {
    if (deck.isAudience) return;                 // la ventana del público sólo obedece
    if (deck.presenterOn) { closePresenter(); return; }

    var url = location.href.split('#')[0];
    url += (url.indexOf('?') < 0 ? '?' : '&') + 'screen=audience';
    // popup=yes obliga a ventana real en Chrome/Edge/Firefox. Sin él, algunos
    // contextos embebidos navegan la pestaña actual y el ponente pierde el deck.
    var win = null;
    try { win = window.open(url, 'fnDeckAudience', 'popup=yes,width=1280,height=720'); } catch (e) {}
    if (win === window) win = null;

    // Sin segunda ventana el modo sigue siendo útil para ensayar: notas,
    // siguiente slide y cronómetro en una sola pantalla.
    deck.audience = win || null;
    document.body.classList.add('is-presenter');
    deck.presenterOn = true;
    buildPresenter();
    var w = $('[data-pv="warn"]');
    if (w) w.hidden = !!win;
    paintPresenter();
    if (!deck.clockTimer) deck.clockTimer = setInterval(paintClock, 1000);
    if (win) setTimeout(sync, 700);
  }

  function closePresenter() {
    document.body.classList.remove('is-presenter');
    deck.presenterOn = false;
    if (deck.audience && !deck.audience.closed) deck.audience.close();
    deck.audience = null;
    if (deck.clockTimer) { clearInterval(deck.clockTimer); deck.clockTimer = null; }
    fit();
  }

  function buildPresenter() {
    if ($('.pv')) return;
    var pv = document.createElement('div');
    pv.className = 'pv';
    pv.innerHTML =
      '<div class="pv-main">' +
        '<div class="pv-lab">En pantalla</div>' +
        '<div class="pv-screen" data-pv="now"></div>' +
        '<div class="pv-clock">' +
          '<div><div class="c-lab">Total</div><div class="c-val" data-pv="tTotal">0:00</div></div>' +
          '<div><div class="c-lab">En esta slide</div><div class="c-val" data-pv="tSlide">0:00</div></div>' +
          '<div><div class="c-lab">Posición</div><div class="c-val" data-pv="tPos">1 / 1</div></div>' +
        '</div>' +
      '</div>' +
      '<div class="pv-side">' +
        '<div class="pv-lab">Siguiente</div>' +
        '<div class="pv-screen" data-pv="next"></div>' +
        '<div class="pv-warn" data-pv="warn" hidden>Sin ventana de público: el navegador la ha ' +
          'bloqueado. Esto sirve igual para ensayar. Permite las ventanas emergentes y pulsa P otra vez.</div>' +
        '<div class="pv-notes" data-pv="notes"></div>' +
      '</div>';
    document.body.appendChild(pv);
  }

  /* Miniatura por clonado del DOM y escalado. Sin iframes: es lo único que
     funciona con file:// sin permisos extra.
     El escalado se reajusta con ResizeObserver porque en el primer frame el
     contenedor del grid todavía no tiene su ancho definitivo. */
  function thumb(host, sl) {
    if (!host) return;
    host.innerHTML = '';
    if (host._ro) { host._ro.disconnect(); host._ro = null; }
    if (!sl) return;

    var box = document.createElement('div');
    box.style.cssText = 'position:absolute;inset:0;overflow:hidden';
    var c = sl.cloneNode(true);
    c.classList.remove('is-enter', 'is-exit');
    c.classList.add('is-active');
    c.style.cssText = 'position:absolute;left:0;top:0;transform-origin:0 0;visibility:visible;opacity:1';
    box.appendChild(c);
    host.appendChild(box);

    var rescale = function () {
      var w = host.clientWidth;
      if (!w) return;
      c.style.transform = 'scale(' + (w / W) + ')';
    };
    rescale();
    if (window.ResizeObserver) {
      host._ro = new ResizeObserver(rescale);
      host._ro.observe(host);
    } else {
      requestAnimationFrame(function () { requestAnimationFrame(rescale); });
    }
  }

  function paintPresenter() {
    if (!deck.presenterOn) return;
    var cur = deck.slides[deck.i], nx = deck.slides[deck.i + 1];
    thumb($('[data-pv="now"]'), cur);
    thumb($('[data-pv="next"]'), nx);
    var n = $('[data-pv="notes"]');
    if (n) {
      var src = $('.s-notes', cur);
      n.innerHTML = '<h4>Notas · slide ' + (deck.i + 1) + '</h4>' +
        (src ? src.innerHTML : '<p style="color:#6a7f9e">Sin notas para esta slide.</p>');
    }
    var p = $('[data-pv="tPos"]');
    if (p) p.textContent = (deck.i + 1) + ' / ' + deck.slides.length +
      (deck.steps ? '  ·  paso ' + deck.step + '/' + deck.steps : '');
  }

  function mmss(ms) {
    var s = Math.floor(ms / 1000);
    return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  }
  function paintClock() {
    var a = $('[data-pv="tTotal"]'), b = $('[data-pv="tSlide"]');
    if (a) a.textContent = mmss(Date.now() - deck.t0);
    if (b) {
      var el = Date.now() - deck.slideT0;
      b.textContent = mmss(el);
      var budget = parseInt(deck.slides[deck.i].getAttribute('data-seconds') || '0', 10);
      b.classList.toggle('over', budget > 0 && el > budget * 1000);
    }
  }

  /* Sincronización presentador -> público */
  function sync() {
    if (deck.audience && !deck.audience.closed) {
      try { deck.audience.postMessage({ fnDeck: 1, i: deck.i, step: deck.step }, '*'); } catch (e) {}
    }
  }
  window.addEventListener('message', function (ev) {
    var d = ev.data;
    if (!d || d.fnDeck !== 1) return;
    if (d.i !== deck.i) show(d.i, { step: d.step });
    else if (d.step !== deck.step) { deck.step = d.step; applyStep(deck.slides[deck.i], deck.step); paintChrome(); }
  });

  /* ------------------------------------------------------------- 8 · teclado */
  function keys(e) {
    if (/^(INPUT|TEXTAREA|SELECT)$/.test((e.target.tagName || '')) || e.target.isContentEditable) return;
    var k = e.key;
    // La transición de capítulo se cierra con cualquier tecla, sin efecto adicional
    if (deck.introOpen && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); closeOverview(); return; }
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ' || k === 'Enter') {
      if (k === ' ' && /^(BUTTON|A)$/.test(e.target.tagName)) return;
      e.preventDefault(); stop(); next(); return;
    }
    if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace') { e.preventDefault(); stop(); prev(); return; }
    if (k === 'ArrowDown') { e.preventDefault(); stop(); show(deck.i + 1); return; }
    if (k === 'ArrowUp')   { e.preventDefault(); stop(); show(deck.i - 1); return; }
    if (k === 'Home')      { e.preventDefault(); stop(); show(0); return; }
    if (k === 'End')       { e.preventDefault(); stop(); show(deck.slides.length - 1); return; }
    if (k === 'Escape')    { closeOverview(); return; }
    if (e.ctrlKey || e.metaKey || e.altKey) return;      // no secuestrar atajos
    var lk = k.toLowerCase();
    if (lk === 'o') { e.preventDefault(); toggleOverview(); }
    if (lk === 'p') { e.preventDefault(); openPresenter(); }
    if (lk === 'r') { e.preventDefault(); stop(); show(deck.i, { step: 0 }); }
    if (lk === 'f') { e.preventDefault(); toggleFull(); }
    if (lk === 'a') { e.preventDefault(); toggle(); }
    if (lk === 't') {
      e.preventDefault();
      var r = document.documentElement;
      r.setAttribute('data-theme', r.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
    }
  }
  function toggleFull() {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen && document.documentElement.requestFullscreen();
  }

  /* ---------------------------------------------------------------- 9 · init */
  function init() {
    deck.slides = $$('.slide');
    if (!deck.slides.length) return;                 // sin slides no tocamos nada

    var q = new URLSearchParams(location.search);
    deck.isAudience = q.get('screen') === 'audience';

    // Longitud real de trazo para cada conector: pathLength=1 lo normaliza,
    // así una sola regla CSS sirve para cualquier geometría.
    $$('.conn-draw, .line-draw').forEach(function (p) { p.setAttribute('pathLength', '1'); });

    // Numeración y pie de marca automáticos
    deck.slides.forEach(function (sl, j) {
      var f = $('.s-foot', sl);
      if (f && !$('.s-num', f)) {
        var n = document.createElement('span');
        n.className = 's-num';
        n.textContent = String(j + 1).padStart(2, '0') + ' / ' + String(deck.slides.length).padStart(2, '0');
        f.appendChild(n);
      }
    });

    window.addEventListener('resize', fit);
    document.addEventListener('keydown', keys);
    fit();
    buildProgress();

    $$('[data-deck-action]').forEach(function (b) {
      var a = b.getAttribute('data-deck-action');
      b.addEventListener('click', function () {
        if (a === 'next') { stop(); next(); }
        if (a === 'prev') { stop(); prev(); }
        if (a === 'play') { toggle(); }
        if (a === 'overview') { toggleOverview(); }
        if (a === 'presenter') { openPresenter(); }
        if (a === 'full') { toggleFull(); }
      });
    });

    // Índice: clic en una slide o capítulo navega; en el fondo o en ✕ cierra
    var ovEl = $('.deck-overview');
    if (ovEl) {
      ovEl.addEventListener('click', function (e) {
        if (deck.introOpen) { closeOverview(); return; }
        var go = e.target.closest('[data-go]');
        if (go) { closeOverview(); stop(); show(parseInt(go.getAttribute('data-go'), 10)); return; }
        if (e.target.closest('[data-ov="close"]') || e.target === ovEl || e.target.classList.contains('ov-journey')) closeOverview();
      });
    }

    // Clic y rueda sobre el escenario (no en el modo público, que sólo obedece)
    if (!deck.isAudience) {
      var vp = $('.deck-viewport');
      if (vp) {
        vp.addEventListener('click', function (e) {
          // Los widgets interactivos (comparador, terminal, inputs) se quedan el clic
          if (e.target.closest('.deck-controls, .deck-overview, a, button, input, .compare, .termplay, [data-no-advance]')) return;
          stop(); next();
        });
        var wheelLock = 0;
        vp.addEventListener('wheel', function (e) {
          var now = Date.now();
          if (now - wheelLock < 420) return;
          wheelLock = now; stop();
          e.deltaY > 0 ? next() : prev();
        }, { passive: true });
      }
    }

    // A partir de aquí el movimiento es seguro: si algo hubiera fallado antes,
    // el CSS habría dejado el deck completo y legible.
    document.documentElement.classList.add('motion-ready');

    var start = parseInt(q.get('slide') || '1', 10) - 1;
    show(isNaN(start) ? 0 : start, { step: q.get('step') != null ? parseInt(q.get('step'), 10) : 0, init: true });

    // El chequeo necesita las fuentes cargadas para medir de verdad
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { setTimeout(check, 60); });
    else setTimeout(check, 400);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  /* ------------------------------------------------- 10 · control de desborde
     El error más caro de un deck es descubrir en la sala que una tabla se
     cortaba. Las slides usan visibility:hidden, no display:none, así que el
     layout de todas está calculado y se pueden medir sin mostrarlas. */
  function check() {
    var bad = [];
    deck.slides.forEach(function (sl, j) {
      var t = (sl.getAttribute('data-title') || 'slide ' + (j + 1)).trim();

      // Conflictos de pseudo-elemento: un elemento sólo tiene un ::before y un
      // ::after. Si dos efectos se pelean por el mismo, uno pisa al otro y el
      // resultado es una capa opaca que no se retira.
      if (sl.classList.contains('cover') && sl.getAttribute('data-transition') === 'curtain') {
        bad.push({ slide: j + 1, titulo: t,
                   problema: 'transición "curtain" no vale en una portada: su retícula ya usa ::after',
                   sobra: 'usar depth o fade' });
      }
      if (sl.classList.contains('cover') && sl.getAttribute('data-bg') &&
          sl.getAttribute('data-bg') !== 'net') {
        bad.push({ slide: j + 1, titulo: t,
                   problema: 'data-bg="' + sl.getAttribute('data-bg') + '" choca con la retícula de la portada (::before)',
                   sobra: 'en portada sólo data-bg="net", que usa canvas' });
      }
      // Un [data-scroll] declara que ahí se scrollea a propósito (una tabla larga, un anexo).
      // Sin esto el detector canta el alto entero de la tabla como si fuera un fallo.
      var libre = !!sl.querySelector('[data-scroll]');
      if (!libre && sl.scrollHeight > sl.clientHeight + 2) {
        bad.push({ slide: j + 1, titulo: t, problema: 'desborda en vertical',
                   sobra: sl.scrollHeight - sl.clientHeight + ' px' });
      }
      if (sl.scrollWidth > sl.clientWidth + 2) {
        bad.push({ slide: j + 1, titulo: t, problema: 'desborda en horizontal',
                   sobra: sl.scrollWidth - sl.clientWidth + ' px' });
      }
      $$('.panel, .code, .console, .lane-b', sl).forEach(function (el) {
        if (el.hasAttribute('data-scroll') || el.closest('[data-scroll]')) return;
        if (el.scrollHeight > el.clientHeight + 2) {
          bad.push({ slide: j + 1, titulo: t,
                     problema: 'contenido cortado en .' + el.className.split(' ')[0],
                     sobra: el.scrollHeight - el.clientHeight + ' px' });
        }
      });
    });
    if (bad.length) {
      console.warn('[Think28 Deck] ' + bad.length + ' aviso(s) de desborde:');
      console.table(bad);
    } else {
      console.log('[Think28 Deck] ' + deck.slides.length + ' slides, ningún desborde.');
    }
    return bad;
  }

  window.FundanetDeck = {
    go: function (n) { stop(); show(n - 1); },
    next: next, prev: prev, play: play, stop: stop,
    presenter: openPresenter, overview: toggleOverview,
    intro: function () { openOverview({ intro: true }); },
    chapters: function () { return chapters().list.map(function (c) { return { nombre: c.name, slides: c.slides.map(function (j) { return j + 1; }), segundos: c.seconds }; }); },
    check: check,
    state: function () { return { slide: deck.i + 1, step: deck.step, of: deck.slides.length }; }
  };
})();
