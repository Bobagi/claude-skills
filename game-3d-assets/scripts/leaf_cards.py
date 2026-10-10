# Leaf-cluster card textures for tree_cards.py, made from the plant's own photographed leaves: the Poly Haven leaf
# atlas is cut into single leaves (connected parts of its alpha that are leaf-shaped: filled, not thin twigs), and
# ~40 of them are scattered over a soft round cluster at random angles and sizes, the ones at the back darker (the
# shade inside a crown). The result goes on crossed cards placed where the original leaves were.
# Run: python SourceAssets/Tools/leaf_cards.py <diffuse> <alpha> <out.png> [--leaves 40] [--seed 5]
import argparse
import random

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SIZE = 512


def leaves(diffuse, alpha):
    colour = Image.open(diffuse).convert("RGB")
    a = Image.open(alpha).convert("L").resize(colour.size)
    mask = np.asarray(a) > 110
    labels, _ = ndimage.label(mask)
    found = []
    total = mask.shape[0] * mask.shape[1]
    for i, box in enumerate(ndimage.find_objects(labels)):
        part = labels[box] == i + 1
        area = part.sum()
        h = box[0].stop - box[0].start
        w = box[1].stop - box[1].start
        # A leaf: not a speck, not the bark strip, and filling its box (twigs and stalks are thin lines).
        if area < total * 0.0015 or area > total * 0.08 or area / float(h * w) < 0.38:
            continue
        cut = ndimage.binary_erosion(part, iterations=1).astype(np.uint8) * 255
        piece = colour.crop((box[1].start, box[0].start, box[1].stop, box[0].stop)).convert("RGBA")
        piece.putalpha(Image.fromarray(cut))
        found.append(piece)
    return found


def main():
    p = argparse.ArgumentParser()
    p.add_argument("diffuse")
    p.add_argument("alpha")
    p.add_argument("out")
    p.add_argument("--leaves", type=int, default=40)
    p.add_argument("--seed", type=int, default=5)
    a = p.parse_args()
    rng = random.Random(a.seed)
    pieces = leaves(a.diffuse, a.alpha)
    if not pieces:
        raise SystemExit("no leaves found in " + a.alpha)
    card = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    biggest = max(max(pc.size) for pc in pieces)
    for k in range(a.leaves):
        # Back to front: the first are the deep ones, darker.
        depth = k / float(a.leaves - 1)
        leaf = rng.choice(pieces)
        scale = SIZE * rng.uniform(0.2, 0.32) / biggest
        lf = leaf.resize((max(4, int(leaf.width * scale)), max(4, int(leaf.height * scale))), Image.LANCZOS)
        lf = lf.rotate(rng.uniform(0, 360), resample=Image.BICUBIC, expand=True)
        arr = np.asarray(lf).astype(np.float32)
        arr[..., :3] *= 0.5 + 0.5 * depth
        lf = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
        # Inside a circle, denser toward the middle.
        r = (SIZE * 0.36) * rng.random() ** 0.7
        ang = rng.uniform(0, 2 * np.pi)
        cx = SIZE / 2 + r * np.cos(ang) - lf.width / 2
        cy = SIZE / 2 + r * np.sin(ang) - lf.height / 2
        card.alpha_composite(lf, (int(np.clip(cx, 0, SIZE - lf.width)), int(np.clip(cy, 0, SIZE - lf.height))))
    # Colour bled under the alpha so the mip levels do not fringe.
    rgb = card.convert("RGB")
    al = card.getchannel("A")
    filled = Image.composite(rgb, rgb.filter(ImageFilter.GaussianBlur(8)), al.point(lambda v: 255 if v > 8 else 0))
    filled.putalpha(al)
    filled.save(a.out)
    print("[cards]", len(pieces), "leaves ->", a.out)


main()
