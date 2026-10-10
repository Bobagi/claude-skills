# Optimise one high-poly model (Meshy, Tripo, scans, marketplace) for a real-time game.
#
#   blender -b --factory-startup --python optimize_model.py -- \
#       --src <zip | folder | .fbx | .glb | .obj> --name Vial --out <dir> \
#       --type hand [--tris 2000] [--max-tris 5000] [--tex 1024] [--size 0.16] [--no-metal] [--previews <dir>]
#
# What it does, in order:
#   1. unpacks a zip, finds the mesh and its texture set (base colour, _normal, _metallic, _roughness);
#   2. joins every mesh part, applies transforms, scales the longest side to --size metres (if given) and puts
#      the pivot at the bottom centre (so it sits on a table at y 0 in the engine);
#   3. decimates (collapse) starting at the MINIMUM of the type's triangle budget and, only if the outline
#      suffers, climbs toward the maximum in 25% steps. Stop rule: mean outline deviation against the original
#      from 4 views (front, side, top, three-quarter) <= --outline px on a 512 px frame (default 0.75 px, about
#      0.15% of the object). IoU is reported too, but it punishes thin parts (a slate seen edge-on);
#      A plateau (+25% triangles, < 5% better outline) goes back one step: more triangles would not help.
#      If the collapse gets stuck well above the target (thin tangled parts), the copy is voxel-remeshed
#      first (--remesh-res voxels along the longest side) and decimated from there.
#   4. bakes EVERY channel of the original onto the light mesh (Cycles, selected to active): base colour,
#      metallic and roughness through emission, and the normal map with the original's geometry AND its own
#      normal map. Baking is mandatory: decimation drags UVs at the seams, and reusing the source textures on
#      the decimated UVs shifted stains and details (measured on the dive slate, 2026-09-30).
#      --uv smart (default) unwraps fresh UVs first (sharper result: the decimated UVs smear stains at the
#      seams); --uv keep bakes into the decimated UVs;
#   5. writes the texture set the engine wants: <Name>_BaseColor.png, <Name>_Normal.png and
#      <Name>_MetallicSmoothness.png (R = metallic, A = 1 - roughness; the Unity URP/HDRP "MetallicSmoothness"
#      layout), all at --tex;
#   6. renders the original and the result from the same 4 cameras and light; a local shading defect (a folded
#      triangle, a tear) above --hotspot sends it one step up the ladder and bakes again. Saves the side-by-side
#      comparison (top row original, bottom row optimised) and a JSON report with the numbers (original / final triangles, IoU per view, ladder tried, sizes).
#
# Budgets per --type (triangles in the engine, i.e. after triangulation). Sources in budgets.md.
import argparse, glob, json, math, os, shutil, sys, tempfile, zipfile

import bpy
import numpy as np
from mathutils import Matrix, Vector

BUDGETS = {
    "background": (1000, 3000, 1024),   # seen far away / through a window
    "hand": (2000, 5000, 1024),         # hand-held or small prop (flask, mask, torch, radio)
    "large": (5000, 8000, 2048),        # big prop seen up close (tank, workbench)
    "creature": (10000, 20000, 2048),   # big creature, the TOTAL of all its pieces
    "character": (10000, 30000, 2048),  # player / NPC body
}

MESH_EXT = (".fbx", ".glb", ".gltf", ".obj")


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--out", required=True, help="folder for the FBX and the textures")
    p.add_argument("--type", choices=sorted(BUDGETS), default="hand")
    p.add_argument("--tris", type=int, help="start of the ladder (default: the type's minimum)")
    p.add_argument("--max-tris", type=int, help="end of the ladder (default: the type's maximum)")
    p.add_argument("--tex", type=int, help="texture size (default per type)")
    p.add_argument("--size", type=float, help="real longest side in metres")
    p.add_argument("--outline", type=float, default=0.75, help="mean outline deviation, px on a 512 frame, that is good enough")
    p.add_argument("--hotspot", type=float, default=0.12, help="local shading defect (see shading_hotspot) that is good enough")
    p.add_argument("--remesh-res", type=int, default=200, help="voxels along the longest side when the collapse gets stuck")
    p.add_argument("--uv", choices=("keep", "smart"), default="smart", help="bake into the decimated UVs or into fresh ones")
    p.add_argument("--no-metal", action="store_true", help="zero the metallic map (AI tools often guess metal on skin, cloth, plastic)")
    p.add_argument("--pivot", choices=("bottom", "center"), default="bottom")
    p.add_argument("--previews", help="folder for the comparison image and the report (default: --out)")
    p.add_argument("--samples", type=int, default=24)
    p.add_argument("--smooth-angle", type=float, default=40.0,
                   help="edges sharper than this stay hard (degrees). 180 = all smooth: use it for skinned characters "
                        "that cast shadows (hard edges split the vertices and the shadow normal bias cracks them apart)")
    return p.parse_args(argv)


# ---------------------------------------------------------------- input

def resolve_source(src, work):
    src = os.path.abspath(src)
    if src.lower().endswith(".zip"):
        with zipfile.ZipFile(src) as z:
            z.extractall(work)
        src = work
    if os.path.isdir(src):
        meshes = [f for f in glob.glob(os.path.join(src, "**", "*"), recursive=True) if f.lower().endswith(MESH_EXT)]
        if not meshes:
            raise SystemExit("no mesh file in " + src)
        # Prefer FBX (Meshy ships the textures beside it), then the biggest file.
        meshes.sort(key=lambda f: (not f.lower().endswith(".fbx"), -os.path.getsize(f)))
        mesh = meshes[0]
    else:
        mesh = src
    # Beside the mesh, in a "textures" folder next to it (Poly Haven) or one level up (a gltf/ subfolder).
    folder = os.path.dirname(mesh)
    images = []
    for d in (folder, os.path.join(folder, "textures"), os.path.join(os.path.dirname(folder), "textures")):
        images += [f for f in glob.glob(os.path.join(d, "*")) if f.lower().endswith((".png", ".jpg", ".jpeg", ".tga"))]

    def pick(*keys):
        for f in images:
            b = os.path.basename(f).lower()
            if any(k in b for k in keys):
                return f
        return None

    # Meshy names (_normal, _metallic, _roughness) and Poly Haven ones (_nor_gl, _metal_, _rough_, _diff_).
    tex = {
        "normal": pick("_normal", "normal.", "_nor_gl"),
        "metallic": pick("_metallic.", "_metalness", "_metallic_", "_metal_"),
        "roughness": pick("_roughness", "_rough_"),
        "base": pick("_diff_", "_diffuse", "_basecolor", "_base_color", "_albedo"),
    }
    if not tex["base"]:
        skip = ("metallic_roughness", "emissive", "_nor_", "_ms.", "opacity", "alpha", "_arm_", "_ao_", "_disp", "_mask")
        used = {v for v in tex.values() if v}
        rest = [f for f in images if f not in used and not any(k in os.path.basename(f).lower() for k in skip)]
        tex["base"] = max(rest, key=os.path.getsize) if rest else None
    return mesh, tex


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 4
    return scene


def import_mesh(path):
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        bpy.ops.wm.obj_import(filepath=path)
    parts = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in [o for o in bpy.data.objects if o not in before and o.type != 'MESH']:
        bpy.data.objects.remove(o, do_unlink=True)
    select_only(*parts)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(parts) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def select_only(*objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[-1]


def verts(obj):
    co = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def tri_count(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def normalise(obj, size, pivot):
    v = verts(obj)
    lo, hi = v.min(0), v.max(0)
    scale = size / float((hi - lo).max()) if size else 1.0
    base_z = lo[2] if pivot == "bottom" else (lo[2] + hi[2]) / 2
    centre = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, base_z))
    obj.data.transform(Matrix.Scale(scale, 4) @ Matrix.Translation(-centre))
    obj.data.update()


# ---------------------------------------------------------------- materials

def load_image(path, non_color=False):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


def source_material(obj, tex):
    """Principled material on the original, WITH its normal map: the bake then carries both the geometric
    relief lost by decimation and the fine detail that was only ever in the source normal map."""
    mat = bpy.data.materials.new("Source")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new('ShaderNodeTexCoord')
    if tex["base"]:
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = load_image(tex["base"])
        nt.links.new(uv.outputs['UV'], n.inputs['Vector'])
        nt.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
    if tex["normal"]:
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = load_image(tex["normal"], True)
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(uv.outputs['UV'], n.inputs['Vector'])
        nt.links.new(n.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if tex["roughness"]:
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = load_image(tex["roughness"], True)
        nt.links.new(uv.outputs['UV'], n.inputs['Vector'])
        nt.links.new(n.outputs['Color'], bsdf.inputs['Roughness'])
    else:
        # No roughness map: most props are worn wood, cloth, painted metal. Blender's 0.5 reads as plastic.
        bsdf.inputs['Roughness'].default_value = 0.7
    if tex["metallic"]:
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = load_image(tex["metallic"], True)
        nt.links.new(uv.outputs['UV'], n.inputs['Vector'])
        nt.links.new(n.outputs['Color'], bsdf.inputs['Metallic'])
    else:
        bsdf.inputs['Metallic'].default_value = 0.0
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return mat


def has_image_textures(obj):
    for m in obj.data.materials:
        if m and m.use_nodes and any(n.type == 'TEX_IMAGE' and n.image for n in m.node_tree.nodes):
            return True
    return False


def surface_bsdf(mat):
    """The Principled BSDF that feeds the material output, or None."""
    if not mat or not mat.use_nodes:
        return None
    out = next((n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
    out = out or next((n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None or not out.inputs['Surface'].links:
        return None
    node = out.inputs['Surface'].links[0].from_node
    if node.type != 'BSDF_PRINCIPLED':
        node = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    return out, node


def preview_material(obj, base_img, normal_img):
    mat = bpy.data.materials.new("Preview")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs['Roughness'].default_value = 0.6
    if base_img:
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = base_img
        nt.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = normal_img
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(n.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------------------------------------------------------- decimation and silhouettes

SMOOTH_ANGLE = 40.0


def decimated_copy(high, tris, remesh_voxel=None):
    """Light copy of high. With remesh_voxel, the copy is first rebuilt as a voxel remesh: Blender's collapse
    refuses to go below a floor on thin, tangled parts (the specimen jar's tendrils stopped it at ~10.7k
    whatever the target, 2026-09-30); a remesh gives it clean topology. Fine detail lost there is baked back."""
    low = high.copy()
    low.data = high.data.copy()
    bpy.context.scene.collection.objects.link(low)
    select_only(low)
    if remesh_voxel:
        rm = low.modifiers.new("Remesh", 'REMESH')
        rm.mode = 'VOXEL'
        rm.voxel_size = remesh_voxel
        bpy.ops.object.modifier_apply(modifier=rm.name)
    ratio = min(1.0, tris / max(1, tri_count(low)))
    mod = low.modifiers.new("Decimate", 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # Smooth by angle, not plain smooth: on thin parts (a slate, a strap) front and back share the rim
    # vertices, plain smooth bends the normals across whole faces and the baked normal map fights it
    # (dark wedges on the dive slate, 2026-09-30). Edges sharper than 40 degrees stay hard (--smooth-angle).
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(SMOOTH_ANGLE))
    return low


VIEWS = {
    "front": (Vector((0, -1, 0)), 0.0),
    "side": (Vector((1, 0, 0)), 0.0),
    "top": (Vector((0, 0, 1)), 0.0),
    "three_quarter": (Vector((1, -1, 0.7)).normalized(), 0.0),
}


def camera_for(obj, direction, res):
    scene = bpy.context.scene
    v = verts(obj)
    lo, hi = v.min(0), v.max(0)
    centre = Vector(((lo + hi) / 2).tolist())
    radius = float(np.linalg.norm(hi - lo)) / 2
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = radius * 2.1
    cam_data.clip_start = 0.001
    cam_data.clip_end = radius * 20
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = centre + direction * radius * 4
    if abs(direction.z) > 0.99:
        cam.rotation_euler = (0.0, 0.0, 0.0)  # straight down, +Y up in the frame
    else:
        # The camera's local Y (its "up") follows world Z, so upright objects stay upright in every view.
        cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam
    scene.render.resolution_x = scene.render.resolution_y = res
    return cam


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def silhouettes(obj, frame_obj, work, tag):
    """Alpha masks from 4 views, framed on frame_obj so the original and the light copy line up exactly."""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.film_transparent = True
    scene.display.shading.light = 'FLAT'
    scene.display.shading.color_type = 'SINGLE'
    for o in scene.objects:
        if o.type == 'MESH':
            o.hide_render = o is not obj
    masks = {}
    for name, (direction, _) in VIEWS.items():
        cam = camera_for(frame_obj, direction, 512)
        masks[name] = render_to(os.path.join(work, "%s_%s.png" % (tag, name)))[..., 3] > 0.5
        bpy.data.objects.remove(cam, do_unlink=True)
    return masks


def iou(a, b):
    return float((a & b).sum()) / max(1, float((a | b).sum()))


def outline_deviation(a, b):
    """Mean distance, in pixels, between the two outlines: the area that differs over the outline length."""
    inner = a.copy()
    inner[1:, :] &= a[:-1, :]
    inner[:-1, :] &= a[1:, :]
    inner[:, 1:] &= a[:, :-1]
    inner[:, :-1] &= a[:, 1:]
    perimeter = float((a & ~inner).sum())
    return float((a ^ b).sum()) / max(1.0, perimeter)


# ---------------------------------------------------------------- bake and textures

def new_image(name, tex_size, non_color):
    img = bpy.data.images.new(name, tex_size, tex_size, alpha=False, float_buffer=non_color)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    return img


def bake_channels(high, low, tex, size, tex_size):
    """Every texture of the original, re-projected onto the light mesh's own UVs."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 4
    for o in scene.objects:
        o.hide_render = False
    target = bpy.data.materials.new("Bake")
    target.use_nodes = True
    node = target.node_tree.nodes.new('ShaderNodeTexImage')
    target.node_tree.nodes.active = node
    low.data.materials.clear()
    low.data.materials.append(target)

    # Every material of the original (a Poly Haven model can have several, each with its own texture set):
    # whatever feeds its Principled BSDF input (texture, or the plain value) goes through an emission shader.
    wired = []
    for mat in high.data.materials:
        found = surface_bsdf(mat)
        if found is None:
            continue
        out, bsdf = found
        nt = mat.node_tree
        wired.append((nt, out, out.inputs['Surface'].links[0].from_socket, bsdf, nt.nodes.new('ShaderNodeEmission')))
    # Distances scale with the object: a 16 cm flask and a 2 m tank both get sensible rays.
    rays = dict(use_selected_to_active=True, cage_extrusion=size * 0.01, max_ray_distance=size * 0.04, margin=16)
    images = {}
    for channel, socket, non_color in (("base", "Base Color", False), ("metallic", "Metallic", True), ("roughness", "Roughness", True)):
        for nt, out, _, bsdf, emit in wired:
            for l in list(emit.inputs['Color'].links):
                nt.links.remove(l)
            source = bsdf.inputs[socket]
            if source.links:
                nt.links.new(source.links[0].from_socket, emit.inputs['Color'])
            else:
                v = source.default_value
                emit.inputs['Color'].default_value = tuple(v) if channel == "base" else (v, v, v, 1.0)
            nt.links.new(emit.outputs[0], out.inputs['Surface'])
        node.image = images[channel] = new_image(channel, tex_size, non_color)
        select_only(high, low)
        bpy.ops.object.bake(type='EMIT', **rays)
        print("BAKED", channel, flush=True)
    for nt, out, socket, _, _ in wired:
        nt.links.new(socket, out.inputs['Surface'])
    node.image = images["normal"] = new_image("normal", tex_size, True)
    select_only(high, low)
    bpy.ops.object.bake(type='NORMAL', **rays)
    print("BAKED normal", flush=True)
    return images


def pixels(img):
    px = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(img.size[1], img.size[0], 4)


def save_image(img, path):
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()


def write_textures(images, out, name, tex_size, no_metal):
    paths = {}
    if "base" in images:
        paths["base"] = os.path.join(out, name + "_BaseColor.png")
        save_image(images["base"], paths["base"])
    paths["normal"] = os.path.join(out, name + "_Normal.png")
    save_image(images["normal"], paths["normal"])
    metal = np.zeros((tex_size, tex_size), dtype=np.float32)
    if "metallic" in images and not no_metal:
        metal = pixels(images["metallic"])[..., 0]
    smooth = np.full((tex_size, tex_size), 0.4, dtype=np.float32)
    if "roughness" in images:
        smooth = 1.0 - pixels(images["roughness"])[..., 0]
    ms = bpy.data.images.new("MS", tex_size, tex_size, alpha=True)
    ms.colorspace_settings.name = 'Non-Color'
    ms.pixels.foreach_set(np.dstack([metal, metal, metal, smooth]).astype(np.float32).ravel())
    paths["metallic_smoothness"] = os.path.join(out, name + "_MetallicSmoothness.png")
    save_image(ms, paths["metallic_smoothness"])
    return paths


def comparison_rig(samples):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.18, 0.18, 1)
    scene.world = world
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    scene.collection.objects.link(sun)


def render_row(obj, frame_obj, work, samples):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.render.film_transparent = False
    for o in scene.objects:
        if o.type == 'MESH':
            o.hide_render = o is not obj
    row = []
    for name, (direction, _) in VIEWS.items():
        cam = camera_for(frame_obj, direction, 384)
        row.append(render_to(os.path.join(work, "cmp_%s_%s.png" % (obj.name, name))))
        bpy.data.objects.remove(cam, do_unlink=True)
    return np.concatenate(row, axis=1)


def shading_hotspot(high_row, low_row):
    """99.5th percentile of the luminance difference in 16 px blocks: finds a local defect (a folded
    triangle, a tear, a wrong bake) that the outline and the average hide. Calibrated on the dive slate:
    0.27 with a visible tear, 0.045 when identical to the eye."""
    lum = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    d = np.abs(high_row[..., :3] @ lum - low_row[..., :3] @ lum)
    b = 16
    h, w = (d.shape[0] // b) * b, (d.shape[1] // b) * b
    blocks = d[:h, :w].reshape(h // b, b, w // b, b).mean(axis=(1, 3))
    return float(np.percentile(blocks, 99.5)), float(d.mean())


def save_comparison(high_row, low_row, path):
    grid = np.concatenate([low_row, high_row], axis=0)  # images are bottom-up: the original ends on top
    img = bpy.data.images.new("Compare", grid.shape[1], grid.shape[0], alpha=True)
    img.pixels.foreach_set(grid.astype(np.float32).ravel())
    save_image(img, path)


def fresh_uvs(obj):
    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------- main

def main():
    global SMOOTH_ANGLE
    a = parse()
    SMOOTH_ANGLE = a.smooth_angle
    a.out = os.path.abspath(a.out)
    a.previews = os.path.abspath(a.previews) if a.previews else None
    lo_budget, hi_budget, tex_default = BUDGETS[a.type]
    start = a.tris or lo_budget
    stop = max(start, a.max_tris or hi_budget)
    tex_size = a.tex or tex_default
    previews = a.previews or a.out
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(previews, exist_ok=True)
    work = tempfile.mkdtemp(prefix="opt3d_")
    try:
        mesh_path, tex = resolve_source(a.src, work)
        reset()
        high = import_mesh(mesh_path)
        high.name = a.name + "_Original"
        normalise(high, a.size, a.pivot)
        source_tris = tri_count(high)
        v = verts(high)
        dims = (v.max(0) - v.min(0)).tolist()
        size = max(dims)
        # Keep the original's own materials when they carry textures and either there are several (one
        # texture set each) or no loose texture set was found; otherwise rebuild one from the files found.
        if has_image_textures(high) and (len(high.data.materials) > 1 or not tex["base"]):
            tex["materials"] = [m.name for m in high.data.materials if m]
        else:
            source_material(high, tex)
        high_masks = silhouettes(high, high, work, "high")
        comparison_rig(a.samples)
        high_row = render_row(high, high, work, a.samples)

        # The ladder: the budget's minimum first, up in 25% steps only while something still shows. Two gates,
        # both measured against the original: the outline (cheap, before baking) and, after baking, a local
        # shading defect in the final render.
        ladder, tris, low, remesh, prev = [], start, None, None, None
        while True:
            if low is not None:
                bpy.data.objects.remove(low, do_unlink=True)
            low = decimated_copy(high, tris, remesh)
            if remesh is None and tri_count(low) > tris * 1.3:
                print("DECIMATE STUCK at", tri_count(low), "for", tris, "-> voxel remesh first", flush=True)
                remesh = size / a.remesh_res
                bpy.data.objects.remove(low, do_unlink=True)
                low = decimated_copy(high, tris, remesh)
            low.name = a.name
            low_masks = silhouettes(low, high, work, "low%d" % tris)
            scores = {k: {"outline_px": round(outline_deviation(high_masks[k], m), 3), "iou": round(iou(high_masks[k], m), 4)}
                      for k, m in low_masks.items()}
            worst = max(sc["outline_px"] for sc in scores.values())
            step = {"tris": tri_count(low), "worst_outline_px": worst, "remeshed": remesh is not None}
            ladder.append(step)
            print("LADDER", tris, "->", tri_count(low), "worst outline px", worst, flush=True)
            last = tris >= stop or tri_count(low) >= source_tris
            # Plateau: 25% more triangles bought less than 5% of outline. The loss is not about triangle
            # count (a remesh floor, a part thinner than a voxel), so go back one step and keep it cheap.
            if worst > a.outline and prev is not None and (prev[1] - worst) < prev[1] * 0.05:
                print("PLATEAU at", tris, "-> back to", prev[0], flush=True)
                step["plateau"] = True
                tris = prev[0]
                bpy.data.objects.remove(low, do_unlink=True)
                low = decimated_copy(high, tris, remesh)
                low.name = a.name
                last = True
            if worst > a.outline and not last:
                prev = (tris, worst)
                tris = min(stop, int(tris * 1.25))
                continue

            if a.uv == "smart":
                fresh_uvs(low)
            images = bake_channels(high, low, tex, size, tex_size)
            preview_material(low, images.get("base"), images["normal"])
            low_row = render_row(low, high, work, a.samples)
            hotspot, mean_diff = shading_hotspot(high_row, low_row)
            step.update({"shading_hotspot": round(hotspot, 3), "shading_mean": round(mean_diff, 4)})
            print("SHADING", tris, "hotspot", round(hotspot, 3), "mean", round(mean_diff, 4), flush=True)
            if hotspot <= a.hotspot or last:
                break
            tris = min(stop, int(tris * 1.25))

        paths = write_textures(images, a.out, a.name, tex_size, a.no_metal)
        compare_path = os.path.join(previews, a.name + "_compare.png")
        save_comparison(high_row, low_row, compare_path)

        low.data.materials.clear()
        select_only(low)
        fbx = os.path.join(a.out, a.name + ".fbx")
        bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_scale_options='FBX_SCALE_ALL',
                                 axis_forward='-Z', axis_up='Y', path_mode='STRIP', embed_textures=False,
                                 mesh_smooth_type='FACE')
        report = {
            "name": a.name, "type": a.type, "source_mesh": mesh_path, "source_triangles": source_tris,
            "final_triangles": tri_count(low), "budget": [lo_budget, hi_budget], "within_budget": tri_count(low) <= hi_budget,
            "ladder": ladder, "silhouette": scores, "outline_target_px": a.outline, "hotspot_target": a.hotspot,
            "uv": a.uv, "size_m": [round(d, 4) for d in dims], "texture_size": tex_size, "metal_zeroed": a.no_metal,
            "fbx": fbx, "textures": paths, "comparison": compare_path, "sources_found": tex,
        }
        with open(os.path.join(previews, a.name + "_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("REPORT", json.dumps(report, ensure_ascii=False), flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)


main()
