"""Gera teste.gcode: quadrado 30x30 mm, 1 camada de 0,2 mm, PLA 200/60, no centro da mesa."""
import math
L, W, H, D = 30.0, 0.4, 0.2, 1.75
EPM = (W * H) / (math.pi * (D / 2) ** 2)          # mm de filamento por mm andado
CX, CY = 117.5, 117.5
x0, y0 = CX - L / 2, CY - L / 2
g = ["M140 S60", "M104 S200", "G28", "M190 S60", "M109 S200", "G90", "M83", "G92 E0",
     "G1 Z2 F600", "G1 X5 Y20 F4000", "G1 Z0.28 F300", "G1 X5 Y120 E15 F1200",   # linha de limpeza
     "G1 X5.4 Y120 F1200", "G1 X5.4 Y20 E15 F1200", "G1 Z1 F600",
     f"G1 X{x0:.2f} Y{y0:.2f} F4000", f"G1 Z{H} F300"]
for (a, b) in [(x0 + L, y0), (x0 + L, y0 + L), (x0, y0 + L), (x0, y0)]:   # contorno
    g.append(f"G1 X{a:.2f} Y{b:.2f} E{L * EPM:.4f} F1200")
n = int(L / W)
for i in range(1, n):                                              # preenchimento em zigue-zague
    y = y0 + i * W
    xa, xb = (x0 + W, x0 + L - W) if i % 2 else (x0 + L - W, x0 + W)
    g.append(f"G1 X{xa:.2f} Y{y:.2f} F3000")
    g.append(f"G1 X{xb:.2f} Y{y:.2f} E{(L - 2 * W) * EPM:.4f} F1500")
g += ["G1 E-2 F1800", "G1 Z20 F600", "G1 X10 Y200 F4000", "M104 S0", "M140 S0", "M84"]
open("teste.gcode", "w").write("\n".join(g) + "\n")
print(len(g), "linhas")
