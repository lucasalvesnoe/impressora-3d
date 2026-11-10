"""Vigia cam2/cam2.jpg: avisa câmera ligada/desligada e JOINHA (polegar para cima) com cooldown."""
import os, sys, time, cv2, mediapipe as mp
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision
ARQ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cam2", "cam2.jpg")
rec = vision.GestureRecognizer.create_from_options(vision.GestureRecognizerOptions(
    base_options=mpp.BaseOptions(model_asset_path=sys.argv[1]), num_hands=2, min_hand_detection_confidence=0.4))
ult, viva, seguidos, pausa = 0, None, 0, 0
print("vigia de joinha pronto", flush=True)
while True:
    try: m = os.path.getmtime(ARQ)
    except OSError: m = 0
    agora = time.time()
    v = agora - m < 10
    if v != viva:
        print("CAMERA IPHONE " + ("LIGADA" if v else "SEM IMAGEM"), flush=True); viva = v
    if v and m != ult:
        ult = m
        img = cv2.imread(ARQ)
        if img is not None:
            r = rec.recognize(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
            achou = any(g and g[0].category_name == "Thumb_Up" and g[0].score > 0.6 for g in r.gestures)
            seguidos = seguidos + 1 if achou else 0
            if seguidos >= 2 and agora > pausa:
                cv2.imwrite(os.path.join(os.path.dirname(sys.argv[1]), "joinha.jpg"), img)
                print(f"JOINHA {time.strftime('%H:%M:%S')}", flush=True); pausa = agora + 12; seguidos = 0
    time.sleep(0.4)
