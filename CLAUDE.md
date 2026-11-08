# CLAUDE.md — impressora-3d

Instruções para o agente que opera a impressora.

## Regras de operação
1. Nunca abrir a porta serial enquanto `imprime.py` estiver rodando (`pgrep -fl imprime.py`). Abrir a
   porta reinicia a placa e perde a impressão.
2. Envio sempre com `nohup ... &`, nunca dentro de ferramenta com tempo limite. Acompanhar pelo
   `progresso.txt`, `imprime.log` ou pela central.
3. Qualidade se julga pela câmera, não pelo progresso: olhar o zoom de cima e o `bico.jpg` a cada poucos
   minutos e parar ao primeiro sinal de peça descolando, fio esticado ou espaguete.
4. Afirmação sobre o bico vem do `bico.jpg` (zoom), nunca da imagem inteira.
5. Porta muda de nome ao religar: conferir com `ls /dev/cu.usb*` e exportar `PORTA_IMPRESSORA`.

## Fluxo de uma peça
1. Fatiar com `ender3_pla.ini` e `--center 110,110`.
2. Se a primeira camada estiver esmagando, inserir `G92 Z-0.05` logo depois do `G28` (arquivo `*_z.gcode`).
3. Cadastrar o gcode em `central/modelos.json` (nome, stl, cor do filamento).
4. Mesa limpa e fria, filamento certo saindo limpo no bico, então enviar.

## Arquivos gerados em tempo de execução (não versionar)
`progresso.txt`, `status.json`, `imprime.log`, `latest*.jpg`, `bico.jpg`, `painel.jpg`, `cam2/cam2.jpg`,
`cam2/*.pem`, `*.gcode`, `modelos/`.
