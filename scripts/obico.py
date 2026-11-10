"""Detector de falha do Obico (antigo The Spaghetti Detective) rodando local, sem Docker.

Usa o modelo ONNX oficial (vendor/obico-model/model-weights.onnx, sha256 conferido com o repositório) e o
pós-processamento do próprio obico-server (vendor/obico-server/ml_api/lib). Classe única: "failure".

Uso:
  obico.py imagem.jpg [...]            imprime as detecções de cada imagem
  obico.py --vigia cams/<id>.jpg       a cada INTERVALO s, grava obico.json e obico.jpg (caixas desenhadas)
Python: venv do vigia-piscina (tem cv2 e onnxruntime).
"""
import json, os, sys, time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML = os.path.join(RAIZ, "vendor", "obico-server", "ml_api")
sys.path.insert(0, ML)

import cv2  # noqa: E402
from lib.onnx import OnnxNet  # noqa: E402
from lib.meta import Meta  # noqa: E402

PESOS = os.path.join(RAIZ, "vendor", "obico-model", "model-weights.onnx")
LIMIAR = 0.08          # mesmo THRESH do servidor do Obico
INTERVALO = 10
ARQ_ROI = os.path.join(RAIZ, "obico_roi.json")   # {"x0","y0","x1","y1"} em pixels: só a mesa e a peça
ALERTA_CONF = 0.3      # confiança que conta como falha
ALERTA_SEGUIDOS = 3    # quadros seguidos acima do limiar para avisar (30 s)

_net = None


def rede():
    global _net
    if _net is None:
        _net = OnnxNet(PESOS, os.path.join(ML, "model", "model.meta"), use_gpu=False)
    return _net


def detecta(img):
    n = rede()
    return [(nome, float(conf), tuple(float(v) for v in caixa))
            for nome, conf, caixa in n.detect(n.meta, img, n.meta.names, thresh=LIMIAR)]


def desenha(img, dets):
    out = img.copy()
    for _, conf, (cx, cy, w, h) in dets:
        p1, p2 = (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2))
        cor = (0, 0, 255) if conf >= 0.3 else (0, 200, 255)
        cv2.rectangle(out, p1, p2, cor, 3)
        cv2.putText(out, f"{conf:.2f}", (p1[0], max(20, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
    return out


def na_roi(dets):
    try:
        r = json.load(open(ARQ_ROI))
    except (OSError, ValueError):
        return dets
    return [d for d in dets if r["x0"] <= d[2][0] <= r["x1"] and r["y0"] <= d[2][1] <= r["y1"]]


def avisa(msg):
    import subprocess
    subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "Impressora" sound name "Basso"'])
    open(os.path.join(RAIZ, "obico_alertas.log"), "a").write(f"{time.strftime('%d/%m %H:%M:%S')} {msg}\n")


def vigia(caminho):
    seguidos = 0
    while True:
        img = cv2.imread(caminho)
        if img is not None:
            dets = na_roi(detecta(img))
            pior = max([c for _, c, _ in dets], default=0)
            seguidos = seguidos + 1 if pior >= ALERTA_CONF else 0
            if seguidos == ALERTA_SEGUIDOS:
                avisa(f"Obico: possível falha (confiança {pior:.2f}) há {ALERTA_SEGUIDOS * INTERVALO} s")
            soma = round(sum(c for _, c, _ in dets), 3)
            tmp = os.path.join(RAIZ, "obico.json.tmp")
            json.dump({"t": time.time(), "soma": soma, "max": max([c for _, c, _ in dets], default=0),
                       "deteccoes": [{"conf": round(c, 3), "caixa": [round(v) for v in b]} for _, c, b in dets]},
                      open(tmp, "w"))
            os.replace(tmp, os.path.join(RAIZ, "obico.json"))
            cv2.imwrite(os.path.join(RAIZ, "obico.jpg"), desenha(img, dets))
        time.sleep(INTERVALO)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--vigia"]:
        vigia(sys.argv[2])
    for arq in sys.argv[1:]:
        img = cv2.imread(arq)
        dets = detecta(img)
        print(arq, [(round(c, 3), [round(v) for v in b]) for _, c, b in dets])
        cv2.imwrite(os.path.splitext(arq)[0] + "_obico.jpg", desenha(img, dets))
