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
    crop(art, (3840, 1240), 0.5, 0.48).save(f"{out}/library_hero_3840x1240.jpg", quality=90)
    bg = crop(art, (1438, 810), 0.5, 0.5)
    ImageEnhance.Brightness(bg).enhance(0.55).save(f"{out}/page_background_1438x810.jpg", quality=90)
    lg = logo_img()
    lg.thumbnail((1280, 720), Image.LANCZOS)
    lg.save(f"{out}/library_logo_1280x720.png")
    print(out)


if __name__ == "__main__":
    main()
