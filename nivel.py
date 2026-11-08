"""Leva o bico a um canto pra nivelar com papel. Uso: nivel.py home | 1..5"""
import serial, sys, time, os
P = {"1": (30, 30), "2": (200, 30), "3": (200, 200), "4": (30, 200), "5": (117, 117)}
s = serial.Serial(os.environ.get('PORTA_IMPRESSORA', '/dev/cu.usbserial-1140'), 115200, timeout=1)
time.sleep(3); s.reset_input_buffer()
def c(x, w=90):
    s.write((x + '\n').encode()); t = time.time(); out = ''
    while time.time() - t < w:
        l = s.readline().decode('latin1'); out += l
        if l.startswith('ok'): break
    return out.strip().replace('\n', ' / ')
a = sys.argv[1]
if a == "home":
    print(c('M140 S60')); print(c('G28', 120)[-80:])
    a = "1"
x, y = P[a]
print(c('G90')); print(c('G1 Z5 F600')); print(c(f'G1 X{x} Y{y} F4000')); print(c('G1 Z0 F300')); print(c('M400', 30)); print(c('M105'))
s.close()
