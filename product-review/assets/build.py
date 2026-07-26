#!/usr/bin/env python3
"""Embute as fontes (woff2 -> data URI) no HTML de origem e gera o index.html final.

Uso:
  python3 build.py [origem.html] [saida.html]

Padroes:
  origem = ./src.html (copia de trabalho; se nao existir, cai para o template.html ao lado deste script)
  saida  = ./index.html

As fontes sao procuradas em ./fonts/ e depois no diretorio do proprio script.
A CSP do Artifact bloqueia CDN de fonte, por isso elas viram data URI aqui.
"""
import base64
import pathlib
import sys

FONTS = {
    "__SORA__": "sora-latin-800.woff2",
    "__JBMONO__": "jbmono-400.woff2",
    "__INTER4__": "inter-400.woff2",
    "__INTER6__": "inter-600.woff2",
}

here = pathlib.Path(__file__).parent
cwd = pathlib.Path.cwd()

src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else cwd / "src.html"
if not src.exists():
    # numa maquina nova ainda nao ha copia de trabalho: parte do template versionado
    src = here / "template.html"
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else cwd / "index.html"


def find_font(fname):
    for base in (cwd / "fonts", cwd, here / "fonts", here):
        p = base / fname
        if p.exists():
            return p
    raise SystemExit(f"ERRO: fonte nao encontrada: {fname} (procurei em ./fonts, ., <skill>/fonts, <skill>)")


html = src.read_text(encoding="utf-8")
for token, fname in FONTS.items():
    b64 = base64.b64encode(find_font(fname).read_bytes()).decode("ascii")
    html = html.replace(token, b64)

out.write_text(html, encoding="utf-8")
print(f"gerado {out} ({len(html)/1024:.0f} KB) a partir de {src}")

missing = [t for t in FONTS if t in html]
if missing:
    raise SystemExit(f"ERRO: placeholders nao substituidos: {missing}")
