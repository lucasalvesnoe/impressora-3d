"""Conceitos 3D das ideias "vamos criar" (docs/IDEIAS.md). Medidas aproximadas: a versão final sai com as medidas reais.

Uso: python criar/conceitos.py  ->  criar/stl/<slug>.stl
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from malha import (Malha, caixa, cilindro, tubo, torno, esfera, toro, cunha, extrusao, estrela, lua, coracao,
                   circulo, ret_arredondado, anel_extrusao)

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")


# ---------- home office ----------
def cyd():
    corpo = caixa(78, 52, 14, r=4)
    moldura = anel_extrusao(ret_arredondado(78, 52, 4, 6), ret_arredondado(64, 46, 2, 6), 2, 14)
    pe = cunha(60, 40, 2, 34).girar_z(180).mover(y=40)
    usb = caixa(12, 6, 5, z0=4).mover(x=39)
    return (corpo + moldura).girar_x(-65).no_chao().mover(y=-5) + pe + usb.girar_x(-65).no_chao()


def carga_iphones():
    m = caixa(200, 90, 12, r=6)
    for i in range(5):
        x = -80 + i * 40
        m += cunha(6, 70, 55, 55).mover(x=x, z=12).girar_x(0) + caixa(6, 70, 4, z0=12).mover(x=x)
    m += caixa(200, 8, 30, z0=12).mover(y=-41)
    return m


def garra_eixo_x():
    perfil = caixa(40, 24, 6) + caixa(6, 24, 26).mover(x=-17) + caixa(6, 24, 26).mover(x=17) + caixa(14, 24, 4, z0=22).mover(x=-13) + caixa(14, 24, 4, z0=22).mover(x=13)
    braco = caixa(10, 10, 70, z0=-70)
    berco = caixa(80, 12, 6, z0=-76) + caixa(6, 12, 30, z0=-76).mover(x=-37) + caixa(6, 12, 30, z0=-76).mover(x=37) + caixa(80, 4, 40, z0=-76).mover(y=-6)
    return (perfil + braco + berco).no_chao()


def painel_antenas():
    m = caixa(200, 120, 8, r=6)
    for i, (h, r) in enumerate([(120, 4), (90, 3.5), (170, 4), (60, 3), (110, 3.5)]):
        m += cilindro(r + 3, 10, z0=8).mover(x=-80 + i * 22, y=35) + cilindro(r, h, z0=18).mover(x=-80 + i * 22, y=35)
    m += anel_extrusao(ret_arredondado(46, 30, 3, 6), ret_arredondado(40, 24, 2, 6), 40, 8).mover(x=60, y=30)
    m += anel_extrusao(ret_arredondado(110, 48, 4, 6), ret_arredondado(104, 42, 3, 6), 14, 8).mover(x=-30, y=-30)
    m += caixa(100, 40, 26, r=8, z0=8).mover(x=-30, y=-30)   # Flipper no berço
    m += anel_extrusao(ret_arredondado(60, 30, 3, 6), ret_arredondado(54, 24, 2, 6), 30, 8).mover(x=60, y=-30)
    return m


def livro_usb():
    capa = caixa(150, 105, 4, r=3) + caixa(150, 105, 4, r=3, z0=28)
    miolo = caixa(144, 100, 24, z0=4).mover(x=3)
    lombada = caixa(8, 105, 32).mover(x=-71)
    furos = Malha()
    for i in range(4):
        for j in range(3):
            furos += caixa(18, 10, 14, z0=32).mover(x=-45 + i * 30, y=-30 + j * 30)
    return capa + miolo + lombada + furos


def gaveteiro():
    corpo = Malha()
    for k in range(3):
        z = k * 40
        corpo += anel_extrusao(ret_arredondado(160, 120, 4, 4), ret_arredondado(152, 112, 3, 4), 38, z)
        corpo += caixa(160, 120, 2, r=4, z0=z)
        corpo += caixa(40, 4, 10, r=2, z0=z + 20).mover(y=-62)
    return corpo


def airpods_airtag():
    base = caixa(120, 70, 10, r=14)
    case = anel_extrusao(ret_arredondado(56, 32, 12, 8), ret_arredondado(50, 26, 10, 8), 10, 10).mover(x=-25)
    tags = tubo(19, 16.5, 6, z0=10).mover(x=28, y=14) + tubo(19, 16.5, 6, z0=10).mover(x=28, y=-14)
    airpods = caixa(46, 22, 52, r=10, z0=10).mover(x=-25).escala(1, 1, 1)
    return base + case + tags + airpods


def elevacao_teclado():
    a = cunha(200, 120, 14, 34)
    b = cunha(200, 120, 14, 34).mover(x=210)
    gaveta = caixa(120, 60, 8, r=3, z0=3).mover(x=105, y=-20)
    return (a + b + gaveta).mover(x=-105)


def porta_ferramentas():
    placa = caixa(120, 6, 60, r=0)
    m = placa + caixa(120, 40, 5, z0=0).mover(y=-23)
    for i, (w, d) in enumerate([(30, 10), (14, 14), (8, 8), (22, 8)]):
        m += anel_extrusao(ret_arredondado(w + 6, d + 6, 3, 4), ret_arredondado(w, d, 2, 4), 30, 5).mover(x=-45 + i * 30, y=-23)
    return m


def dock_macbooks():
    base = caixa(120, 90, 10, r=8)
    m = base
    for x in (-27, 0, 27):          # duas fendas de 17 mm: MacBook Pro e Air fechados
        m += caixa(10, 80, 70, r=4, z0=10).mover(x=x)
    return m


# ---------- Celina e Antonella ----------
def torre_argolas():
    base = torno([(0, 0), (60, 0), (62, 4), (60, 14), (0, 14)])
    pino = cilindro(11, 120, z0=14)
    m = base + pino
    z = 14
    for i, r in enumerate([45, 41, 37, 33, 29]):
        m += toro(r - 7, 9, z0=z); z += 18
    return m + esfera(22, z0=z)


def blocos():
    m = Malha()
    for i, (x, y, h) in enumerate([(0, 0, 70), (75, 0, 35), (0, 75, 70), (75, 75, 70)]):
        m += caixa(70, 70, h, r=8).mover(x=x - 37, y=y - 37)
        for dx in (-15, 15):
            for dy in (-15, 15):
                m += cilindro(10, 12, z0=h).mover(x=x - 37 + dx, y=y - 37 + dy)
    return m


def jogo_velha():
    tab = caixa(180, 180, 6, r=12)
    for k in (-30, 30):
        tab += caixa(4, 168, 4, z0=6).mover(x=k) + caixa(168, 4, 4, z0=6).mover(y=k)
    sol = cilindro(14, 12) + estrela(22, 14, 10, 12)
    l1 = lua(19, 12)
    pecas = sol.mover(x=-60, y=60, z=10) + l1.mover(x=0, y=0, z=10) + sol.mover(x=60, y=-60, z=10) + l1.mover(x=-60, y=-60, z=10)
    return tab + pecas


def trilha():
    tab = caixa(200, 200, 6, r=10)
    pts = []
    for i in range(40):
        a = i * 0.42; r = 85 - i * 1.9
        pts.append((r * math.cos(a), r * math.sin(a)))
    for x, y in pts:
        tab += cilindro(8, 2, z0=6).mover(x=x, y=y)
    peao = torno([(0, 0), (11, 0), (11, 3), (6, 8), (4, 22), (0, 30)]) + esfera(7, z0=24)
    for i, (x, y) in enumerate([pts[0], pts[3], pts[7], pts[12]]):
        tab += peao.mover(x=x, y=y, z=8)
    return tab


def quebra_cabeca_foto():
    m = caixa(150, 150, 3)
    for i in range(30):
        for j in range(30):
            x, y = -72.5 + i * 5, -72.5 + j * 5
            h = 0.6 + 2.4 * (0.5 + 0.5 * math.sin(math.hypot(x, y) / 9))
            if (x / 40) ** 2 + ((y - 10) / 48) ** 2 < 1:
                h = 3.0
            m += caixa(5, 5, h, z0=3).mover(x=x, y=y)
    return m


def domino():
    m = Malha()
    for k in range(3):
        t = caixa(70, 35, 12, r=5).mover(y=k * 42)
        t += caixa(2, 30, 2, z0=12).mover(y=k * 42)
        t += [coracao(24, 3, 12), estrela(13, 6, 5, 3, 12), cilindro(10, 3, z0=12)][k].mover(x=-17, y=k * 42)
        t += [estrela(13, 6, 5, 3, 12), cilindro(10, 3, z0=12), coracao(24, 3, 12)][k].mover(x=17, y=k * 42)
        m += t
    return m.mover(y=-42)


def pista_bola():
    m = caixa(200, 60, 8, r=6)
    m += caixa(12, 60, 200, z0=0).mover(x=-94) + caixa(12, 60, 200, z0=0).mover(x=94)
    for i in range(4):
        z = 40 + i * 42
        ramp = cunha(176, 50, 0, 1).girar_y(4 if i % 2 else -4).mover(z=z)
        m += caixa(176, 50, 4, z0=z).mover() + caixa(176, 4, 10, z0=z).mover(y=-25)
    m += esfera(20, z0=172 + 4).mover(x=-60)
    return m


def placa_sensorial():
    m = caixa(210, 210, 6, r=10)
    for i in range(6):
        for j in range(6):
            m += esfera(5, z0=1).mover(x=-90 + i * 14, y=20 + j * 14)
    for k in range(7):
        m += cilindro(3, 100, n=12).girar_y(90).mover(x=-1, y=-90 + k * 14, z=6).mover(x=-49)
    for k in range(7):
        m += caixa(4, 90, 3, z0=6).mover(x=10 + k * 13, y=50)
    for i in range(6):
        for j in range(6):
            m += caixa(9, 9, 3, z0=6).mover(x=12 + i * 14, y=-85 + j * 14)
    return m


def boliche():
    pino = torno([(0, 0), (22, 0), (24, 6), (25, 22), (20, 48), (12, 62), (13, 72), (16, 80), (12, 88), (0, 90)])
    m = Malha()
    for x, y in [(0, 0), (-30, 52), (30, 52), (-60, 104), (0, 104), (60, 104)]:
        m += pino.mover(x=x, y=y - 50)
    return m + esfera(33).mover(x=0, y=-110)


def memoria():
    m = Malha()
    formas = [estrela(16, 7, 5, 3, 8), coracao(30, 3, 8), lua(15, 3, 8), cilindro(14, 3, z0=8),
              extrusao([(-14, -14), (14, -14), (0, 16)], 3, 8), extrusao(ret_arredondado(26, 26, 4), 3, 8)]
    for k in range(12):
        i, j = k % 4, k // 4
        t = caixa(50, 50, 8, r=6).mover(x=-82 + i * 55, y=-55 + j * 55)
        t += formas[k % 6].mover(x=-82 + i * 55, y=-55 + j * 55)
        m += t
    return m


CONCEITOS = {
    "cyd": ("Caixa da CYD", cyd), "carga": ("Estação de carga", carga_iphones), "garra": ("Garra de iPhone", garra_eixo_x),
    "antenas": ("Painel de antenas", painel_antenas), "livro": ("Caixa-livro", livro_usb), "gaveteiro": ("Gaveteiro", gaveteiro),
    "airpods": ("Base de AirPods", airpods_airtag), "teclado": ("Elevação do teclado", elevacao_teclado),
    "ferramentas": ("Porta-ferramentas", porta_ferramentas), "dock": ("Dock vertical", dock_macbooks),
    "argolas": ("Torre de argolas", torre_argolas), "blocos": ("Blocos de encaixe", blocos), "velha": ("Jogo da velha", jogo_velha),
    "trilha": ("Trilha da Família", trilha), "foto": ("Quebra-cabeça com foto", quebra_cabeca_foto), "domino": ("Dominó", domino),
    "pista": ("Pista de bola", pista_bola), "sensorial": ("Placa sensorial", placa_sensorial), "boliche": ("Boliche gigante", boliche),
    "memoria": ("Memória de pares", memoria),
}

if __name__ == "__main__":
    os.makedirs(SAIDA, exist_ok=True)
    for slug, (_, f) in CONCEITOS.items():
        m = f().no_chao()
        m.salva(os.path.join(SAIDA, slug + ".stl"))
        lo, hi = m.t.reshape(-1, 3).min(0), m.t.reshape(-1, 3).max(0)
        print(f"{slug:12s} {len(m.t):6d} tri  {hi[0]-lo[0]:.0f} x {hi[1]-lo[1]:.0f} x {hi[2]-lo[2]:.0f} mm")
