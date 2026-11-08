"""Central da impressora: serve central/index.html e a API de estado.

Roda da pasta impressora-3d:  python3 central/server.py   ->  http://localhost:8090
Só lê arquivos (progresso.txt, status.json, imagens, gcode, stl). Nunca abre a porta serial.
"""
import json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolpath
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = 8090
_tok = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".token")
TOKEN = os.environ.get("CENTRAL_TOKEN") or (open(_tok).read().strip() if os.path.exists(_tok) else "")
IMAGENS = {"frente": "latest_full.jpg", "bico": "bico.jpg", "cima": "cam2/cam2.jpg", "painel": "painel.jpg"}
RE_TEMPO = re.compile(r"(?:(\d+)d\s*)?(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?")
_cache = {}


def caminho(rel):
    return os.path.join(RAIZ, rel)


def modelos():
    try:
        return json.load(open(caminho("central/modelos.json")))
    except Exception:
        return {}


def segundos(txt):
    m = RE_TEMPO.search(txt.strip())
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def analisa_gcode(nome):
    """Mapa índice de comando (como o imprime.py conta) -> camada e Z; mais metadados do cabeçalho."""
    p = caminho(nome)
    chave = (p, os.path.getmtime(p))
    if chave in _cache:
        return _cache[chave]
    z_por_cmd, camadas, z, n = [], [], 0.0, 0
    info = {"tempo_est": None, "filamento_mm": None, "filamento_g": None, "altura_camada": None,
            "bico_alvo": None, "mesa_alvo": None}
    for bruta in open(p, errors="replace"):
        if bruta.startswith(";Z:"):
            z = float(bruta[3:]); camadas.append(z)
        elif bruta.startswith("; estimated printing time (normal"):
            info["tempo_est"] = segundos(bruta.split("=", 1)[1])
        elif bruta.startswith("; filament used [mm]"):
            info["filamento_mm"] = float(bruta.split("=")[1])
        elif bruta.startswith("; filament used [g]"):
            info["filamento_g"] = float(bruta.split("=")[1])
        elif bruta.startswith("; layer_height ="):
            info["altura_camada"] = float(bruta.split("=")[1])
        cmd = bruta.split(";")[0].strip()
        if not cmd:
            continue
        if info["bico_alvo"] is None and cmd.startswith(("M104", "M109")) and " S" in cmd:
            info["bico_alvo"] = float(cmd.split(" S")[1].split()[0])
        if info["mesa_alvo"] is None and cmd.startswith(("M140", "M190")) and " S" in cmd:
            info["mesa_alvo"] = float(cmd.split(" S")[1].split()[0])
        z_por_cmd.append((len(camadas), z))
        n += 1
    res = {"z_por_cmd": z_por_cmd, "camadas": len(camadas), "z_max": max(camadas) if camadas else 0, **info}
    _cache.clear(); _cache[chave] = res
    return res


def processo_ativo():
    try:
        out = subprocess.run(["pgrep", "-fl", "imprime.py"], capture_output=True, text=True).stdout
        for l in out.splitlines():
            partes = l.split()
            if "imprime.py" in l and partes[-1].endswith(".gcode"):
                return os.path.basename(partes[-1])
    except Exception:
        pass
    return None


def inicio_processo():
    """Hora de início do imprime.py em execução, pelo etime do ps (formato [[dd-]hh:]mm:ss)."""
    try:
        pid = subprocess.run(["pgrep", "-f", "imprime.py"], capture_output=True, text=True).stdout.split()[0]
        et = subprocess.run(["ps", "-o", "etime=", "-p", pid], capture_output=True, text=True).stdout.strip()
        dias, _, resto = et.rpartition("-")
        partes = [int(x) for x in resto.split(":")]
        while len(partes) < 3:
            partes.insert(0, 0)
        h, m, s = partes
        return time.time() - ((int(dias) if dias else 0) * 86400 + h * 3600 + m * 60 + s)
    except Exception:
        return None


def ler_json(rel):
    try:
        return json.load(open(caminho(rel)))
    except Exception:
        return {}


def registro(ativo, arquivo, inicio, i, total):
    linhas = []
    if inicio:
        linhas.append(f"{time.strftime('%H:%M', time.localtime(inicio))} início de {arquivo}")
    if ativo:
        linhas.append(f"{time.strftime('%H:%M')} enviando linha {i} de {total}")
    try:
        linhas += [l for l in open(caminho("imprime.log")).read().strip().splitlines()[-4:] if l]
    except Exception:
        pass
    for nome, v in ler_json("cams.json").items():
        if not v.get("ok", True):
            linhas.append(f"câmera {nome}: {v.get('motivo')}")
    return linhas


def estado():
    ativo = processo_ativo()
    st = {}
    try:
        st = json.load(open(caminho("status.json")))
    except Exception:
        pass
    arquivo = ativo or st.get("arquivo")
    try:
        prog = open(caminho("progresso.txt")).read().strip()
        i, resto = prog.split("/", 1); total = int(resto.split()[0]); i = int(i)
        linha = resto.split(" ", 1)[1] if " " in resto else ""
    except Exception:
        i, total, linha = 0, 1, ""
    # status.json só vale se for desta impressão; senão, início = criação do imprime.log
    if st.get("arquivo") and arquivo and os.path.basename(st["arquivo"]) != os.path.basename(arquivo):
        st = {}
    inicio = st.get("inicio") or inicio_processo()
    g = {}
    if arquivo and os.path.exists(caminho(arquivo)):
        g = analisa_gcode(arquivo)
    camada, z = (0, 0.0)
    if g and 0 < i <= len(g["z_por_cmd"]):
        camada, z = g["z_por_cmd"][i - 1]
    agora = time.time()
    fim = st.get("fim")
    decorrido = ((fim or agora) - inicio) if inicio else None
    frac = i / max(total, 1)
    restante = None
    if g.get("tempo_est"):
        restante = max(0, g["tempo_est"] * (1 - frac))
        if decorrido and frac > 0.15:  # depois de 15%, mistura com o ritmo real
            restante = 0.5 * restante + 0.5 * decorrido * (1 - frac) / frac
    meta = modelos().get(os.path.basename(arquivo or ""), {})
    return {
        "arquivo": arquivo, "imprimindo": bool(ativo), "nome": meta.get("nome", arquivo), "cor": meta.get("cor", "#d9d9d9"),
        "tem_modelo": bool(meta.get("stl")), "linha": i, "total": total, "cmd": linha, "frac": frac,
        "camada": camada, "camadas": g.get("camadas"), "z": z, "z_max": g.get("z_max"),
        "inicio": inicio, "decorrido": decorrido, "restante": None if not ativo else restante,
        "tempo_est": g.get("tempo_est"), "filamento_mm": g.get("filamento_mm"), "filamento_g": g.get("filamento_g"),
        "bico": st.get("bico"), "bico_alvo": st.get("bico_alvo") or g.get("bico_alvo"),
        "mesa": st.get("mesa"), "mesa_alvo": st.get("mesa_alvo") or g.get("mesa_alvo"),
        "temp_idade": (agora - st["temp_em"]) if st.get("temp_em") else None,
        "imagens": {k: (os.path.getmtime(caminho(v)) if os.path.exists(caminho(v)) else None) for k, v in IMAGENS.items()},
        "log": registro(ativo, arquivo, inicio, i, total),
        "saude": ler_json("cams.json"),
        "agora": agora,
    }


def fila():
    """Gcodes da pasta com nome e tempo estimado, para a lista lateral."""
    out = []
    for nome, meta in modelos().items():
        if os.path.exists(caminho(nome)):
            g = analisa_gcode_leve(nome)
            out.append({"arquivo": nome, "nome": meta.get("nome", nome), "cor": meta.get("cor"), "tempo_est": g})
    return out


def analisa_gcode_leve(nome):
    with open(caminho(nome), errors="replace") as f:
        for l in f:
            if l.startswith("; estimated printing time (normal"):
                return segundos(l.split("=", 1)[1])
    # cabeçalho no fim do arquivo (PrusaSlicer grava lá)
    with open(caminho(nome), "rb") as f:
        f.seek(max(0, os.path.getsize(caminho(nome)) - 60000))
        for l in f.read().decode(errors="replace").splitlines():
            if l.startswith("; estimated printing time (normal"):
                return segundos(l.split("=", 1)[1])
    return None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def envia(self, corpo, tipo, codigo=200):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers(); self.wfile.write(corpo)

    def autorizado(self):
        """Acesso pela internet (túnel do Cloudflare) exige o token; rede local passa direto."""
        if not TOKEN or "Cf-Connecting-Ip" not in self.headers:
            return True
        from urllib.parse import parse_qs, urlparse
        if parse_qs(urlparse(self.path).query).get("k", [""])[0] == TOKEN:
            return "url"
        return f"k={TOKEN}" in (self.headers.get("Cookie") or "")

    def do_GET(self):
        rota = self.path.split("?")[0]
        ok = self.autorizado()
        if not ok:
            return self.envia("acesso negado: abra o link com ?k=...".encode(), "text/plain; charset=utf-8", 403)
        if ok == "url":   # grava o cookie e tira o token da barra de endereço
            self.send_response(302)
            self.send_header("Set-Cookie", f"k={TOKEN}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax")
            self.send_header("Location", rota); self.end_headers(); return
        try:
            if rota in ("/", "/index.html"):
                return self.envia(open(caminho("central/index.html"), "rb").read(), "text/html; charset=utf-8")
            if rota == "/vista3d.js":
                return self.envia(open(caminho("central/vista3d.js"), "rb").read(), "text/javascript; charset=utf-8")
            if rota == "/api/estado":
                return self.envia(json.dumps(estado()).encode(), "application/json")
            if rota == "/api/fila":
                return self.envia(json.dumps(fila()).encode(), "application/json")
            if rota.startswith("/img/") and rota[5:] in IMAGENS:
                leve = caminho(f"web_{rota[5:]}.jpg")   # versão reduzida gerada pelo painel.py
                arq = leve if os.path.exists(leve) and os.path.getmtime(leve) > time.time() - 10 else caminho(IMAGENS[rota[5:]])
                return self.envia(open(arq, "rb").read(), "image/jpeg")
            if rota == "/api/toolpath":
                from urllib.parse import parse_qs, urlparse
                arq = os.path.basename(parse_qs(urlparse(self.path).query).get("a", [""])[0])
                if arq.endswith(".gcode") and os.path.exists(caminho(arq)):
                    return self.envia(toolpath.segmentos(caminho(arq)), "application/octet-stream")
            if rota == "/modelo.stl":
                arq = processo_ativo()
                if not arq:
                    try:
                        arq = os.path.basename(json.load(open(caminho("status.json")))["arquivo"])
                    except Exception:
                        arq = None
                meta = modelos().get(arq or "", {})
                if meta.get("stl") and os.path.exists(caminho(meta["stl"])):
                    return self.envia(open(caminho(meta["stl"]), "rb").read(), "model/stl")
            self.envia(b"nao achei", "text/plain", 404)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    os.chdir(RAIZ)
    print(f"central em http://localhost:{PORTA}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORTA), H).serve_forever()
