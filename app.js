(() => {
  'use strict';
  const root = document.documentElement;
  const $ = (s, p = document) => p.querySelector(s);
  const $$ = (s, p = document) => [...p.querySelectorAll(s)];
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const ease = t => 1 - Math.pow(1 - t, 3);
  const rand = (a, b) => a + Math.random() * (b - a);

  /* ---------- Content from config.js ---------- */
  const C = window.SITE || {};
  $$('[data-bind]').forEach(el => { const v = C[el.dataset.bind]; if (v) el.textContent = v; });
  $$('[data-href]').forEach(el => { if (C[el.dataset.href]) el.href = C[el.dataset.href]; });
  const mail = `mailto:${C.email}`;
  $('#cEmail').href = mail;
  $('#chat').href = mail;
  $('#cTel').href = `tel:${(C.phone || '').replace(/[^+\d]/g, '')}`;

  /* ---------- Page interactions ---------- */
  const filterBtns = $$('.filters button');
  const cards = $$('.card');
  filterBtns.forEach(btn => btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.toggle('is-on', b === btn));
    let shown = 0;
    cards.forEach(card => {
      const hit = btn.dataset.f === 'all' || card.dataset.tags === btn.dataset.f;
      card.hidden = !hit;
      if (hit) shown++;
    });
    $('.count b').textContent = shown;
    $('.empty').hidden = shown > 0;
  }));

  const compare = $('#compare');
  $('input', compare).addEventListener('input', e => compare.style.setProperty('--pos', `${e.target.value}%`));

  /* ---------- Agent build engine ---------- */
  const wantsMotion = root.classList.contains('js');
  const bail = () => { root.classList.remove('js', 'lock'); };
  window.addEventListener('error', bail);

  const canvas = $('#swarm');
  const ctx = canvas.getContext('2d');
  const stage = $('#stage');
  const veil = $('#veil');
  const dock = $('#dock');
  const pill = $('#pill');
  const ui = {
    text: $('#pText'), agents: $('#pAgents'), layers: $('#pLayers'), bar: $('#pBar'),
    main: $('#pMain'), speed: $('#pSpeed'), sound: $('#pSound')
  };
  const scanT = $('#scanT');
  const scanL = $('#scanL');

  const AGENTS = 24;
  const COLORS = ['#f2f1f4', '#5fe3d4', '#f2f1f4', '#ff8fa0', '#b9bcc6', '#7fe9f0', '#8fa2ff', '#f2f1f4'];
  const DUR = { t: 760, b: 620, h: 900, i: 1500, c: 1250, w: 950, ph: 2300 };
  const SCAN_MS = 1900, SCATTER_MS = 340;

  let W = 0, H = 0, DPR = 1;
  const resize = () => {
    W = innerWidth; H = innerHeight; DPR = Math.min(devicePixelRatio || 1, 2);
    canvas.width = W * DPR; canvas.height = H * DPR;
  };
  addEventListener('resize', resize, { passive: true });
  resize();

  const layers = $$('[data-l]').map((el, i) => ({
    el, i, type: el.dataset.l,
    at: el.dataset.at ? +el.dataset.at : null,
    wait: el.dataset.wait || null,
    state: 0, start: 0, dur: 0, ov: null, crew: [], rect: null
  }));
  ui.layers.textContent = `0 / ${layers.length} layers`;

  const agents = Array.from({ length: AGENTS }, (_, i) => ({
    i, x: W / 2, y: H / 2, vx: 0, vy: 0, a: rand(0, 6.28),
    tx: W / 2, ty: H / 2, wx: rand(0, W), wy: rand(0, H), wa: rand(0, 6.28), ws: rand(50, 130),
    color: COLORS[i % COLORS.length], tool: 'arrow', busy: false,
    lead: i % 3 === 2 ? i - 1 : i, ox: rand(-34, 34), oy: rand(-26, 26),
    arc: rand(-.42, .42), rr: rand(-16, 16), bot: i % 6 === 1
  }));

  const S = {
    phase: 'idle', clock: 0, last: 0, phaseAt: 0, layoutAt: 0, doneAt: 0,
    done: 0, rate: 1, paused: false, dismissed: false, muted: true, guides: [], frame: 0, ticks: 0
  };

  /* ---------- Small sound tick, off by default ---------- */
  let audio = null;
  const tick = () => {
    if (S.muted) return;
    audio = audio || new (window.AudioContext || window.webkitAudioContext)();
    const o = audio.createOscillator(), g = audio.createGain();
    o.frequency.value = rand(620, 980); g.gain.value = .012;
    g.gain.exponentialRampToValueAtTime(.0001, audio.currentTime + .05);
    o.connect(g).connect(audio.destination); o.start(); o.stop(audio.currentTime + .06);
  };

  /* ---------- Overlay pieces ---------- */
  const makeBox = (l) => {
    const box = document.createElement('div');
    const small = l.type === 't' || l.type === 'b';
    box.className = `bp${l.type === 'i' || l.type === 'ph' ? ' img' : ''}${l.type === 'c' ? ' red' : ''}${small ? ' tiny' : ''}${l.type === 'w' ? ' quiet' : ''}`;
    box.innerHTML = `<i class="f"></i><s></s><s></s><s></s><s></s>${l.type !== 'w' ? `<span class="tag">agent-${String((l.i % AGENTS) + 1).padStart(2, '0')}</span>` : ''}`;
    stage.append(box);
    l.ov = { box, fill: $('.f', box) };
  };
  const guide = (kind, l, life = 1100) => {
    const el = document.createElement('i');
    el.className = `gl ${kind}`;
    stage.append(el);
    S.guides.push({ el, kind, l, born: S.clock, life });
  };
  const pulseScan = () => {
    [scanT, scanL].forEach(b => { b.classList.remove('go'); void b.offsetWidth; b.classList.add('go'); });
  };

  const freeAgents = (n) => agents.filter(a => !a.busy).sort((p, q) => p.bot - q.bot).slice(0, n);

  const startLayer = (l, backlog) => {
    l.state = 1;
    l.start = S.clock;
    l.dur = DUR[l.type] / (1 + Math.min(backlog, 24) * .07);
    l.el.classList.add('bld');
    l.el.style.setProperty('--p', 0);
    makeBox(l);
    const need = l.type === 'i' || l.type === 'ph' ? 3 : 1;
    l.crew = freeAgents(need);
    l.crew.forEach((a, n) => {
      a.busy = true;
      a.tool = l.type === 't' ? 'ibeam' : (l.type === 'b' || l.type === 'h' || n > 0) ? 'plus' : 'arrow';
      if (a.bot) a.tool = 'bot';
    });
    S.ticks++;
    if (l.at === null && S.ticks % 7 === 0) guide('row', l, 900);
    if (l.at !== null) { guide('h', l, 1400); if (l.i % 2) guide('v', l, 1400); }
  };

  const finishLayer = (l) => {
    if (l.state === 2) return;
    l.state = 2;
    l.el.classList.remove('bld');
    l.el.classList.add('on');
    l.el.style.removeProperty('--p');
    l.el.style.removeProperty('--o');
    l.el.style.removeProperty('--g');
    l.el.style.removeProperty('transform');
    l.el.style.removeProperty('filter');
    if (l.ov) { l.ov.box.remove(); l.ov = null; }
    l.crew.forEach(a => { a.busy = false; a.tool = 'arrow'; a.wx = a.x; a.wy = a.y; });
    l.crew = [];
    S.done++;
    tick();
  };

  const stepLayer = (l, r) => {
    const p = clamp((S.clock - l.start) / l.dur);
    const { box, fill } = l.ov;
    const el = l.el;
    const pad = l.type === 't' ? 4 : 0;
    const x = r.left - pad, y = r.top - pad, w = r.width + pad * 2, h = r.height + pad * 2;
    box.style.transform = `translate(${x}px,${y}px)`;
    box.style.width = `${w}px`;
    box.style.height = `${h}px`;
    let boxA = Math.min(1, p / .08);
    let ax = x, ay = y;

    if (l.type === 't' || l.type === 'b') {
      const rev = ease(clamp((p - .1) / .62));
      el.style.setProperty('--p', rev);
      fill.style.width = `${rev * 100}%`;
      fill.style.opacity = p < .72 ? .75 : (1 - p) / .28 * .75;
      boxA *= p > .84 ? (1 - p) / .16 : 1;
      ax = x + w * rev; ay = y + h * .55;
    } else if (l.type === 'h' || l.type === 'w') {
      const rev = ease(clamp((p - .06) / .6));
      el.style.setProperty('--p', rev);
      fill.style.display = 'none';
      boxA *= p > .86 ? (1 - p) / .14 : 1;
      ax = x + w * rev; ay = y + h * (l.type === 'w' ? .5 : .85);
    } else if (l.type === 'i' || l.type === 'ph') {
      const grow = ease(clamp(p / (l.type === 'ph' ? .24 : .3)));
      const fadeAt = l.type === 'ph' ? .86 : .46;
      const wipe = l.type === 'ph' ? 0 : ease(clamp((p - .46) / .44));
      fill.style.width = `${grow * 100}%`;
      fill.style.height = `${grow * 100}%`;
      fill.style.clipPath = `inset(${wipe * 100}% 0 0 0)`;
      if (l.type === 'ph') {
        fill.style.opacity = p < fadeAt ? 1 : (1 - p) / (1 - fadeAt);
        el.style.setProperty('--o', 0);
      } else {
        el.style.setProperty('--o', p > .32 ? 1 : 0);
      }
      box.style.width = `${w * grow}px`;
      box.style.height = `${h * grow}px`;
      boxA *= p > .9 ? (1 - p) / .1 : 1;
      const corners = [[x, y], [x + w * grow, y], [x + w * grow, y + h * grow], [x, y + h * grow]];
      const k = Math.floor(p * 8);
      l.crew.forEach((a, n) => {
        const [cx, cy] = corners[(k + n * 2) % 4];
        a.tx = cx; a.ty = cy;
      });
    } else if (l.type === 'c') {
      // Duplicate of the first card: dragged across, then it resolves into its own frame
      const src = layers.find(o => o.el.id === l.wait);
      const sr = src ? src.el.getBoundingClientRect() : r;
      const slide = ease(clamp(p / .46));
      const base = l.home === undefined ? (l.home = r.left - sr.left) : l.home;
      el.style.setProperty('--o', 1);
      el.style.transform = `translateX(${-base * (1 - slide)}px)`;
      el.style.filter = slide < .98 ? 'url(#hblur)' : 'none';
      el.style.setProperty('--g', 1 - clamp((p - .6) / .34));
      boxA *= p > .9 ? (1 - p) / .1 : 1;
      ax = r.left + r.width; ay = r.top + r.height * .5;
    }

    box.style.opacity = boxA;
    if (l.type !== 'i' && l.type !== 'ph' && l.crew[0]) { l.crew[0].tx = ax; l.crew[0].ty = ay; }
    if (p >= 1) { delete l.home; finishLayer(l); }
  };

  const stepLayers = () => {
    const vh = H, reads = [];
    for (const l of layers) if (l.state < 2) reads.push([l, l.el.getBoundingClientRect()]);
    let active = 0, backlog = 0;
    const ready = [];
    for (const [l, r] of reads) {
      if (l.state === 1) { active++; continue; }
      if (!r.width && !r.height) { finishLayer(l); continue; }
      if (l.at !== null) { if (S.clock - S.layoutAt >= l.at) ready.push([l, r]); continue; }
      if (S.clock - S.layoutAt < 900) continue;
      if (r.bottom < -40) { finishLayer(l); continue; }
      if (r.top < vh - 6) {
        if (l.wait && !layers.some(o => o.el.id === l.wait && o.state === 2)) continue;
        ready.push([l, r]); backlog++;
      }
    }
    const room = (5 + Math.floor(backlog / 3)) - active;
    let started = 0;
    for (const [l] of ready) {
      if (l.at === null && started >= room) break;
      startLayer(l, backlog);
      if (l.at === null) started++;
    }
    for (const [l, r] of reads) if (l.state === 1) stepLayer(l, r);
  };

  const stepGuides = () => {
    S.guides = S.guides.filter(g => {
      const t = (S.clock - g.born) / g.life;
      if (t >= 1) { g.el.remove(); return false; }
      const r = g.l.el.getBoundingClientRect();
      const a = t < .2 ? t / .2 : (1 - t) / .8;
      g.el.style.opacity = a;
      if (g.kind === 'h') g.el.style.transform = `translateY(${r.top}px)`;
      else if (g.kind === 'v') g.el.style.transform = `translateX(${r.left}px)`;
      else {
        g.el.style.width = `${(W - 120) * ease(clamp(t / .5))}px`;
        g.el.style.transform = `translate(60px,${r.bottom + 8}px)`;
      }
      return true;
    });
  };

  /* ---------- Swarm motion ---------- */
  const wander = (a, dt, t) => {
    a.wa += Math.sin(t * .0007 + a.i * 2.1) * dt * 1.6;
    a.wx += Math.cos(a.wa) * a.ws * dt;
    a.wy += Math.sin(a.wa) * a.ws * dt;
    if (a.wx < 40 || a.wx > W - 40) { a.wa = Math.PI - a.wa; a.wx = clamp(a.wx, 40, W - 40); }
    if (a.wy < 90 || a.wy > H - 90) { a.wa = -a.wa; a.wy = clamp(a.wy, 90, H - 90); }
  };

  const stepSwarm = (dt, ms) => {
    const t = performance.now();
    const secs = t / 1000;
    const cx = W / 2, cy = H / 2;
    let ring = null;
    if (S.phase === 'ring') {
      const r = $('#reelCard').getBoundingClientRect();
      ring = { x: clamp(r.left + r.width / 2, 200, W - 200), y: clamp(r.top + r.height / 2, 220, H - 220) };
    }
    for (const a of agents) {
      let k = 2.6, c = 3;
      if (S.phase === 'scan') {
        const side = a.i % 2 ? 0 : Math.PI;
        const ang = side + secs * 1.75 + a.arc;
        const rad = 170 + a.rr;
        a.tx = cx + Math.cos(ang) * rad; a.ty = cy + Math.sin(ang) * rad;
        k = 34; c = 11;
      } else if (S.phase === 'scatter') {
        const left = a.i % 3 !== 0;
        const n = a.i / AGENTS;
        a.tx = left ? 60 + (a.i % 4) * 34 : W - 170 + (a.i % 3) * 30;
        a.ty = 70 + n * (H - 150);
        k = 60; c = 13;
      } else if (S.phase === 'ring') {
        const ang = (a.i / AGENTS) * Math.PI * 2 + secs * .62 + Math.sin(secs * .7 + a.i) * .08;
        const rad = 165 + Math.sin(secs * 1.3 + a.i * .6) * 14 + a.rr * .5;
        a.tx = ring.x + Math.cos(ang) * rad; a.ty = ring.y + Math.sin(ang) * rad;
        k = 9; c = 5.6;
      } else if (a.busy) {
        k = 90; c = 17;
      } else {
        wander(a, dt, t);
        const lead = agents[a.lead];
        a.tx = lead.wx + (a.lead === a.i ? 0 : a.ox);
        a.ty = lead.wy + (a.lead === a.i ? 0 : a.oy);
      }
      a.vx += (k * (a.tx - a.x) - c * a.vx) * dt;
      a.vy += (k * (a.ty - a.y) - c * a.vy) * dt;
      a.x += a.vx * dt; a.y += a.vy * dt;
      const sp = Math.hypot(a.vx, a.vy);
      if (sp > 14) {
        const want = Math.atan2(a.vy, a.vx);
        let d = want - a.a;
        d = Math.atan2(Math.sin(d), Math.cos(d));
        a.a += d * clamp(dt * 9);
      }
      a.sp = sp;
    }
  };

  /* ---------- Cursor sprites ---------- */
  const arrow = (x, y, ang, color, alpha = 1) => {
    ctx.save();
    ctx.translate(x, y); ctx.rotate(ang); ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.moveTo(10, 0); ctx.lineTo(-7.5, -6.8); ctx.lineTo(-3.4, 0); ctx.lineTo(-7.5, 6.8); ctx.closePath();
    ctx.fillStyle = color; ctx.fill();
    ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(0,0,0,.6)'; ctx.stroke();
    ctx.restore();
  };
  const plus = (x, y, color) => {
    ctx.fillStyle = color;
    ctx.fillRect(x - 7, y - 1, 14, 2); ctx.fillRect(x - 1, y - 7, 2, 14);
  };
  const ibeam = (x, y) => {
    ctx.fillStyle = '#fff';
    ctx.fillRect(x - .9, y - 9, 1.8, 18);
    ctx.fillRect(x - 4, y - 10, 8, 1.8); ctx.fillRect(x - 4, y + 8.2, 8, 1.8);
  };
  const BOT = ['..#....#..', '...####...', '.########.', '.#w####w#.', '.########.', '..######..', '.#.####.#.', '...#..#...'];
  const bot = (x, y) => {
    const u = 1.8;
    BOT.forEach((row, j) => [...row].forEach((c, i) => {
      if (c === '.') return;
      ctx.fillStyle = c === 'w' ? '#e9fbff' : '#2f8cff';
      ctx.fillRect(x + (i - 5) * u, y + (j - 4) * u, u, u);
    }));
  };
  const draw = () => {
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx.clearRect(0, 0, W, H);
    if (S.dismissed) return;
    for (const a of agents) {
      if (a.tool === 'plus') plus(a.x, a.y, a.color);
      else if (a.tool === 'ibeam') ibeam(a.x, a.y);
      else if (a.tool === 'bot') bot(a.x, a.y);
      else {
        if (a.sp > 420) for (let g = 3; g > 0; g--) {
          const f = g * .014;
          arrow(a.x - a.vx * f, a.y - a.vy * f, a.a, a.color, .16 * (4 - g) / 3);
        }
        arrow(a.x, a.y, a.a, a.color);
      }
    }
  };

  /* ---------- Status pill ---------- */
  const setPill = () => {
    ui.bar.style.width = `${(S.done / layers.length) * 100}%`;
    if (S.phase === 'build' || S.phase === 'scatter') ui.layers.textContent = `${S.done} / ${layers.length} layers`;
  };
  const pillScan = () => {
    pill.className = 'pill scan-state';
    ui.text.textContent = 'Scanning page…';
    ui.bar.style.width = '0%';
    ui.main.textContent = 'Building';
    ui.main.className = 'main';
    ui.speed.textContent = `${S.rate}x`;
  };
  const pillBuild = () => {
    pill.className = 'pill';
    ui.text.replaceChildren(ui.agents, Object.assign(document.createElement('span'), { className: 'sep', textContent: '·' }), ui.layers);
  };
  const pillDone = () => {
    const s = Math.round((S.doneAt - S.layoutAt) / 1000);
    pill.className = 'pill done-state';
    ui.text.textContent = `Rebuilt by ${AGENTS} agents in ${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
    ui.bar.style.width = '100%';
    ui.main.textContent = 'Replay';
    ui.speed.textContent = 'Share';
  };

  /* ---------- Phases ---------- */
  const setPhase = (name) => { S.phase = name; S.phaseAt = S.clock; };

  const boot = () => {
    S.dismissed = false; S.paused = false; S.done = 0; S.ticks = 0;
    S.guides.forEach(g => g.el.remove()); S.guides = [];
    stage.replaceChildren();
    layers.forEach(l => {
      l.state = 0; l.ov = null; l.crew = []; delete l.home;
      l.el.classList.remove('on', 'bld');
      l.el.style.removeProperty('transform');
      l.el.style.removeProperty('filter');
    });
    agents.forEach(a => { a.busy = false; a.tool = 'arrow'; });
    root.style.scrollBehavior = 'auto';
    scrollTo(0, 0);
    root.style.scrollBehavior = '';
    root.classList.add('lock');
    veil.classList.remove('off');
    canvas.style.display = '';
    dock.classList.remove('gone');
    pillScan();
    setPhase('scan');
  };

  const dismiss = () => {
    layers.forEach(l => { if (l.state < 2) { l.state = 1; finishLayer(l); } });
    S.guides.forEach(g => g.el.remove()); S.guides = [];
    S.dismissed = true;
    setPhase('idle');
    root.classList.remove('lock');
    veil.classList.add('off');
    dock.classList.add('gone');
    canvas.style.display = 'none';
  };

  ui.main.addEventListener('click', () => {
    if (!root.classList.contains('js')) {
      try { localStorage.setItem('playBuild', '1'); } catch {}
      root.classList.remove('static');
      root.classList.add('js');
      return start();
    }
    if (S.phase === 'finish' || S.phase === 'ring') return boot();
    if (S.phase !== 'build') return;
    S.paused = !S.paused;
    ui.main.textContent = S.paused ? 'Paused' : 'Building';
  });
  ui.speed.addEventListener('click', async () => {
    if (S.phase === 'finish' || S.phase === 'ring') {
      try { await navigator.clipboard.writeText(location.href); ui.speed.textContent = 'Copied'; }
      catch { ui.speed.textContent = location.host; }
      return;
    }
    S.rate = S.rate === 1 ? 2 : 1;
    ui.speed.textContent = `${S.rate}x`;
  });
  ui.sound.addEventListener('click', () => {
    S.muted = !S.muted;
    ui.sound.setAttribute('aria-pressed', String(!S.muted));
  });

  const frame = (now) => {
    const ms = Math.min(now - (S.last || now), 120);
    S.last = now;
    const dt = ms / 1000;
    if (!S.paused) S.clock += ms * S.rate;
    const since = S.clock - S.phaseAt;

    if (S.phase === 'scan' && since > SCAN_MS) {
      setPhase('scatter');
      S.layoutAt = S.clock + SCATTER_MS;
      veil.classList.add('off');
      root.classList.remove('lock');
      pillBuild();
      pulseScan();
    } else if (S.phase === 'scatter' && since > SCATTER_MS) {
      setPhase('build');
    } else if (S.phase === 'build') {
      if (!S.paused) stepLayers();
      stepGuides();
      setPill();
      if (S.done >= layers.length) {
        S.doneAt = S.clock;
        setPhase('finish');
        pillDone();
      }
    } else if (S.phase === 'finish') {
      stepGuides();
      if (since > 1500) setPhase('ring');
    }

    if (S.phase !== 'idle') { stepSwarm(Math.min(dt, .033)); draw(); }
    requestAnimationFrame(frame);
  };

  const start = () => {
    agents.forEach(a => {
      const ang = rand(0, 6.28);
      a.x = W / 2 + Math.cos(ang) * 170; a.y = H / 2 + Math.sin(ang) * 170;
      a.wx = rand(60, W - 60); a.wy = rand(100, H - 100);
    });
    boot();
    requestAnimationFrame(frame);
  };
  if (wantsMotion) {
    const fonts = document.fonts ? document.fonts.ready : Promise.resolve();
    Promise.race([fonts, new Promise(r => setTimeout(r, 1500))]).then(start);
  } else {
    // Reduced motion: the finished page shows immediately and the build animation is opt-in
    root.classList.add('static');
    pill.className = 'pill static-state';
    ui.text.textContent = 'Reduced motion is on';
    ui.main.textContent = 'Play build';
  }

  // Hooks for automated visual checks
  window.__swarm = { S, layers, agents, skip: dismiss };
})();
