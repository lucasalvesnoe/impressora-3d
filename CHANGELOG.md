# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), versão em [SemVer](https://semver.org/lang/pt-BR/).

## [0.1.0] — 2026-11-08

Primeira versão. Montada em uma tarde, operando uma Creality Ender-3 de verdade pelo USB, com o
Claude Code como operador e instrutor por voz.

### Adicionado
- `imprime.py`: envia o `.gcode` linha a linha pela serial esperando `ok`; grava `progresso.txt`,
  `imprime.log` e `status.json` com as temperaturas reais (M105 a cada 5 s). Porta configurável por
  `PORTA_IMPRESSORA`. Roda com `nohup` para sobreviver ao fim do terminal que o chamou.
- `cmd.py`, `nivel.py`, `ext.py`: G-code avulso, bico nos cantos para nivelar com papel, testes do extrusor.
- `gera_teste.py` e `gera_cachorro.py`: geram G-code direto, sem fatiador (quadrado de 30 mm, cachorrinho).
- `ender3_pla.ini`: perfil do PrusaSlicer para Ender-3 com PLA (mesa 220x220, 205/60 °C, camada 0,2 mm).
- Câmeras: `zoom.py` (iPhone por Continuity, recorte da impressora e zoom travado no bico), `cam2/`
  (segundo iPhone envia quadros por uma página HTTPS local), `painel.py` (as duas câmeras, normal e
  zoom, com detecção YOLO e barra de progresso), `vigia.py` (avisa mudança de cena).
- Voz: `falar.py` (TTS do Fish Audio em pt-BR) e `ouvir.py` (microfone com whisper local).
- Central web (`central/`): servidor Python sem dependências na porta 8090 que só lê arquivos, nunca
  a serial. Mostra o caminho real do bico em 3D (cada filete do gcode, com a grade interna), um
  display no estilo do LCD da Ender, tempos, filamento, as câmeras com aviso de câmera parada e a
  lista de arquivos prontos.
- Vista 3D com bico animado de forma contínua: anda em milímetros pelo caminho, uns 2 s atrás do
  progresso real, e o filete atual cresce enquanto ele passa. Botões de camada, só a camada, corte
  ao meio, cor por tipo ou do filamento, e vistas iso, topo e frente.

### Por que algumas escolhas
- A vista 3D desenha o gcode, não o STL: o STL não mostra a grade interna nem o que já saiu do bico.
- O bico sobe 0,05 mm no início (`G92 Z-0.05` depois do `G28`, arquivos `*_z.gcode`): a primeira
  camada estava esmagada e a peça não soltava da mesa.
- O envio nunca roda dentro de uma ferramenta com tempo limite (o Monitor do Claude Code mata o
  processo em 30 min): impressão de 1 h pararia no meio.
