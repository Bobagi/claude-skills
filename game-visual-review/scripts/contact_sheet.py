#!/usr/bin/env python3
"""contact_sheet.py: side-by-side review sheet plus simple image metrics for game screenshots.

Usage:
  python -I contact_sheet.py --out review.png --shot capture.png [--ref reference.png] [--before old.png] [--label menu]

Writes the sheet (all images scaled to the same height, labelled) and prints one metrics block per
image. Metrics (all in 0..1 unless noted):
  lum_mean / lum_std   average luminance and its spread
  sat_mean             average HSV saturation
  contrast_p5_p95      luminance spread between the 5th and 95th percentile
  hue_variety          number of 30-degree hue bins that hold more than 1 percent of the saturated pixels
  flat_area            fraction of 32x32 blocks whose luminance std is below 0.012 (flat, placeholder look)
  edge_density         mean gradient magnitude (detail)
  text_min_px          not measured here; read the sheet
If --ref is given: hist_distance (0 identical .. 1 unrelated, on a 8x8x8 RGB histogram) and lum_delta.
Only needs Pillow and numpy.
"""
import argparse, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def load(p):
    return Image.open(p).convert("RGB")

def metrics(img):
    a = np.asarray(img.resize((960, int(960 * img.height / img.width)))).astype(np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx = a.max(axis=2); mn = a.min(axis=2)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # hue in degrees
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    strong = sat > 0.25
    bins = np.histogram(h[strong], bins=12, range=(0, 360))[0]
    variety = int((bins / max(1, bins.sum()) > 0.01).sum()) if strong.any() else 0
    # flat blocks
    H, W = lum.shape; bs = 32; flats = 0; total = 0
    for y in range(0, H - bs + 1, bs):
        for x in range(0, W - bs + 1, bs):
            total += 1
            if lum[y:y + bs, x:x + bs].std() < 0.012: flats += 1
    gy, gx = np.gradient(lum)
    edges = float(np.sqrt(gx * gx + gy * gy).mean())
    p5, p95 = np.percentile(lum, 5), np.percentile(lum, 95)
    return {
        "lum_mean": round(float(lum.mean()), 3), "lum_std": round(float(lum.std()), 3),
        "sat_mean": round(float(sat.mean()), 3), "contrast_p5_p95": round(float(p95 - p5), 3),
        "hue_variety": variety, "flat_area": round(flats / max(1, total), 3), "edge_density": round(edges, 4),
    }

def hist(img):
    a = np.asarray(img.resize((256, 256))).reshape(-1, 3) // 32
    idx = a[:, 0] * 64 + a[:, 1] * 8 + a[:, 2]
    h = np.bincount(idx, minlength=512).astype(np.float64)
    return h / h.sum()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--shot", required=True)
    ap.add_argument("--ref"); ap.add_argument("--before"); ap.add_argument("--label", default="")
    ap.add_argument("--height", type=int, default=540)
    a = ap.parse_args()
    panels = [("CAPTURE " + a.label, load(a.shot))]
    if a.ref: panels.append(("REFERENCE", load(a.ref)))
    if a.before: panels.append(("BEFORE", load(a.before)))
    scaled = [(t, im.resize((int(im.width * a.height / im.height), a.height))) for t, im in panels]
    pad = 16; top = 34
    W = sum(im.width for _, im in scaled) + pad * (len(scaled) + 1)
    sheet = Image.new("RGB", (W, a.height + top + pad), (24, 24, 28))
    dr = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype("arial.ttf", 20)
    except Exception: font = ImageFont.load_default()
    x = pad
    for t, im in scaled:
        sheet.paste(im, (x, top)); dr.text((x, 8), t, fill=(235, 230, 210), font=font); x += im.width + pad
    sheet.save(a.out)
    print("sheet:", a.out)
    shot = panels[0][1]
    for t, im in panels:
        print(t + ":", metrics(im))
    if a.ref:
        ref = panels[1][1]
        hd = 0.5 * float(np.abs(hist(shot) - hist(ref)).sum())
        ld = metrics(shot)["lum_mean"] - metrics(ref)["lum_mean"]
        print("vs reference: hist_distance=%.3f lum_delta=%+.3f" % (hd, ld))
        if hd > 0.6: print("  warning: palette far from the reference")
    m = metrics(shot)
    flags = []
    if m["flat_area"] > 0.45: flags.append("flat_area high: placeholder look (rubric A2)")
    if m["hue_variety"] < 4: flags.append("hue_variety low: monochrome scene (rubric B3)")
    if m["contrast_p5_p95"] < 0.25: flags.append("contrast low: washed out or too dark (rubric B4)")
    if m["lum_mean"] > 0.8: flags.append("very bright: check for blown-out light (rubric B4)")
    for f in flags: print("  flag:", f)
    return 0

if __name__ == "__main__":
    sys.exit(main())
