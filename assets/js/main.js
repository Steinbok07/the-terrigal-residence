/* The Terrigal Residence — site behaviour. Content settings live in site-config.js. */
(function () {
  'use strict';

  var cfg = window.SITE_CONFIG || {};
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    for (var k in attrs || {}) node.setAttribute(k, attrs[k]);
    if (text != null) node.textContent = text;
    return node;
  }

  /* ---------- Specifications ---------- */
  var specs = document.getElementById('specs');
  if (specs && cfg.specs) {
    specs.textContent = ''; // replace the written-out copy in index.html
    var notes = [];
    cfg.specs.forEach(function (s) {
      var row = el('div');
      var dt = el('dt', null, s.label);
      var dd = el('dd', null, s.value);
      if (!/^\d+$/.test(s.value)) dd.className = 'is-text';
      if (s.note) {
        notes.push(s.note);
        dd.appendChild(el('sup', { 'aria-hidden': 'true' }, '*'));
      }
      row.appendChild(dt);
      row.appendChild(dd);
      specs.appendChild(row);
    });
    if (notes.length) document.getElementById('specs-note').textContent = '* ' + notes.join(' · ');
  }

  /* ---------- Floor plans ---------- */
  var fpCfg = cfg.floorPlans;
  var fp = document.getElementById('fp');
  if (fp && fpCfg && fpCfg.levels) {
    var list = document.getElementById('fp-list');
    var stage = document.getElementById('fp-stage');
    var canvas = document.getElementById('fp-canvas');
    var hint = document.getElementById('fp-hint');
    var nameEl = document.getElementById('fp-name');
    var rlEl = document.getElementById('fp-rl');
    var roomsEl = document.getElementById('fp-rooms');
    var entries = fpCfg.levels.slice();
    if (fpCfg.section) entries.push(fpCfg.section);
    var svgCache = {};
    var current = null;
    var z = { s: 1, x: 0, y: 0 };
    var MAX = 6;

    entries.forEach(function (lv) {
      var li = el('li', { 'class': lv === fpCfg.section ? 'fp__item fp__item--drawing' : 'fp__item' });
      var b = el('button', { type: 'button', 'data-level': lv.id, 'aria-pressed': 'false' });
      b.appendChild(el('span', { 'class': 'fp__item-name' }, lv.name));
      b.appendChild(el('span', { 'class': 'fp__item-rl' }, lv.rl ? 'RL ' + lv.rl : 'Vertical Arrangement'));
      b.addEventListener('click', function () { show(lv.id); });
      li.appendChild(b);
      list.appendChild(li);
    });

    function apply() {
      canvas.style.transform = 'translate(' + z.x + 'px,' + z.y + 'px) scale(' + z.s + ')';
      stage.classList.toggle('is-zoomed', z.s > 1.001);
    }
    function clamp() {
      var w = stage.clientWidth, h = stage.clientHeight;
      z.x = Math.min(0, Math.max(w - w * z.s, z.x));
      z.y = Math.min(0, Math.max(h - h * z.s, z.y));
    }
    function zoomAt(ns, cx, cy) {
      ns = Math.max(1, Math.min(MAX, ns));
      if (cx == null) { cx = stage.clientWidth / 2; cy = stage.clientHeight / 2; }
      z.x = cx - (cx - z.x) * (ns / z.s);
      z.y = cy - (cy - z.y) * (ns / z.s);
      z.s = ns; clamp(); apply();
      if (hint) hint.hidden = true;
    }
    function reset() { z = { s: 1, x: 0, y: 0 }; apply(); }

    function show(id) {
      var lv = entries.filter(function (e) { return e.id === id; })[0] || entries[0];
      current = lv;
      list.querySelectorAll('button').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-level') === lv.id));
      });
      nameEl.textContent = lv === fpCfg.section ? 'Architectural Section' : lv.name;
      rlEl.textContent = lv.rl ? 'Floor level · RL ' + lv.rl : 'Through the residence · levels in metres';
      roomsEl.textContent = lv.rooms ? lv.rooms.join('  ·  ')
        : 'How the floor levels step up the site, with the heights noted on the architect’s drawing.';
      stage.classList.toggle('is-wide', lv === fpCfg.section);
      reset();
      if (svgCache[lv.id]) { canvas.innerHTML = svgCache[lv.id]; return; }
      canvas.innerHTML = '<p class="fp__loading">Loading plan…</p>';
      function load(tries) {
        return fetch(lv.svg).then(function (r) { if (!r.ok) throw r; return r.text(); }).catch(function (err) {
          if (tries > 1) return new Promise(function (res) { setTimeout(res, 600); }).then(function () { return load(tries - 1); });
          throw err;
        });
      }
      load(3).then(function (t) {
        svgCache[lv.id] = t;
        if (current === lv) canvas.innerHTML = t;
      }).catch(function () {
        if (current !== lv) return;
        canvas.innerHTML = '';
        var p = el('p', { 'class': 'fp__loading' }, 'This plan could not be displayed. Please reload the page.');
        canvas.appendChild(p);
      });
    }

    // toolbar
    fp.addEventListener('click', function (e) {
      var t = e.target.closest('[data-fp]');
      if (!t) return;
      var a = t.getAttribute('data-fp');
      if (a === 'in') zoomAt(z.s * 1.5);
      else if (a === 'out') zoomAt(z.s / 1.5);
      else if (a === 'reset') reset();
      else if (a === 'full') setFull(!fp.classList.contains('is-full'));
    });
    function setFull(on) {
      fp.classList.toggle('is-full', on);
      document.body.style.overflow = on ? 'hidden' : '';
      var ft = fp.querySelector('.fp__tool[data-fp="full"]');
      ft.textContent = on ? 'Exit full screen' : 'Full screen';
      ft.setAttribute('aria-label', on ? 'Exit full screen' : 'View full screen');
      requestAnimationFrame(function () { reset(); stage.focus({ preventScroll: true }); });
    }

    // wheel: zoom in full screen, or with Ctrl / trackpad pinch inline
    stage.addEventListener('wheel', function (e) {
      if (!fp.classList.contains('is-full') && !e.ctrlKey) return;
      e.preventDefault();
      var r = stage.getBoundingClientRect();
      zoomAt(z.s * Math.exp(-e.deltaY * 0.0022), e.clientX - r.left, e.clientY - r.top);
    }, { passive: false });

    // drag to pan, two-finger pinch to zoom
    var pts = {}, last = null, pinch = null;
    stage.addEventListener('pointerdown', function (e) {
      pts[e.pointerId] = { x: e.clientX, y: e.clientY };
      var ids = Object.keys(pts);
      if (ids.length === 2) {
        var a = pts[ids[0]], b = pts[ids[1]];
        pinch = { d: Math.hypot(a.x - b.x, a.y - b.y) || 1, s: z.s };
        last = null;
      } else if (z.s > 1) {
        last = { x: e.clientX, y: e.clientY };
        try { stage.setPointerCapture(e.pointerId); } catch (err) { /* pointer already released */ }
      }
    });
    stage.addEventListener('pointermove', function (e) {
      if (!pts[e.pointerId]) return;
      pts[e.pointerId] = { x: e.clientX, y: e.clientY };
      var ids = Object.keys(pts);
      if (pinch && ids.length === 2) {
        var a = pts[ids[0]], b = pts[ids[1]], r = stage.getBoundingClientRect();
        zoomAt(pinch.s * Math.hypot(a.x - b.x, a.y - b.y) / pinch.d, (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top);
      } else if (last) {
        z.x += e.clientX - last.x; z.y += e.clientY - last.y;
        last = { x: e.clientX, y: e.clientY }; clamp(); apply();
      }
    });
    function up(e) {
      delete pts[e.pointerId];
      if (Object.keys(pts).length < 2) pinch = null;
      if (!Object.keys(pts).length) last = null;
    }
    stage.addEventListener('pointerup', up);
    stage.addEventListener('pointercancel', up);
    stage.addEventListener('dblclick', function (e) {
      var r = stage.getBoundingClientRect();
      if (z.s > 1.001) reset(); else zoomAt(2.5, e.clientX - r.left, e.clientY - r.top);
    });

    // keyboard: + / - / 0 and arrow keys on the plan; Escape leaves full screen
    stage.addEventListener('keydown', function (e) {
      var k = e.key, step = 60;
      if (k === '+' || k === '=') zoomAt(z.s * 1.5);
      else if (k === '-' || k === '_') zoomAt(z.s / 1.5);
      else if (k === '0') reset();
      else if (z.s > 1 && /^Arrow/.test(k)) {
        z.x += k === 'ArrowLeft' ? step : k === 'ArrowRight' ? -step : 0;
        z.y += k === 'ArrowUp' ? step : k === 'ArrowDown' ? -step : 0;
        clamp(); apply();
      } else return;
      e.preventDefault();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && fp.classList.contains('is-full')) setFull(false);
    });
    window.addEventListener('resize', function () { clamp(); apply(); });

    show(fpCfg.defaultLevel || entries[0].id);
  }

  /* ---------- Enquiry actions ---------- */
  var actions = document.getElementById('actions');
  if (actions) {
    var c = cfg.contact || {};
    var inspectHref = c.inspectionUrl ||
      (c.email ? 'mailto:' + c.email + '?subject=' + encodeURIComponent('Private inspection — The Terrigal Residence') : '');

    function action(label, href, opts) {
      opts = opts || {};
      if (!href) {
        var p = el('span', { 'class': 'btn btn--pending', role: 'note' });
        p.appendChild(el('span', null, label));
        p.appendChild(el('span', { 'class': 'btn__note' }, opts.pending));
        return p;
      }
      var a = el('a', { 'class': 'btn' + (opts.primary ? ' btn--primary' : ''), href: href }, label);
      if (opts.download) a.setAttribute('download', '');
      if (/^https?:/.test(href)) { a.target = '_blank'; a.rel = 'noopener'; }
      return a;
    }

    actions.appendChild(action('Request a Private Inspection', inspectHref,
      { primary: true, pending: 'Placeholder — contact details to be supplied' }));
    actions.appendChild(action('View Floor Plans', '#plans'));
    actions.appendChild(action('Download Property Brochure', cfg.brochurePdf,
      { download: true, pending: 'Placeholder — brochure to be supplied' }));

    var contact = document.getElementById('contact');
    var bits = [];
    if (c.name) bits.push(document.createTextNode(c.name));
    if (c.phone) bits.push(el('a', { href: 'tel:' + c.phone.replace(/[^\d+]/g, '') }, c.phone));
    if (c.email) bits.push(el('a', { href: 'mailto:' + c.email }, c.email));
    bits.forEach(function (b, i) {
      if (i) contact.appendChild(document.createTextNode('  ·  '));
      contact.appendChild(b);
    });
  }

  /* ---------- Full-screen viewer ---------- */
  var viewer = (function () {
    var root = document.getElementById('viewer');
    var img = document.getElementById('viewer-img');
    var count = document.getElementById('viewer-count');
    var caption = document.getElementById('viewer-caption');
    var items = [], index = 0, opener = null;

    function show(i) {
      index = (i + items.length) % items.length;
      var it = items[index];
      img.classList.add('is-loading');
      img.onload = function () { img.classList.remove('is-loading'); };
      img.removeAttribute('srcset');
      if (it.srcset) { img.srcset = it.srcset; img.sizes = '100vw'; }
      img.src = it.src;
      img.alt = it.alt || '';
      if (img.complete) img.classList.remove('is-loading');
      caption.textContent = it.caption || '';
      count.textContent = items.length > 1 ? pad(index + 1) + ' / ' + pad(items.length) : '';
      root.querySelectorAll('.viewer__nav').forEach(function (b) { b.hidden = items.length < 2; });
      // warm the neighbours
      [index + 1, index - 1].forEach(function (n) {
        var nb = items[(n + items.length) % items.length];
        if (nb) { var pre = new Image(); if (nb.srcset) { pre.sizes = '100vw'; pre.srcset = nb.srcset; } pre.src = nb.src; }
      });
    }
    function pad(n) { return n < 10 ? '0' + n : '' + n; }

    function open(list, i, from) {
      items = list; opener = from || document.activeElement;
      root.hidden = false;
      document.body.style.overflow = 'hidden';
      show(i);
      root.querySelector('.viewer__close').focus();
    }
    function close() {
      root.hidden = true;
      document.body.style.overflow = '';
      img.removeAttribute('src');
      if (opener && opener.focus) opener.focus({ preventScroll: true });
    }

    root.addEventListener('click', function (e) {
      var act = e.target.closest('[data-viewer]');
      if (act) { var a = act.getAttribute('data-viewer'); if (a === 'close') close(); else show(index + (a === 'next' ? 1 : -1)); return; }
      if (e.target === root || e.target.classList.contains('viewer__stage')) close();
    });
    document.addEventListener('keydown', function (e) {
      if (root.hidden) return;
      if (e.key === 'Escape') { e.preventDefault(); close(); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); show(index + 1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); show(index - 1); }
      else if (e.key === 'Tab') {
        var f = Array.prototype.filter.call(root.querySelectorAll('button'), function (b) { return !b.hidden; });
        var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    // swipe
    var x0 = null;
    img.addEventListener('pointerdown', function (e) { x0 = e.clientX; });
    img.addEventListener('pointerup', function (e) {
      if (x0 === null) return;
      var dx = e.clientX - x0; x0 = null;
      if (Math.abs(dx) > 40) show(index + (dx < 0 ? 1 : -1));
    });

    return { open: open };
  })();

  // Photographs: every [data-plate] button, in page order
  var plateBtns = Array.prototype.slice.call(document.querySelectorAll('[data-plate]'));
  var photoItems = plateBtns.map(function (b) {
    var im = b.querySelector('img');
    var fc = b.closest('figure').querySelector('figcaption');
    var no = fc && fc.querySelector('.plate__no');
    var text = fc ? fc.textContent.replace(no ? no.textContent : '', '').trim() : '';
    var srcs = im.getAttribute('srcset').split(',');
    return {
      src: srcs[srcs.length - 1].trim().split(' ')[0],
      srcset: im.getAttribute('srcset'),
      alt: im.alt,
      caption: text
    };
  });
  plateBtns.forEach(function (b, i) {
    b.setAttribute('aria-label', 'Enlarge photograph ' + (i + 1) + ' of ' + plateBtns.length + ': ' + photoItems[i].caption);
    b.addEventListener('click', function () { viewer.open(photoItems, i, b); });
  });
  document.querySelectorAll('[data-goto]').forEach(function (b) {
    b.addEventListener('click', function () {
      var i = parseInt(b.getAttribute('data-goto'), 10) - 1;
      viewer.open(photoItems, i, b);
    });
  });

  /* ---------- Mobile menu ---------- */
  var toggle = document.querySelector('.menu-toggle');
  var menu = document.getElementById('menu');
  function setMenu(open) {
    menu.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = open ? 'Close' : 'Menu';
    document.body.style.overflow = open ? 'hidden' : '';
  }
  toggle.addEventListener('click', function () { setMenu(menu.hidden); });
  menu.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (!a) return;
    e.preventDefault();
    setMenu(false);
    var target = document.querySelector(a.getAttribute('href'));
    requestAnimationFrame(function () {
      if (target) target.scrollIntoView({ behavior: reduceMotion.matches ? 'auto' : 'smooth' });
      history.replaceState(null, '', a.getAttribute('href'));
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !menu.hidden) { setMenu(false); toggle.focus(); }
  });

  /* ---------- Header state & active section ---------- */
  var header = document.querySelector('.site-header');
  function onScroll() { header.classList.toggle('is-scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if ('IntersectionObserver' in window) {
    var links = {};
    document.querySelectorAll('.nav__list a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = links[en.target.id];
        if (a && en.isIntersecting) {
          Object.keys(links).forEach(function (k) { links[k].classList.remove('is-active'); });
          a.classList.add('is-active');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    Object.keys(links).forEach(function (id) { var s = document.getElementById(id); if (s) spy.observe(s); });

    /* Reveal on scroll */
    var reveals = document.querySelectorAll('.reveal');
    if (reduceMotion.matches) {
      reveals.forEach(function (r) { r.classList.add('is-in'); });
    } else {
      var ro = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add('is-in'); ro.unobserve(en.target); }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.01 });
      reveals.forEach(function (r) { ro.observe(r); });
    }
  } else {
    document.querySelectorAll('.reveal').forEach(function (r) { r.classList.add('is-in'); });
  }
})();
