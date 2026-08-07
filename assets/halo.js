/* ===========================================================================
   HALO · shared behaviour
   No dependencies. Every module is a no-op when its markup is absent, so the
   same file ships on every page.
   =========================================================================== */
(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var fine    = window.matchMedia('(pointer: fine)');
  var clamp   = function (v, a, b) { return v < a ? a : v > b ? b : v; };

  /* --------------------------------------------------------------- loader --
     The page underneath is already painted. This is an overlay we remove, and
     it is capped hard so a stalled font or image can never hold the site. */
  (function () {
    var el = $('#loader'), msg = $('#loaderMsg');
    if (!el) return;
    var lines = ['Preparing appreciation', 'Building your workspace', 'Almost there'];
    var i = 0, timer = null, done = false;

    if (!reduced.matches) {
      timer = setInterval(function () {
        i = (i + 1) % lines.length;
        msg.style.opacity = '0';
        setTimeout(function () { msg.textContent = lines[i]; msg.style.opacity = '1'; }, 260);
      }, 780);
    }
    function dismiss() {
      if (done) return;
      done = true;
      clearInterval(timer);
      el.classList.add('done');
      setTimeout(function () { el.hidden = true; }, 900);
      document.documentElement.classList.add('ready');
    }
    var floor = reduced.matches ? 0 : 1400;
    var t0 = performance.now();
    function whenLoaded() { setTimeout(dismiss, Math.max(0, floor - (performance.now() - t0))); }
    if (document.readyState === 'complete') whenLoaded();
    else window.addEventListener('load', whenLoaded);
    setTimeout(dismiss, 2400);

    /* Only the first visit in a session gets the full loader. */
    try {
      if (sessionStorage.getItem('halo-seen')) { floor = 0; dismiss(); }
      else sessionStorage.setItem('halo-seen', '1');
    } catch (e) { /* private mode: keep the loader */ }
  })();

  /* ------------------------------------------------------------------ nav -- */
  (function () {
    var nav = $('#nav');
    if (!nav) return;
    var onScroll = function () { nav.classList.toggle('stuck', window.scrollY > 24); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    /* Mega menus: click always works, hover is an enhancement on fine pointers. */
    var groups = $$('[data-mega]').map(function (btn) {
      return { btn: btn, panel: btn.nextElementSibling, li: btn.closest('li') };
    });
    var openTimer = null, closeTimer = null;

    function setOpen(g, open) {
      g.btn.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('menu-open', groups.some(function (x) {
        return x.btn.getAttribute('aria-expanded') === 'true';
      }));
    }
    function closeAll(except) {
      groups.forEach(function (g) { if (g !== except) setOpen(g, false); });
    }

    groups.forEach(function (g) {
      g.btn.addEventListener('click', function (e) {
        e.preventDefault();
        var open = g.btn.getAttribute('aria-expanded') === 'true';
        closeAll(g);
        setOpen(g, !open);
      });
      if (fine.matches) {
        g.li.addEventListener('pointerenter', function () {
          clearTimeout(closeTimer);
          openTimer = setTimeout(function () { closeAll(g); setOpen(g, true); }, 90);
        });
        g.li.addEventListener('pointerleave', function () {
          clearTimeout(openTimer);
          closeTimer = setTimeout(function () { setOpen(g, false); }, 180);
        });
      }
      g.li.addEventListener('focusout', function (e) {
        if (!g.li.contains(e.relatedTarget)) setOpen(g, false);
      });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      var open = groups.filter(function (g) { return g.btn.getAttribute('aria-expanded') === 'true'; });
      if (open.length) { open.forEach(function (g) { setOpen(g, false); }); open[0].btn.focus(); }
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.nav-links')) closeAll(null);
    });

    /* Mobile sheet */
    var toggle = $('#navToggle'), sheet = $('#sheet');
    if (!toggle || !sheet) return;
    $$('a', sheet).forEach(function (a, i) { a.style.setProperty('--i', i); });

    function setSheet(open) {
      toggle.setAttribute('aria-expanded', String(open));
      sheet.classList.toggle('open', open);
      nav.classList.toggle('menu-open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    }
    toggle.addEventListener('click', function () {
      setSheet(toggle.getAttribute('aria-expanded') !== 'true');
    });
    sheet.addEventListener('click', function (e) { if (e.target.closest('a')) setSheet(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { setSheet(false); toggle.focus(); }
    });
    window.addEventListener('resize', function () { if (window.innerWidth > 1024) setSheet(false); });
  })();

  /* -------------------------------------------------------------- reveals -- */
  (function () {
    var targets = $$('[data-rise], [data-mask]');
    if (!targets.length) return;
    if (!('IntersectionObserver' in window) || reduced.matches) {
      targets.forEach(function (el) { el.classList.add('in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });
    targets.forEach(function (el) { io.observe(el); });
    setTimeout(function () { targets.forEach(function (el) { el.classList.add('in'); }); }, 4000);
  })();

  /* -------------------------------------------------------- hero parallax -- */
  (function () {
    var hero = $('.hero');
    if (!hero || reduced.matches || !fine.matches) return;
    var tx = 0, ty = 0, queued = false;
    hero.addEventListener('pointermove', function (e) {
      var r = hero.getBoundingClientRect();
      tx = ((e.clientX - r.left) / r.width - 0.5) * 2;
      ty = ((e.clientY - r.top) / r.height - 0.5) * 2;
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () {
        hero.style.setProperty('--mx', tx.toFixed(3));
        hero.style.setProperty('--my', ty.toFixed(3));
        queued = false;
      });
    });
    hero.addEventListener('pointerleave', function () {
      hero.style.setProperty('--mx', 0); hero.style.setProperty('--my', 0);
    });
  })();

  /* ------------------------------------------------------------ spotlight --
     One delegated listener for every .spot on the page instead of N. */
  (function () {
    var spots = $$('.spot');
    if (!spots.length || reduced.matches || !fine.matches) return;
    var queued = false, pending = [];
    document.addEventListener('pointermove', function (e) {
      var el = e.target.closest('.spot');
      if (!el) return;
      pending.push([el, e.clientX, e.clientY]);
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () {
        pending.forEach(function (p) {
          var r = p[0].getBoundingClientRect();
          p[0].style.setProperty('--sx', ((p[1] - r.left) / r.width * 100).toFixed(1) + '%');
          p[0].style.setProperty('--sy', ((p[2] - r.top) / r.height * 100).toFixed(1) + '%');
        });
        pending = []; queued = false;
      });
    }, { passive: true });
  })();

  /* --------------------------------------------------------------- magnet --
     Primary CTAs only. 6px of pull, which reads as weight rather than as a
     trick; anything larger and the button feels loose. */
  (function () {
    if (reduced.matches || !fine.matches) return;
    $$('[data-magnet]').forEach(function (el) {
      var raf = null;
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
        var dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
        if (raf) return;
        raf = requestAnimationFrame(function () {
          el.style.translate = (dx * 6).toFixed(2) + 'px ' + (dy * 4).toFixed(2) + 'px';
          raf = null;
        });
      });
      el.addEventListener('pointerleave', function () { el.style.translate = ''; });
    });
  })();

  /* ----------------------------------------------- scroll-linked sections -- */
  (function () {
    if (reduced.matches) return;
    var forget  = $('#forget');
    var lines   = forget ? $$('li', forget) : [];
    var sticky  = $('#railSticky');
    var rail    = $('#rail');
    var railBar = $('#railBar');
    if (!lines.length && !sticky) return;

    var overflow = 0, active = 0, running = false;

    function measure() {
      if (!rail) return;
      var last = rail.lastElementChild;
      if (!last) { overflow = 0; return; }
      var gut = parseFloat(getComputedStyle(rail).paddingLeft) || 0;
      overflow = Math.max(0, last.offsetLeft + last.offsetWidth + gut - window.innerWidth);
    }

    function frame() {
      var vh = window.innerHeight;
      if (lines.length) {
        var focal = vh * 0.56;
        for (var i = 0; i < lines.length; i++) {
          var r = lines[i].getBoundingClientRect();
          var d = (focal - (r.top + r.height / 2)) / (vh * 0.42);
          lines[i].style.setProperty('--lit', clamp(1 - Math.max(0, d) * 0.92, 0.12, 1).toFixed(3));
        }
      }
      if (sticky && rail) {
        var s = sticky.getBoundingClientRect();
        var travel = s.height - vh;
        var p = travel > 0 ? clamp(-s.top / travel, 0, 1) : 0;
        rail.style.setProperty('--rail', (p * overflow).toFixed(1));
        if (railBar) railBar.style.setProperty('--railpct', p.toFixed(4));
      }
      if (active > 0) requestAnimationFrame(frame); else running = false;
    }
    function start() { if (!running) { running = true; requestAnimationFrame(frame); } }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { active += e.isIntersecting ? 1 : -1; });
      active = Math.max(0, active);
      if (active > 0) start();
    }, { rootMargin: '20% 0px 20% 0px' });
    [forget, sticky].forEach(function (el) { if (el) io.observe(el); });

    measure();
    window.addEventListener('resize', function () { measure(); start(); });
    window.addEventListener('load', measure);
  })();

  /* ----------------------------------------------------------- card deck -- */
  (function () {
    var deck = $('#deck');
    if (!deck) return;
    var items = $$('.deck-item', deck);
    var dots  = $$('.deck-dot', document.querySelector('#deckCtl') || document);
    var top = 0;

    function render() {
      items.forEach(function (el, i) {
        var rel = (i - top + items.length) % items.length;
        el.style.setProperty('--i', rel);
        el.setAttribute('aria-hidden', rel === 0 ? 'false' : 'true');
        el.tabIndex = rel === 0 ? 0 : -1;
      });
      dots.forEach(function (d, i) { d.setAttribute('aria-current', String(i === top)); });
    }
    function advance(n) { top = (top + n + items.length) % items.length; render(); }

    deck.addEventListener('click', function (e) {
      if (e.target.closest('.deck-item')) advance(1);
    });
    deck.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); advance(1); }
      if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   { e.preventDefault(); advance(-1); }
    });
    dots.forEach(function (d, i) {
      d.addEventListener('click', function () { top = i; render(); });
    });
    render();
  })();

  /* ------------------------------------------------------------- composer -- */
  (function () {
    var ta = $('#msg');
    if (!ta) return;
    var pvMsg = $('#pvMsg'), pvKick = $('#pvKicker'), face = $('#face');
    var count = $('#count'), preview = $('#preview'), sendBtn = $('#send');
    var LIMIT = 280;

    function group(root, onPick) {
      if (!root) return;
      var btns = $$('button', root);
      btns.forEach(function (b) {
        b.addEventListener('click', function () {
          btns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
          onPick(b);
        });
      });
    }
    function sync() {
      var v = ta.value.trim();
      pvMsg.textContent = v || 'Say what they actually did, and what it meant.';
      pvMsg.style.opacity = v ? '1' : '.45';
      count.textContent = ta.value.length + ' / ' + LIMIT;
    }
    ta.addEventListener('input', sync); sync();

    group($('#moments'), function (b) { pvKick.textContent = b.dataset.kicker; });
    group($('#swatches'), function (b) {
      face.style.setProperty('--face', getComputedStyle(b).getPropertyValue('--sw'));
    });

    $$('.sugg').forEach(function (s) {
      s.addEventListener('click', function () { ta.value = s.textContent.trim(); sync(); ta.focus(); });
    });

    var resetT = null;
    if (sendBtn) sendBtn.addEventListener('click', function () {
      if (!ta.value.trim()) { ta.focus(); return; }
      preview.classList.add('sent');
      sendBtn.disabled = true;
      clearTimeout(resetT);
      resetT = setTimeout(function () { preview.classList.remove('sent'); sendBtn.disabled = false; }, 2800);
    });
  })();

  /* ----------------------------------------------------------------- tone -- */
  (function () {
    var out = $('#toneOut');
    if (!out) return;
    var variants = {
      'As written':  'You stayed late to walk me through the migration script. I would still be stuck on it. Thank you.',
      'Warmer':      'You gave up your evening to sit with me through that migration script, and it completely unblocked me. I really appreciate it.',
      'Shorter':     'You stayed late to unblock me on the migration script. Thank you.',
      'More formal': 'Thank you for staying late to talk me through the migration script. Your help resolved a blocker I could not have cleared alone.',
      'In Dutch':    'Je bent laat gebleven om het migratiescript met me door te nemen. Zonder jou zat ik er nu nog vast. Dank je wel.'
    };
    var btns = $$('.tone-btn');
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        btns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
        var text = variants[b.textContent.trim()] || variants['As written'];
        out.lang = b.textContent.trim() === 'In Dutch' ? 'nl' : 'en';
        if (reduced.matches) { out.textContent = text; return; }
        out.classList.add('morph');
        setTimeout(function () { out.textContent = text; out.classList.remove('morph'); }, 340);
      });
    });
  })();

  /* -------------------------------------------------------------- pricing -- */
  (function () {
    var root = $('#billing');
    if (!root) return;
    var btns = $$('button', root);
    var amounts = $$('[data-price-monthly]');
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        btns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
        var key = b.dataset.period === 'annual' ? 'priceAnnual' : 'priceMonthly';
        amounts.forEach(function (a) { a.textContent = a.dataset[key]; });
      });
    });
  })();

  /* ------------------------------------------------------ template filter -- */
  (function () {
    var bar = $('#filters');
    if (!bar) return;
    var btns = $$('button', bar);
    var items = $$('[data-cat]');
    var live = $('#filterCount');
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        btns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
        var f = b.dataset.filter, shown = 0;
        items.forEach(function (el) {
          var ok = f === 'all' || el.dataset.cat.split(' ').indexOf(f) > -1;
          el.hidden = !ok;
          if (ok) shown++;
        });
        if (live) live.textContent = shown + (shown === 1 ? ' template' : ' templates');
      });
    });
  })();

  /* --------------------------------------------------- specular button --
     Tracks the pointer so the highlight sits under it. One delegated
     listener; the two gradient layers are CSS. */
  (function () {
    if (reduced.matches || !fine.matches) return;
    var q = [], queued = false;
    document.addEventListener('pointermove', function (e) {
      var el = e.target.closest('.btn--spec');
      if (!el) return;
      q.push([el, e.clientX, e.clientY]);
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () {
        q.forEach(function (p) {
          var r = p[0].getBoundingClientRect();
          p[0].style.setProperty('--sx', ((p[1] - r.left) / r.width * 100).toFixed(1) + '%');
          p[0].style.setProperty('--sy', ((p[2] - r.top) / r.height * 100).toFixed(1) + '%');
        });
        q = []; queued = false;
      });
    }, { passive: true });
  })();

  /* ------------------------------------------------------------ carousel --
     Real overflow scrolling, so trackpad, touch and keyboard already work.
     JS only mirrors the scroll position into the dots and the arrows. */
  $$('[data-carousel]').forEach(function (root) {
    var track = $('.carousel-track', root);
    var prev  = $('[data-car-prev]', root);
    var next  = $('[data-car-next]', root);
    var dots  = $('.carousel-dots', root);
    if (!track) return;
    var items = $$(':scope > *', track);
    if (!items.length) return;

    if (dots) {
      items.forEach(function (_, i) {
        var b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('aria-label', 'Go to item ' + (i + 1));
        b.addEventListener('click', function () { scrollTo(i); });
        dots.appendChild(b);
      });
    }

    function current() {
      var mid = track.scrollLeft + track.clientWidth / 2, best = 0, dist = Infinity;
      items.forEach(function (el, i) {
        var c = el.offsetLeft + el.offsetWidth / 2;
        var d = Math.abs(c - mid);
        if (d < dist) { dist = d; best = i; }
      });
      return best;
    }
    function scrollTo(i) {
      var el = items[clamp(i, 0, items.length - 1)];
      track.scrollTo({ left: el.offsetLeft - (track.clientWidth - el.offsetWidth) / 2,
                       behavior: reduced.matches ? 'auto' : 'smooth' });
    }
    function sync() {
      var i = current();
      if (dots) $$('button', dots).forEach(function (d, n) { d.setAttribute('aria-current', String(n === i)); });
      if (prev) prev.disabled = track.scrollLeft <= 2;
      if (next) next.disabled = track.scrollLeft >= track.scrollWidth - track.clientWidth - 2;
    }
    var t = null;
    track.addEventListener('scroll', function () {
      clearTimeout(t); t = setTimeout(sync, 60);
    }, { passive: true });
    if (prev) prev.addEventListener('click', function () { scrollTo(current() - 1); });
    if (next) next.addEventListener('click', function () { scrollTo(current() + 1); });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); scrollTo(current() + 1); }
      if (e.key === 'ArrowLeft')  { e.preventDefault(); scrollTo(current() - 1); }
    });
    window.addEventListener('resize', sync);
    sync();
  });

  /* ----------------------------------------------------------- driftwall --
     Each column is duplicated once so the CSS loop can translate by exactly
     -50% and seam invisibly. Only the pointer parallax runs in JS. */
  $$('[data-wall]').forEach(function (wall) {
    $$('.wall-col', wall).forEach(function (col, i) {
      var originals = Array.prototype.slice.call(col.children);
      originals.forEach(function (node) {
        var copy = node.cloneNode(true);
        copy.setAttribute('aria-hidden', 'true');
        $$('button, a, input', copy).forEach(function (f) { f.tabIndex = -1; });
        col.appendChild(copy);
      });
      /* Golden-ratio stagger: no two columns land in phase. */
      col.style.setProperty('--dur', (46 + ((i * 0.6180339887) % 1) * 26).toFixed(1) + 's');
      col.style.setProperty('--delay', (-(i * 3.7)).toFixed(1) + 's');
    });

    if (reduced.matches || !fine.matches) return;
    var plane = $('.wall-plane', wall), queued = false, px = 0, py = 0;
    if (!plane) return;
    wall.addEventListener('pointermove', function (e) {
      var r = wall.getBoundingClientRect();
      px = ((e.clientX - r.left) / r.width - 0.5) * 2;
      py = ((e.clientY - r.top) / r.height - 0.5) * 2;
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () {
        wall.style.setProperty('--wx', px.toFixed(3));
        wall.style.setProperty('--wy', py.toFixed(3));
        queued = false;
      });
    });
    wall.addEventListener('pointerleave', function () {
      wall.style.setProperty('--wx', 0); wall.style.setProperty('--wy', 0);
    });
  });

  /* --------------------------------------------------------- line sidebar --
     Built from the page's own sections, so it can never drift out of sync
     with the content. Scroll-spy drives the active state; pointer proximity
     is the hover feel on top of it. */
  (function () {
    var bar = $('[data-linebar]');
    if (!bar) return;
    var secs = $$('main section[id][data-label]');
    if (secs.length < 3) { bar.remove(); return; }

    var ol = document.createElement('ol');
    var lis = secs.map(function (s, i) {
      var li = document.createElement('li');
      li.innerHTML = '<a href="#' + s.id + '"><span class="tick"></span>'
        + '<span class="num">' + String(i + 1).padStart(2, '0') + '</span>'
        + '<span class="lbl">' + s.dataset.label + '</span></a>';
      ol.appendChild(li);
      return li;
    });
    bar.appendChild(ol);
    bar.setAttribute('aria-label', 'Sections on this page');

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var i = secs.indexOf(e.target);
        lis.forEach(function (li, n) { li.setAttribute('aria-current', String(n === i)); });
        /* The bar sits over alternating registers, so it has to follow. */
        bar.classList.toggle('linebar--on-dark',
          /band--dark|band--void|close|wall/.test(e.target.className));
        bar.style.color = /band--paper|hero--light/.test(e.target.className)
          ? 'var(--on-paper)' : 'var(--on-ink)';
      });
    }, { rootMargin: '-45% 0px -45% 0px' });
    secs.forEach(function (s) { io.observe(s); });

    if (reduced.matches || !fine.matches) return;
    var raf = null;
    document.addEventListener('pointermove', function (e) {
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = null;
        var r = bar.getBoundingClientRect();
        /* Only react while the pointer is anywhere near the left edge. */
        if (e.clientX > r.right + 220) {
          lis.forEach(function (li) { li.style.setProperty('--effect', 0); });
          return;
        }
        lis.forEach(function (li) {
          var b = li.getBoundingClientRect();
          var d = Math.abs(e.clientY - (b.top + b.height / 2));
          var p = clamp(1 - d / 110, 0, 1);
          li.style.setProperty('--effect', (p * p * (3 - 2 * p)).toFixed(3));
        });
      });
    }, { passive: true });
  })();

  /* ----------------------------------------------------- page transitions --
     Chrome and Safari handle this natively via @view-transition. This is the
     fallback for engines that do not: a short fade instead of a hard cut. */
  (function () {
    if (reduced.matches) return;
    if ('startViewTransition' in document && CSS.supports('view-transition-name', 'a')) return;

    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href]');
      if (!a || a.target || a.hasAttribute('download') || a.getAttribute('aria-disabled') === 'true') return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;

      var url;
      try { url = new URL(a.href, location.href); } catch (err) { return; }
      if (url.origin !== location.origin) return;
      if (url.pathname === location.pathname) return;   // in-page anchor

      e.preventDefault();
      document.body.classList.add('leaving');
      var go = function () { location.href = url.href; };
      setTimeout(go, 160);
    });

    /* Restore on back/forward, where the page comes out of bfcache faded. */
    window.addEventListener('pageshow', function () { document.body.classList.remove('leaving'); });
  })();

}());
