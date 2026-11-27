/* Kantor ASN Go Digital Lantai 2 — mesin 3D (Three.js r128, tanpa dependensi lain).
   makeOffice3D(host, agents, {bg, onPick}) -> {set(id, state, text)} | null bila WebGL tidak tersedia.
   agents: [{id,n,r,room,sk,h,hc,g,hero}]  state: 'on' | 'done' | 'idle' */
window.makeOffice3D = function (host, AGENTS, opt) {
  opt = opt || {};
  const T = window.THREE;
  if (!T) return null;
  let R;
  try { R = new T.WebGLRenderer({ antialias: true }); } catch (e) { return null; }
  R.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  R.shadowMap.enabled = true; R.shadowMap.type = T.PCFSoftShadowMap; R.outputEncoding = T.sRGBEncoding;
  R.domElement.style.cssText = 'display:block;width:100%;height:100%;touch-action:none;cursor:grab';
  host.style.position = 'relative'; host.appendChild(R.domElement);
  if (!document.getElementById('o3css')) {
    const st = document.createElement('style'); st.id = 'o3css';
    st.textContent = '.o3l{position:absolute;left:0;top:0;transform:translate(-50%,-100%);text-align:center;pointer-events:auto;cursor:pointer;white-space:nowrap;font-family:Montserrat,system-ui,sans-serif;will-change:transform}' +
      '.o3b{display:inline-block;font-size:11px;font-weight:800;padding:2px 8px;border-radius:9px;background:#e9edf5;color:#55607a;box-shadow:0 2px 8px #0002;max-width:150px;overflow:hidden;text-overflow:ellipsis}' +
      '.o3l.on .o3b{background:#ffc52a;color:#0d2b66}.o3l.done .o3b{background:#d9f3e2;color:#0d5a2a}' +
      '.o3n{display:block;margin-top:3px;font-size:11.5px;font-weight:800;color:#fff;background:#0d2b66d9;border-radius:6px;padding:1px 7px}' +
      '.o3r{position:absolute;left:0;top:0;transform:translate(-50%,-50%);font:800 11px Montserrat,system-ui,sans-serif;color:#0d2b66;background:#ffffffd9;border:1.5px solid #0d2b66;border-radius:6px;padding:1px 7px;pointer-events:none;white-space:nowrap}';
    document.head.appendChild(st);
  }
  const S = new T.Scene();
  S.background = new T.Color(opt.bg || '#dfe6ef');
  const cam = new T.PerspectiveCamera(36, 1, 0.1, 400);
  const lay = document.createElement('div');
  lay.style.cssText = 'position:absolute;inset:0;pointer-events:none;overflow:hidden';
  host.appendChild(lay);

  S.add(new T.HemisphereLight(0xffffff, 0x56627a, 0.85));
  S.add(new T.AmbientLight(0xffffff, 0.12));
  const sun = new T.DirectionalLight(0xfff1dc, 0.7);
  sun.position.set(-16, 34, 24); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -26, right: 26, top: 20, bottom: -20, near: 1, far: 90 });
  sun.shadow.bias = -0.0008; S.add(sun);

  const cache = {};
  const M = (c, o) => { const k = c + JSON.stringify(o || {}); return cache[k] || (cache[k] = new T.MeshStandardMaterial(Object.assign({ color: c, roughness: 0.85 }, o || {}))); };
  const add = (me, p, x, y, z) => { me.position.set(x, y, z); me.castShadow = true; me.receiveShadow = true; (p || S).add(me); return me; };
  const B = (w, h, d, m, x, y, z, p) => add(new T.Mesh(new T.BoxGeometry(w, h, d), m), p, x, y, z);
  const C = (rt, rb, h, m, x, y, z, p) => add(new T.Mesh(new T.CylinderGeometry(rt, rb, h, 22), m), p, x, y, z);
  const Sp = (r, m, x, y, z, p) => add(new T.Mesh(new T.SphereGeometry(r, 22, 16), m), p, x, y, z);
  function tex(w, h, draw) {
    const cv = document.createElement('canvas'); cv.width = w; cv.height = h; draw(cv.getContext('2d'), w, h);
    const t = new T.CanvasTexture(cv); t.encoding = T.sRGBEncoding; t.anisotropy = 4; return t;
  }
  const font = (w, s) => w + ' ' + s + 'px Montserrat, Arial, sans-serif';
  const sign = (w, h, draw) => new T.MeshBasicMaterial({ map: tex(w, h, draw) });

  /* ---------- gedung ---------- */
  B(41.4, 0.5, 21.4, M(0x3a4252), 0, -0.25, 0);
  const wood = tex(256, 256, (c) => { c.fillStyle = '#e7d7b8'; c.fillRect(0, 0, 256, 256); for (let i = 0; i < 8; i++) { c.fillStyle = i % 2 ? '#e1cfad' : '#ead9bb'; c.fillRect(0, i * 32, 256, 31); c.fillStyle = '#cdb994'; c.fillRect((i * 97) % 256, i * 32, 2, 31); } });
  wood.wrapS = wood.wrapT = T.RepeatWrapping;
  const carpet = tex(128, 128, (c) => { c.fillStyle = '#d5deec'; c.fillRect(0, 0, 128, 128); c.fillStyle = '#c3cfe3'; for (let x = 0; x < 128; x += 8) for (let y = 0; y < 128; y += 8) c.fillRect(x + 3, y + 3, 2, 2); });
  carpet.wrapS = carpet.wrapT = T.RepeatWrapping;
  const tile = tex(128, 128, (c) => { c.fillStyle = '#eceef1'; c.fillRect(0, 0, 128, 128); c.strokeStyle = '#d3d7de'; c.lineWidth = 2; c.strokeRect(1, 1, 126, 126); });
  tile.wrapS = tile.wrapT = T.RepeatWrapping;
  const RM = {
    dir: { x: -20, z: -10, w: 10, d: 10, f: carpet, n: 'Ruang Direktur' },
    redaksi: { x: -10, z: -10, w: 16, d: 10, f: wood, n: 'Ruang Redaksi' },
    studio: { x: 6, z: -10, w: 7, d: 10, f: wood, n: 'Studio Kreatif' },
    meet: { x: 13, z: -10, w: 7, d: 10, f: carpet, n: 'Ruang Rapat' },
    lobby: { x: -20, z: 0, w: 10, d: 10, f: tile, n: 'Lobi' },
    sosmed: { x: -10, z: 0, w: 16, d: 10, f: wood, n: 'Pusat Media Sosial' },
    sales: { x: 6, z: 0, w: 7, d: 10, f: wood, n: 'Sales & Growth' },
    pantry: { x: 13, z: 0, w: 7, d: 10, f: tile, n: 'Pantry & Musala' }
  };
  for (const k in RM) {
    const r = RM[k], t = r.f.clone(); t.needsUpdate = true; t.repeat.set(r.w / 3, r.d / 3);
    const fl = B(r.w - 0.1, 0.08, r.d - 0.1, new T.MeshStandardMaterial({ map: t, roughness: 0.9 }), r.x + r.w / 2, 0.04, r.z + r.d / 2);
    fl.castShadow = false;
  }
  const wallM = M(0xf4f0e7), glassM = new T.MeshStandardMaterial({ color: 0xbfe3ff, transparent: true, opacity: 0.32, roughness: 0.1 });
  const WH = 2.2;
  const wx = (x0, x1, z, h, m) => B(Math.abs(x1 - x0), h, 0.2, m || wallM, (x0 + x1) / 2, h / 2, z);
  const wz = (z0, z1, x, h, m) => B(0.2, h, Math.abs(z1 - z0), m || wallM, x, h / 2, (z0 + z1) / 2);
  wx(-20.6, 20.6, -10.3, 3.4);
  wz(-10.4, 10.2, -20.4, WH); wz(-10.4, 10.2, 20.4, WH);
  const winM = new T.MeshStandardMaterial({ color: 0xa9d8f7, emissive: 0x6fb8ea, emissiveIntensity: 0.35, roughness: 0.2 });
  for (const k of ['dir', 'redaksi', 'studio', 'meet']) { const r = RM[k]; B(r.w * 0.62, 1.4, 0.06, winM, r.x + r.w / 2, 2.15, -10.18); B(0.08, 1.4, 0.1, wallM, r.x + r.w / 2, 2.15, -10.15); }
  for (const k of ['dir', 'redaksi', 'studio', 'meet']) { const r = RM[k]; wx(r.x, r.x + 1.2, 0, WH); wx(r.x + 2.8, r.x + r.w, 0, WH); }
  wz(-10.2, 0, -10, WH, glassM); wz(-10.2, -3, 6, WH); wz(-10.2, 0, 13, WH, glassM);
  B(0.12, WH, 0.12, wallM, -10, WH / 2, -10.1); B(0.12, WH, 0.12, wallM, 13, WH / 2, -10.1);
  wz(0, 7.4, -10, WH); wz(0, 7.4, 6, WH); wz(0, 7.4, 13, WH);

  /* ---------- perabot ---------- */
  function plant(x, z, s) { s = s || 1; C(0.24 * s, 0.18 * s, 0.45 * s, M(0x8a5a33), x, 0.22 * s, z); Sp(0.45 * s, M(0x2f8f46), x, 0.8 * s, z); Sp(0.3 * s, M(0x4cb460), x + 0.18 * s, 1.08 * s, z + 0.1 * s); }
  function chair(x, z, col, p) { B(0.62, 0.1, 0.62, M(col || 0x2b3245), x, 0.55, z, p); B(0.62, 0.72, 0.1, M(col || 0x2b3245), x, 0.95, z - 0.3, p); C(0.04, 0.04, 0.5, M(0x666e7d), x, 0.27, z, p); }
  function board(w, h, draw, x, y, z, ry) { const me = B(w, h, 0.06, sign(Math.round(w * 128), Math.round(h * 128), draw), x, y, z); me.rotation.y = ry || 0; me.castShadow = false; return me; }
  const navyTxt = (c, w, h, lines, bg) => { c.fillStyle = bg || '#ffffff'; c.fillRect(0, 0, w, h); c.strokeStyle = '#b9c1d1'; c.lineWidth = 10; c.strokeRect(0, 0, w, h); c.fillStyle = '#0d2b66'; c.textAlign = 'center'; c.textBaseline = 'middle'; lines.forEach((l, i) => { c.font = font(i ? 700 : 900, i ? h * 0.13 : h * 0.18); c.fillText(l, w / 2, h * (0.25 + i * 0.22)); }); };

  board(4.2, 1.5, (c, w, h) => navyTxt(c, w, h, ['PILAR KONTEN', 'Regulasi Desa/Kampung', 'AI untuk ASN', 'Target: 1 carousel/hari']), -2, 1.55, -10.17);
  board(2.4, 1.2, (c, w, h) => { c.fillStyle = '#fff'; c.fillRect(0, 0, w, h); ['#0d2b66', '#ffc52a', '#d8232a', '#13843f'].forEach((k, i) => { c.fillStyle = k; c.fillRect(30 + i * (w - 60) / 4, 40, (w - 60) / 4 - 14, h - 80); }); }, 9.5, 1.5, -10.17);
  B(2.4, 2.1, 0.45, M(0x6b4a2c), -18, 1.05, -9.75);
  for (let i = 0; i < 3; i++) B(2.2, 0.05, 0.4, M(0x8a5f37), -18, 0.5 + i * 0.6, -9.7);
  for (let i = 0; i < 9; i++) B(0.14, 0.42, 0.3, M([0xd8232a, 0x0d2b66, 0xffc52a, 0x13843f][i % 4]), -18.9 + i * 0.22, 1.36, -9.7);
  C(0.03, 0.03, 2.3, M(0x9aa3b2), -11.3, 1.15, -9.4); B(0.7, 0.22, 0.02, M(0xd8232a), -10.92, 2.14, -9.4); B(0.7, 0.22, 0.02, M(0xffffff), -10.92, 1.92, -9.4);
  board(3.2, 1.6, (c, w, h) => navyTxt(c, w, h, ['RAPAT PRODUKSI', 'Riset → Naskah → Desain', 'Caption → Cek fakta'], '#fffbea'), 16.5, 1.7, -10.17);
  const tbl = C(1, 1, 0.1, M(0x9c6c40), 16.5, 0.85, -5); tbl.scale.set(2.2, 1, 1.15); C(0.18, 0.28, 0.8, M(0x6b4a2c), 16.5, 0.4, -5);
  for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2, cx = 16.5 + Math.cos(a) * 2.9, cz = -5 + Math.sin(a) * 1.75, g = new T.Group(); g.position.set(cx, 0, cz); g.rotation.y = -a - Math.PI / 2; S.add(g); chair(0, 0, 0x0d2b66, g); }
  plant(19.3, -9.2); plant(-19.2, -1.0); plant(5.2, -0.9, 0.8); plant(12.3, 9.2, 0.9); plant(-10.8, 9.2, 0.8);
  const scr = new T.MeshBasicMaterial({ map: tex(640, 256, (c, w, h) => { c.fillStyle = '#0b1736'; c.fillRect(0, 0, w, h); const t = [['INSTAGRAM', '#e1306c'], ['THREADS', '#ffffff'], ['FACEBOOK', '#1877f2']]; t.forEach(([n, k], i) => { const x = 20 + i * 205; c.fillStyle = '#16244d'; c.fillRect(x, 40, 190, 176); c.fillStyle = k; c.fillRect(x, 40, 190, 10); c.font = font(900, 26); c.fillStyle = '#fff'; c.textAlign = 'center'; c.fillText(n, x + 95, 100); c.fillStyle = '#ffc52a'; c.font = font(800, 20); c.fillText('@arifitra_muhammad', x + 95, 150); c.fillStyle = '#7fa0d8'; c.fillRect(x + 30, 175, 130, 10); }); c.fillStyle = '#ffc52a'; c.font = font(900, 22); c.textAlign = 'left'; c.fillText('PUSAT KOMANDO MEDIA SOSIAL', 20, 28); }) });
  B(0.2, 2.2, 0.2, M(0x2b3245), -2, 1.1, 0.25); const tv = B(5.4, 2.1, 0.1, scr, -2, 1.55, 0.18); tv.castShadow = false;
  board(2.6, 1.2, (c, w, h) => navyTxt(c, w, h, ['lynk.id/asngodigital', 'Generator Naskah Dinas', 'Simulasi CAT CPNS']), 9.5, 1.5, 0.15);
  B(4.6, 0.95, 0.75, M(0xcfd6e2), 15.5, 0.48, 0.55); B(4.6, 0.06, 0.8, M(0x8f99ab), 15.5, 0.98, 0.55);
  B(0.4, 0.5, 0.4, M(0x22262f), 14.2, 1.26, 0.5); B(0.3, 0.4, 0.3, M(0xdfe8f5), 15.0, 1.21, 0.5); C(0.12, 0.12, 0.5, M(0x9bd3ff, { transparent: true, opacity: 0.6 }), 15.0, 1.65, 0.5);
  B(0.95, 2.0, 0.8, M(0xe6ebf3), 19.4, 1.0, 0.6);
  const rug = B(1.3, 0.03, 2.1, sign(130, 210, (c, w, h) => { c.fillStyle = '#13843f'; c.fillRect(0, 0, w, h); c.strokeStyle = '#ffc52a'; c.lineWidth = 6; c.strokeRect(10, 10, w - 20, h - 20); c.beginPath(); c.moveTo(w / 2, 22); c.lineTo(w - 25, 60); c.lineTo(25, 60); c.closePath(); c.stroke(); }), 17.8, 0.09, 6.2); rug.castShadow = false;
  B(0.95, 2.05, 0.08, M(0xb4bcc9, { metalness: 0.6, roughness: 0.3 }), -17.6, 1.03, 0.16); B(0.95, 2.05, 0.08, M(0xb4bcc9, { metalness: 0.6, roughness: 0.3 }), -16.5, 1.03, 0.16);
  board(1.2, 0.45, (c, w, h) => { c.fillStyle = '#ffc52a'; c.fillRect(0, 0, w, h); c.fillStyle = '#0d2b66'; c.font = font(900, h * 0.6); c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('LT. 2', w / 2, h / 2); }, -17.05, 2.35, 0.17);
  board(3.2, 0.7, (c, w, h) => { c.fillStyle = '#0d2b66'; c.fillRect(0, 0, w, h); c.fillStyle = '#ffc52a'; c.font = font(900, h * 0.42); c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('ASN GO DIGITAL', w / 2, h / 2); }, -13.2, 1.8, 0.17);
  B(2.2, 0.45, 0.85, M(0x0d2b66), -12.8, 0.32, 8.3); B(2.2, 0.55, 0.2, M(0x0d2b66), -12.8, 0.7, 8.75); B(0.9, 0.04, 0.6, M(0xffc52a), -14.6, 0.45, 8.2);

  /* ---------- karyawan ---------- */
  const agents = {}, pickables = [];
  const hex = (s, d) => new T.Color(s || d);
  function person(a, p) {
    const skin = M(hex(a.sk, '#c68b5e').getHex()), hairM = M(hex(a.hc, '#1b1b1b').getHex()), dark = M(0x161616);
    const shirt = M(a.hero ? 0x0d2b66 : 0xc9a96b);
    C(0.3, 0.37, 0.78, shirt, 0, 1.12, 0, p);
    B(0.16, 0.05, 0.12, M(a.hero ? 0xffc52a : 0x8a6d3e), -0.3, 1.5, 0, p); B(0.16, 0.05, 0.12, M(a.hero ? 0xffc52a : 0x8a6d3e), 0.3, 1.5, 0, p);
    B(0.16, 0.05, 0.02, dark, 0.15, 1.28, 0.33, p);
    C(0.09, 0.09, 0.14, skin, 0, 1.55, 0, p);
    const arms = [];
    for (const sx of [-1, 1]) { const piv = new T.Group(); piv.position.set(sx * 0.36, 1.42, 0.02); p.add(piv); C(0.075, 0.07, 0.55, shirt, 0, -0.26, 0, piv); Sp(0.075, skin, 0, -0.55, 0, piv); piv.rotation.x = -1.05; piv.rotation.z = sx * 0.12; arms.push(piv); }
    if (a.h === 'hijab') {
      Sp(0.32, hairM, 0, 1.8, -0.04, p); C(0.3, 0.44, 0.42, hairM, 0, 1.47, -0.02, p);
      Sp(0.22, skin, 0, 1.79, 0.1, p);
    } else {
      Sp(0.27, skin, 0, 1.8, 0, p);
      if (a.h === 'curly') { [[0, 2.04, -0.02], [-0.16, 1.98, -0.04], [0.16, 1.98, -0.04], [-0.24, 1.86, -0.05], [0.24, 1.86, -0.05], [0, 1.95, -0.16], [-0.1, 2.02, 0.08], [0.1, 2.02, 0.08]].forEach(q => Sp(0.12, hairM, q[0], q[1], q[2], p)); }
      else if (a.h === 'long') { Sp(0.29, hairM, 0, 1.86, -0.05, p); B(0.5, 0.62, 0.16, hairM, 0, 1.58, -0.16, p); }
      else if (a.h === 'bob') { const h = Sp(0.3, hairM, 0, 1.82, -0.06, p); h.scale.set(1.02, 0.95, 1); }
      else { const h = Sp(0.285, hairM, 0, 1.87, -0.05, p); h.scale.set(1, 0.78, 1); }
    }
    const ez = a.h === 'hijab' ? 0.3 : 0.25;
    Sp(0.034, dark, -0.09, 1.82, ez, p); Sp(0.034, dark, 0.09, 1.82, ez, p);
    const sm = new T.Mesh(new T.TorusGeometry(0.06, 0.012, 6, 12, Math.PI), M(0x7a3d2a)); sm.position.set(0, 1.71, ez - 0.01); sm.rotation.z = Math.PI; p.add(sm);
    if (a.g) for (const sx of [-1, 1]) { const g = new T.Mesh(new T.TorusGeometry(0.06, 0.012, 6, 16), dark); g.position.set(sx * 0.09, 1.82, ez + 0.03); p.add(g); }
    return arms;
  }
  const by = {}; AGENTS.forEach(a => (by[a.room] = by[a.room] || []).push(a));
  for (const room in by) {
    const r = RM[room]; if (!r) continue; const list = by[room];
    list.forEach((a, i) => {
      const x = r.x + r.w * (i + 0.5) / list.length, zd = r.z + r.d * 0.56;
      const g = new T.Group(); g.position.set(x, 0, zd); S.add(g); g.userData.id = a.id;
      const dw = a.hero ? 2.6 : 2.0, top = a.hero ? 0x5a3a22 : 0xa8784a;
      B(dw, 0.1, 1.0, M(top), 0, 0.92, 0, g);
      B(0.08, 0.88, 0.9, M(0x6b4a2c), -dw / 2 + 0.06, 0.45, 0, g); B(0.08, 0.88, 0.9, M(0x6b4a2c), dw / 2 - 0.06, 0.45, 0, g);
      B(dw - 0.2, 0.5, 0.06, M(a.room === 'lobby' ? 0x0d2b66 : 0x8a5f37), 0, 0.62, 0.46, g);
      const kb = new T.MeshStandardMaterial({ color: 0x2a3142, emissive: 0x000000, roughness: 0.5 });
      B(0.72, 0.03, 0.46, kb, 0, 0.985, -0.05, g);
      const lid = B(0.72, 0.46, 0.03, M(0x1d2a4a), 0, 1.22, 0.2, g); lid.rotation.x = -0.18;
      B(0.2, 0.2, 0.01, M(0xffc52a), 0, 1.24, 0.225, g).rotation.x = -0.18;
      B(0.24, 0.02, 0.34, M(0xffffff), -0.62, 0.985, 0.05, g);
      C(0.05, 0.05, 0.12, M(0xd8232a), 0.65, 1.03, 0.05, g);
      const lampM = new T.MeshStandardMaterial({ color: 0x777777, emissive: 0x000000 });
      C(0.03, 0.03, 0.42, M(0x2b3245), dw / 2 - 0.25, 1.18, -0.3, g); const bulb = Sp(0.09, lampM, dw / 2 - 0.25, 1.42, -0.3, g);
      const pp = new T.Group(); pp.position.set(0, 0, -0.85); g.add(pp);
      chair(0, -0.05, a.hero ? 0x101820 : 0x2b3245, pp);
      const arms = person(a, pp);
      const ringM = new T.MeshBasicMaterial({ color: 0xffc52a, transparent: true, opacity: 0, depthWrite: false });
      const ring = new T.Mesh(new T.RingGeometry(0.62, 0.8, 40), ringM); ring.rotation.x = -Math.PI / 2; ring.position.set(0, 0.1, -0.85); g.add(ring);
      const head = new T.Vector3(); const el = document.createElement('div'); el.className = 'o3l';
      const bub = document.createElement('span'); bub.className = 'o3b'; bub.textContent = a.hero ? 'Memimpin' : 'Siaga';
      const nm = document.createElement('span'); nm.className = 'o3n'; nm.textContent = a.n;
      el.append(bub, nm); el.addEventListener('click', () => opt.onPick && opt.onPick(a.id)); lay.appendChild(el);
      agents[a.id] = { g, pp, arms, kb, lampM, ringM, el, bub, head, state: 'idle', ph: Math.random() * 6 };
      pickables.push(g);
    });
  }
  const roomLabels = Object.keys(RM).map(k => { const r = RM[k], el = document.createElement('div'); el.className = 'o3r'; el.textContent = r.n; lay.appendChild(el); return { el, v: r.z < 0 ? new T.Vector3(r.x + r.w / 2, 3.75, -10.3) : new T.Vector3(r.x + r.w / 2, 0.15, r.z + r.d - 0.55) }; });

  /* ---------- kamera ---------- */
  let th = 0, ph = 0.92, rad = 48, aspect = 1;
  const tgt = new T.Vector3(0, 0, -1.2);
  const fitRad = () => aspect >= 1.6 ? 39 : aspect >= 1.15 ? 48 : aspect >= 0.9 ? 62 : 58;
  const home = () => { const tall = aspect < 0.9; th = tall ? Math.PI / 2 : 0; ph = tall ? 0.62 : 0.92; rad = fitRad(); };
  function place() { cam.position.set(tgt.x + rad * Math.sin(ph) * Math.sin(th), tgt.y + rad * Math.cos(ph), tgt.z + rad * Math.sin(ph) * Math.cos(th)); cam.lookAt(tgt); }
  function resize() { const w = host.clientWidth, h = host.clientHeight; if (!w || !h) return; const first = aspect === 1; aspect = w / h; R.setSize(w, h, false); cam.aspect = aspect; cam.updateProjectionMatrix(); if (first) home(); place(); }
  const ro = new ResizeObserver(resize); ro.observe(host); resize();
  const pts = new Map(); let moved = 0, pinch = 0;
  const cv = R.domElement;
  cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY }); moved = 0; cv.style.cursor = 'grabbing'; });
  cv.addEventListener('pointermove', e => {
    const p = pts.get(e.pointerId); if (!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY; moved += Math.abs(dx) + Math.abs(dy);
    if (pts.size === 1) { th -= dx * 0.006; ph = Math.min(1.3, Math.max(0.3, ph - dy * 0.005)); }
    else if (pts.size === 2) { const [a, b] = [...pts.values()]; const d = Math.hypot(a.x - b.x, a.y - b.y); if (pinch) rad = Math.min(100, Math.max(14, rad * pinch / d)); pinch = d; }
    place();
  });
  const up = e => {
    if (pts.size === 1 && moved < 6 && opt.onPick) {
      const rc = cv.getBoundingClientRect(), v = new T.Vector2((e.clientX - rc.left) / rc.width * 2 - 1, -((e.clientY - rc.top) / rc.height) * 2 + 1);
      const ray = new T.Raycaster(); ray.setFromCamera(v, cam);
      const hit = ray.intersectObjects(pickables, true)[0];
      if (hit) { let o = hit.object; while (o && !o.userData.id) o = o.parent; if (o) opt.onPick(o.userData.id); }
    }
    pts.delete(e.pointerId); pinch = 0; cv.style.cursor = 'grab';
  };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', e => { pts.delete(e.pointerId); pinch = 0; });
  cv.addEventListener('wheel', e => { e.preventDefault(); rad = Math.min(100, Math.max(14, rad * (1 + e.deltaY * 0.0012))); place(); }, { passive: false });

  /* ---------- animasi ---------- */
  const calm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  let vis = true; new IntersectionObserver(es => { vis = es[0].isIntersecting; }).observe(host);
  const tmp = new T.Vector3();
  function frame(t) {
    requestAnimationFrame(frame); if (!vis) return; const s = t / 1000;
    for (const id in agents) {
      const A = agents[id], on = A.state === 'on';
      if (!calm) { A.pp.position.y = on ? Math.abs(Math.sin(s * 6 + A.ph)) * 0.04 : Math.sin(s * 1.4 + A.ph) * 0.012; A.arms.forEach((m, i) => { m.rotation.x = -1.05 + (on ? Math.sin(s * 14 + i * 2 + A.ph) * 0.09 : 0); }); }
      A.ringM.opacity = on ? 0.55 + Math.sin(s * 4) * 0.25 : A.state === 'done' ? 0.55 : 0;
    }
    const w = host.clientWidth, h = host.clientHeight;
    for (const id in agents) {
      const A = agents[id]; A.head.set(0, 2.55, -0.85); A.g.localToWorld(A.head); tmp.copy(A.head).project(cam);
      if (tmp.z > 1) { A.el.style.display = 'none'; continue; }
      A.el.style.display = ''; A.el.style.transform = `translate(${(tmp.x + 1) / 2 * w}px,${(1 - tmp.y) / 2 * h}px) translate(-50%,-100%)`;
    }
    roomLabels.forEach(L => { tmp.copy(L.v).project(cam); L.el.style.display = tmp.z > 1 ? 'none' : ''; L.el.style.transform = `translate(${(tmp.x + 1) / 2 * w}px,${(1 - tmp.y) / 2 * h}px) translate(-50%,-50%)`; });
    R.render(S, cam);
  }
  requestAnimationFrame(frame);

  return {
    set(id, state, text) {
      const A = agents[id]; if (!A) return; A.state = state;
      A.el.className = 'o3l' + (state === 'on' ? ' on' : state === 'done' ? ' done' : '');
      A.bub.textContent = text || (state === 'idle' ? 'Siaga' : '');
      const col = state === 'on' ? 0xffc52a : state === 'done' ? 0x22b34c : 0x000000;
      A.lampM.emissive.setHex(col); A.lampM.emissiveIntensity = state === 'idle' ? 0 : 1.4;
      A.kb.emissive.setHex(state === 'on' ? 0x2a6bd8 : 0x000000); A.kb.emissiveIntensity = 0.8;
      A.ringM.color.setHex(state === 'done' ? 0x22b34c : 0xffc52a);
    },
    view(which) { if (which === 'home') home(); else if (which === 'top') { th = 0; ph = 0.3; rad = fitRad() * 0.95; } else if (which === 'in') rad = Math.max(14, rad * 0.8); else if (which === 'out') rad = Math.min(100, rad * 1.25); place(); }
  };
};
