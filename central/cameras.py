"""Câmeras do Mac ligáveis pela central: lista os dispositivos de vídeo do AVFoundation e mantém um ffmpeg
por câmera ligada, gravando o quadro mais recente em cams/<id>.jpg (1 quadro por segundo).

A câmera é identificada pelo nome (o índice muda quando um iPhone conecta ou desconecta). As câmeras ligadas
ficam em central/cameras_ativas.json e voltam a abrir quando a central reinicia, se estiverem disponíveis.
"""
import hashlib, json, os, re, shutil, subprocess, threading, time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "cams")
ARQ_ATIVAS = os.path.join(RAIZ, "central", "cameras_ativas.json")
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
IGNORAR = ("Capture screen",)
RE_DISP = re.compile(r"\[(\d+)\] (.+)$")

_trava = threading.Lock()
_procs = {}            # id -> Popen
_cache = {"t": 0, "lista": []}


def _id(nome):
    return hashlib.sha1(nome.encode()).hexdigest()[:10]


def dispositivos():
    """[(id, nome)] das câmeras de vídeo vistas agora (cache de 10 s)."""
    if time.time() - _cache["t"] < 10:
        return _cache["lista"]
    try:
        saida = subprocess.run([FFMPEG, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                               capture_output=True, text=True, timeout=15).stderr
    except (OSError, subprocess.TimeoutExpired):
        return _cache["lista"]
    lista, video = [], False
    for linha in saida.splitlines():
        if "video devices" in linha:
            video = True; continue
        if "audio devices" in linha:
            break
        m = RE_DISP.search(linha)
        if video and m and not m.group(2).startswith(IGNORAR):
            lista.append((_id(m.group(2).strip()), m.group(2).strip()))
    _cache.update(t=time.time(), lista=lista)
    return lista


def _salva_ativas():
    nomes = sorted(n for i, n in dispositivos() if i in _procs)
    with open(ARQ_ATIVAS, "w") as f:
        json.dump(nomes, f, ensure_ascii=False)


def imagem(id_):
    p = os.path.join(PASTA, f"{id_}.jpg")
    return p if re.fullmatch(r"[0-9a-f]{10}", id_ or "") and os.path.exists(p) else None


def ligar(id_):
    nomes = dict(dispositivos())
    if id_ not in nomes:
        return "câmera não disponível"
    with _trava:
        p = _procs.get(id_)
        if p and p.poll() is None:
            return None
        os.makedirs(PASTA, exist_ok=True)
        log = open(os.path.join(PASTA, f"{id_}.log"), "w")
        _procs[id_] = subprocess.Popen(
            [FFMPEG, "-hide_banner", "-loglevel", "error", "-f", "avfoundation", "-framerate", "30", "-pixel_format", "nv12",
             "-i", f"{nomes[id_]}:none", "-vf", "fps=1,scale='min(1280,iw)':-2", "-q:v", "5",
             "-update", "1", "-y", os.path.join(PASTA, f"{id_}.jpg")],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=log, start_new_session=True)
        _salva_ativas()
    return None


def desligar(id_):
    with _trava:
        p = _procs.pop(id_, None)
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(5)
            except subprocess.TimeoutExpired:
                p.kill()
        _salva_ativas()


def estado():
    agora, out = time.time(), []
    for id_, nome in dispositivos():
        p = _procs.get(id_)
        viva = bool(p and p.poll() is None)
        img = imagem(id_)
        erro = None
        if p and not viva:
            try:
                erro = open(os.path.join(PASTA, f"{id_}.log")).read().strip().splitlines()[-1][:160]
            except (OSError, IndexError):
                erro = "a câmera fechou"
        out.append({"id": id_, "nome": nome, "ativa": viva, "erro": erro,
                    "idade": round(agora - os.path.getmtime(img), 1) if img else None})
    return out


def restaura():
    """Reabre as câmeras que estavam ligadas, se continuarem disponíveis."""
    subprocess.run(["pkill", "-f", f"{PASTA}/[0-9a-f]+\\.jpg"], capture_output=True)   # ffmpeg órfão de uma central anterior
    try:
        nomes = set(json.load(open(ARQ_ATIVAS)))
    except (OSError, ValueError):
        return
    for id_, nome in dispositivos():
        if nome in nomes:
            ligar(id_)
