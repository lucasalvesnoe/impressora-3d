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


# Formato compacto e fiel (TP2): todo filete do gcode, sem simplificar a geometria.
# Antes (até 10/11/2026) os filetes curtos eram fundidos até 3 mm para caber no túnel; isso deixava
# círculos pequenos (galhos do suporte orgânico, curvas finas) triangulares no 3D.
# Agora o caminho vai em polilinhas: cada trecho contínuo (mesma camada, tipo, largura e altura) tem um
# cabeçalho e os pontos seguintes vão como Int16 em centésimos de mm, mais o salto do índice do comando.
#   cabeçalho: b"TP2\0", uint32 n_trechos, uint32 n_filetes
#   trechos (32 bytes cada): float32 x0, y0, z, largura, altura; uint32 cmd0, n; uint8 tipo + 3 bytes
#   depois: int16 x[n_filetes], int16 y[n_filetes], uint16 dcmd[n_filetes]
_cache_tp2 = {}


def compacto(caminho):
    import struct, gzip
    chave = (caminho, os.path.getmtime(caminho))
    if chave in _cache_tp2:
        return _cache_tp2[chave]
    seg = array.array("f"); seg.frombytes(segmentos(caminho))
    n = len(seg) // 9
    trechos = bytearray(); xs = array.array("h"); ys = array.array("h"); dc = array.array("H")
    nt = 0; i = 0
    while i < n:
        o = i * 9
        z, w, h, t = seg[o+4], seg[o+5], seg[o+6], seg[o+7]
        cmd = int(seg[o+8]); j = i
        while j < n:
            p = j * 9
            if j > i and (seg[p] != seg[p-7] or seg[p+1] != seg[p-6] or seg[p+4] != z or seg[p+5] != w
                          or seg[p+6] != h or seg[p+7] != t or not 0 <= int(seg[p+8]) - cmd <= 65535):
                break
            xs.append(round(seg[p+2] * 100)); ys.append(round(seg[p+3] * 100))
            dc.append(int(seg[p+8]) - cmd if j > i else 0); cmd = int(seg[p+8]); j += 1
        trechos += struct.pack("<5f2I4B", seg[o], seg[o+1], z, w, h, int(seg[o+8]), j - i, int(t), 0, 0, 0)
        nt += 1; i = j
    corpo = b"TP2\0" + struct.pack("<2I", nt, n) + bytes(trechos) + xs.tobytes() + ys.tobytes() + dc.tobytes()
    dados = gzip.compress(corpo, 6)
    _cache_tp2.clear(); _cache_tp2[chave] = dados
    return dados


if __name__ == "__main__":
    import sys, time
    t = time.time(); d = segmentos(sys.argv[1])
    print(len(d) // 36, "segmentos", round(time.time() - t, 2), "s", len(d) // 1024, "KB")
    t = time.time(); c = compacto(sys.argv[1])
    print("TP2 gzip", len(c) // 1024, "KB", round(time.time() - t, 2), "s")
