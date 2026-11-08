"""Biblioteca de modelos: lista os .3mf/.stl/.obj baixados, devolve miniatura e STL para a vista 3D.

Pastas lidas: ~/Downloads (só o primeiro nível) e modelos/ do projeto (recursivo).
Cada arquivo ganha um id estável (hash do caminho); o navegador só pede por id, nunca por caminho.
"""
import hashlib, os, subprocess, zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTAS = [(os.path.expanduser("~/Downloads"), False), (os.path.join(RAIZ, "modelos"), True)]
EXT = (".3mf", ".stl", ".obj")
CACHE = os.path.join(RAIZ, ".cache")
PRUSA = "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"


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
    return sorted(out, key=lambda x: -x["data"])


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
