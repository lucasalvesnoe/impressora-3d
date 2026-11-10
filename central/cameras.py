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
CABO = os.path.join(RAIZ, "scripts", "iphone_cabo")      # iPhone por cabo, lido pela tela (scripts/iphone_cabo.swift)
SUFIXO_CABO = " (cabo, tela)"
RE_DISP = re.compile(r"\[(\d+)\] (.+)$")

_trava = threading.Lock()
_procs = {}            # id -> Popen
_cache = {"t": 0, "lista": []}
_desejadas = set()     # nomes de dispositivo que o usuário deixou ligados; voltam sozinhos ao reaparecer
VIGIA_S = 10

# Nome de tela por dispositivo. Vale o "apelidos" do cameras.json; sem ele, estes padrões.
APELIDOS = {
    "Câmera FaceTime HD": "MacBook Pro (câmera embutida)",
    "Câmera do iPhone": "iPhone por Continuidade",
    "Câmera da Visualização da Mesa iPhone": "iPhone por Continuidade (vista da mesa)",
}


def apelido(nome):
    try:
        extra = json.load(open(os.path.join(RAIZ, "cameras.json"))).get("apelidos", {})
    except (OSError, ValueError):
        extra = {}
    if nome in extra:
        return extra[nome]
    if nome in APELIDOS:
        return APELIDOS[nome]
    if nome.endswith(SUFIXO_CABO):
        return "iPhone velho pelo cabo"
    return nome


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
    lista += [(_id(n), n) for n in _iphones_cabo()]
    _cache.update(t=time.time(), lista=lista)
    return lista


def _iphones_cabo():
    """iPhones ligados por cabo cuja tela o Mac consegue ler (app Câmera aberto = câmera da impressora)."""
    if not os.access(CABO, os.X_OK):
        return []
    try:
        r = subprocess.run([CABO, "--lista"], capture_output=True, text=True, timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [l.strip() + SUFIXO_CABO for l in r.stdout.splitlines() if l.strip()]


def _salva_ativas():
    """Grava o que o usuário quer ligado, mesmo que o aparelho tenha sumido agora (cabo solto, iPhone longe).
    Antes gravava só o que estava rodando, e uma câmera desconectada era esquecida de vez."""
    with open(ARQ_ATIVAS, "w") as f:
        json.dump(sorted(_desejadas), f, ensure_ascii=False)


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
        destino = os.path.join(PASTA, f"{id_}.jpg")
        if nomes[id_].endswith(SUFIXO_CABO):
            try:   # iPhone deitado: "iphone_cabo_giro" em cameras.json (0, 90 ou -90)
                giro = str(json.load(open(os.path.join(RAIZ, "cameras.json"))).get("iphone_cabo_giro", 0))
            except (OSError, ValueError):
                giro = "0"
            cmd = [CABO, destino, "0.0705", "0.821", giro]
        else:
            cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-f", "avfoundation", "-framerate", "30", "-pixel_format", "nv12",
             "-i", f"{nomes[id_]}:none", "-vf", "fps=1,scale='min(1280,iw)':-2", "-q:v", "5",
             "-update", "1", "-y", destino]
        _procs[id_] = subprocess.Popen(
            cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=log, start_new_session=True)
        _desejadas.add(nomes[id_])
        _salva_ativas()
    return None


def desligar(id_):
    with _trava:
        for nome in [n for n in _desejadas if _id(n) == id_]:
            _desejadas.discard(nome)
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
        out.append({"id": id_, "nome": apelido(nome), "dispositivo": nome, "ativa": viva,
                    "erro": erro if nome not in _desejadas or viva else "religando sozinha quando voltar",
                    "idade": round(agora - os.path.getmtime(img), 1) if img else None})
    vistos = {n for _, n in dispositivos()}
    for nome in sorted(_desejadas - vistos):   # ligada pelo usuário, mas o aparelho sumiu: mostra esperando
        id_ = _id(nome); img = imagem(id_)
        out.append({"id": id_, "nome": apelido(nome), "dispositivo": nome, "ativa": False,
                    "erro": "desconectada; volta sozinha quando o aparelho reaparecer",
                    "idade": round(agora - os.path.getmtime(img), 1) if img else None})
    return out


def restaura():
    """Reabre as câmeras que estavam ligadas e fica vigiando: se o aparelho cair (cabo solto) e voltar,
    a câmera religa sozinha."""
    subprocess.run(["pkill", "-f", f"{PASTA}/[0-9a-f]+\\.jpg"], capture_output=True)   # ffmpeg órfão de uma central anterior
    try:
        _desejadas.update(json.load(open(ARQ_ATIVAS)))
    except (OSError, ValueError):
        pass
    while True:
        try:
            for id_, nome in dispositivos():
                p = _procs.get(id_)
                if nome in _desejadas and not (p and p.poll() is None):
                    ligar(id_)
        except Exception:
            pass
        time.sleep(VIGIA_S)
