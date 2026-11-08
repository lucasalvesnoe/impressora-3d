"""Microfone aberto: grava blocos de 6s, transcreve com whisper-cli local, imprime 'OUVI: texto'.
Ignora blocos enquanto o Claude fala (afplay rodando). Uso: ouvir.py [indice_mic_avfoundation]"""
import os, subprocess, sys, time, glob, wave, re
import numpy as np
MIC = sys.argv[1] if len(sys.argv) > 1 else "1"
D = "/private/tmp/claude-501/-Users-admin-Documents-Labs/aa93b7ce-24b4-4a77-b6b0-0df8d6dbdc09/scratchpad/mic"
os.makedirs(D, exist_ok=True)
for f in glob.glob(D + "/*.wav"): os.replace(f, f + ".old")
MODEL = os.path.expanduser("~/Documents/Labs/voice-claude/models/ggml-small.bin")
LIXO = re.compile(r"^(obrigad[oa]|legendas?.*|tchau|\.+|\[.*\]|\(.*\)|música)\W*$", re.I)
rec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-f", "avfoundation", "-i", f":{MIC}", "-ac", "1", "-ar", "16000",
                        "-f", "segment", "-segment_time", "6", f"{D}/c%05d.wav"])
feitos = set(); falando_ate = 0
while True:
    if subprocess.run(["pgrep", "-x", "afplay"], capture_output=True).returncode == 0:
        falando_ate = time.time() + 1.5
    arqs = sorted(glob.glob(D + "/c*.wav"))
    for a in arqs[:-1]:
        if a in feitos: continue
        feitos.add(a)
        if os.path.getmtime(a) < falando_ate: continue
        try:
            w = wave.open(a); fr = w.readframes(w.getnframes()); w.close()
            x = np.frombuffer(fr, dtype=np.int16).astype(float)
            if len(x) == 0 or np.sqrt((x ** 2).mean()) < 250: continue
        except Exception: continue
        r = subprocess.run(["whisper-cli", "-m", MODEL, "-l", "pt", "-nt", "-np", "-f", a], capture_output=True, text=True)
        t = " ".join(r.stdout.split()).strip()
        if t and not LIXO.match(t): print("OUVI:", t, flush=True)
    time.sleep(0.5)
