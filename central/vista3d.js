// Vista 3D da central: desenha o caminho de extrusão real do gcode (cada filete), não o STL.
// Assim aparece a grade interna, os perímetros e o que já foi impresso, camada por camada.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const MESA = 220, CENTRO = 110;
const NOMES = ["Outro", "Perímetro externo", "Perímetro", "Perímetro em balanço", "Grade interna", "Preenchimento sólido",
  "Topo sólido", "Ponte", "Preenche fresta", "Saia", "Suporte", "Interface do suporte", "Passada de alisar"];
const CORES_TIPO = [0x9aa3ad, 0xff8a3d, 0xffc857, 0x4f7cff, 0xc2413a, 0x9b5de5, 0xff5d73, 0x4ea8de, 0xf1f1f1, 0x2bb39a, 0x5fd35f, 0x8fe08f, 0xb0b0ff];

export function criaVista(box, aoMudar) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.localClippingEnabled = true;
  box.prepend(renderer.domElement);

  const cena = new THREE.Scene();
  cena.background = new THREE.Color(0x14171b);
  const pmrem = new THREE.PMREMGenerator(renderer);
  cena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  cena.fog = new THREE.Fog(0x14171b, 400, 900);

  const cam = new THREE.PerspectiveCamera(35, 1, 1, 3000);
  const ctl = new OrbitControls(cam, renderer.domElement);
  ctl.enableDamping = true; ctl.dampingFactor = 0.08; ctl.maxPolarAngle = Math.PI * 0.495;
  ctl.zoomSpeed = 2.5; ctl.zoomToCursor = true;   // pinça no celular amplia rápido e onde o dedo está

  const sol = new THREE.DirectionalLight(0xffffff, 1.4);
  sol.position.set(-80, 160, 120); sol.castShadow = true;
  sol.shadow.mapSize.set(2048, 2048); sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.02;
  Object.assign(sol.shadow.camera, { left: -70, right: 70, top: 70, bottom: -70, near: 10, far: 500 });
  cena.add(sol, sol.target);
  cena.add(new THREE.HemisphereLight(0xdfe8ff, 0x20242a, 0.35));

  // mesa: chapa escura texturizada com grade de 10 mm
  const tex = (() => {
    const c = document.createElement("canvas"); c.width = c.height = 1024; const g = c.getContext("2d");
    g.fillStyle = "#1c1f23"; g.fillRect(0, 0, 1024, 1024);
    for (let i = 0; i < 9000; i++) { g.fillStyle = `rgba(255,255,255,${Math.random() * 0.025})`; g.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 2); }
    g.strokeStyle = "rgba(255,255,255,0.06)"; g.lineWidth = 1;
    for (let i = 0; i <= 22; i++) { const p = i * 1024 / 22; g.beginPath(); g.moveTo(p, 0); g.lineTo(p, 1024); g.moveTo(0, p); g.lineTo(1024, p); g.stroke(); }
    g.strokeStyle = "rgba(255,138,61,0.25)"; g.lineWidth = 2; g.strokeRect(2, 2, 1020, 1020);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
  })();
  const mesa = new THREE.Mesh(new THREE.BoxGeometry(MESA, 3, MESA),
    [0, 0, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.85, metalness: 0.05 }), 0, 0, 0].map(m => m || new THREE.MeshStandardMaterial({ color: 0x111316, roughness: 0.6 })));
  mesa.position.y = -1.5; mesa.receiveShadow = true; cena.add(mesa);

  // bico: bloco aquecedor + ponta de latão, segue o último filete impresso
  const bico = new THREE.Group();
  const bloco = new THREE.Mesh(new THREE.BoxGeometry(16, 11, 20), new THREE.MeshStandardMaterial({ color: 0xb8bcc2, metalness: 0.6, roughness: 0.35, transparent: true, opacity: 0.18, depthWrite: false }));
  bloco.position.y = 12.5;
  const ponta = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 0.5, 6, 6), new THREE.MeshStandardMaterial({ color: 0xd9a441, metalness: 0.9, roughness: 0.25 }));
  ponta.position.y = 3.6;
  const brilho = new THREE.PointLight(0xff9a4d, 0, 30, 2); brilho.position.y = 1;
  bico.add(bloco, ponta, brilho); ponta.castShadow = true; cena.add(bico);

  // plano de corte para enxergar o interior
  const plano = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0);

  let D = null;                // dados do caminho
  let malha = null, camadaMalha = null, fantasma = null;
  let modoCor = "tipo", corFil = new THREE.Color(0x8a5a3b);
  let progresso = 0, camadaVer = null, soCamada = false, corte = false, aoVivo = true;
  let enquadrado = false, ultimaCamadaMontada = -1, ultimoN = -1;

  // geometria de um filete: cilindro achatado deitado ao longo de X (seção elíptica)
  const geoFilete = new THREE.CylinderGeometry(0.5, 0.5, 1, 10, 1, true);
  geoFilete.rotateZ(Math.PI / 2);

  const matFilete = new THREE.MeshStandardMaterial({ roughness: 0.42, metalness: 0.0, clippingPlanes: [], clipShadows: true, side: THREE.DoubleSide });
  const matCamada = new THREE.MeshStandardMaterial({ roughness: 0.35, emissive: 0xff7a1a, emissiveIntensity: 0.35, clippingPlanes: [], clipShadows: true, side: THREE.DoubleSide });

  let sujo = true;   // precisa redesenhar (ver o laço anima)
  function ajusta() { const w = box.clientWidth, h = box.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); sujo = true; }
  addEventListener("resize", ajusta); ajusta();

  function corDe(tipo, out) {
    if (modoCor === "tipo") return out.setHex(CORES_TIPO[tipo] ?? CORES_TIPO[0]);
    // cor do filamento com leve variação por tipo para ainda distinguir as partes
    const f = tipo === 1 ? 1.0 : tipo === 4 ? 0.78 : tipo === 2 ? 0.9 : 0.85;
    return out.copy(corFil).multiplyScalar(f);
  }

  const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3(), _eixo = new THREE.Vector3(0, 1, 0);
  // matriz do filete i no slot k; frac < 1 desenha só o começo do filete (o bico ainda está passando)
  function umaMatriz(alvo, k, i, frac = 1) {
    const a = D.seg, o = i * 9;
    const x0 = a[o] - CENTRO, y0 = a[o + 1] - CENTRO, z = a[o + 4], w = a[o + 5], h = a[o + 6];
    const x1 = x0 + (a[o + 2] - a[o]) * frac, y1 = y0 + (a[o + 3] - a[o + 1]) * frac;
    const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy);
    _p.set((x0 + x1) / 2, z - h / 2, -(y0 + y1) / 2);
    _q.setFromAxisAngle(_eixo, Math.atan2(a[o + 3] - a[o + 1], a[o + 2] - a[o]));
    _s.set(Math.max(L + w * 0.35 * frac, 0.001), h, w);
    _m.compose(_p, _q, _s); alvo.setMatrixAt(k, _m);
  }
  function matrizes(alvo, de, ate) {
    for (let i = de, k = 0; i < ate; i++, k++) umaMatriz(alvo, k, i);
    alvo.instanceMatrix.needsUpdate = true;
  }

  function pinta(alvo, de, ate) {
    const c = new THREE.Color();
    for (let i = de, k = 0; i < ate; i++, k++) alvo.setColorAt(k, corDe(D.seg[i * 9 + 7], c));
    if (alvo.instanceColor) alvo.instanceColor.needsUpdate = true;
  }

  // TP2 (central/toolpath.py, compacto): polilinhas fiéis ao gcode -> 9 floats por filete
  function decodifica(buf) {
    const u8 = new Uint8Array(buf);
    if (!(u8[0] === 84 && u8[1] === 80 && u8[2] === 50 && u8[3] === 0)) return new Float32Array(buf);
    const dv = new DataView(buf), nt = dv.getUint32(4, true), n = dv.getUint32(8, true);
    const base = 12 + nt * 32;
    const xs = new Int16Array(buf, base, n), ys = new Int16Array(buf, base + n * 2, n), dc = new Uint16Array(buf, base + n * 4, n);
    const seg = new Float32Array(n * 9);
    let k = 0;
    for (let r = 0; r < nt; r++) {
      const o = 12 + r * 32;
      let x = dv.getFloat32(o, true), y = dv.getFloat32(o + 4, true);
      const z = dv.getFloat32(o + 8, true), w = dv.getFloat32(o + 12, true), h = dv.getFloat32(o + 16, true);
      let cmd = dv.getUint32(o + 20, true); const cnt = dv.getUint32(o + 24, true), t = dv.getUint8(o + 28);
      for (let j = 0; j < cnt; j++, k++) {
        const x1 = xs[k] / 100, y1 = ys[k] / 100; cmd += dc[k];
        const p = k * 9;
        seg[p] = x; seg[p + 1] = y; seg[p + 2] = x1; seg[p + 3] = y1; seg[p + 4] = z;
        seg[p + 5] = w; seg[p + 6] = h; seg[p + 7] = t; seg[p + 8] = cmd;
        x = x1; y = y1;
      }
    }
    return seg;
  }

  function monta(buf) {
    [malha, camadaMalha, fantasma].forEach(o => { if (o) { cena.remove(o); o.geometry !== geoFilete && o.geometry.dispose(); } });
    const bruto = decodifica(buf);
    let manter = 0; for (let i = 0; i < bruto.length / 9; i++) if (bruto[i * 9 + 7] !== 0) manter++;
    const seg = new Float32Array(manter * 9);
    for (let i = 0, k = 0; i < bruto.length / 9; i++) if (bruto[i * 9 + 7] !== 0) { seg.set(bruto.subarray(i * 9, i * 9 + 9), k * 9); k++; }
    const n = manter;
    // camadas pelo Z e o índice do primeiro filete de cada camada
    const zs = [], inicio = [], cmdFim = new Float64Array(n);
    let zAnt = -1;
    for (let i = 0; i < n; i++) {
      const z = seg[i * 9 + 4];
      if (Math.abs(z - zAnt) > 1e-4) { zs.push(z); inicio.push(i); zAnt = z; }
      cmdFim[i] = seg[i * 9 + 8];
    }
    inicio.push(n);
    const dIni = new Float64Array(n), dFim = new Float64Array(n);
    let acc = 0;
    for (let i = 0; i < n; i++) {
      const o = i * 9;
      if (i) acc += Math.hypot(seg[o] - seg[o - 7], seg[o + 1] - seg[o - 6]);   // viagem desde o fim do anterior
      dIni[i] = acc; acc += Math.hypot(seg[o + 2] - seg[o], seg[o + 3] - seg[o + 1]); dFim[i] = acc;
    }
    const caixa = new THREE.Box3();
    for (let i = 0; i < n; i++) { const o = i * 9; if (seg[o + 7] === 9) continue; caixa.expandByPoint(new THREE.Vector3(seg[o] - CENTRO, seg[o + 4], -(seg[o + 1] - CENTRO))); }
    D = { seg, n, zs, inicio, cmdFim, caixa, dIni, dFim };
    cabeca = -1; alvoD = 0; parcial = -1; camadaViva = -1;

    malha = new THREE.InstancedMesh(geoFilete, matFilete, n);
    malha.castShadow = malha.receiveShadow = true; malha.frustumCulled = false;
    matrizes(malha, 0, n); pinta(malha, 0, n);
    let maior = 1; for (let i = 0; i < zs.length; i++) maior = Math.max(maior, inicio[i + 1] - inicio[i]);
    camadaMalha = new THREE.InstancedMesh(geoFilete, matCamada, maior);
    camadaMalha.castShadow = true; camadaMalha.frustumCulled = false; camadaMalha.count = 0;

    // fantasma: o que ainda falta, em linhas finas translúcidas
    const pos = new Float32Array(n * 6);
    for (let i = 0; i < n; i++) { const o = i * 9; pos.set([seg[o] - CENTRO, seg[o + 4], -(seg[o + 1] - CENTRO), seg[o + 2] - CENTRO, seg[o + 4], -(seg[o + 3] - CENTRO)], i * 6); }
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    fantasma = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x8fa3bf, transparent: true, opacity: 0.07, depthWrite: false }));
    cena.add(fantasma, malha, camadaMalha);
    ultimaCamadaMontada = -1; ultimoN = -1;
    if (!enquadrado) { vista("iso"); enquadrado = true; }
    aplica();
  }

  // quantos filetes já saíram do bico (busca binária no índice de comando)
  function impressos() {
    if (!D) return 0;
    let lo = 0, hi = D.n;
    while (lo < hi) { const m = (lo + hi) >> 1; if (D.cmdFim[m] <= progresso) lo = m + 1; else hi = m; }
    return lo;
  }
  function camadaDe(i) {
    let lo = 0, hi = D.zs.length - 1;
    while (lo < hi) { const m = (lo + hi + 1) >> 1; if (D.inicio[m] <= i) lo = m; else hi = m - 1; }
    return lo;
  }

  // ---- animação do bico: a "cabeça" anda em mm pelo caminho, perseguindo o progresso real ----
  let cabeca = -1, alvoD = 0, vel = 20, tAlvo = 0, parcial = -1, camadaViva = -1;
  function segEm(d) {            // último filete cujo começo já passou de d
    let lo = 0, hi = D.n - 1;
    while (lo < hi) { const m = (lo + hi + 1) >> 1; if (D.dIni[m] <= d) lo = m; else hi = m - 1; }
    return lo;
  }
  function novoAlvo() {
    const feitos = impressos();
    const d = feitos ? D.dFim[feitos - 1] : 0, t = performance.now() / 1000;
    if (tAlvo && d > alvoD) vel = 0.6 * vel + 0.4 * Math.max(2, (d - alvoD) / (t - tAlvo));
    if (d !== alvoD) { alvoD = d; tAlvo = t; }
    if (cabeca < 0 || d < cabeca || d - cabeca > vel * 12) cabeca = Math.max(0, d - vel * 1.5);   // pulo grande: encosta
  }
  function montaCamada(L, inteira) {
    const ini = D.inicio[L], fim = D.inicio[L + 1];
    matrizes(camadaMalha, ini, fim); pinta(camadaMalha, ini, fim);
    camadaMalha.count = inteira ? fim - ini : 0;
    malha.count = soCamada ? 0 : ini;
    camadaViva = L; parcial = -1;
  }
  function quadroAoVivo(dt) {
    if (!D || !aoVivo) return;
    // anda na velocidade real, acelerando se ficou muito atrás
    const falta = alvoD - cabeca;
    // mantém o bico uns 2 s atrás do real, variando a velocidade suavemente (sem parar e arrancar)
    cabeca = Math.min(alvoD, cabeca + vel * Math.min(4, Math.max(0.3, falta / (vel * 2))) * dt);
    const i = segEm(cabeca), o = i * 9;
    const L = camadaDe(i);
    if (L !== camadaViva) montaCamada(L, false);
    const ini = D.inicio[L];
    let frac = 0, px, py;
    if (cabeca < D.dIni[i]) frac = 0;
    else frac = Math.min(1, (cabeca - D.dIni[i]) / Math.max(1e-6, D.dFim[i] - D.dIni[i]));
    if (cabeca >= D.dIni[i]) { px = D.seg[o] + (D.seg[o + 2] - D.seg[o]) * frac; py = D.seg[o + 1] + (D.seg[o + 3] - D.seg[o + 1]) * frac; }
    else { px = D.seg[o]; py = D.seg[o + 1]; }
    // filetes completos + o atual crescendo
    if (parcial >= 0 && parcial !== i - ini) umaMatriz(camadaMalha, parcial, ini + parcial);
    umaMatriz(camadaMalha, i - ini, i, Math.max(frac, 0.001));
    parcial = i - ini;
    camadaMalha.count = i - ini + (frac > 0 ? 1 : 0);
    camadaMalha.instanceMatrix.needsUpdate = true;
    fantasma.geometry.setDrawRange(i * 2, (D.n - i) * 2);
    bico.position.set(px - CENTRO, D.seg[o + 4], -(py - CENTRO));
    brilho.intensity = cabeca < alvoD + 1 && alvoD < D.dFim[D.n - 1] ? 40 : 0;
    if (L !== ultimaCamadaMontada) { ultimaCamadaMontada = L; aoMudar && aoMudar({ camada: L, camadas: D.zs.length, z: D.zs[L], aoVivo, camAtual: L }); }
  }

  function aplica() {
    sujo = true; renderer.shadowMap.needsUpdate = true;
    if (!D) return;
    novoAlvo();
    const planos = corte ? [plano] : [];
    matFilete.clippingPlanes = planos; matCamada.clippingPlanes = planos; fantasma.material.clippingPlanes = planos;
    fantasma.visible = !soCamada;
    const camAtual = camadaDe(segEm(Math.max(0, alvoD - 1e-6)));
    if (aoVivo) {
      malha.count = soCamada ? 0 : D.inicio[camadaViva < 0 ? 0 : camadaViva];
      bico.visible = true;
      aoMudar && aoMudar({ camada: camadaViva < 0 ? camAtual : camadaViva, camadas: D.zs.length, z: D.zs[camadaViva < 0 ? camAtual : camadaViva], aoVivo, camAtual });
      return;
    }
    const L = camadaVer;
    montaCamada(L, true);
    fantasma.geometry.setDrawRange(D.inicio[L + 1] * 2, (D.n - D.inicio[L + 1]) * 2);
    brilho.intensity = 0; bico.visible = !soCamada;
    const o = (D.inicio[L + 1] - 1) * 9; bico.position.set(D.seg[o + 2] - CENTRO, D.seg[o + 4], -(D.seg[o + 3] - CENTRO));
    ultimaCamadaMontada = -1;
    aoMudar && aoMudar({ camada: L, camadas: D.zs.length, z: D.zs[L], aoVivo, camAtual });
  }

  function vista(tipo) {
    if (!D) return;
    const c = new THREE.Vector3(), s = new THREE.Vector3(); D.caixa.getCenter(c); D.caixa.getSize(s);
    const r = Math.max(s.x, s.y, s.z, 20);
    ctl.target.copy(c);
    if (tipo === "topo") cam.position.set(c.x, c.y + r * 2.6, c.z + 0.01);
    else if (tipo === "frente") cam.position.set(c.x, c.y + r * 0.3, c.z + r * 2.6);
    else cam.position.set(c.x + r * 1.5, c.y + r * 1.35, c.z + r * 1.9);
    sol.target.position.copy(c); sol.position.set(c.x - 80, 160, c.z + 120);
    ctl.update(); sujo = true; renderer.shadowMap.needsUpdate = true;
  }

  // Desenha só quando precisa (antes: 60 quadros/s sempre, até com a aba escondida, e com 1 milhão de
  // filetes isso travava a página). Mexer na câmera, chegar progresso novo ou mudar opção marca "sujo";
  // o bico ao vivo anda a FPS_VIVO enquanto ainda está atrás do real; a sombra se recalcula a cada SOMBRA_MS.
  const FPS_VIVO = 12, SOMBRA_MS = 2000;
  let ultimoVivo = 0, sombraEm = 0, estavaVisivel = false;
  renderer.shadowMap.autoUpdate = false;
  ctl.addEventListener("change", () => { sujo = true; });
  document.addEventListener("visibilitychange", () => { sujo = true; });
  (function anima(t) {
    requestAnimationFrame(anima);
    t = t ?? performance.now();
    if (document.hidden || renderer.domElement.offsetParent === null) { estavaVisivel = false; return; }   // aba escondida: nada
    if (!estavaVisivel) { estavaVisivel = true; ajusta(); sujo = true; }   // voltou para a aba: acerta o tamanho
    ctl.update();
    const vivo = D && aoVivo && cabeca < alvoD && t - ultimoVivo >= 1000 / FPS_VIVO;
    if (vivo || (D && aoVivo && camadaViva < 0)) { quadroAoVivo(Math.min(0.2, (t - (ultimoVivo || t)) / 1000)); ultimoVivo = t; sujo = true; }
    if (!sujo) return;
    if (t - sombraEm > SOMBRA_MS) { renderer.shadowMap.needsUpdate = true; sombraEm = t; }
    renderer.render(cena, cam); sujo = false;
  })();

  let arquivo = null;
  return {
    async carrega(arq, cor) {
      if (arq === arquivo) return; arquivo = arq; enquadrado = false;
      if (cor) corFil.set(cor);
      const r = await fetch("/api/toolpath?a=" + encodeURIComponent(arq));
      if (!r.ok) throw new Error("sem caminho para " + arq);
      monta(await r.arrayBuffer());
    },
    progresso(cmd) { if (cmd !== progresso) { progresso = cmd; aplica(); } },
    camada(n) { aoVivo = false; camadaVer = Math.max(0, Math.min(n, (D?.zs.length || 1) - 1)); aplica(); },
    aoVivo() { aoVivo = true; camadaVer = null; camadaViva = -1; aplica(); },
    soCamada(v) { soCamada = v; camadaViva = -1; aplica(); },
    corte(v) { corte = v; aplica(); },
    cores(m) { modoCor = m; if (D) { pinta(malha, 0, D.n); camadaViva = -1; aplica(); } },
    vista,
    legenda() { return NOMES.map((n, i) => ({ nome: n, cor: "#" + CORES_TIPO[i].toString(16).padStart(6, "0") })); },
    tiposUsados() { if (!D) return []; const u = new Set(); for (let i = 0; i < D.n; i++) u.add(D.seg[i * 9 + 7]); return [...u].sort((a, b) => a - b); },
  };
}
