# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), versão em [SemVer](https://semver.org/lang/pt-BR/).

## [0.2.0] — 2026-11-08

### Adicionado
- Central: barra "Câmeras" para ligar e desligar câmeras. As três fixas (frente, zoom do bico, cima)
  aparecem ou somem na página, com a escolha guardada no navegador. As câmeras de vídeo do Mac
  (FaceTime, iPhone por Continuidade, Visualização da Mesa) são listadas pelo AVFoundation e, quando
  ligadas, abrem um `ffmpeg` que grava um quadro por segundo em `cams/<id>.jpg`; desligar encerra o
  processo. As ligadas ficam em `central/cameras_ativas.json` e reabrem quando a central reinicia
  (`central/cameras.py`, rotas `GET /api/cameras`, `POST /api/cameras` e `GET /img/dev/<id>`).
- Aba Modelos: arquivos baixados (3MF, STL, OBJ) com miniatura e visualizador 3D com medidas e
  verificação de tamanho da mesa; ideias planejadas com capa e conceitos 3D modelados em `criar/`.
- `docs/CAMERAS.md`: pesquisa de fazer ou comprar para três câmeras próprias (bico, mesa, alto), com
  suportes prontos para baixar, câmeras indicadas e preços de referência.
- `cameras.json`: escolha da fonte de cada câmera (câmera do Mac pelo índice, iPhone por Continuidade
  ou página `cam2`).

### Corrigido
- Central avisa câmera escura, borrada ou congelada e esconde a câmera sem imagem.

### Alterado
- Imagens reduzidas (`web_*.jpg`) para a central acessada pela internet; voz padrão Rick.

### Por que
- A câmera é identificada pelo nome, não pelo índice: o índice do AVFoundation muda quando um
  iPhone conecta ou desconecta.
- Ligar câmera é `POST` e segue o mesmo controle de acesso da página (cookie com o token pela
  internet), porque abre um processo no Mac.

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
