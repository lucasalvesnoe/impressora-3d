"""Painel único: 2 câmeras (frente iPhone 1, cima iPhone 2), cada uma normal + zoom, com detecção YOLO
desenhada por cima, mais progresso. q sai.
O zoom da câmera de cima segue a peça (região onde a mesa mudou desde o começo da impressão)."""
import cv2, numpy as np, os, time
from ultralytics import YOLO
MODEL = YOLO(os.environ.get("YOLO_MODEL", "yolo11m.pt"))  # ultralytics baixa o peso se faltar
def le(p):
    try:
        im = cv2.imread(p); return im if im is not None and im.size else None
    except Exception: return None
def caixa(im, w, h):
    tela = np.zeros((h, w, 3), np.uint8)
    if im is None: return tela
    s = min(w / im.shape[1], h / im.shape[0]); r = cv2.resize(im, (int(im.shape[1] * s), int(im.shape[0] * s)))
    y, x = (h - r.shape[0]) // 2, (w - r.shape[1]) // 2; tela[y:y + r.shape[0], x:x + r.shape[1]] = r; return tela
def rotulo(t, txt, cor=(255, 255, 255)):
    cv2.putText(t, txt, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4); cv2.putText(t, txt, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2); return t
def yolo(im):
    if im is None: return None, []
    r = MODEL.predict(im, imgsz=640, conf=0.3, verbose=False)[0]; out = im.copy(); nomes = []
    for b in r.boxes:
        x0, y0, x1, y1 = map(int, b.xyxy[0]); n = MODEL.names[int(b.cls)]; nomes.append(n)
        cv2.rectangle(out, (x0, y0), (x1, y1), (0, 255, 255), 3)
        cv2.putText(out, f"{n} {float(b.conf):.2f}", (x0, max(20, y0 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    return out, nomes
ref = None; zb = None
import json
saude_ant = {}
def saude(nome, im):
    """brilho, nitidez e se a imagem congelou (macOS pausa a Continuity Camera e repete um quadro borrado)."""
    if im is None: return {"ok": False, "motivo": "sem imagem"}
    g = cv2.cvtColor(cv2.resize(im, (320, int(320 * im.shape[0] / im.shape[1]))), cv2.COLOR_BGR2GRAY)
    brilho, nitidez = float(g.mean()), float(cv2.Laplacian(g, cv2.CV_64F).var())
    ant = saude_ant.get(nome); saude_ant[nome] = g
    mexeu = None if ant is None or ant.shape != g.shape else float(np.abs(ant.astype(float) - g).mean())
    motivo = "escuro (acenda a luz)" if brilho < 20 else "borrada ou pausada" if nitidez < 15 else None
    return {"ok": motivo is None, "motivo": motivo, "brilho": round(brilho, 1), "nitidez": round(nitidez, 1), "mudanca": mexeu}
congelado = {}
while True:
    frente, cima, bico = le("latest_full.jpg"), le("cam2/cam2.jpg"), le("bico.jpg")
    zc = None
    if cima is not None:
        h, w = cima.shape[:2]
        hsv = cv2.cvtColor(cv2.resize(cima, (w // 2, h // 2)), cv2.COLOR_BGR2HSV)
        ym = cv2.inRange(hsv, (18, 110, 140), (35, 255, 255))
        ycs, _ = cv2.findContours(ym, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cands = []
        for yc in ycs:
            qx, qy, qw, qh = cv2.boundingRect(yc)
            fill = cv2.contourArea(yc) / float(qw * qh + 1)
            if qw * qh > 40 and 0.6 < qw / qh < 1.6 and 0.25 < fill < 0.85: cands.append((cv2.contourArea(yc), (qx, qy, qw, qh)))
        if cands:
            bx, by, bw2, bh2 = max(cands)[1]; cx, cy, s = (bx + bw2 / 2) * 2, (by + bh2 / 2) * 2, max(bw2, bh2) * 2
            new = np.array([cx - 9 * s, cy - 2.5 * s, cx + 4 * s, cy + 5 * s])
            zb = new if zb is None else (zb if np.abs(new - zb).max() < 1.5 * s else 0.9 * zb + 0.1 * new)
        if zb is not None:
            a, b, c2, dd = [int(v) for v in zb]; zc = cima[max(0, b):min(h, dd), max(0, a):min(w, c2)]
    try:
        sd = {"frente": saude("frente", frente), "cima": saude("cima", cima)}
        for k, v in sd.items():
            congelado[k] = congelado.get(k, 0) + 1 if v.get("mudanca") == 0.0 else 0
            if congelado[k] > 10 and v["ok"]: v.update(ok=False, motivo="imagem congelada")
        open("cams.json.tmp", "w").write(json.dumps(sd)); os.replace("cams.json.tmp", "cams.json")
    except Exception: pass
    for nome, im in (("frente", frente), ("cima", cima), ("bico", bico)):   # versões leves para a central pela internet
        if im is not None:
            k = 960 / max(im.shape[:2])
            cv2.imwrite(f"web_{nome}.jpg", cv2.resize(im, (int(im.shape[1] * k), int(im.shape[0] * k))) if k < 1 else im, [cv2.IMWRITE_JPEG_QUALITY, 72])
    fy, fn = yolo(frente); cy_, cn = yolo(cima)
    A = rotulo(caixa(fy, 640, 360), "FRENTE normal + IA " + ",".join(sorted(set(fn)))[:30])
    B = rotulo(caixa(bico, 640, 360), "FRENTE zoom (bico)")
    C = rotulo(caixa(cy_, 640, 360), "CIMA normal + IA " + ",".join(sorted(set(cn)))[:30])
    D = rotulo(caixa(zc, 640, 360), "CIMA zoom (peca)")
    P = np.full((90, 1280, 3), 30, np.uint8)
    try:
        l = open("progresso.txt").read().strip(); ai, r = l.split("/", 1); t = int(r.split()[0]); pc = int(ai) * 100 // max(t, 1)
    except Exception: ai, t, pc = "0", 1, 0
    cv2.rectangle(P, (20, 25), (900, 65), (90, 90, 90), 2); cv2.rectangle(P, (22, 27), (22 + int(876 * pc / 100), 63), (60, 200, 60), -1)
    cv2.putText(P, f"{pc}%  linha {ai}/{t}  {time.strftime('%H:%M:%S')}", (920, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2)
    painel = np.vstack([np.hstack([A, B]), np.hstack([C, D]), P])
    cv2.imwrite("painel.jpg", painel)
    cv2.imshow("painel impressora", painel)
    if cv2.waitKey(300) & 0xFF == ord("q"): break
