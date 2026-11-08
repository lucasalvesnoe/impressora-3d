"""Avisa (1 linha) quando a cena da impressora muda. Le latest.jpg gerado pelo zoom.py."""
import cv2, time, numpy as np
def g():
    im = cv2.imread("latest_full.jpg")
    if im is None: return None
    im = cv2.resize(im, (320, 240))
    x = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), (9, 9), 0).astype("float32")
    return (x - x.mean()) / (x.std() + 1e-6) * 40  # compensa exposicao automatica
base = None; last_emit = 0
while True:
    cur = g()
    if cur is not None:
        if base is None: base = cur
        d = float(np.mean(np.abs(cur - base)))
        if d > 12 and time.time() - last_emit > 12:
            print(f"MUDOU diff={d:.1f}", flush=True); last_emit = time.time(); base = cur
        else:
            base = base * 0.9 + cur * 0.1
    time.sleep(1.5)
