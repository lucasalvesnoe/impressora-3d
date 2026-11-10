#!/bin/zsh
# mantém cam2/cam2.jpg vindo do iPhone por Continuidade; reconecta quando o aparelho volta
cd "$(dirname "$0")/.." || exit 1
while true; do
  if ffmpeg -hide_banner -f avfoundation -list_devices true -i "" 2>&1 | grep -q "Câmera do iPhone"; then
    ffmpeg -hide_banner -loglevel error -f avfoundation -framerate 30 -pixel_format nv12 -i "Câmera do iPhone:none" -vf "fps=2,scale='min(1280,iw)':-2" -q:v 4 -update 1 -y cam2/cam2.jpg
  fi
  sleep 3
done
