# Pendências

## Abertas
1. Central: pausar e cancelar pela página. Hoje a serial é só do `imprime.py`; precisa de um arquivo de
   comando que ele leia entre linhas (M25/M24 não servem: quem pausa é o envio).
2. Câmera de cima (iPhone 2) para de mandar quando a tela bloqueia. Contorno: bloqueio automático em
   Nunca. Melhor: avisar por voz quando a central detectar câmera parada durante impressão.
3. Detecção automática de falha (peça descolando, espaguete) comparando a câmera com a vista 3D da
   camada atual. Hoje a checagem é visual, feita pelo agente a cada poucos minutos.
4. Croissant articulado: o STL começa em z 0,5 sem face plana e não grudou. Cortar 1,5 mm da base ou
   usar brim largo.
5. `zoom.py` e `painel.py` acham o cabeçote pelo triângulo amarelo de aviso; em outra impressora o
   recorte precisa de outra referência.
6. Câmeras próprias da impressora (bico, mesa, alto) para não depender do iPhone nem do Mac: opções em
   `docs/CAMERAS.md`, aguardando a compra.
7. Queda do USB no meio da impressão (cabo solto ao mover o Mac) mata o envio. Retomada hoje é manual;
   automatizar a partir da última linha enviada, com o bico 0,3 mm mais alto.
8. Caminhos fixos que ainda dependem da máquina: venv com OpenCV e ultralytics, `~/.fish-audio/key`.
9. iPhone pelo cabo às vezes não reaparece na USB depois de trocado de aparelho (carrega, mas o Mac não
   enumera). Em 10/11/2026 voltou sozinho depois de cerca de 40 min, sem causa identificada.
10. Obico com falso positivo nas bordas curvas do quebra-cabeça e no preenchimento em grade (até 0,54);
    limite de alerta em 0,65 e conferência visual de cada alerta.
11. Brim é global quando várias peças são fatiadas juntas num STL único; peças planas ganharam brim sem
    precisar. Fatiar por objeto (3MF com configuração por peça) ou sem brim.
12. Link da central: o `link_fixo.py --vigia` para quando o Mac reinicia; falta subir sozinho no login
    (LaunchAgent). Endereço que nunca muda e sem token exige túnel nomeado com domínio próprio ou VPN
    entre os aparelhos (Tailscale).
13. Time-lapse: a câmera escolhida pode deixar de filmar a impressora no meio da impressão (troca de
    cabo ou de aparelho). Detectar quadro sem a mesa e pausar a gravação daquela câmera.

## Resolvidas
- Link da central perdido a cada reinício do túnel: nota "Observatório" atualizada sozinha. 2026-11-10.
- Vista 3D com suportes triangulares (geometria simplificada para caber no túnel): formato TP2 fiel ao
  gcode. 2026-11-10.
- Página da central lenta: vista 3D desenha sob demanda. 2026-11-10.
- Câmera esquecida quando o cabo solta: religação automática. 2026-11-10.
- Bico encostando nos grampos dos cantos da mesa no início: referência de Z no centro. 2026-11-10.
- Primeira camada esmagada (peça presa na mesa): bico 0,05 mm mais alto no início. 2026-11-08.
- Envio morto aos 30 min pelo Monitor: envio com `nohup`, Monitor só lê o log. 2026-11-08.
- Vista 3D piscando (dois desenhos no mesmo plano): trocada pelo caminho do gcode. 2026-11-08.
