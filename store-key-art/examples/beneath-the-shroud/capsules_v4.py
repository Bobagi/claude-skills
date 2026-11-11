"""Capsulas v4 (11/11/2026): layout aprovado pelo Gustavo (casa embaixo, letreiro logo acima e POR CIMA dos tentaculos),
sobre a arte de compose_keyart_v4.py (ceu de tempestade, relampago, janelas acesas).

  python capsules_v4.py <arte horizontal 3840x2160> <arte vertical 2400x3000> <saida>
"""
import os
import sys

from PIL import Image, ImageEnhance

from capsules_v2 import crop, logo_img, put_logo, vignette


def main():
    hart, vart, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    art = Image.open(hart).convert("RGB")
    va = Image.open(vart).convert("RGB")
    # casa centrada em x ~0,45; telhado em y ~0,62; base 0,81
    put_logo(vignette(crop(art, (920, 430), 0.46, 0.43), 0.35), 0.58, 0.5, 0.40).save(
        f"{out}/header_capsule_920x430.jpg", quality=93)
    put_logo(vignette(crop(art, (1232, 706), 0.46, 0.45), 0.35), 0.52, 0.5, 0.40).save(
        f"{out}/main_capsule_1232x706.jpg", quality=93)
    small = ImageEnhance.Brightness(crop(art, (462, 174), 0.46, 0.66)).enhance(0.7)
    put_logo(small, 0.86, 0.5, 0.48, big_top=True).save(f"{out}/small_capsule_462x174.jpg", quality=93)
    put_logo(vignette(crop(va, (748, 896), 0.5, 0.52), 0.4), 0.88, 0.5, 0.40, big_top=True).save(
        f"{out}/vertical_capsule_748x896.jpg", quality=93)
    put_logo(vignette(crop(va, (600, 900), 0.5, 0.52), 0.4), 0.9, 0.5, 0.39, big_top=True).save(
        f"{out}/library_capsule_600x900.jpg", quality=93)
    # casa acima da barra do PLAY na biblioteca (pedido 11/11)
    # hero: casa centralizada (zoom 1,12) e acima da barra do PLAY; janelas viram brilho continuo, porque o detector
    # de texto da Steam recusou a fileira de janelas acesas ("hero appears to contain text or a logo", 11/11)
    import numpy as np
    from PIL import ImageFilter
    a = np.asarray(art).astype(np.float32)
    xs = np.where(((a[..., 0] > 110) & (a[..., 0] > a[..., 2] * 1.3)).any(axis=0))[0]
    hx = (xs.min() + xs.max()) / 2 / art.width if xs.size else 0.5
    hero = crop(art, (3840, 1240), hx, 0.69, zoom=1.12)
    b = np.asarray(hero).astype(np.float32)
    w = (b[..., 0] > 45) & (b[..., 0] > b[..., 2] * 1.15) & (b[..., 0] > b[..., 1] * 1.05)
    m = Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)).filter(
        ImageFilter.MaxFilter(41)).filter(ImageFilter.GaussianBlur(30))
    Image.composite(hero.filter(ImageFilter.GaussianBlur(28)), hero, m).save(
        f"{out}/library_hero_3840x1240.jpg", quality=90)
    bg = crop(art, (1438, 810), 0.5, 0.5)
    ImageEnhance.Brightness(bg).enhance(0.55).save(f"{out}/page_background_1438x810.jpg", quality=90)
    lg = logo_img()
    lg.thumbnail((1280, 720), Image.LANCZOS)
    lg.save(f"{out}/library_logo_1280x720.png")
    print(out)


if __name__ == "__main__":
    main()
