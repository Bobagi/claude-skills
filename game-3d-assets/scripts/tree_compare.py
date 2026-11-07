# Original x result for trees made by tree_cards.py (or foliage_reduce.py): the same camera, light and real size, with
# the leaves cut out by their alpha on both rows, so a bald or blobby crown shows at once. optimize_model.py does this
# for solid props; trees need it apart because their materials keep alpha (the bake there would lose it).
# Writes <Name>_compare.png (top row original, bottom row result: front, side, three-quarter from above) and
# <Name>_report.json (triangles, size, materials, textures, crown coverage and silhouette IoU per view).
# Run (Blender 5.2, background):
#   blender -b --factory-startup --python tree_compare.py -- --src <polyhaven folder> --result <out>/<Name>.fbx
#       --name OakA --leaf leaves [--height 10] [--res 384] [--samples 24]
# --height must be the one given to tree_cards.py (the original is scaled the same way).
import argparse
import json
import math
import os
import re
import sys

import bpy
from mathutils import Vector


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--result", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--leaf", required=True)
    p.add_argument("--height", type=float, default=0.0)
    p.add_argument("--res", type=int, default=384)
    p.add_argument("--samples", type=int, default=24)
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:])


def import_joined(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in new:
        if o.type != 'MESH':
            for c in o.children:
                m = c.matrix_world.copy()
                c.parent = None
                c.matrix_world = m
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def ground(obj, height):
    co = [v.co for v in obj.data.vertices]
    lo = Vector((min(v.x for v in co), min(v.y for v in co), min(v.z for v in co)))
    hi = Vector((max(v.x for v in co), max(v.y for v in co), max(v.z for v in co)))
    s = height / (hi.z - lo.z) if height > 0 else 1.0
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in obj.data.vertices:
        v.co = (v.co - base) * s
    obj.data.update()


def textured(name, colour, alpha=None, normal=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.8
    img = bpy.data.images.load(colour)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    if alpha == "own":
        nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
    elif alpha:
        am = bpy.data.images.load(alpha)
        am.colorspace_settings.name = 'Non-Color'
        ta = nt.nodes.new("ShaderNodeTexImage")
        ta.image = am
        nt.links.new(ta.outputs["Color"], bsdf.inputs["Alpha"])
    if normal:
        n = bpy.data.images.load(normal)
        n.colorspace_settings.name = 'Non-Color'
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = n
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def source_materials(obj, src, leaf):
    tex = os.path.join(src, "textures")
    files = os.listdir(tex)
    asset = os.path.basename(os.path.normpath(src))
    parts = sorted({f.split("_diff_")[0][len(asset):].strip("_") or "main" for f in files if "_diff_" in f})
    for slot in obj.material_slots:
        part = slot.material.name[len(asset):].strip("_") if slot.material else ""
        if part not in parts:
            part = next((p for p in parts if p != "main" and (part.startswith(p) or p.startswith(part))), "main")
        prefix = asset + ("" if part == "main" else "_" + part)
        diff = next((f for f in files if f.startswith(prefix + "_diff_")), None)
        if not diff:
            continue
        alpha = next((f for f in files if f.startswith(prefix + "_alpha_")), None)
        nor = next((f for f in files if f.startswith(prefix + "_nor_gl_")), None)
        slot.material = textured(slot.material.name + "_src", os.path.join(tex, diff),
                                 os.path.join(tex, alpha) if alpha else None,
                                 os.path.join(tex, nor) if nor else None)


def result_materials(obj, out, name, src):
    asset = os.path.basename(os.path.normpath(src))
    files = os.listdir(out)
    used = []
    for slot in obj.material_slots:
        # The source import left materials of the same names behind: the result ones come back as "<name>.001".
        mname = re.sub(r"\.\d{3}$", "", slot.material.name) if slot.material else ""
        if mname.startswith(name + "_"):
            part = mname[len(name) + 1:]
        else:
            part = mname[len(asset):].strip("_") or "main"
        base = name + "_" + part + "_BaseColor.png"
        if base not in files:
            print(f"[compare] WARNING no {base} for material {mname}")
            continue
        nor = next((f for f in files if f.startswith(name + "_" + part + "_Normal")), None)
        slot.material = textured(mname + "_res", os.path.join(out, base), "own",
                                 os.path.join(out, nor) if nor and part != "cards" else None)
        used.append({"material": mname, "part": part, "base": base, "normal": nor,
                     "ms": name + "_" + part + "_MetallicSmoothness.png"
                     if name + "_" + part + "_MetallicSmoothness.png" in files else None,
                     "alpha_clip": part == "cards" or part == "leaves"})
    return used


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def setup(res, samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.62, 0.75, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = world
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.type = 'ORTHO'
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


VIEWS = [("front", (0, -1, 0.0)), ("side", (1, 0, 0.0)), ("above", (-0.7, -0.7, 0.55))]


def render(obj, cam, extent, work, tag):
    paths = []
    for vname, d in VIEWS:
        d = Vector(d).normalized()
        centre = Vector((0, 0, extent.z / 2))
        cam.location = centre + d * extent.length * 2
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = max(extent.x, extent.y, extent.z) * 1.15
        p = os.path.join(work, f"{tag}_{vname}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths


def main():
    a = args()
    out = os.path.dirname(os.path.abspath(a.result))
    work = os.path.join(out, "_compare_work")
    os.makedirs(work, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cam = setup(a.res, a.samples)

    fbx = next(os.path.join(a.src, f) for f in os.listdir(a.src) if f.lower().endswith(".fbx"))
    src = import_joined(fbx)
    ground(src, a.height)
    source_materials(src, a.src, a.leaf)
    src_tris = tris(src)
    co = [v.co for v in src.data.vertices]
    extent = Vector((max(abs(v.x) for v in co) * 2, max(abs(v.y) for v in co) * 2, max(v.z for v in co)))
    top = render(src, cam, extent, work, "src")
    bpy.data.objects.remove(src)

    res = import_joined(a.result)
    ground(res, 0.0)
    used = result_materials(res, out, a.name, a.src)
    res_tris = tris(res)
    rco = [v.co for v in res.data.vertices]
    size = [max(v.x for v in rco) - min(v.x for v in rco), max(v.y for v in rco) - min(v.y for v in rco),
            max(v.z for v in rco)]
    bottom = render(res, cam, extent, work, "res")

    # Sheet, coverage (alpha > 0.5) and IoU per view, with numpy if Blender has it.
    import numpy as np
    def load(p):
        im = bpy.data.images.load(p)
        w, h = im.size
        arr = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        return arr
    rows = [[load(p) for p in top], [load(p) for p in bottom]]
    views = {}
    for i, (vname, _) in enumerate(VIEWS):
        ma = rows[0][i][..., 3] > 0.5
        mb = rows[1][i][..., 3] > 0.5
        inter = float((ma & mb).sum())
        union = float((ma | mb).sum()) or 1.0
        views[vname] = {"iou": round(inter / union, 3), "coverage_ratio": round(float(mb.sum()) / max(1.0, float(ma.sum())), 3)}
    r = a.res
    sheet = np.zeros((2 * r, 3 * r, 4), dtype=np.float32)
    bg = np.array([0.82, 0.84, 0.86, 1.0], dtype=np.float32)
    for y, row in enumerate(rows):
        for x, im in enumerate(row):
            al = im[..., 3:4]
            sheet[(1 - y) * r:(2 - y) * r, x * r:(x + 1) * r] = im * al + bg * (1 - al)
    sheet[..., 3] = 1.0
    img = bpy.data.images.new(a.name + "_compare", 3 * r, 2 * r, alpha=True)
    img.pixels[:] = sheet.ravel()
    cpath = os.path.join(out, a.name + "_compare.png")
    img.filepath_raw = cpath
    img.file_format = 'PNG'
    img.save()

    report = {"name": a.name, "source": os.path.basename(fbx), "source_triangles": src_tris, "triangles": res_tris,
              "size_m": [round(s, 2) for s in size], "materials": used, "views": views, "comparison": cpath,
              "fbx": a.result, "fbx_axes": "exported by tree_cards.py with axis_forward -Z, axis_up Y; mesh Z up in Blender",
              "pivot": "base centre"}
    with open(os.path.join(out, a.name + "_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[compare] {a.name}: {src_tris} -> {res_tris}, size {report['size_m']}, views {views}")


main()
