#!/usr/bin/env python3
"""Mantém uma nota "Observatório" no app Notas com o link atual da central.

O túnel rápido do Cloudflare troca de endereço sempre que reinicia. A nota, sincronizada pelo iCloud,
aparece em todos os aparelhos da mesma conta; basta fixá-la uma vez no app Notas.

A nota leva o token de acesso da central. Não compartilhe a nota; o app Notas só tem criptografia de
ponta a ponta com a Proteção Avançada de Dados do iCloud ligada.

Uso:
  python3 scripts/link_fixo.py           atualiza a nota uma vez
  python3 scripts/link_fixo.py --vigia   confere a cada 60 s e atualiza quando o endereço muda

O token vai para o osascript pela entrada padrão, nunca pela linha de comando.
"""
import html
import os
import re
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_TUNEL = os.path.join(RAIZ, "central", "tunel.log")
ARQ_TOKEN = os.path.join(RAIZ, "central", ".token")
TITULO = "Observatório"
INTERVALO_S = 60
TEMPO_LIMITE_S = 60


def url_tunel():
    try:
        texto = open(LOG_TUNEL, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    achados = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", texto)
    return achados[-1] if achados else None



def corpo(url):
    token = open(ARQ_TOKEN).read().strip()
    fora = f"{url}/?k={token}"
    hora = time.strftime("%d/%m %H:%M")
    # só o link pelo túnel: o endereço .local só resolve na mesma rede do Mac, e os aparelhos trocam de rede
    linhas = [
        f"<h1>{TITULO}</h1>",
        f'<div><a href="{html.escape(fora)}">abrir a central</a> (funciona em qualquer rede)</div>',
        "<div><br></div>",
        f"<div>Atualizada sozinha em {hora}. O endereço de fora muda quando o túnel reinicia.</div>",
    ]
    return "".join(linhas)


def escreve_nota(conteudo):
    esc = conteudo.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "Notes"
    set achadas to (notes whose name is "{TITULO}")
    if (count of achadas) > 0 then
        set body of item 1 of achadas to "{esc}"
    else
        make new note at folder "Notes" of default account with properties {{body:"{esc}"}}
    end if
end tell
'''
    ok, erro = _osascript(script)
    if not ok:
        # pasta padrão pode se chamar "Notas" em português
        ok, erro = _osascript(script.replace('folder "Notes"', 'folder "Notas"'))
    return ok, erro


def _osascript(script):
    """O app Notas às vezes não responde (sincronização do iCloud); sem limite, o vigia travava para sempre."""
    try:
        r = subprocess.run(["osascript", "-"], input=script, capture_output=True, text=True, timeout=TEMPO_LIMITE_S)
    except subprocess.TimeoutExpired:
        return False, f"Notas não respondeu em {TEMPO_LIMITE_S} s"
    return r.returncode == 0, r.stderr.strip()


def main():
    vigia = "--vigia" in sys.argv
    ultimo = None
    while True:
        url = url_tunel()
        if url and url != ultimo:
            ok, erro = escreve_nota(corpo(url))
            print(time.strftime("%H:%M"), "nota atualizada" if ok else f"falhou: {erro}", url, flush=True)
            if ok:
                ultimo = url
        if not vigia:
            return
        time.sleep(INTERVALO_S)


if __name__ == "__main__":
    main()
