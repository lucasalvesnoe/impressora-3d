"""Gera cachorro.gcode: silhueta de cachorrinho deitada na mesa, extrudada. PLA 200/60.
Uso: gera_cachorro.py [comprimento_mm=32] [altura_mm=3]"""
import math, sys
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity

COMP = float(sys.argv[1]) if len(sys.argv) > 1 else 32.0
ALT = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
LH, W, D = 0.2, 0.4, 1.75
EPM = (W * LH) / (math.pi * (D / 2) ** 2)

def rr(x0, y0, x1, y1, r):  # retângulo arredondado
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r)

partes = [
    rr(8, 8, 28, 18, 3),                                   # corpo
    Point(31, 21).buffer(6),                               # cabeça
    rr(33, 15, 40, 21, 2.5),                               # focinho
    affinity.rotate(Point(0, 0).buffer(1).pipe if False else Point(0, 0).buffer(1), 0),
]
partes = [
    rr(8, 8, 28, 18, 3),
    Point(31, 21).buffer(6),
    rr(33, 15, 40, 21, 2.5),
    affinity.translate(affinity.rotate(affinity.scale(Point(0, 0).buffer(1), 2.2, 4.2), -20), 27.5, 22),  # orelha
    rr(9, 0, 12.5, 11, 1.5), rr(14, 0, 17.5, 11, 1.5),    # patas de trás
    rr(21, 0, 24.5, 11, 1.5), rr(25.5, 0, 29, 11, 1.5),   # patas da frente
    LineString([(9, 15), (5, 19), (3.5, 24)]).buffer(1.4), # rabo
]
cao = unary_union(partes).buffer(0.8).buffer(-0.8)
cao = cao.difference(Point(32.5, 23).buffer(1.1))          # olho (furo)
minx, miny, maxx, maxy = cao.bounds
s = COMP / (maxx - minx)
cao = affinity.scale(cao, s, s, origin=(minx, miny))
minx, miny, maxx, maxy = cao.bounds
cao = affinity.translate(cao, 117.5 - (minx + maxx) / 2, 117.5 - (miny + maxy) / 2)

g = ["M140 S60", "M104 S200", "G28", "M190 S60", "M109 S200", "G90", "M83", "M107",
     "G1 Z2 F600", "G1 X5 Y20 F4000", "G1 Z0.28 F300", "G1 X5 Y120 E15 F1200",
     "G1 X5.4 Y120 F1200", "G1 X5.4 Y20 E15 F1200", "G1 E-1 F1800", "G1 Z1 F600"]

def anda(p, f=4000): g.append(f"G1 X{p[0]:.2f} Y{p[1]:.2f} F{f}")
def extruda(a, b, f):
    L = math.dist(a, b)
    if L > 0.01: g.append(f"G1 X{b[0]:.2f} Y{b[1]:.2f} E{L * EPM:.4f} F{f}")
def aneis(geom):
    gs = getattr(geom, "geoms", [geom])
    for p in gs:
        yield list(p.exterior.coords)
        for i in p.interiors: yield list(i.coords)

n = round(ALT / LH)
for k in range(n):
    z = LH * (k + 1)
    vel = 1200 if k == 0 else 2400
    g.append(f";CAMADA {k + 1}/{n}")
    if k == 1: g.append("M106 S255")
    g.append(f"G1 Z{z + 0.6:.2f} F600")
    peri = cao.buffer(-W / 2)
    for anel in aneis(peri):
        anda(anel[0]); g.append(f"G1 Z{z:.2f} F600"); g.append("G1 E1 F1800")
        for a, b in zip(anel, anel[1:]): extruda(a, b, vel)
        g.append("G1 E-1 F1800"); g.append(f"G1 Z{z + 0.4:.2f} F600")
    miolo = cao.buffer(-W * 0.95)
    ang = 45 if k % 2 == 0 else -45
    rot = affinity.rotate(miolo, ang, origin=(117.5, 117.5))
    x0, y0, x1, y1 = rot.bounds
    y = y0 + W / 2; idx = 0; fim = None
    while y < y1:
        seg = LineString([(x0 - 1, y), (x1 + 1, y)]).intersection(rot)
        segs = [s_ for s_ in getattr(seg, "geoms", [seg]) if s_.length > 0.3]
        if idx % 2: segs = segs[::-1]
        for s_ in segs:
            c = list(affinity.rotate(s_, -ang, origin=(117.5, 117.5)).coords)
            if idx % 2: c = c[::-1]
            if fim is not None and math.dist(fim, c[0]) < 2:
                anda(c[0], 3000)                       # vizinho: vai direto, sem levantar
            else:
                if fim is not None: g.append("G1 E-1 F1800"); g.append(f"G1 Z{z + 0.4:.2f} F600")
                anda(c[0]); g.append(f"G1 Z{z:.2f} F600"); g.append("G1 E1 F1800")
            extruda(c[0], c[1], vel); fim = c[1]
        y += W; idx += 1
    if fim is not None: g.append("G1 E-1 F1800"); g.append(f"G1 Z{z + 0.4:.2f} F600")
g += ["M107", "G1 Z30 F600", "G1 X10 Y200 F4000", "M104 S0", "M140 S0", "M84"]
open("cachorro.gcode", "w").write("\n".join(g) + "\n")
# estimativa simples de tempo
t = 0; last = None
for l in g:
    if l.startswith("G1") and "X" in l:
        p = dict((w[0], float(w[1:])) for w in l.split()[1:] if w[0] in "XYF")
        if last: t += math.dist(last, (p["X"], p["Y"])) / (p.get("F", 4000) / 60)
        last = (p["X"], p["Y"])
print(f"{len(g)} linhas, {n} camadas, area {cao.area:.0f} mm2, bounds {[round(v,1) for v in cao.bounds]}, movimento ~{t/60:.1f} min")
# preview em PNG
import json
json.dump([list(a) for a in aneis(cao)], open('cachorro_contorno.json','w'))
