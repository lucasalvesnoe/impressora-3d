"""Extrai os objetos de um 3mf (Bambu/Creality/Orca), aplica as transformações do build e grava STL.

Uso: extrai_3mf.py arquivo.3mf saida.stl [dx dy]
Imprime bbox de cada peça e a área apoiada na mesa (faces voltadas para baixo no Z mínimo).
"""
import re, struct, sys, zipfile

def ler_malha(z, nome, obj_id=None):
    s = z.read(nome).decode()
    if obj_id is not None:
        m = re.search(r'<object id="%s"[^>]*>(.*?)</object>' % obj_id, s, re.S)
        s = m.group(1) if m else s
    v = [tuple(float(a) for a in m) for m in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', s)]
    t = [tuple(int(a) for a in m) for m in re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', s)]
    return v, t

def matriz(txt):
    a = [float(x) for x in txt.split()]
    return a  # m00 m01 m02 m10 m11 m12 m20 m21 m22 tx ty tz (3MF: linha = vetor)

def aplica(v, m):
    return [(x*m[0] + y*m[3] + z*m[6] + m[9], x*m[1] + y*m[4] + z*m[7] + m[10], x*m[2] + y*m[5] + z*m[8] + m[11]) for x, y, z in v]

def main():
    src, dst = sys.argv[1], sys.argv[2]
    dx = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    dy = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    z = zipfile.ZipFile(src)
    raiz = z.read("3D/3dmodel.model").decode()
    objetos = {}
    for m in re.finditer(r'<object id="(\d+)"[^>]*>(.*?)</object>', raiz, re.S):
        comps = re.findall(r'<component[^>]*p:path="([^"]+)"[^>]*objectid="(\d+)"[^>]*transform="([^"]+)"', m.group(2))
        objetos[m.group(1)] = comps
    pecas = []
    for item in re.finditer(r'<item objectid="(\d+)"[^>]*transform="([^"]+)"', raiz):
        mi = matriz(item.group(2))
        for path, oid, tr in objetos.get(item.group(1), []):
            v, t = ler_malha(z, path.lstrip("/"), oid)
            v = aplica(aplica(v, matriz(tr)), mi)
            pecas.append((path, v, t))
    zmin = min(p[2] for _, v, _ in pecas for p in v)
    tri = []
    for path, v, t in pecas:
        v = [(x + dx, y + dy, zz - zmin) for x, y, zz in v]
        area = 0.0
        for a, b, c in t:
            A, B, C = v[a], v[b], v[c]
            tri.append((A, B, C))
            if max(A[2], B[2], C[2]) < 0.05:
                area += abs((B[0]-A[0])*(C[1]-A[1]) - (C[0]-A[0])*(B[1]-A[1])) / 2
        xs, ys, zs = [p[0] for p in v], [p[1] for p in v], [p[2] for p in v]
        print("%s X %.1f-%.1f Y %.1f-%.1f Z %.1f-%.1f apoio %.0f mm2" % (path.split("/")[-1], min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), area))
    with open(dst, "wb") as f:
        f.write(b"extrai_3mf".ljust(80, b" ")); f.write(struct.pack("<I", len(tri)))
        for a, b, c in tri:
            f.write(struct.pack("<3f", 0, 0, 0)); [f.write(struct.pack("<3f", *p)) for p in (a, b, c)]; f.write(b"\0\0")
    xs = [p[0] for a in tri for p in a]; ys = [p[1] for a in tri for p in a]; zs = [p[2] for a in tri for p in a]
    print("TOTAL X %.1f-%.1f Y %.1f-%.1f Z %.1f centro %.2f,%.2f" % (min(xs), max(xs), min(ys), max(ys), max(zs), (min(xs)+max(xs))/2, (min(ys)+max(ys))/2))

main()
