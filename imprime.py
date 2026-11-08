"""Manda um .gcode linha a linha pela serial, esperando 'ok'.

Grava:
  progresso.txt  "i/total linha"  (lido por painel.py, prog.sh e central)
  status.json    arquivo, inicio, temperaturas reais (M105 a cada 5 s), fim
  imprime.log    FIM ou ERRO
Uso: imprime.py arquivo.gcode
"""
import json, re, serial, sys, time, os

PORTA = os.environ.get('PORTA_IMPRESSORA', '/dev/cu.usbserial-1140')
INTERVALO_TEMP = 5.0
RE_T = re.compile(r'T:\s*([\d.]+)\s*/\s*([\d.]+)')
RE_B = re.compile(r'B:\s*([\d.]+)\s*/\s*([\d.]+)')

arquivo = sys.argv[1]
linhas = [l.split(";")[0].strip() for l in open(arquivo)]
linhas = [l for l in linhas if l]
status = {"arquivo": arquivo, "inicio": time.time(), "fim": None, "estado": "imprimindo",
          "bico": None, "bico_alvo": None, "mesa": None, "mesa_alvo": None, "temp_em": None}


def grava():
    tmp = "status.json.tmp"
    open(tmp, "w").write(json.dumps(status))
    import os; os.replace(tmp, "status.json")


def le_temp(r):
    t, b = RE_T.search(r), RE_B.search(r)
    if not t:
        return
    status["bico"], status["bico_alvo"] = float(t.group(1)), float(t.group(2))
    if b:
        status["mesa"], status["mesa_alvo"] = float(b.group(1)), float(b.group(2))
    status["temp_em"] = time.time()
    grava()


def manda(cmd):
    s.write((cmd + "\n").encode())
    while True:
        r = s.readline().decode('latin1')
        if 'T:' in r:
            le_temp(r)
        if r.startswith('ok'):
            return
        if 'Error' in r:
            print('ERRO', r.strip(), flush=True)
            open('imprime.log', 'a').write('ERRO ' + r.strip() + '\n')


s = serial.Serial(PORTA, 115200, timeout=1)
time.sleep(3); s.reset_input_buffer()
grava()
ultimo = 0.0
for i, l in enumerate(linhas, 1):
    manda(l)
    open("progresso.txt", "w").write(f"{i}/{len(linhas)} {l}\n")
    if time.time() - ultimo > INTERVALO_TEMP:
        manda("M105"); ultimo = time.time()
status["fim"], status["estado"] = time.time(), "fim"
grava()
print("FIM", flush=True)
open("imprime.log", "a").write("FIM\n")
s.close()
