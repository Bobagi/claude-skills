"""Renders de comparacao (mesma camera e luz) de varios modelos 3D, Blender em segundo plano.

  blender -b --factory-startup --python render_compare.py -- --out <pasta> --model "Rotulo=caminho.glb" ...

Para cada modelo: junta as malhas, conta triangulos, centraliza com a base no chao e escala o maior lado para 1.
Gera <pasta>/<rotulo>_tex_a.png (texturizado, 3/4 frente), _tex_b.png (3/4 costas), _clay_a.png e _clay_b.png
(cinza, so a forma) e <pasta>/stats.json com os triangulos. A folha e montada depois por make_sheet.py.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = Path(argv[argv.index("--out") + 1])
models = [argv[i + 1] for i, a in enumerate(argv) if a == "--model"]
res = int(argv[argv.index("--res") + 1]) if "--res" in argv else 640
out.mkdir(parents=True, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    # Cycles na CPU: nao disputa a VRAM com os geradores nem com outro agente
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.33, 0.35, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = w
    for name, rot, energy in (("key", (math.radians(50), 0, math.radians(35)), 3.2),
                              ("rim", (math.radians(60), 0, math.radians(200)), 1.6)):
        ld = bpy.data.lights.new(name, "SUN")
        ld.energy = energy
        ld.angle = math.radians(8)
        lo = bpy.data.objects.new(name, ld)
        lo.rotation_euler = rot
        sc.collection.objects.link(lo)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 50
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


def attach_loose_textures(obj, src: Path):
    """FBX do Meshy: se o material nao tem imagem, liga o PNG de cor vizinho."""
    has_img = any(n.type == "TEX_IMAGE" and n.image for m in obj.data.materials if m and m.use_nodes
                  for n in m.node_tree.nodes)
    if has_img:
        return
    cands = [p for p in src.parent.glob("*.png") if not any(k in p.stem.lower() for k in
                                                            ("normal", "metal", "rough", "thumb", "compare"))]
    if not cands:
        return
    m = bpy.data.materials.new("auto")
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(str(max(cands, key=lambda p: p.stat().st_size)))
    m.node_tree.links.new(t.outputs[0], bsdf.inputs["Base Color"])
    obj.data.materials.clear()
    obj.data.materials.append(m)


def load(path: Path):
    before = set(bpy.data.objects)
    if path.suffix.lower() in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif path.suffix.lower() == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    elif path.suffix.lower() == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    meshes = [o for o in set(bpy.data.objects) - before if o.type == "MESH"]
    for o in set(bpy.data.objects) - before:
        if o.type not in ("MESH",):
            pass
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in list(bpy.data.objects):
        if o.type == "EMPTY":
            bpy.data.objects.remove(o)
    attach_loose_textures(obj, path)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    size = max(mx - mn)
    obj.location -= Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    bpy.ops.object.transform_apply(location=True)
    obj.scale = (1 / size,) * 3
    bpy.ops.object.transform_apply(scale=True)
    dims = (mx - mn) / size
    return obj, tris, dims


def aim(cam, az_deg, dims):
    h = dims.z
    target = Vector((0, 0, h / 2))
    dist = 1.85
    az = math.radians(az_deg)
    el = math.radians(18)
    cam.location = target + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    d = target - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


stats = json.loads((out / "stats.json").read_text()) if (out / "stats.json").exists() else {}
for spec in models:
    label, p = spec.split("=", 1)
    path = Path(p)
    sc, cam = reset()
    obj, tris, dims = load(path)
    stats[label] = {"tris": tris, "src": str(path), "dims_norm": [round(x, 3) for x in dims]}
    mats = list(obj.data.materials)
    for tag, az in (("a", 35), ("b", 215)):
        aim(cam, az, dims)
        sc.render.filepath = str(out / f"{label}_tex_{tag}.png")
        bpy.ops.render.render(write_still=True)
    clay = bpy.data.materials.new("clay")
    clay.use_nodes = True
    b = clay.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.3, 0.3, 0.3, 1)
    b.inputs["Roughness"].default_value = 0.6
    obj.data.materials.clear()
    obj.data.materials.append(clay)
    for tag, az in (("a", 35), ("b", 215)):
        aim(cam, az, dims)
        sc.render.filepath = str(out / f"{label}_clay_{tag}.png")
        bpy.ops.render.render(write_still=True)
    print("RENDERED", label, tris)
(out / "stats.json").write_text(json.dumps(stats, indent=2))
