"""Visao ao vivo que segue a impressora (recorte automatico na parte preta). q sai.
Salva latest.jpg (recorte) e latest_full.jpg a cada 1s."""
import cv2, time, numpy as np
import os
import json
try: _cfg = json.load(open("cameras.json"))
except Exception: _cfg = {}
FONTE = os.environ.get("CAM_FRENTE") or str(_cfg.get("frente", "1"))   # índice AVFoundation ou caminho de um .jpg (iPhone pela página cam2)
class Arquivo:
    """Lê quadros de um jpg que outro processo atualiza (cam2/frente.jpg)."""
    def __init__(s, p): s.p, s.t = p, 0
    def read(s):
        try:
            t = os.path.getmtime(s.p)
            if t == s.t: time.sleep(0.05); return False, None
            s.t = t; f = cv2.imread(s.p); return f is not None, f
        except OSError: time.sleep(0.2); return False, None
cap = cv2.VideoCapture(int(FONTE), cv2.CAP_AVFOUNDATION) if FONTE.isdigit() else Arquivo(FONTE)
box = None; last = 0; nb = None; nframes = 0
while True:
    ok, f = cap.read()
    if not ok: time.sleep(0.1); continue
    h, w = f.shape[:2]
    small = cv2.resize(f, (w // 4, h // 4))
    dark = (cv2.cvtColor(small, cv2.COLOR_BGR2GRAY) < 55).astype("uint8") * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((15, 15), "uint8"))
    cs, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cs = [c for c in cs if cv2.contourArea(c) > 400]
    if cs:
        x, y, bw, bh = cv2.boundingRect(max(cs, key=cv2.contourArea))
        pad = int(0.08 * max(bw, bh))
        new = np.array([x - pad, y - pad, x + bw + pad, y + bh + pad]) * 4
        nframes += 1
        if nframes < 30: box = new if box is None else (0.8 * box + 0.2 * new)  # trava depois de 30 quadros
    if box is None: box = np.array([0, 0, w, h], dtype=float)
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    half = cv2.resize(f, (w // 2, h // 2)); hsv = cv2.cvtColor(half, cv2.COLOR_BGR2HSV)
    ym = cv2.inRange(hsv, (18, 120, 150), (35, 255, 255))
    ycs, _ = cv2.findContours(ym, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cands = []
    for yc in ycs:
        qx, qy, qw, qh = cv2.boundingRect(yc)
        fill = cv2.contourArea(yc) / float(qw * qh + 1)
        if qw * qh > 80 and 0.7 < qw / qh < 1.4 and 0.3 < fill < 0.8 and (qx + qw / 2) * 2 < 0.7 * w:
            cands.append((cv2.contourArea(yc), (qx, qy, qw, qh)))
    if cands:
        bx, by, bw2, bh2 = max(cands)[1]
        cx, cy, s = (bx + bw2 // 2) * 2, (by + bh2 // 2) * 2, max(bw2, bh2) * 2
        new = np.array([cx - 3.6 * s, cy - 2.0 * s, cx + 3.6 * s, cy + 4.0 * s])
        nb = new if nb is None else nb if np.abs(new - nb).max() < 1.0 * s else (0.8 * nb + 0.2 * new)
    if nb is not None:
        a, b, c2, d = [int(v) for v in nb]
        bico = f[max(0, b):min(h, d), max(0, a):min(w, c2)]
        if bico.size:
            bico = cv2.resize(bico, (800, int(800 * bico.shape[0] / bico.shape[1])), interpolation=cv2.INTER_CUBIC)
            pass  # janela unica: painel.py
            if time.time() - last > 1: cv2.imwrite("bico.jpg", bico)
    c = f[y0:y1, x0:x1]
    if c.size == 0: continue
    c = cv2.resize(c, (1000, int(1000 * c.shape[0] / c.shape[1])), interpolation=cv2.INTER_CUBIC)
    if time.time() - last > 1:
        cv2.imwrite("latest.jpg", c); cv2.imwrite("latest_full.jpg", f); last = time.time()
    pass  # janela unica: painel.py
    time.sleep(0.03)
