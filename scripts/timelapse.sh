#!/bin/bash
# Time-lapse: copia um quadro de cada câmera a cada INTERVALO segundos até a impressão terminar
# (status.json com estado "fim" e imprime.py parado). Depois monta um mp4 por câmera a 30 quadros/s.
# Uso: scripts/timelapse.sh nome [intervalo_s] [cam1.jpg cam2.jpg ...]
cd "$(dirname "$0")/.." || exit 1
NOME=${1:-timelapse}; INT=${2:-20}; shift 2 2>/dev/null
CAMS=("$@"); [ ${#CAMS[@]} -eq 0 ] && CAMS=(cams/746e858d57.jpg cams/48d0c85642.jpg)
DIR=timelapse/$NOME; mkdir -p "$DIR"
n=$(ls "$DIR"/$(basename "${CAMS[0]}" .jpg)_*.jpg 2>/dev/null | wc -l | tr -d ' ')
while true; do
  n=$((n + 1))
  for c in "${CAMS[@]}"; do
    [ -f "$c" ] && cp "$c" "$DIR/$(basename "$c" .jpg)_$(printf %05d $n).jpg"
  done
  est=$(/opt/homebrew/bin/python3.14 -c "import json;print(json.load(open('status.json')).get('estado'))" 2>/dev/null)
  if [ "$est" = "fim" ] && ! pgrep -f "Python -u imprime.py" >/dev/null; then break; fi
  sleep "$INT"
done
for c in "${CAMS[@]}"; do
  b=$(basename "$c" .jpg)
  ffmpeg -y -loglevel error -framerate 30 -pattern_type glob -i "$DIR/${b}_*.jpg" \
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -pix_fmt yuv420p "$DIR/$NOME-$b.mp4"
done
echo "PRONTO $(date +%H:%M) $(ls "$DIR"/*.mp4)"
