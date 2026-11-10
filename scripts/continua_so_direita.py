"""Continua rotores.gcode a partir da linha n, só com o que tem X >= xlim (rotor da direita).
A placa foi reiniciada (serial reaberta): o cabeçalho aquece, sobe, faz G28 de X e Y, faz o Z num ponto livre
(X215 Y80), escorva lá e só então entra no corpo. Na região pulada nada é percorrido; na saída o bico desloca
alto até o ponto de destino, desce e segue (a extrusão do segmento que cruza a fronteira é descartada)."""
import re, sys
ent, n, xlim, sai = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
L = open(ent).read().split("\n")
SOBE = 2.0
rx, ry, rz, rf, re_ = (re.compile(r"\b%s(-?[\d.]+)" % c) for c in "XYZFE")
x = y = z = f = None
for l in L[:n]:
    c = l.split(";")[0]
    if not c.startswith(("G0", "G1")): continue
    for r, nome in ((rx, "x"), (ry, "y"), (rz, "z"), (rf, "f")):
        m = r.search(c)
        if m: globals()[nome] = float(m.group(1))
print("estado na linha", n, "X", x, "Y", y, "Z", z, "F", f)
out = ["M140 S60", "M104 S205", "G91", "G1 Z15 F600", "G90", "G28 X Y", "G1 X215 Y80 F4000", "G28 Z", "G92 Z-0.05",
       f"G1 Z{z + 10:g} F600", "M190 S60", "M109 S205", "M83", "G1 E4 F200", "G4 S2", f"G1 Z{z + SOBE:g} F600", f"G1 F{f:g}"]
pulando = True; pulos = 0; saidas = 0
for l in L[n:]:
    c = l.split(";")[0].strip()
    if c.startswith(("G0", "G1")):
        mx, my, mz, mf, me = (r.search(c) for r in (rx, ry, rz, rf, re_))
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
            elif not dentro and pulando:
                pulando = False; saidas += 1
                out += [f"G1 X{nx:g} Y{ny:g} F7200", f"G1 Z{z:g} F7200", f"G1 F{f:g}"]
            elif not dentro:
                out.append(l)
            x, y = nx, ny; continue
    out.append(l)
open(sai, "w").write("\n".join(out))
print("linhas", len(out), "entradas na região pulada", pulos, "saídas", saidas)
