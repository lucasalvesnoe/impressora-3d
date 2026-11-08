#!/usr/bin/env python3
"""Fala o texto com Fish Audio (pt-BR) e toca com afplay. Parar: bash parar.sh"""
import json, os, subprocess, sys, tempfile, urllib.request
KEY = open(os.path.expanduser("~/.fish-audio/key")).read().strip()
VOZES = {"rick": "bdb4986093f8403d8dad0858c0628aa1", "jarvis": "a5f754f073a14ce3bf544b30efebc2f5"}  # catálogo Fish Audio
VOICE = VOZES.get(os.environ.get("FALAR_VOZ", "rick"), os.environ.get("FALAR_VOZ", ""))
subprocess.run(["pkill", "afplay"])
body = {"text": " ".join(sys.argv[1:]), "reference_id": VOICE, "format": "mp3", "normalize": True, "latency": "balanced"}
req = urllib.request.Request("https://api.fish.audio/v1/tts", data=json.dumps(body).encode(), method="POST",
    headers={"Authorization": f"Bearer {KEY}", "model": "s2.1-pro-free", "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60) as r:
    audio = r.read()
f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False); f.write(audio); f.close()
subprocess.Popen(["afplay", f.name])
