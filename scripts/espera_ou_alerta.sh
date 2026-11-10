#!/bin/bash
# Espera até N minutos; sai antes se o Obico passar do limite ou se o imprime.py acabar.
# Uso: scripts/espera_ou_alerta.sh minutos [limite]
cd "$(dirname "$0")/.." || exit 1
fim=$(( $(date +%s) + ${1:-20} * 60 )); lim=${2:-0.30}
while [ "$(date +%s)" -lt "$fim" ]; do
  m=$(/opt/homebrew/bin/python3.14 -c "import json;print(json.load(open('obico.json'))['max'])" 2>/dev/null || echo 0)
  if /opt/homebrew/bin/python3.14 -c "import sys;sys.exit(0 if float('$m')>=float('$lim') else 1)"; then echo "ALERTA obico max=$m"; break; fi
  livre=$(df -m "$PWD" | tail -1 | awk '{print $4}')
  [ "$livre" -lt 2000 ] && { echo "ALERTA disco livre ${livre} MB"; break; }
  pgrep -f "Python -u imprime.py" >/dev/null || { echo "IMPRIME TERMINOU"; break; }
  sleep 30
done
date +%H:%M:%S; cat progresso.txt; echo; tail -1 imprime.out.* 2>/dev/null | tail -1
