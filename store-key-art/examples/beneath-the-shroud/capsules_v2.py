"""Capsulas da Steam v2 (11/11/2026): arte-chave renderizada da cena do jogo (casa + tentaculos reais) + logo grande.

  python capsules_v2.py <arte 3840x2160> <saida>

Padrao seguido (pesquisa de 11/11, folha em Docs/Marketing/Steam/2026-11-11/referencias): logo enorme e legivel em
120x45, uma ameaca iconica em silhueta, uma cor dominante (azul de tempestade) e um acento (janela ambar).
Regras Steam: so arte + nome do jogo; small capsule com o logo quase enchendo; library hero sem texto.
"""
import os
import sys

from PIL import Image, ImageEnhance, ImageFilter

LOGO = r"D:\Downloads\GameTitle\gameTitle (1).png"


def logo_img(big_top=False):
    lg = Image.open(LOGO).convert("RGBA")
    a = lg.getchannel("A").point(lambda v: 0 if v <= 24 else v)  # residuo de alfa fazia uma caixa escura na sombra
    lg.putalpha(a)
    lg = lg.crop(a.getbbox())
    if not big_top:
        return lg
    # versao para tamanhos pequenos: "BENEATH THE" do mesmo largo que "SHROUD" (a linha fina sumia em miniatura)
    top, bot = lg.crop((0, 0, lg.width, 96)), lg.crop((0, 110, lg.width, lg.height))
    top = top.crop(top.getchannel("A").point(lambda v: 255 if v > 12 else 0).getbbox())
    tw = round(bot.width * 0.98)
    top = top.resize((tw, round(top.height * tw / top.width)), Image.LANCZOS)
    gap = round(bot.height * 0.06)
    out = Image.new("RGBA", (bot.width, top.height + gap + bot.height), (0, 0, 0, 0))
    out.alpha_composite(top, ((bot.width - tw) // 2, 0))
    out.alpha_composite(bot, (0, top.height + gap))
    return out


def grade(im):
    return im  # a arte v3 ja sai graduada do compose_keyart.py
    im = ImageEnhance.Contrast(im).enhance(1.12)
    lut = [round(255 * (i / 255) ** 0.92) for i in range(256)] * 3
    return im.point(lut)


def crop(im, size, cx, cy, zoom=1.0):
    """Recorte na proporcao de size, centrado em (cx, cy) (fracoes), zoom>1 aproxima."""
    tw, th = size
    r = tw / th
    w, h = im.size
    cw, ch = (round(h * r), h) if w / h > r else (w, round(w / r))
    cw, ch = round(cw / zoom), round(ch / zoom)
    x = min(max(round(cx * w - cw / 2), 0), w - cw)
    y = min(max(round(cy * h - ch / 2), 0), h - ch)
    out = im.crop((x, y, x + cw, y + ch)).resize(size, Image.LANCZOS)
    return out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=2))


def vignette(im, strength=0.55):
    w, h = im.size
    m = Image.radial_gradient("L").resize((w, h)).point(lambda v: int(min(255, v * strength * 1.4)))
    return Image.composite(Image.new("RGB", im.size, (2, 6, 10)), im, m)


def bottom_shade(im, strength=0.9, reach=0.42):
    w, h = im.size
    mask = Image.new("L", (1, h))
    for y in range(h):
        f = (h - y) / h
        mask.putpixel((0, y), int(255 * strength * max(0.0, 1 - f / reach)))
    return Image.composite(Image.new("RGB", im.size, (2, 6, 10)), im, mask.resize(im.size))


def left_shade(im, strength=0.72, reach=0.6):
    """Escurece o ceu atras do logo (no teste em cinza o creme do logo tinha a mesma luminancia do azul)."""
    w, h = im.size
    m = Image.new("L", (w, 1))
    for x in range(w):
        f = x / w
        m.putpixel((x, 0), int(255 * strength * max(0.0, 1 - f / reach) ** 0.8))
    return Image.composite(Image.new("RGB", im.size, (1, 4, 8)), im, m.resize(im.size))


def put_logo(im, width_frac, cx, cy, big_top=False, lift=1.12):
    lg = logo_img(big_top)
    if lift != 1.0:
        al = lg.getchannel("A")
        lg = ImageEnhance.Brightness(lg.convert("RGB")).enhance(lift).convert("RGBA")
        lg.putalpha(al)
    lw = round(im.width * width_frac)
    lg = lg.resize((lw, round(lg.height * lw / lg.width)), Image.LANCZOS)
    x, y = round(im.width * cx - lw / 2), round(im.height * cy - lg.height / 2)
    base = im.convert("RGBA")
    pad = max(12, lw // 6)  # margem: sem ela o desfoque era cortado na borda e aparecia uma caixa escura
    a = Image.new("L", (lg.width + 2 * pad, lg.height + 2 * pad), 0)
    a.paste(lg.getchannel("A"), (pad, pad))
    for blur, alpha in ((max(6, lw // 18), 0.75), (max(2, lw // 90), 0.9)):  # halo escuro largo + sombra justa
        sh = Image.new("RGBA", a.size, (0, 0, 0, 0))
        sh.putalpha(a.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(sh, (x - pad, y - pad + max(1, lw // 200)))
        base.alpha_composite(layer)
    base.alpha_composite(lg, (x, y))
    return base.convert("RGB")


def front_mask(path, x0, x1):
    """Mascara (passe so dos tentaculos) limitada a faixa x0..x1: o tentaculo dessa faixa passa NA FRENTE do logo."""
    m = Image.open(path).convert("L").point(lambda v: 255 if v > 140 else 0)
    w, h = m.size
    keep = Image.new("L", m.size, 0)
    keep.paste(255, (round(x0 * w), 0, round(x1 * w), h))
    from PIL import ImageChops
    return ImageChops.multiply(m, keep).filter(ImageFilter.GaussianBlur(1.2))


def with_front(make, art, mask, size, *crop_args, **crop_kw):
    """make(img_cortada) -> img com logo; depois devolve o tentaculo da frente por cima."""
    c = crop(art, size, *crop_args, **crop_kw)
    out = make(c)
    if mask is None:
        return out
    mc = mask.resize(art.size).crop((0, 0) + art.size)
    mc = crop(mc.convert("RGB"), size, *crop_args, **crop_kw).convert("L")
    return Image.composite(c, out, mc)


def main():
    art_path, out = sys.argv[1], sys.argv[2]
    mask_path = sys.argv[3] if len(sys.argv) > 3 else None
    vart_path = sys.argv[4] if len(sys.argv) > 4 else None
    os.makedirs(out, exist_ok=True)
    art = grade(Image.open(art_path).convert("RGB"))
    fm = front_mask(mask_path, 0.53, 0.68) if mask_path else None
    # casa: centro x ~0,44, base em y ~0,83; arco dos tentaculos: x 0,2..0,64, topo y ~0,1
    # v3 (11/11): logo a esquerda no ceu limpo, nada passa na frente das letras (feedback: atrapalhava a leitura)
    put_logo(left_shade(vignette(crop(art, (920, 430), 0.5, 0.42), 0.45)), 0.49, 0.27, 0.42).save(
        f"{out}/header_capsule_920x430.jpg", quality=93)
    put_logo(left_shade(vignette(crop(art, (1232, 706), 0.5, 0.45), 0.45)), 0.42, 0.235, 0.42).save(
        f"{out}/main_capsule_1232x706.jpg", quality=93)
    small = ImageEnhance.Brightness(crop(art, (462, 174), 0.62, 0.5, zoom=1.0)).enhance(0.6)
    put_logo(small, 0.86, 0.5, 0.5, big_top=True).save(f"{out}/small_capsule_462x174.jpg", quality=93)
    # vertical: render proprio em pe; logo no ceu vazio do alto, como cartaz
    vart = grade(Image.open(vart_path).convert("RGB")) if vart_path else art
    put_logo(vignette(crop(vart, (748, 896), 0.5, 0.5), 0.6), 0.9, 0.5, 0.15, big_top=True).save(
        f"{out}/vertical_capsule_748x896.jpg", quality=93)
    put_logo(vignette(crop(vart, (600, 900), 0.5, 0.5), 0.6), 0.92, 0.5, 0.14, big_top=True).save(
        f"{out}/library_capsule_600x900.jpg", quality=93)
    crop(art, (3840, 1240), 0.5, 0.45).save(f"{out}/library_hero_3840x1240.jpg", quality=90)
    bg = crop(art, (1438, 810), 0.5, 0.5).filter(ImageFilter.GaussianBlur(3))
    ImageEnhance.Brightness(bg).enhance(0.5).save(f"{out}/page_background_1438x810.jpg", quality=90)
    lg = logo_img()
    lg.thumbnail((1280, 720), Image.LANCZOS)
    lg.save(f"{out}/library_logo_1280x720.png")
    print(out)


if __name__ == "__main__":
    main()
