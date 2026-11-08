import serial,time,re, os
s=serial.Serial(os.environ.get('PORTA_IMPRESSORA', '/dev/cu.usbserial-1140'),115200,timeout=1)
time.sleep(3); s.reset_input_buffer()
def c(x,w=1.2):
    s.write((x+'\n').encode()); time.sleep(w); return s.read(400).decode('latin1').strip()
r=c('M105'); print(r,flush=True)
m=re.search(r'T:([\d.]+) /([\d.]+)',r)
if m and float(m.group(1))>=190:
    print(c('M83')); print(c('G1 E40 F150',1)); print(c('M400',20),flush=True)
else:
    print('bico frio, nao extrudo',flush=True)
s.close()
