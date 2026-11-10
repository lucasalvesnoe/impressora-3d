"""Gera um gcode que continua a partir de uma linha e deixa de imprimir tudo com X abaixo de um limite.

Uso: pula_regiao.py entrada.gcode linha_ja_enviada x_limite saida.gcode
Dentro da região pulada: os movimentos são descartados (o bico só sobe 2 mm e vai direto para o próximo ponto fora dela).
Ao sair, desloca alto até o ponto de destino, desce e restaura o F original.
O cabeçalho desfaz a pausa do imprime.py (bico 10 mm acima, 2 mm recolhidos) e repõe 1,5 mm do que escorreu.
"""
import re, sys

ent, n, xlim, sai = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
L = open(ent).read().split("\n")
SOBE = 2.0
rx, ry, rz, rf, re_ = (re.compile(r"\b%s(-?[\d.]+)" % c) for c in "XYZFE")

# estado na linha n (já executada)
x = y = z = None; f = None
for l in L[:n]:
    if not l.startswith(("G0", "G1")): continue
    for r, nome in ((rx, "x"), (ry, "y"), (rz, "z"), (rf, "f")):
        m = r.search(l)
        if m: globals()[nome] = float(m.group(1))
print("estado na linha", n, "X", x, "Y", y, "Z", z, "F", f)

out = ["M83", "G91", "G1 Z-9 F600", "G90", "M83", "G1 E3.5 F300", "G91", "G1 Z-1 F600", "G90", "M83", f"G1 F{f:g}"]
pulando = False; saidas_extrudindo = 0; pulos = 0
for l in L[n:]:
    if l.startswith(("G0", "G1")):
        mx, my, mz, mf, me = (r.search(l) for r in (rx, ry, rz, rf, re_))
        if mf: f = float(mf.group(1))
        if mz and not (mx or my):
            z = float(mz.group(1))
            out.append(f"G1 Z{z + SOBE:g} F7200" if pulando else l); continue
        if mx or my:
            nx = float(mx.group(1)) if mx else x; ny = float(my.group(1)) if my else y
            extrude = me is not None and float(me.group(1)) > 0
            dentro = nx < xlim
            if dentro and not pulando:
                pulando = True; pulos += 1
                out.append(f"G1 Z{z + SOBE:g} F7200")
            if dentro:
                pass  # não percorre a região: ficar zanzando sem plástico parece entupimento (09/11, Lucas desligou achando que entupiu)
            elif pulando:
                pulando = False
                if extrude: saidas_extrudindo += 1
                out.append(f"G1 X{nx:g} Y{ny:g} F7200") if not extrude else None
                out.append(f"G1 Z{z:g} F7200"); out.append(f"G1 F{f:g}")
                if extrude: out.append(l)
            else:
                out.append(l)
            x, y = nx, ny; continue
    out.append(l)
open(sai, "w").write("\n".join(out))
print("linhas", len(out), "regioes puladas", pulos, "saidas no meio de extrusao", saidas_extrudindo)
