// Aba "Modelos": grade com os arquivos baixados e um visualizador 3D com medidas e a mesa da Ender-3 em escala.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const MESA = 220;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const kb = b => b > 1048576 ? (b / 1048576).toFixed(1) + " MB" : Math.round(b / 1024) + " KB";
const dia = t => new Date(t * 1000).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });

let viewer = null;

function criaViewer(box) {
  const r = new THREE.WebGLRenderer({ antialias: true });
  r.setPixelRatio(Math.min(devicePixelRatio, 2)); r.toneMapping = THREE.ACESFilmicToneMapping; r.outputColorSpace = THREE.SRGBColorSpace;
  box.prepend(r.domElement);
  const cena = new THREE.Scene(); cena.background = new THREE.Color(0x14171b);
  cena.environment = new THREE.PMREMGenerator(r).fromScene(new RoomEnvironment(), 0.04).texture;
  const cam = new THREE.PerspectiveCamera(35, 1, 1, 3000);
  const ctl = new OrbitControls(cam, r.domElement); ctl.enableDamping = true; ctl.autoRotate = true; ctl.autoRotateSpeed = 0.8;
  const sol = new THREE.DirectionalLight(0xffffff, 1.3); sol.position.set(-80, 160, 120); cena.add(sol);
  cena.add(new THREE.HemisphereLight(0xdfe8ff, 0x20242a, 0.4));
  const mesa = new THREE.Mesh(new THREE.BoxGeometry(MESA, 2, MESA), new THREE.MeshStandardMaterial({ color: 0x1c1f23, roughness: 0.9 }));
  mesa.position.y = -1; cena.add(mesa);
  const grade = new THREE.GridHelper(MESA, 22, 0x3a4250, 0x2a3038); grade.position.y = 0.02; cena.add(grade);
  let malha = null;
  const mat = new THREE.MeshStandardMaterial({ color: 0xff8a3d, roughness: 0.5, metalness: 0.05 });
  function ajusta() { const w = box.clientWidth, h = box.clientHeight; if (!w || !h) return; r.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); }
  addEventListener("resize", ajusta);
  (function anima() { requestAnimationFrame(anima); ctl.update(); r.render(cena, cam); })();
  return {
    ajusta,
    mostra(geo) {
      if (malha) { cena.remove(malha); malha.geometry.dispose(); }
      geo.rotateX(-Math.PI / 2); geo.computeBoundingBox();
      const b = geo.boundingBox, c = new THREE.Vector3(); b.getCenter(c);
      geo.translate(-c.x, -b.min.y, -c.z); geo.computeVertexNormals(); geo.computeBoundingBox();
      const s = new THREE.Vector3(); geo.boundingBox.getSize(s);
      malha = new THREE.Mesh(geo, mat); cena.add(malha);
      const R = Math.max(s.x, s.y, s.z, 20);
      cam.position.set(R * 1.4, R * 1.2, R * 1.8); ctl.target.set(0, s.y * 0.4, 0); ctl.update(); ajusta();
      return { x: s.x, y: s.z, z: s.y };   // largura, profundidade, altura (mm)
    },
  };
}

async function abre(m) {
  $("mvTitulo").textContent = m.nome;
  $("mvInfo").textContent = "carregando...";
  $("mvBox").parentElement.style.display = "block";
  if (!viewer) viewer = criaViewer($("mvBox"));
  viewer.ajusta();
  $("mvBox").scrollIntoView({ behavior: "smooth", block: "nearest" });
  try {
    const buf = await (await fetch("/api/modelo/stl?id=" + m.id)).arrayBuffer();
    if (!buf.byteLength) throw new Error("vazio");
    const d = viewer.mostra(new STLLoader().parse(buf));
    const cabe = d.x <= MESA && d.y <= MESA && d.z <= 250;
    $("mvInfo").innerHTML = `${d.x.toFixed(1)} × ${d.y.toFixed(1)} × ${d.z.toFixed(1)} mm · ${cabe ? "cabe na Ender-3" : "<b style='color:#ef5a5a'>não cabe na mesa</b>"} · ${esc(m.arquivo)} (${m.pasta})`;
  } catch {
    $("mvInfo").textContent = "não consegui abrir este arquivo em 3D";
  }
}

export async function carregaModelos() {
  const lista = await (await fetch("/api/modelos")).json();
  $("mGrade").innerHTML = lista.map((m, i) => `
    <button class="mcard" data-i="${i}">
      <div class="mthumb">${m.tem_miniatura ? `<img loading="lazy" src="/api/modelo/mini?id=${m.id}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('span'),{textContent:'3D'}))">` : "<span>STL</span>"}</div>
      <div class="mnome">${esc(m.nome)}</div>
      <div class="mmeta">${dia(m.data)} · ${kb(m.tamanho)}</div>
    </button>`).join("");
  $("mTotal").textContent = `${lista.length} modelos`;
  document.querySelectorAll(".mcard").forEach(b => b.onclick = () => {
    document.querySelectorAll(".mcard").forEach(x => x.classList.remove("on")); b.classList.add("on");
    abre(lista[+b.dataset.i]);
  });
}
