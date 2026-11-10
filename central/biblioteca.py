"""Biblioteca de modelos: lista os .3mf/.stl/.obj baixados, devolve miniatura e STL para a vista 3D.

Pastas lidas: ~/Downloads (só o primeiro nível) e modelos/ do projeto (recursivo).
Cada arquivo ganha um id estável (hash do caminho); o navegador só pede por id, nunca por caminho.
"""
import hashlib, json, os, re, subprocess, threading, zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTAS = [(os.path.expanduser("~/Downloads"), False), (os.path.join(RAIZ, "modelos"), True)]
EXT = (".3mf", ".stl", ".obj")
CACHE = os.path.join(RAIZ, ".cache")
PRUSA = "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"
PERFIL = os.path.join(RAIZ, "ender3_pla.ini")
ARQ_TEMPOS = os.path.join(CACHE, "tempos.json")
RE_TEMPO = re.compile(r"estimated printing time \(normal mode\) = (.+)")
RE_FIL = re.compile(r"filament used \[mm\] = ([\d.]+)")
_trava_tempos = threading.Lock()


def _id(p):
    return hashlib.sha1(p.encode()).hexdigest()[:12]


def lista():
    vistos, out = set(), []
    for pasta, rec in PASTAS:
        if not os.path.isdir(pasta):
            continue
        andar = os.walk(pasta) if rec else [(pasta, [], os.listdir(pasta))]
        for raiz, _, arqs in andar:
            for a in arqs:
                p = os.path.join(raiz, a)
                if not a.lower().endswith(EXT) or not os.path.isfile(p) or a == "corte.stl":
                    continue
                st = os.stat(p)
                chave = (a.lower(), st.st_size)
                if chave in vistos:          # mesmo arquivo copiado para modelos/
                    continue
                vistos.add(chave)
                out.append({"id": _id(p), "nome": _bonito(a), "arquivo": a, "pasta": os.path.basename(raiz),
                            "tamanho": st.st_size, "data": st.st_mtime, "tem_miniatura": a.lower().endswith(".3mf")})
    tempos = _le_tempos()
    for m in out:
        t = tempos.get(_chave_tempo(m))
        if t:
            m.update(tempo_s=t.get("s"), filamento_m=t.get("m"), tempo_erro=t.get("erro"))
    return sorted(out, key=lambda x: -x["data"])


def _chave_tempo(m):
    return f"{m['id']}_{int(m['data'])}"


def _le_tempos():
    try:
        return json.load(open(ARQ_TEMPOS))
    except (OSError, ValueError):
        return {}


def _segundos(txt):
    """'2h 35m 36s' ou '1d 2h 3m 4s' -> segundos."""
    mult = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    return sum(int(n) * mult[u] for n, u in re.findall(r"(\d+)([dhms])", txt))


def _fatia(p):
    """Fatia com o perfil da Ender-3 só para ler o tempo estimado; o G-code vai para um arquivo temporário."""
    os.makedirs(CACHE, exist_ok=True)
    tmp = os.path.join(CACHE, "_tempo.gcode")
    try:
        r = subprocess.run([PRUSA, "--export-gcode", "--load", PERFIL, "--center", "110,110", "-o", tmp, p],
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return {"erro": "fatiar demorou demais"}
    if r.returncode != 0 or not os.path.exists(tmp):
        return {"erro": "não fatiou (talvez não caiba na mesa)"}
    with open(tmp, errors="ignore") as f:
        txt = f.read()
    os.remove(tmp)
    t, fil = RE_TEMPO.search(txt), RE_FIL.search(txt)
    if not t:
        return {"erro": "sem estimativa"}
    return {"s": _segundos(t.group(1)), "m": round(float(fil.group(1)) / 1000, 1) if fil else None}


def preenche_tempos():
    """Em segundo plano: estima o tempo de cada modelo ainda sem estimativa (um por vez, com cache em disco)."""
    with _trava_tempos:
        for m in lista():
            chave = _chave_tempo(m)
            if chave in _le_tempos():
                continue
            p = caminho(m["id"])
            if not p:
                continue
            res = _fatia(p)
            tempos = _le_tempos()
            tempos[chave] = res
            with open(ARQ_TEMPOS + ".tmp", "w") as f:
                json.dump(tempos, f)
            os.replace(ARQ_TEMPOS + ".tmp", ARQ_TEMPOS)


def _bonito(a):
    n = os.path.splitext(a)[0]
    for ext in (".stl", ".3mf"):
        n = n.replace(ext, "")
    return n.replace("+", " ").replace("_", " ").strip()


def caminho(id_):
    for pasta, rec in PASTAS:
        if not os.path.isdir(pasta):
            continue
        andar = os.walk(pasta) if rec else [(pasta, [], os.listdir(pasta))]
        for raiz, _, arqs in andar:
            for a in arqs:
                p = os.path.join(raiz, a)
                if a.lower().endswith(EXT) and _id(p) == id_:
                    return p
    return None


def miniatura(id_):
    p = caminho(id_)
    if not p or not p.lower().endswith(".3mf"):
        return None
    try:
        with zipfile.ZipFile(p) as z:
            nomes = z.namelist()
            for alvo in ("Metadata/plate_1.png", "Metadata/thumbnail.png", "Metadata/top_1.png"):
                if alvo in nomes:
                    return z.read(alvo)
            pngs = [n for n in nomes if n.lower().endswith(".png") and "thumbnail" in n.lower()]
            return z.read(pngs[0]) if pngs else None
    except (zipfile.BadZipFile, OSError):
        return None


def stl(id_):
    """STL do modelo inteiro (3MF e OBJ convertidos pelo PrusaSlicer, com cache)."""
    p = caminho(id_)
    if not p:
        return None
    if p.lower().endswith(".stl"):
        return open(p, "rb").read()
    os.makedirs(CACHE, exist_ok=True)
    destino = os.path.join(CACHE, f"{id_}_{int(os.path.getmtime(p))}.stl")
    if not os.path.exists(destino):
        r = subprocess.run([PRUSA, "--export-stl", "-o", destino, p], capture_output=True, timeout=120)
        if r.returncode != 0 or not os.path.exists(destino):
            return None
    return open(destino, "rb").read()
