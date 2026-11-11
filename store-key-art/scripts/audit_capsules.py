"""Auditoria de capsulas/arte de loja ANTES de mostrar ao dono (obrigatoria pela skill store-key-art).

  python -I audit_capsules.py <pasta das capsulas> [--refs <pasta>] [--appids 282140,1622910,...] [--genre horror]
                              [--prev <pasta da versao anterior>] [--out <pasta>]

O que faz:
  1. Confere nomes/tamanhos exatos da Steam (header 920x430, small 462x174, main 1232x706, vertical 748x896,
     library 600x900, hero 3840x1240, logo PNG com alfa, page background 1438x810). Tamanho errado = BLOQUEIA.
  2. Baixa (se faltar) as capas de referencia do genero pela CDN publica da Steam e monta a VITRINE: a nossa no meio
     de 20+ capas reais, em tamanho de loja (292x136), colorida e em cinza borrado (teste do olho apertado).
  3. Mede por capsula: luminancia media, contraste (p5-p95), saturacao, variedade de matiz, area chapada, e a
     "separacao do logo" (diferenca de luminancia entre as letras e o fundo logo em volta), na miniatura 120x45.
  4. Escreve report.md com BLOQUEIOS e AVISOS e as imagens vitrine.jpg / vitrine_cinza.jpg / tamanhos.jpg.
     So mostre a arte ao dono se nao houver BLOQUEIO; mostre SEMPRE a vitrine junto.
"""
import argparse
import os
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SIZES = {
    "header_capsule": (920, 430), "small_capsule": (462, 174), "main_capsule": (1232, 706),
    "vertical_capsule": (748, 896), "library_capsule": (600, 900), "library_hero": (3840, 1240),
    "page_background": (1438, 810),
}
GENRES = {  # capas de sucesso conferidas em 11/11/2026 (appids da Steam)
    "horror": [282140, 1622910, 1562430, 1846170, 264710, 1944430, 1262350, 2475490, 1996010, 1295920, 2124490,
               860510, 1693980, 238320, 750130, 399810, 939850, 1946700, 594330, 1670870, 739630, 1966720, 304650,
               999220, 1092790, 274520],
}
CDN = "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{}/header.jpg"


def metrics(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255
    lum = a @ np.array([0.299, 0.587, 0.114])
    hsv = np.asarray(im.convert("HSV")).astype(np.float32)
    sat = hsv[..., 1] / 255
    hue = hsv[..., 0][sat > 0.15]
    hist = np.bincount((hue / 256 * 24).astype(int), minlength=24) / max(1, hue.size)
    g = np.asarray(im.convert("L").resize((im.width // 4 * 4, im.height // 4 * 4))).astype(np.float32)
    h, w = g.shape
    blocks = g.reshape(h // 4, 4, w // 4, 4).std(axis=(1, 3))
    return {
        "lum": float(lum.mean()), "contrast": float(np.percentile(lum, 95) - np.percentile(lum, 5)),
        "sat": float(sat.mean()), "hues": int((hist > 0.01).sum()), "flat": float((blocks < 2.0).mean()),
    }


def logo_separation(small):
    """Na miniatura 120x45: diferenca entre os pixels mais claros (letras) e o fundo mediano. <0,25 = logo some."""
    t = np.asarray(small.convert("L").resize((120, 45), Image.LANCZOS)).astype(np.float32) / 255
    return float(np.percentile(t, 92) - np.median(t))


def fetch_refs(refs, appids):
    os.makedirs(refs, exist_ok=True)
    for ap in appids:
        p = os.path.join(refs, f"{ap}_header.jpg")
        if os.path.exists(p):
            continue
        try:
            urllib.request.urlretrieve(CDN.format(ap), p)
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("caps")
    ap.add_argument("--refs", default=None)
    ap.add_argument("--appids", default=None)
    ap.add_argument("--genre", default="horror")
    ap.add_argument("--prev", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(a.caps, "_auditoria")
    os.makedirs(out, exist_ok=True)
    refs = a.refs or os.path.join(out, "referencias")
    appids = [int(x) for x in a.appids.split(",")] if a.appids else GENRES.get(a.genre, [])
    fetch_refs(refs, appids)

    block, warn, rows = [], [], []
    # limiares relativos ao genero: as proprias capas de sucesso dizem o que e "chapado" ou "sem contraste" demais
    rm = [metrics(Image.open(os.path.join(refs, f))) for f in os.listdir(refs) if f.endswith(".jpg")]
    flat_max = float(np.percentile([m["flat"] for m in rm], 90)) if rm else 0.45
    con_min = float(np.percentile([m["contrast"] for m in rm], 10)) if rm else 0.35
    files = {f.rsplit(".", 1)[0]: os.path.join(a.caps, f) for f in os.listdir(a.caps) if f.lower().endswith((".jpg", ".png"))}
    for key, size in SIZES.items():
        f = next((p for n, p in files.items() if n.startswith(key)), None)
        if not f:
            block.append(f"falta {key} ({size[0]}x{size[1]})")
            continue
        im = Image.open(f)
        if im.size != size:
            block.append(f"{os.path.basename(f)} tem {im.size}, a Steam pede {size}")
        m = metrics(im)
        rows.append((os.path.basename(f), m))
        if key == "page_background":
            continue  # a Steam escurece e borra o fundo da pagina de proposito
        if m["flat"] > flat_max:
            warn.append(f"{os.path.basename(f)}: area chapada {m['flat']:.2f} > {flat_max:.2f} (p90 das referencias)")
        if m["contrast"] < con_min:
            warn.append(f"{os.path.basename(f)}: contraste {m['contrast']:.2f} < {con_min:.2f} (p10 das referencias)")
    logo = next((p for n, p in files.items() if n.startswith("library_logo")), None)
    if not logo:
        block.append("falta library_logo (PNG transparente, ate 1280x720)")
    elif Image.open(logo).mode != "RGBA":
        block.append("library_logo precisa ser PNG com transparencia")
    small = next((p for n, p in files.items() if n.startswith("small_capsule")), None)
    if small:
        sep = logo_separation(Image.open(small))
        (block if sep < 0.25 else warn if sep < 0.35 else []).append(
            f"separacao do logo na small 120x45 = {sep:.2f} (bloqueia <0,25; bom >=0,35)")

    # vitrine
    header = next((p for n, p in files.items() if n.startswith("header_capsule")), None)
    rfs = sorted(os.path.join(refs, f) for f in os.listdir(refs) if f.endswith(".jpg"))
    grid = rfs[:]
    if header:
        grid.insert(min(9, len(grid)), header)
    if a.prev:
        ph = next((os.path.join(a.prev, f) for f in os.listdir(a.prev) if f.startswith("header_capsule")), None)
        if ph:
            grid.insert(min(3, len(grid)), ph)
    W, H, cols = 292, 136, 6
    rws = (len(grid) + cols - 1) // cols

    def sheet(t):
        o = Image.new("RGB", (cols * (W + 8) + 8, rws * (H + 8) + 8), (27, 40, 56))
        d = ImageDraw.Draw(o)
        for i, f in enumerate(grid):
            x, y = 8 + (i % cols) * (W + 8), 8 + (i // cols) * (H + 8)
            o.paste(t(Image.open(f).convert("RGB").resize((W, H))), (x, y))
            if f == header:
                d.rectangle((x - 3, y - 3, x + W + 2, y + H + 2), outline=(255, 200, 0), width=3)
            elif a.prev and f.startswith(a.prev):
                d.rectangle((x - 3, y - 3, x + W + 2, y + H + 2), outline=(200, 60, 60), width=3)
        return o

    sheet(lambda im: im).save(os.path.join(out, "vitrine.jpg"), quality=88)
    sheet(lambda im: ImageOps.grayscale(im.filter(ImageFilter.GaussianBlur(4))).convert("RGB")).save(
        os.path.join(out, "vitrine_cinza.jpg"), quality=88)
    if small and header:
        s, hd = Image.open(small).convert("RGB"), Image.open(header).convert("RGB")
        o = Image.new("RGB", (920 + 470, 430), (27, 40, 56))
        o.paste(hd, (0, 0))
        o.paste(s, (928, 0))
        o.paste(s.resize((184, 69)), (928, 190))
        o.paste(s.resize((120, 45)), (1130, 190))
        o.paste(hd.resize((292, 136)), (928, 280))
        o.save(os.path.join(out, "tamanhos.jpg"), quality=88)

    with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("# Auditoria de capsulas\n\n")
        fh.write("## BLOQUEIOS\n" + ("".join(f"- {b}\n" for b in block) or "- nenhum\n"))
        fh.write("\n## AVISOS\n" + ("".join(f"- {w_}\n" for w_ in warn) or "- nenhum\n"))
        fh.write("\n## Metricas\n| arquivo | lum | contraste | sat | matizes | chapado |\n|---|---|---|---|---|---|\n")
        for n, m in rows:
            fh.write(f"| {n} | {m['lum']:.2f} | {m['contrast']:.2f} | {m['sat']:.2f} | {m['hues']} | {m['flat']:.2f} |\n")
        fh.write("\nAbra vitrine.jpg e vitrine_cinza.jpg: a nossa (borda amarela) precisa ler o NOME e a AMEACA "
                 "no meio das outras, inclusive borrada. Responda por escrito os itens do checklist do SKILL.md.\n")
    print(open(os.path.join(out, "report.md"), encoding="utf-8").read())
    print("saida:", out)
    raise SystemExit(1 if block else 0)


if __name__ == "__main__":
    main()
