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
# The card texture <Name>_cards_BaseColor.png must already be in --out (leaf_cards.py).
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


def main():
    global SRC
    a = args()
    SRC = a.src
    rng = random.Random(a.seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = joined()
    mats = [m.name if m else "" for m in obj.data.materials]
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
    wood = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    if wood > wood_budget:
        mod = obj.modifiers.new("Decimate", 'DECIMATE')
        mod.ratio = max(0.002, wood_budget / wood)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    wood = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    # The collapse stalls on thousands of tiny loose twigs (searsia_lucida: 4447 left of a 800 budget, 03/10):
    # drop loose parts, smallest first and at random among equals, until the wood fits; the big limbs stay.
    if wood > wood_budget * 1.2:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
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
        rng.shuffle(parts)
        parts.sort(key=len)
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
        if nor:
            shutil.copy(os.path.join(tex, nor), os.path.join(a.out, a.name + "_" + part + "_Normal" + os.path.splitext(nor)[1]))
    h = max(v.co.z for v in obj.data.vertices)
    print(f"[cards] materials: {[m.name for m in obj.data.materials]}")
    print(f"[cards] {a.name}: {before} -> {final} triangles (wood {wood}, {len(centres)} cards of {size * a.card_scale:.2f} m), height {h:.2f} m")


main()
