import re, serial, time, sys
N = int(sys.argv[1])
L = [l.split(";")[0].strip() for l in open(sys.argv[2] if len(sys.argv)>2 else "noite_z.gcode")]
L = [l for l in L if l]
z = x = y = e = None; rel = False
for l in L[:N]:
    u = l.split()[0]
    if u in ("G0","G1"):
        for p in l.split()[1:]:
            v = p[1:]
            try:
                if p[0]=="Z": z=float(v)
                if p[0]=="X": x=float(v)
                if p[0]=="Y": y=float(v)
            except: pass
print("gcode ate N:", "X",x,"Y",y,"Z",z, "ultimas:", L[N-3:N+1])
s = serial.Serial("/dev/cu.usbserial-1140",115200,timeout=1); time.sleep(2); s.reset_input_buffer()
for c in ("M114","M105"):
    s.write((c+"\n").encode()); t=time.time(); out=[]
    while time.time()-t<4:
        r=s.readline().decode("latin1").strip()
        if r: out.append(r)
        if r.startswith("ok"): break
    print(c,out)
s.close()
