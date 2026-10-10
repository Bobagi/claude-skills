# Foliage (leaf cards with an alpha cut-out) into the triangle budget without losing the cut-out: collapse
# decimation melts the cards and a bake onto new UVs loses the alpha, so plants are reduced the way foliage LODs
# are made by hand: whole leaves (loose parts) are dropped at random down to 5x the budget, the kept ones grow a
# little about their own centre to keep the plant as full, then everything is collapsed to the budget (UVs kept,
# so the alpha still cuts each leaf's outline). Stems (parts far bigger than a leaf) are never dropped. Original UVs and textures stay; the alpha map goes into the base colour's A for URP alpha clip.
# Run (Blender 5.2, background):
#   blender -b --factory-startup --python foliage_reduce.py -- --src <folder with the 1k FBX and textures/>
#       --name Fern --out <Assets/.../Vegetation/Fern> --tris 1500 [--seed 3]
# Prints the triangle count before and after. Compare in the engine at the distance it is seen from.
import argparse
import math
import os
import random
import shutil
import sys

import bmesh
import bpy
from mathutils import Vector


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--tris", type=int, default=2000)
    p.add_argument("--seed", type=int, default=3)
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:])


def main():
    a = args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fbx = next(os.path.join(a.src, f) for f in os.listdir(a.src) if f.lower().endswith(".fbx"))
    bpy.ops.import_scene.fbx(filepath=fbx)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in [o for o in bpy.data.objects if o.type != 'MESH']:
        for child in o.children:
            m = child.matrix_world.copy()
            child.parent = None
            child.matrix_world = m
        bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.faces.ensure_lookup_table()
    before = len(bm.faces)

    # Loose parts.
    seen = set()
    parts = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]
        group = []
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            group.append(cur)
            for e in cur.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        parts.append(group)

    parts.sort(key=len, reverse=True)
    rng = random.Random(a.seed)
    budget = a.tris
    # Stems: parts much bigger than a typical leaf are kept (the plant's structure).
    typical = sorted(len(p) for p in parts)[len(parts) // 2]
    stems = [p for p in parts if len(p) > typical * 8]
    leaves = [p for p in parts if len(p) <= typical * 8]
    stem_tris = sum(len(p) for p in stems)
    rng.shuffle(leaves)
    # Poly Haven leaves are small meshes (a frond is ~120 triangles with its outline in the alpha), not single
    # cards: drop only down to 5x the budget, then collapse what is left (each leaf keeps its UVs, so the alpha
    # still cuts its outline).
    room = max(budget * 5 - stem_tris, budget * 3)
    kept, used = [], 0
    for p in leaves:
        if used + len(p) > room:
            continue
        kept.append(p)
        used += len(p)
    leaf_total = sum(len(p) for p in leaves)
    grow = min(1.3, (leaf_total / max(1, used)) ** 0.25) if used else 1.0

    drop = set()
    for p in leaves:
        if p not in kept:
            drop.update(p)
    keep_faces = set()
    for p in kept:
        keep_faces.update(p)
    # Grow each kept leaf about its own centre.
    for p in kept:
        verts = {v for f in p for v in f.verts}
        c = sum((v.co for v in verts), Vector()) / len(verts)
        for v in verts:
            v.co = c + (v.co - c) * grow
    bmesh.ops.delete(bm, geom=list(drop), context='FACES')
    bm.to_mesh(obj.data)
    bm.free()

    after = len(obj.data.polygons)
    if after > budget:
        mod = obj.modifiers.new("Decimate", 'DECIMATE')
        mod.ratio = max(0.05, budget / after)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    final = sum(len(p.vertices) - 2 for p in obj.data.polygons)

    # Pivot at the base centre.
    co = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = min(v.z for v in co)
    cx = sum(v.x for v in co) / len(co)
    cy = sum(v.y for v in co) / len(co)
    for v in obj.data.vertices:
        v.co -= Vector((cx, cy, lo))
    obj.name = a.name
    os.makedirs(a.out, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(a.out, a.name + ".fbx"), use_selection=True, apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y', path_mode='STRIP', embed_textures=False, mesh_smooth_type='FACE')

    # Textures, per material (a plant can have bark and leaves): base colour with the alpha in A, the GL normal map
    # as is. Named <Name>_<part>_BaseColor.png, part = what follows the asset id in the Poly Haven file name.
    tex = os.path.join(a.src, "textures")
    files = os.listdir(tex)
    asset = os.path.basename(os.path.normpath(a.src))
    for diff in [f for f in files if "_diff_" in f]:
        prefix = diff.split("_diff_")[0]
        part = prefix[len(asset):].strip("_") or "main"
        alpha = next((f for f in files if f.startswith(prefix + "_alpha_")), None)
        nor = next((f for f in files if f.startswith(prefix + "_nor_gl_")), None)
        base = bpy.data.images.load(os.path.join(tex, diff))
        w, h = base.size
        px = list(base.pixels[:])
        if alpha:
            am = bpy.data.images.load(os.path.join(tex, alpha))
            am.scale(w, h)
            ap = am.pixels[:]
            for i in range(w * h):
                px[i * 4 + 3] = ap[i * 4]
        out = bpy.data.images.new(a.name + "_" + part + "_BaseColor", w, h, alpha=True)
        out.pixels[:] = px
        out.filepath_raw = os.path.join(a.out, a.name + "_" + part + "_BaseColor.png")
        out.file_format = 'PNG'
        out.save()
        if nor:
            shutil.copy(os.path.join(tex, nor), os.path.join(a.out, a.name + "_" + part + "_Normal" + os.path.splitext(nor)[1]))
    print("[foliage] materials:", [m.name for m in obj.data.materials])
    print(f"[foliage] {a.name}: {before} -> {final} triangles ({len(parts)} parts, {len(stems)} stems, kept {len(kept)}/{len(leaves)} leaves, grow {grow:.2f})")


main()
