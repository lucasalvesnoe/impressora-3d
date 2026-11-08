"""Mini modelador em Python puro (numpy): primitivas fechadas que se juntam numa malha e viram STL.

Serve para conceitos e peças simples. Sólidos podem se sobrepor: o fatiador une os volumes.
Unidades em mm, Z para cima, mesa em z = 0.
"""
import math, struct
import numpy as np


class Malha:
    def __init__(self, tris=None):
        self.t = np.zeros((0, 3, 3)) if tris is None else np.asarray(tris, float)

    def __add__(self, o):
        return Malha(np.concatenate([self.t, o.t]))

    def mover(self, x=0, y=0, z=0):
        return Malha(self.t + np.array([x, y, z]))

    def girar_z(self, graus):
        a = math.radians(graus); c, s = math.cos(a), math.sin(a)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        return Malha(self.t @ R.T)

    def girar_x(self, graus):
        a = math.radians(graus); c, s = math.cos(a), math.sin(a)
        R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        return Malha(self.t @ R.T)

    def girar_y(self, graus):
        a = math.radians(graus); c, s = math.cos(a), math.sin(a)
        R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        return Malha(self.t @ R.T)

    def escala(self, sx, sy=None, sz=None):
        return Malha(self.t * np.array([sx, sy or sx, sz or sx]))

    def no_chao(self):
        return self.mover(z=-self.t[:, :, 2].min()) if len(self.t) else self

    def salva(self, caminho):
        t = self.t.astype(np.float32)
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        with open(caminho, "wb") as f:
            f.write(b"criar/malha.py".ljust(80, b" ") + struct.pack("<I", len(t)))
            reg = np.zeros(len(t), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
            reg["n"] = n; reg["v"] = t.reshape(-1, 9)
            f.write(reg.tobytes())


def _ear(poly):
    """Triangula polígono simples (anti-horário) por orelhas."""
    idx = list(range(len(poly))); out = []
    def area2(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    def dentro(p, a, b, c):
        return area2(a, b, p) >= 0 and area2(b, c, p) >= 0 and area2(c, a, p) >= 0
    guarda = 0
    while len(idx) > 3 and guarda < 10000:
        guarda += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if area2(a, b, c) <= 1e-9:
                continue
            if any(dentro(poly[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            out.append((i0, i1, i2)); idx.pop(k); break
        else:
            break
    if len(idx) == 3:
        out.append(tuple(idx))
    return out


def extrusao(poly, h, z0=0.0):
    """Prisma a partir de polígono 2D (lista de (x, y))."""
    p = list(poly)
    a = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    if a < 0:
        p = p[::-1]
    tris = []
    for i0, i1, i2 in _ear(p):
        A, B, C = p[i0], p[i1], p[i2]
        tris.append([(A[0], A[1], z0 + h), (B[0], B[1], z0 + h), (C[0], C[1], z0 + h)])
        tris.append([(A[0], A[1], z0), (C[0], C[1], z0), (B[0], B[1], z0)])
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        tris.append([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z0 + h)])
        tris.append([(a[0], a[1], z0), (b[0], b[1], z0 + h), (a[0], a[1], z0 + h)])
    return Malha(tris)


def anel_extrusao(ext, inter, h, z0=0.0):
    """Prisma com furo: dois contornos com o mesmo número de pontos (externo anti-horário)."""
    tris = []
    n = len(ext)
    for i in range(n):
        a, b = ext[i], ext[(i + 1) % n]; c, d = inter[i], inter[(i + 1) % n]
        tris += [[(a[0], a[1], z0 + h), (b[0], b[1], z0 + h), (d[0], d[1], z0 + h)], [(a[0], a[1], z0 + h), (d[0], d[1], z0 + h), (c[0], c[1], z0 + h)]]
        tris += [[(a[0], a[1], z0), (d[0], d[1], z0), (b[0], b[1], z0)], [(a[0], a[1], z0), (c[0], c[1], z0), (d[0], d[1], z0)]]
        tris += [[(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z0 + h)], [(a[0], a[1], z0), (b[0], b[1], z0 + h), (a[0], a[1], z0 + h)]]
        tris += [[(c[0], c[1], z0), (d[0], d[1], z0 + h), (d[0], d[1], z0)], [(c[0], c[1], z0), (c[0], c[1], z0 + h), (d[0], d[1], z0 + h)]]
    return Malha(tris)


def circulo(r, n=48, cx=0, cy=0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def ret_arredondado(w, d, r, n=8):
    r = min(r, w / 2 - 0.01, d / 2 - 0.01); pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def caixa(w, d, h, r=0.0, z0=0.0):
    return extrusao(ret_arredondado(w, d, r) if r > 0 else [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)], h, z0)


def cilindro(r, h, n=48, z0=0.0):
    return extrusao(circulo(r, n), h, z0)


def tubo(r_ext, r_int, h, n=64, z0=0.0):
    return anel_extrusao(circulo(r_ext, n), circulo(r_int, n), h, z0)


def torno(perfil, n=48):
    """Revolução de um perfil [(r, z)] em torno do eixo Z (r=0 nas pontas fecha o sólido)."""
    tris = []
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        for (r0, z0), (r1, z1) in zip(perfil, perfil[1:]):
            p = [(r0 * math.cos(a0), r0 * math.sin(a0), z0), (r1 * math.cos(a0), r1 * math.sin(a0), z1),
                 (r1 * math.cos(a1), r1 * math.sin(a1), z1), (r0 * math.cos(a1), r0 * math.sin(a1), z0)]
            tris += [[p[0], p[1], p[2]], [p[0], p[2], p[3]]]
    return Malha(tris)


def esfera(r, n=32, z0=0.0):
    return torno([(r * math.sin(math.pi * i / n), z0 + r - r * math.cos(math.pi * i / n)) for i in range(n + 1)], n * 2)


def toro(R, r, n=48, m=20, z0=0.0):
    perf = [(R + r * math.cos(2 * math.pi * j / m), z0 + r + r * math.sin(2 * math.pi * j / m)) for j in range(m + 1)]
    return torno(perf, n)


def cunha(w, d, hf, ht):
    """Rampa: largura w (x), profundidade d (y), altura hf na frente (y=-d/2) e ht atrás."""
    perfil = [(-d / 2, 0), (d / 2, 0), (d / 2, ht), (-d / 2, hf)]   # (y, z)
    m = extrusao(perfil, w)                                       # extrudado em "z" = x
    t = m.t.copy(); t = t[:, :, [2, 0, 1]]                         # (y, z, x) -> (x, y, z)
    t[:, :, 0] -= w / 2
    return Malha(t[:, ::-1, :])


def estrela(r_ext, r_int, pontas=5, h=3, z0=0.0):
    pts = []
    for i in range(pontas * 2):
        r = r_ext if i % 2 == 0 else r_int; a = math.pi / 2 + math.pi * i / pontas
        pts.append((r * math.cos(a), r * math.sin(a)))
    return extrusao(pts, h, z0)


def lua(r, h, z0=0.0, desloc=0.45, n=48):
    """Lua crescente: arco externo do círculo menos um círculo deslocado."""
    pts = []
    for i in range(n + 1):
        a = math.radians(-120 + 240 * i / n); pts.append((r * math.cos(a), r * math.sin(a)))
    r2 = r * 0.85; cx = r * desloc
    for i in range(n + 1):
        a = math.radians(110 - 220 * i / n); pts.append((cx + r2 * math.cos(a), r2 * math.sin(a)))
    return extrusao(pts, h, z0)


def coracao(s, h, z0=0.0, n=60):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3; y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * s / 32, y * s / 32))
    return extrusao(pts, h, z0)
