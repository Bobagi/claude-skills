# Trees and bushes into the triangle budget with a FULL crown: foliage_reduce.py drops whole leaves until the budget
# fits, which left island_tree_02 with 400 of its 35 thousand leaves (a bare trunk, 03/10). This does what game
# foliage is made of instead: the leaves are replaced by leaf-cluster cards (leaf_cards.py makes the texture from the
# plant's own leaves). The original leaves are grouped on a grid; each occupied cell becomes two crossed cards at the
# cell's leaf centre, as big as the cell, turned at random, so the crown keeps its exact outline and density. The
# trunk and branches (everything not on the leaf material) are collapsed to what is left of the budget, UVs kept.
# Card normals point out from the crown's centre (a crown lit as one rounded mass, not as flat cards).
# Run (Blender 5.2, background):
#   blender -b --factory-startup --python tree_cards.py -- --src <polyhaven folder with the 1k FBX and textures/>
#       --name IslandTree --out <Assets/.../Vegetation/IslandTree> --tris 4000 --leaf leaves [--wood 1500] [--seed 3]
#       [--height 10]
# The card texture <Name>_cards_BaseColor.png must already be in --out (leaf_cards.py).
# --height scales the tree to that real height in metres first (Poly Haven trees come at scan size: island_tree_01 is
# 5 m, jacaranda_tree 19 m). Each wood part also gets <Name>_<part>_MetallicSmoothness.png (R 0, A 1 - roughness).
# Then check it with tree_compare.py (original x result render, coverage per view, report json).
import argparse
import math
import os
import random
import shutil
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--tris", type=int, default=4000)
    p.add_argument("--leaf", required=True, help="text in the leaf material's name")
    p.add_argument("--wood", type=int, default=0, help="triangles for trunk and branches (default: 35%% of --tris)")
    p.add_argument("--card-scale", type=float, default=1.7)
    p.add_argument("--seed", type=int, default=3)
    p.add_argument("--wood-area", type=float, default=1.0,
                   help="keep the loose wood parts with the most surface up to this share of it (0.9 drops fine twigs)")
    p.add_argument("--weld", type=float, default=0.0,
                   help="weld split seams closer than this share of the height before the collapse (default off: on "
                        "tree_small_02, 26/10, welding turned the trunk into a fat wedge)")
    p.add_argument("--height", type=float, default=0.0, help="scale to this height in metres (0 keeps the source size)")
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:])


def joined():
    fbx = next(os.path.join(SRC, f) for f in os.listdir(SRC) if f.lower().endswith(".fbx"))
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
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def texture_parts(tex, asset, leaf):
    """Parts named by the diffuse textures: <asset>_<part>_diff_* ("main" for the bare <asset>_diff_*)."""
    parts = []
    for f in os.listdir(tex):
        if "_diff_" in f:
            part = f.split("_diff_")[0][len(asset):].strip("_") or "main"
            if leaf not in part and part not in parts:
                parts.append(part)
    return parts


def match_part(mat_part, parts):
    """Texture part for a material part: same name, one the prefix of the other (branches/branch), else main."""
    if mat_part in parts:
        return mat_part
    if not mat_part:
        return "main" if "main" in parts else (parts[0] if parts else "main")
    for p in parts:
        if p != "main" and (mat_part.startswith(p) or p.startswith(mat_part)):
            return p
    return "main" if "main" in parts else (parts[0] if parts else mat_part)


def loose_parts(bm):
    bm.faces.ensure_lookup_table()
    seen, parts = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, group = [f], []
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
    return parts


def main():
    global SRC
    a = args()
    SRC = a.src
    rng = random.Random(a.seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = joined()
    if a.height > 0:
        zs = [v.co.z for v in obj.data.vertices]
        obj.data.transform(Matrix.Scale(a.height / (max(zs) - min(zs)), 4))
    mats =[m.name if m else "" for m in obj.data.materials]
    leaf_slots = {i for i, n in enumerate(mats) if a.leaf in n}
    if not leaf_slots:
        raise SystemExit(f"no material with '{a.leaf}' in {mats}")

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    before = len(bm.faces)
    leaf_faces = [f for f in bm.faces if f.material_index in leaf_slots]
    points = [(f.calc_center_median().copy(), f.calc_area()) for f in leaf_faces]
    bmesh.ops.delete(bm, geom=leaf_faces, context='FACES')
    bm.to_mesh(obj.data)
    bm.free()

    # Wood: collapse to its share of the budget.
    wood_budget = a.wood or int(a.tris * 0.35)
    # Fine twigs first (island_tree_01, 26/10: 500 thousand triangles of loose twigs inside the crown; the uniform
    # collapse then shrank the trunk to a few faces and the loose-part pass below threw it away as "small", leaving
    # a crown floating on air). Keep the loose parts with the most surface until --wood-area of it; the cards
    # cover the rest.
    if a.wood_area < 1.0:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        parts = loose_parts(bm)
        areas = [sum(f.calc_area() for f in p) for p in parts]
        total = sum(areas) or 1.0
        order = sorted(range(len(parts)), key=lambda i: -areas[i])
        kept, drop = 0.0, []
        for i in order:
            if kept >= total * a.wood_area:
                drop.extend(parts[i])
            kept += areas[i]
        bmesh.ops.delete(bm, geom=drop, context='FACES')
        bm.to_mesh(obj.data)
        bm.free()
        print(f"[cards] wood: {len(parts)} loose parts, dropped {len(drop)} faces of the smallest ones")
    wood = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    # Optional seam weld before the collapse (UVs stay per loop). Off by default: it did not unstick jacaranda_tree
    # and it wedged tree_small_02's trunk (26/10).
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    zs = [v.co.z for v in bm.verts]
    if a.weld > 0:
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=(max(zs) - min(zs)) * a.weld)
    bm.to_mesh(obj.data)
    bm.free()
    # One collapse pass can stop far above the ratio (jacaranda_tree, 26/10: 891 thousand -> 9.7 thousand for a
    # 525 target): repeat while it still shrinks.
    for _ in range(5):
        if wood <= wood_budget * 1.1:
            break
        mod = obj.modifiers.new("Decimate", 'DECIMATE')
        mod.ratio = max(0.002, wood_budget / wood)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        now = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        if now > wood * 0.9:
            break
        wood = now
    wood = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    # The collapse stalls on thousands of tiny loose twigs (searsia_lucida: 4447 left of a 800 budget, 03/10):
    # drop loose parts, smallest SURFACE first (not face count: a collapsed trunk has few faces and a big surface)
    # and at random among equals, until the wood fits; the big limbs stay.
    if wood > wood_budget * 1.2:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        parts = loose_parts(bm)
        rng.shuffle(parts)
        parts.sort(key=lambda p: sum(f.calc_area() for f in p))
        drop, left = [], wood
        for p in parts[:-1]:
            if left <= wood_budget:
                break
            drop.extend(p)
            left -= len(p)
        bmesh.ops.delete(bm, geom=drop, context='FACES')
        bm.to_mesh(obj.data)
        bm.free()
        wood = sum(len(p.vertices) - 2 for p in obj.data.polygons)

    # Leaves: a grid sized so the occupied cells give the cards the rest of the budget (4 triangles per cell).
    target = max(20, (a.tris - wood) // 4)
    lo = Vector((min(p.x for p, _ in points), min(p.y for p, _ in points), min(p.z for p, _ in points)))
    hi = Vector((max(p.x for p, _ in points), max(p.y for p, _ in points), max(p.z for p, _ in points)))
    small, big = 0.01, max(hi - lo)
    cells = {}
    for _ in range(40):
        size = math.sqrt(small * big)
        cells = {}
        for p, w in points:
            key = (int((p.x - lo.x) / size), int((p.y - lo.y) / size), int((p.z - lo.z) / size))
            c = cells.setdefault(key, [Vector(), 0.0])
            c[0] += p * w
            c[1] += w
        if len(cells) > target:
            small = size
        else:
            big = size
    size = big
    cells = {}
    for p, w in points:
        key = (int((p.x - lo.x) / size), int((p.y - lo.y) / size), int((p.z - lo.z) / size))
        c = cells.setdefault(key, [Vector(), 0.0])
        c[0] += p * w
        c[1] += w
    centres = [c / w for c, w in cells.values() if w > 0]
    crown = sum(centres, Vector()) / len(centres)

    mesh = bpy.data.meshes.new("Cards")
    verts, faces, uvs, normals = [], [], [], []
    for c in centres:
        s = size * a.card_scale * rng.uniform(0.85, 1.2) * 0.5
        out = (c - crown)
        out = out.normalized() if out.length > 1e-4 else Vector((0, 0, 1))
        spin = Matrix.Rotation(rng.uniform(0, math.pi), 4, 'Z') @ Matrix.Rotation(rng.uniform(-0.5, 0.5), 4, 'X')
        for q in range(2):
            turn = spin @ Matrix.Rotation(q * math.pi / 2, 4, 'Z')
            right = (turn @ Vector((1, 0, 0, 0))).to_3d() * s
            up = (turn @ Vector((0, 0, 1, 0))).to_3d() * s
            b = len(verts)
            verts += [c - right - up, c + right - up, c + right + up, c - right + up]
            faces.append((b, b + 1, b + 2, b + 3))
            uvs += [(0, 0), (1, 0), (1, 1), (0, 1)]
            normals += [out] * 4
    mesh.from_pydata([v.to_tuple() for v in verts], [], faces)
    layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        layer.data[loop.index].uv = uvs[loop.vertex_index]
    mesh.normals_split_custom_set_from_vertices([n.to_tuple() for n in normals])
    cards_mat = bpy.data.materials.new(a.name + "_cards")
    mesh.materials.append(cards_mat)
    cards = bpy.data.objects.new("Cards", mesh)
    bpy.context.collection.objects.link(cards)

    # Wood's own UV layer must be named like the cards' one for the join to keep both.
    if obj.data.uv_layers:
        obj.data.uv_layers.active.name = "UVMap"
    bpy.ops.object.select_all(action='DESELECT')
    cards.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    # Unused leaf slots out.
    for i in sorted(leaf_slots, reverse=True):
        obj.active_material_index = i
        bpy.ops.object.material_slot_remove()

    # Wood materials renamed <Name>_<part>, the part being the one in the texture names written below (tree_small_02
    # has a "branches" material on "branch" textures and a "trunk" one on the bare asset textures, 26/10).
    asset = os.path.basename(os.path.normpath(SRC))
    tex_parts = texture_parts(os.path.join(SRC, "textures"), asset, a.leaf)
    for m in obj.data.materials:
        if m and not m.name.startswith(a.name + "_cards"):
            m.name = a.name + "_" + match_part(m.name[len(asset):].strip("_"), tex_parts)

    final = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    co = [v.co for v in obj.data.vertices]
    base = Vector((sum(v.x for v in co) / len(co), sum(v.y for v in co) / len(co), min(v.z for v in co)))
    obj.data.transform(Matrix.Translation(-base))
    obj.name = a.name
    os.makedirs(a.out, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(a.out, a.name + ".fbx"), use_selection=True, apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y', path_mode='STRIP', embed_textures=False, mesh_smooth_type='FACE')

    # Wood textures, as foliage_reduce.py writes them: <Name>_<part>_BaseColor.png (+ _Normal).
    tex = os.path.join(SRC, "textures")
    files = os.listdir(tex)
    asset = os.path.basename(os.path.normpath(SRC))
    for diff in [f for f in files if "_diff_" in f]:
        prefix = diff.split("_diff_")[0]
        part = prefix[len(asset):].strip("_") or "main"
        if a.leaf in part:
            continue
        nor = next((f for f in files if f.startswith(prefix + "_nor_gl_")), None)
        # The wood can be on an atlas with cut-outs (a bush's twigs): its alpha map goes into A, as foliage_reduce.py.
        alpha = next((f for f in files if f.startswith(prefix + "_alpha_")), None)
        target = os.path.join(a.out, a.name + "_" + part + "_BaseColor.png")
        try:
            img = bpy.data.images.load(os.path.join(tex, diff))
            w, h = img.size
            px = list(img.pixels[:])
            if alpha:
                am = bpy.data.images.load(os.path.join(tex, alpha))
                am.scale(w, h)
                ap = am.pixels[:]
                for i in range(w * h):
                    px[i * 4 + 3] = ap[i * 4]
            out = bpy.data.images.new(a.name + "_" + part, w, h, alpha=True)
            out.pixels[:] = px
            out.filepath_raw = target
            out.file_format = 'PNG'
            out.save()
        except RuntimeError as e:
            # Seen once with searsia_lucida's JPG (03/10): convert it outside (PIL) to the same name.
            print(f"[cards] WARNING could not write {target}: {e}")
        rough = next((f for f in files if f.startswith(prefix + "_rough_")), None)
        if rough:
            try:
                r = bpy.data.images.load(os.path.join(tex, rough))
                rw, rh = r.size
                rp = r.pixels[:]
                ms = [0.0] * (rw * rh * 4)
                for i in range(rw * rh):
                    ms[i * 4 + 3] = 1.0 - rp[i * 4]
                img = bpy.data.images.new(a.name + "_" + part + "_ms", rw, rh, alpha=True)
                img.colorspace_settings.name = 'Non-Color'
                img.pixels[:] = ms
                img.filepath_raw = os.path.join(a.out, a.name + "_" + part + "_MetallicSmoothness.png")
                img.file_format = 'PNG'
                img.save()
            except RuntimeError as e:
                print(f"[cards] WARNING could not write the MetallicSmoothness of {part}: {e}")
        if nor and nor.lower().endswith(".png"):
            shutil.copy(os.path.join(tex, nor), os.path.join(a.out, a.name + "_" + part + "_Normal.png"))
        elif nor:
            # Poly Haven ships some trunk normals as EXR (island_tree_01, tree_small_02): 8-bit PNG for the engine.
            n = bpy.data.images.load(os.path.join(tex, nor))
            n.colorspace_settings.name = 'Non-Color'
            png = bpy.data.images.new(a.name + "_" + part + "_nor", n.size[0], n.size[1], alpha=False)
            png.colorspace_settings.name = 'Non-Color'
            png.pixels[:] = n.pixels[:]
            png.filepath_raw = os.path.join(a.out, a.name + "_" + part + "_Normal.png")
            png.file_format = 'PNG'
            png.save()
    h = max(v.co.z for v in obj.data.vertices)
    print(f"[cards] materials: {[m.name for m in obj.data.materials]}")
    print(f"[cards] {a.name}: {before} -> {final} triangles (wood {wood}, {len(centres)} cards of {size * a.card_scale:.2f} m), height {h:.2f} m")


main()
