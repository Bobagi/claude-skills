"""Monta a folha PNG de comparacao a partir dos renders do render_compare.py (rodar com tools\\.venv).

  python make_sheet.py --renders <pasta> --out folha.png --title "..." --row "Rotulo|linha de info|imagem_entrada.png" ...

Cada linha: imagem de entrada (ou vazio) + texturizado 3/4 frente, recorte ampliado do topo, 3/4 costas + forma cinza frente
e costas.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CELL = 360
HEAD = 64


def font(sz):
    for f in (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def fit(p, bg=(82, 84, 89)):
    im = Image.new("RGB", (CELL, CELL), bg)
    if p and Path(p).exists():
        src = Image.open(p)
        if src.mode == "RGBA":
            b = Image.new("RGBA", src.size, bg + (255,))
            b.alpha_composite(src)
            src = b
        src = src.convert("RGB")
        src.thumbnail((CELL, CELL))
        im.paste(src, ((CELL - src.width) // 2, (CELL - src.height) // 2))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--row", action="append", required=True)
    a = ap.parse_args()
    r = Path(a.renders)
    stats = json.loads((r / "stats.json").read_text()) if (r / "stats.json").exists() else {}
    cols = ["entrada", "textura 3/4 frente", "detalhe (zoom)", "textura 3/4 costas", "forma frente", "forma costas"]
    W = CELL * len(cols)
    rows = [x.split("|") for x in a.row]
    sheet = Image.new("RGB", (W, HEAD + 34 + len(rows) * (CELL + 52)), (24, 25, 28))
    d = ImageDraw.Draw(sheet)
    d.text((14, 12), a.title, fill=(235, 235, 235), font=font(30))
    for i, c in enumerate(cols):
        d.text((i * CELL + 10, HEAD + 6), c, fill=(170, 170, 170), font=font(18))
    y = HEAD + 34
    for label, info, inp in rows:
        tris = stats.get(label, {}).get("tris")
        head = f"{label}  ·  {tris:,} triângulos".replace(",", ".") if tris else label
        d.text((10, y + 4), head, fill=(255, 214, 120), font=font(22))
        d.text((W // 2, y + 8), info, fill=(200, 200, 200), font=font(17))
        y += 40
        imgs = [inp] + [str(r / f"{label}_{k}.png") for k in ("tex_a", "zoom", "tex_b", "clay_a", "clay_b")]
        for i, p in enumerate(imgs):
            if p.endswith("_zoom.png"):
                src = Image.open(str(r / f"{label}_tex_a.png")).convert("RGB")
                w, h = src.size
                cell = src.crop((int(w * .3), int(h * .08), int(w * .7), int(h * .48))).resize((CELL, CELL), Image.LANCZOS)
            else:
                cell = fit(p)
            sheet.paste(cell, (i * CELL, y))
        y += CELL + 12
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
