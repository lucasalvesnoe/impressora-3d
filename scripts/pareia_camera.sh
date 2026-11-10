#!/bin/bash
# Coloca uma câmera Mini A9 (tipo iLnk, rede BATC.../FTYC...) no Wi-Fi de casa, sem app.
# A senha do Wi-Fi é digitada pelo Lucas num diálogo do macOS (texto oculto); não fica em arquivo nem em log.
# O Mac sai da internet por cerca de 1 minuto: entra na rede da câmera, manda a configuração e volta.
# A impressão não é afetada (a impressora está no USB).
set -u
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
CR="$RAIZ/vendor/cam-reverse"
LOG="$RAIZ/vendor/pareia.log"
CASA_ATUAL="$(networksetup -getairportnetwork en0 | sed -n 's/^Current Wi-Fi Network: //p')"
# macOS novo esconde o nome da rede atual; cai na primeira rede preferida (a de casa)
[ -z "$CASA_ATUAL" ] && CASA_ATUAL="$(networksetup -listpreferredwirelessnetworks en0 | sed -n '2s/^[[:space:]]*//p')"
REDE_CAMERA_PADRAO="${REDE_CAMERA:-}"   # nome da rede de 2,4 GHz; vem do ambiente, nunca fica no repositório

pergunta() {  # $1 texto, $2 padrão, $3 "oculto" ou vazio
  local oculto=""; [ "${3:-}" = oculto ] && oculto="with hidden answer"
  osascript -e "text returned of (display dialog \"$1\" default answer \"$2\" $oculto with title \"Câmera da impressora\")" 2>/dev/null
}

CAM=$(pergunta "Nome da rede Wi-Fi da câmera (a que começa com BAT, igual aparece no iPhone):" "${1:-BATC}") || exit 1
CASA=$(pergunta "Wi-Fi de 2,4 GHz para a câmera usar:" "$REDE_CAMERA_PADRAO") || exit 1
SENHA=$(pergunta "Senha do Wi-Fi $CASA (fica só na câmera; não é salva em lugar nenhum):" "" oculto) || exit 1

echo "$(date +%T) rede atual: $CASA_ATUAL; entrando em $CAM" > "$LOG"
if networksetup -setairportnetwork en0 "$CAM" 2>&1 | tee -a "$LOG" | grep -q "Could not find"; then
  osascript -e "display dialog \"Não achei a rede $CAM. Confira o nome completo no iPhone (Ajustes > Wi-Fi) e rode de novo.\" buttons {\"OK\"} with title \"Câmera da impressora\"" >/dev/null 2>&1
  unset SENHA; exit 2
fi
# esperar o DHCP da câmera (169.254.x = ainda sem endereço)
for i in $(seq 1 60); do case "$(ipconfig getifaddr en0)" in ""|169.254.*) sleep 1;; *) break;; esac; done
IP=$(ipconfig getifaddr en0); echo "$(date +%T) IP na rede da câmera: $IP" >> "$LOG"
BC=$(echo "$IP" | sed 's/\.[0-9]*$/.255/')
case "$IP" in 169.254.*) BC=255.255.255.255;; esac
( cd "$CR" && timeout 40 node dist/bin.cjs pair --ssid "$CASA" --password "$SENHA" --discovery_ip "$BC" ) 2>&1 \
  | grep -v -- "$SENHA" >> "$LOG"
unset SENHA
echo "$(date +%T) voltando para $CASA_ATUAL" >> "$LOG"
networksetup -setairportnetwork en0 "$CASA_ATUAL" >> "$LOG" 2>&1
for i in $(seq 1 30); do ping -c1 -t2 1.1.1.1 >/dev/null 2>&1 && break; sleep 2; done
echo "$(date +%T) internet: $(ping -c1 -t2 1.1.1.1 >/dev/null 2>&1 && echo ok || echo FORA)" >> "$LOG"
cat "$LOG"
