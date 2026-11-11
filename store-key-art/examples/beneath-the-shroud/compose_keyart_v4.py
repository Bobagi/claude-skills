"""Arte-chave v4 (11/11/2026): layout aprovado (casa embaixo, letreiro logo acima, tentaculos em volta) com ceu de
tempestade fotografico, relampago e janelas acesas que chamam a atencao.

  python compose_keyart_v4.py <prefixo dos passes> <foto do ceu> <saida.png> [opcoes]

Passes (shot2.cs/render.py): _p0 completo, _p2 sem tentaculos, _p3 tentaculos em cores (R,G,B,branco), _p4 so vidros.
Ceu: foto CC0 (SourceAssets/Marketing/storm_sky), recolorida para o azul-petroleo do jogo.
Feedback que guiou (Gustavo, 11/11): ceu "limpo, sem nada", luzes da casa "horriveis, sem chamar atencao", letreiro
deve ficar POR CIMA dos tentaculos e logo acima da casa.
"""
import argparse
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import distance_transform_edt, label, sobel


def load(p, size=None):
    im = Image.open(p).convert("RGB")
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def blur(a, r):
    if a.ndim == 2:
        im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "L")
        return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0


def fblur(a, r):
    """Desfoque em float (sem truncar em 8 bits), por canal, via reducao + ampliacao para raios grandes."""
    h, w = a.shape[:2]
    k = max(1, int(r // 8))
    small = Image.fromarray(np.clip(a * 255 / max(a.max(), 1e-6), 0, 255).astype(np.uint8))
    sm = small.resize((max(1, w // k), max(1, h // k)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(r / k))
    out = np.asarray(sm.resize((w, h), Image.BILINEAR)).astype(np.float32) / 255.0
    return out * max(a.max(), 1e-6)


def cover(photo, w, h, cx, cy, zoom, flip):
    im = Image.open(photo).convert("RGB")
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    pw, ph = im.size
    s = max(w / pw, h / ph) * zoom
    im = im.resize((round(pw * s), round(ph * s)), Image.LANCZOS)
    x = int(np.clip(cx * im.width - w / 2, 0, im.width - w))
    y = int(np.clip(cy * im.height - h / 2, 0, im.height - h))
    return np.asarray(im.crop((x, y, x + w, y + h))).astype(np.float32) / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix")
    ap.add_argument("sky")
    ap.add_argument("out")
    ap.add_argument("--hz", type=float, default=0.80, help="horizonte (fracao da altura)")
    ap.add_argument("--sky-pos", default="0.5,0.45,1.0,0", help="cx,cy,zoom,flip da foto do ceu")
    ap.add_argument("--glow", default="0.55,0.55")
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    rnd = random.Random(a.seed)

    full = load(a.prefix + "_p0.png")
    h, w, _ = full.shape
    hp = load(a.prefix + "_p2.png", (w, h))
    tm = load(a.prefix + "_p3.png", (w, h))
    wm = load(a.prefix + "_p4.png", (w, h)).max(axis=2)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hz = int(a.hz * h)
    gx, gy = [float(v) for v in a.glow.split(",")]

    # mascaras
    r, g, b = tm[..., 0], tm[..., 1], tm[..., 2]
    tmasks = [(r > .5) & (g < .4) & (b < .4), (g > .5) & (r < .4) & (b < .4), (b > .5) & (r < .4) & (g < .4),
              (r > .5) & (g > .5) & (b > .5)]
    tdepth = [0.05, 0.03, 0.06, 0.38]
    anyt = np.zeros((h, w), bool)
    for m in tmasks:
        anyt |= m
    # casa: diferenca entre o passe sem tentaculos (_p2) e o so-ceu (_p1) + os vidros
    p1 = load(a.prefix + "_p1.png", (w, h))
    diff = np.abs(hp - p1).max(axis=2)
    house = ((diff > 0.05) & (yy > h * 0.15) & (yy < hz + h * 0.01)) | (wm > 0.5)
    house = np.asarray(Image.fromarray((house * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))) > 127
    hl = label(house)[0]
    if hl.max() > 0:
        sizes = np.bincount(hl.ravel())
        sizes[0] = 0
        keep = sizes > sizes.max() * 0.02
        keep[0] = False
        house = keep[hl] | (wm > 0.5)

    # 1. ceu de tempestade (foto), recolorido: sombras azul-marinho, luzes ciano frio, relampago branco-azulado
    cx, cy, z, fl = [float(v) for v in a.sky_pos.split(",")]
    ph = cover(a.sky, w, hz + int(h * 0.05), cx, cy, z, fl > 0.5)
    sky = np.zeros((h, w, 3), np.float32)
    sky[: ph.shape[0]] = ph
    sky[ph.shape[0]:] = ph[-1]
    L = sky.mean(axis=2)
    L = np.clip((L - 0.03) / 0.85, 0, 1) ** 0.9
    lo, mid, hi = np.array([0.01, 0.025, 0.045]), np.array([0.10, 0.22, 0.30]), np.array([0.80, 0.93, 1.0])
    t = L[..., None]
    sky = np.where(t < 0.5, lo + (mid - lo) * (t / 0.5), mid + (hi - mid) * ((t - 0.5) / 0.5))
    # brilho de tempestade atras da casa (contraluz das silhuetas)
    d = np.sqrt(((xx - gx * w) / (w * 0.55)) ** 2 + ((yy - gy * h) / (h * 0.55)) ** 2)
    sky = sky * (1 + np.exp(-d ** 2 * 1.2)[..., None] * 1.3) + np.exp(-d ** 2 * 1.5)[..., None] * np.array([0.10, 0.22, 0.27]) * 1.6
    out = np.clip(sky, 0, 1).astype(np.float32)
    sky_lit = out.copy()

    # 2. tentaculos: silhueta escura com volume e contorno de luz (do brilho/relampago)
    for i in sorted(range(4), key=lambda k: -tdepth[k]):
        m = tmasks[i].astype(np.float32)
        if m.sum() < 50:
            continue
        fogk = tdepth[i]
        dt = distance_transform_edt(m > 0.5)
        rad = max(3.0, np.percentile(dt[dt > 0], 97))
        nz = np.sqrt(np.clip(1 - (1 - np.clip(dt / rad, 0, 1)) ** 2, 0, 1))
        gxm, gym = sobel(dt, axis=1), sobel(dt, axis=0)
        gl = np.hypot(gxm, gym) + 1e-6
        lx, ly = gx * w - xx, gy * h - yy
        ll = np.hypot(lx, ly) + 1e-6
        facing = np.clip(-(gxm / gl) * lx / ll - (gym / gl) * ly / ll, 0, 1) * (1 - nz) ** 2 * (m > .5)
        fl_ = full.mean(axis=2)
        detail = np.clip((fl_ - blur(full, 6).mean(axis=2)) * 6, -1, 1)
        base = np.clip((yy - (hz - h * 0.2)) / (h * 0.22), 0, 1)[..., None]
        fill = np.array([0.008, 0.016, 0.026]) * (1 - fogk) + sky_lit * fogk
        fill = fill * (0.6 + 0.2 * nz[..., None]) * (1 + detail[..., None] * 0.8)
        fill = fill * (1 - base * 0.45) + sky_lit * base * 0.45
        fill = fill + facing[..., None] * np.array([0.35, 0.62, 0.72]) * (1 - fogk * 0.6)
        ms = blur(m, 1.1)[..., None]
        out = out * (1 - ms) + np.clip(fill, 0, 1) * ms

    # 3. casa: silhueta quase preta, contorno frio no telhado
    hm = blur(house.astype(np.float32), 1.0)[..., None]
    out = out * (1 - hm) + np.array([0.006, 0.012, 0.02]) * hm
    top = np.clip(house.astype(np.float32) - np.roll(house, 4, axis=0), 0, 1)
    out = out + blur(top, 1.5)[..., None] * np.array([0.12, 0.22, 0.27])

    # 4. primeiro plano abaixo do horizonte (ilha/mar do render), escuro e frio
    below = ((yy > hz) & ~house & ~anyt)[..., None]
    out = np.where(below, np.clip(hp * np.array([0.40, 0.55, 0.70]) * 0.75, 0, 1), out)

    # 5. janelas: todas acesas em ambar quente com intensidade variada; nucleo quente + halo grande + luz vazando
    win = (wm > 0.5).astype(np.float32)
    lab, n = label(win > 0.5)
    inten = np.zeros((h, w), np.float32)
    for k in range(1, n + 1):
        inten[lab == k] = rnd.uniform(0.75, 1.25)
    # interior real (passe com a lampada) dá variacao dentro do vidro; caixilho em cruz desenhado por janela
    il = hp.mean(axis=2)
    il = np.clip((il - il[win > 0.5].min()) / (np.ptp(il[win > 0.5]) + 1e-6), 0, 1) if (win > 0.5).any() else il
    from scipy.ndimage import find_objects
    mull = np.ones((h, w), np.float32)
    for k, sl in enumerate(find_objects(lab), 1):
        if sl is None:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        bw, bh = x1 - x0, y1 - y0
        if bw < 6 or bh < 6:
            continue
        t = max(1, round(min(bw, bh) * 0.07))
        cxm = x0 + bw // 2
        mull[y0:y1, cxm - t // 2: cxm - t // 2 + t] = 0.12
        for fy in ((0.38,) if bh < bw * 1.2 else (0.33, 0.66)):
            yl = y0 + int(bh * fy)
            mull[yl - t // 2: yl - t // 2 + t, x0:x1] = 0.12
        # mais quente embaixo (lampada no chao), mais escuro no alto
        gy_ = np.linspace(0.75, 1.15, bh)[:, None]
        inten[y0:y1, x0:x1] *= gy_
    core = win * inten * (0.6 + 0.6 * il) * mull
    wcol = np.array([1.0, 0.58, 0.22], np.float32)
    emit = core[..., None] * wcol
    # caixilho: a grade das janelas fica escura por cima do brilho (vem da propria mascara: linhas finas = 0)
    out = np.maximum(out, emit * 1.05)
    out = out + fblur(emit, 10) * 0.9 + fblur(emit, 45) * 0.9 + fblur(emit, 160) * 0.55
    # luz vazando para baixo na nevoa (feixes verticais suaves)
    spill = fblur(np.roll(emit, int(h * 0.02), axis=0), 30)
    out = out + spill * (yy > hz - h * 0.08)[..., None] * 0.35

    # 6. nevoa na linha d'agua, chuva, grao, vinheta
    for cy_, sd, k in ((hz - h * 0.01, h * 0.03, 0.30), (hz + h * 0.04, h * 0.06, 0.18)):
        band = np.exp(-((yy - cy_) / sd) ** 2)[..., None]
        out = out * (1 - band * k) + band * k * np.array([0.30, 0.42, 0.50])
    rain = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(rain)
    for _ in range(int(w * h / 4500)):
        x0, y0 = rnd.uniform(-200, w), rnd.uniform(-200, h)
        ln = rnd.uniform(h * 0.02, h * 0.07)
        dr.line((x0, y0, x0 + ln * 0.2, y0 + ln), fill=rnd.randint(25, 85), width=1)
    rain = np.asarray(rain.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32)[..., None] / 255
    out = out + rain * np.array([0.6, 0.75, 0.85]) * 0.45
    out = out + np.random.default_rng(a.seed).normal(0, 0.012, out.shape)
    v = np.sqrt(((xx - w / 2) / (w * 0.72)) ** 2 + ((yy - h / 2) / (h * 0.72)) ** 2)
    out = out * (1 - np.clip(v - 0.45, 0, 1)[..., None] * 0.95)
    Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8)).save(a.out)
    print(a.out, "janelas", n)


if __name__ == "__main__":
    main()
