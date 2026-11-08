"""Manda G-codes pela serial. Uso: cmd.py 'G1 Z50' 'M104 S0' ..."""
import serial, sys, time, os
s = serial.Serial(os.environ.get('PORTA_IMPRESSORA', '/dev/cu.usbserial-1140'), 115200, timeout=1)
time.sleep(3); s.reset_input_buffer()
for x in sys.argv[1:]:
    s.write((x + '\n').encode()); t = time.time(); out = ''
    while time.time() - t < 60:
        l = s.readline().decode('latin1'); out += l
        if l.startswith('ok'): break
    print('>>', x, '|', out.strip().replace('\n', ' / '), flush=True)
s.close()
