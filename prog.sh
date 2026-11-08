#!/bin/bash
# barra de progresso da impressao (le progresso.txt); para sozinha no fim
while true; do
  l=$(cat progresso.txt 2>/dev/null); a=${l%%/*}; r=${l#*/}; t=${r%% *}
  [ -z "$t" ] && t=1; p=$((a*100/t)); n=$((p/2))
  printf "\r[%-50s] %3d%%  linha %s/%s" "$(printf '#%.0s' $(seq 1 $n))" "$p" "$a" "$t"
  [ "$a" = "$t" ] && echo && break; sleep 2
done
