# Câmeras próprias da impressora: fazer ou comprar (pesquisa de 2026-11-08)

Objetivo: três câmeras dedicadas, independentes do iPhone e da câmera do MacBook Pro.
1. Presa na impressora, enquadrando a mesa e a peça.
2. Do alto, olhando a bancada inteira.
3. Com zoom no bico.

Preços lidos em 08/11/2026 nas páginas indicadas. Valor sem fonte aparece como NÃO CONFIRMADO.

## Opção 1: suportes prontos para baixar e câmera indicada pelo autor

| Posição | Suporte (download) | Câmera | Preço de referência |
|---|---|---|---|
| Bico | Endoscope Mount for Ender 3, CR-10 (Makers Mashup), https://www.printables.com/model/16299-endoscope-mount-for-ender-3-cr-10 — prende no parafuso do ventilador frontal, sem suporte de impressão, 1 parafuso M3x12, aceita endoscópio de até 9 mm, CC BY 4.0 | Endoscópio USB de 5,5 a 7 mm | R$ 31,29 a R$ 48,10 na Shopee (listagens de busca) |
| Bico (alternativa) | Ender Endoscope Mount (Hans), https://www.printables.com/model/352992-ender-endoscope-mount — endoscópio de 7 mm, ângulo de 60 graus, CC BY 4.0 | Endoscópio USB de 7 mm | idem |
| Mesa | Ender 3 Bed Handle with ESP32 Camera Mount, https://www.printables.com/model/464108-ender-3-bed-handle-with-esp32-camera-mount — a câmera anda com a mesa e mantém a peça sempre no mesmo enquadramento; imprimir com suporte, 4 perímetros, 50% de preenchimento; CC BY-NC 4.0 | ESP32-CAM OV2640 com placa ESP32-CAM-MB (micro USB) | R$ 83,32 na Fermarc; Shopee e AliExpress NÃO CONFIRMADO |
| Alto | Não há suporte pronto específico; a câmera usa o próprio clipe ou uma garra genérica | Webcam USB 1080p com foco manual (UVC) | R$ 80,36 na Shopee (listagem) |

## Opção 2: recomendação (três câmeras USB ligadas ao Mac, suportes modelados no projeto)

Todas as câmeras são UVC (USB Video Class) e ligam num hub USB com fonte própria. O `painel.py` e o `zoom.py` já
leem câmeras pelo índice do AVFoundation, de modo que nenhuma etapa de firmware ou de rede é necessária.

| Posição | Câmera | Suporte |
|---|---|---|
| Bico | Endoscópio USB de 5,5 mm, de preferência com foco curto informado (3 a 5 cm) | Modelado em `criar/`, a partir do encaixe do 16299, com a lente de 30 a 50 mm do bico e inclinada para baixo (recomendação do guia da Obico) |
| Mesa | Webcam USB 1080p com foco manual | Braço modelado em `criar/`, preso no perfil vertical esquerdo, com articulação para ajustar o ângulo |
| Alto | Webcam USB 1080p grande angular | Garra de prateleira ou de tampo modelada em `criar/` |

## Cuidados levantados na pesquisa

1. A maioria dos endoscópios foca entre 5 e 10 cm; é preciso posicionar a lente a essa distância ou girar a lente
   colada para refocar (CNC Kitchen, https://www.cnckitchen.com/blog/3d-printer-nozzle-camera).
2. Endoscópio anunciado como 1080p pode entregar só 640x480 em vídeo (mesma fonte).
3. O calor do bloco aquecedor pode danificar a câmera; o ventilador de peça e uma meia de silicone reduzem o risco.
4. O ESP32-CAM processa a imagem em software, com baixa taxa de quadros e imagem fraca em pouca luz; serve para
   acompanhar, mas limita a detecção de defeitos.
5. O guia de câmera de bico da Obico, https://www.obico.io/docs/user-guides/first_layer_ai/nozzle-camera-printer-installation/,
   aceita qualquer endoscópio USB de 720p ou mais e lista outros suportes para Ender-3.
