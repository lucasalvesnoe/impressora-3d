"""Lê um .gcode do PrusaSlicer e devolve os segmentos de extrusão em binário (Float32, 9 valores por segmento).

Cada segmento: x0, y0, x1, y1, z, largura, altura, tipo, indice_do_comando
O índice do comando é contado igual ao imprime.py (linhas não vazias depois de tirar o comentário),
assim o navegador sabe quais segmentos já foram impressos comparando com progresso.txt.
"""
import array, os

TIPOS = ["Outro", "External perimeter", "Perimeter", "Overhang perimeter", "Internal infill", "Solid infill",
         "Top solid infill", "Bridge infill", "Gap fill", "Skirt/Brim", "Support material",
         "Support material interface", "Ironing"]
_IDX = {t: i for i, t in enumerate(TIPOS)}
_cache = {}


def _num(palavras, letra):
    for p in palavras:
        if p and p[0] == letra:
            try:
                return float(p[1:])
            except ValueError:
                return None
    return None


def segmentos(caminho):
    chave = (caminho, os.path.getmtime(caminho))
    if chave in _cache:
        return _cache[chave]
    out = array.array("f")
    x = y = z = 0.0
    absoluto, e_relativo = True, True
    tipo, largura, altura = 0, 0.45, 0.2
    n = 0
    for bruta in open(caminho, errors="replace"):
        if bruta.startswith(";TYPE:"):
            tipo = _IDX.get(bruta[6:].strip(), 0); continue
        if bruta.startswith(";WIDTH:"):
            largura = float(bruta[7:]); continue
        if bruta.startswith(";HEIGHT:"):
            altura = float(bruta[8:]); continue
        cmd = bruta.split(";")[0].strip()
        if not cmd:
            continue
        n += 1
        p = cmd.split()
        g = p[0]
        if g == "G90":
            absoluto = True
        elif g == "G91":
            absoluto = False
        elif g == "M82":
            e_relativo = False
        elif g == "M83":
            e_relativo = True
        elif g == "G92":
            pass
        elif g in ("G0", "G1"):
            nx, ny, nz, ne = _num(p, "X"), _num(p, "Y"), _num(p, "Z"), _num(p, "E")
            if absoluto:
                x1 = nx if nx is not None else x
                y1 = ny if ny is not None else y
                z1 = nz if nz is not None else z
            else:
                x1, y1, z1 = x + (nx or 0), y + (ny or 0), z + (nz or 0)
            if ne is not None and ne > 0 and e_relativo and (x1 != x or y1 != y):
                out.extend((x, y, x1, y1, z1, largura, altura, tipo, n))
            x, y, z = x1, y1, z1
        elif g == "G28":
            x = y = z = 0.0
    dados = out.tobytes()
    _cache.clear(); _cache[chave] = dados
    return dados


if __name__ == "__main__":
    import sys, time
    t = time.time(); d = segmentos(sys.argv[1])
    print(len(d) // 36, "segmentos", round(time.time() - t, 2), "s", len(d) // 1024, "KB")
