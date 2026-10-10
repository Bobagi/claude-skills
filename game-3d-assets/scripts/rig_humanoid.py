# Rigs a humanoid mesh standing in T-pose with a Mixamo-named skeleton (so Mixamo animations and Unity's Humanoid
# avatar map onto it directly), when the Mixamo auto-rigger fails or is unavailable.
#   blender -b --factory-startup --python rig_humanoid.py -- --src <mesh.fbx> --out <rigged.fbx> [--previews <dir>]
#          [--chin 0.868 --shoulder 0.82 ...]   (heights as a fraction of the total height; defaults fit an adult)
# Assumptions (check the front render first): feet on the ground, faces -Y, arms along X, T-pose. Joints are
# found by measuring the mesh itself: the cross-section centroid of the arm, leg or trunk at each joint's height
# or reach, so the bones sit inside the volume. Weights: automatic (bone heat) on a voxel-remeshed watertight copy
# (heat fails on meshes with clutter and thin parts), then transferred to the real mesh by nearest surface,
# normalised and limited to 4 influences (Unity's default skin weights). Writes a posed preview (arms down, a knee
# and an elbow bent, head turned) to check the deformation before going to the engine.
import argparse
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--previews")
# Proportions as a fraction of height (feet at 0, head top at 1) and of half the arm span (0 centre, 1 fingertip).
ap.add_argument("--chin", type=float, default=0.868)
ap.add_argument("--neck", type=float, default=0.82)       # base of the neck / shoulder line
ap.add_argument("--hips", type=float, default=0.56)       # hip joint height
ap.add_argument("--knee", type=float, default=0.30)
ap.add_argument("--ankle", type=float, default=0.045)
ap.add_argument("--shoulder", type=float, default=0.19)   # shoulder joint, fraction of half span
ap.add_argument("--elbow", type=float, default=0.48)
ap.add_argument("--wrist", type=float, default=0.78)
ap.add_argument("--leg-x", type=float, default=0.1, help="fallback hip offset (fraction of height) if not measured")
ap.add_argument("--voxel", type=float, default=0.012, help="voxel size of the weighting proxy, metres")
a = ap.parse_args(argv)
a.src, a.out = os.path.abspath(a.src), os.path.abspath(a.out)
if a.previews:
    a.previews = os.path.abspath(a.previews)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=a.src)
mesh = [o for o in bpy.data.objects if o.type == "MESH"][0]
for o in list(bpy.data.objects):
    if o != mesh and o.type != "MESH":
        bpy.data.objects.remove(o)
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

V = [v.co.copy() for v in mesh.data.vertices]
zmin = min(v.z for v in V); zmax = max(v.z for v in V)
H = zmax - zmin
xmax = max(abs(v.x) for v in V)
# Centre line from the bounds (a symmetric T-pose model), not the vertex average: clutter on one side pulls it.
cx = (min(v.x for v in V) + max(v.x for v in V)) / 2
print(f"height {H:.3f} half span {xmax:.3f}")


def z_at(f):
    return zmin + f * H


def centroid(sel, fallback):
    pts = [v for v in V if sel(v)]
    if len(pts) < 8:
        return fallback
    return sum(pts, Vector()) / len(pts)


def trunk(f, half=0.12):
    z = z_at(f)
    return centroid(lambda v: abs(v.z - z) < 0.015 * H and abs(v.x - cx) < half * H, Vector((cx, 0, z)))


def arm(side, f):
    x = side * f * xmax
    c = centroid(lambda v: abs(v.x - x) < 0.012 * H and v.z > z_at(0.6), Vector((x, 0, z_at(a.neck))))
    c.x = x
    return c


def leg(side, f):
    z = z_at(f)
    c = centroid(lambda v: abs(v.z - z) < 0.012 * H and side * (v.x - cx) > 0.01 * H, Vector((cx + side * a.leg_x * H, 0, z)))
    c.z = z
    return c


J = {}
J["Hips"] = trunk(a.hips + 0.02)
J["Spine"] = trunk(a.hips + 0.08)
J["Spine1"] = trunk(a.hips + 0.15)
J["Spine2"] = trunk(a.neck - 0.08)
J["Neck"] = trunk(a.neck, 0.05)
J["Head"] = trunk((a.neck + a.chin) / 2 + 0.01, 0.06)
J["HeadTop_End"] = Vector((J["Head"].x, J["Head"].y, zmax))
for side, s in ((1, "Left"), (-1, "Right")):  # facing -Y, the character's left is +X
    J[s + "Shoulder"] = trunk(a.neck - 0.02, 0.05) + Vector((side * 0.02 * H, 0, 0))
    J[s + "Arm"] = arm(side, a.shoulder)
    J[s + "ForeArm"] = arm(side, a.elbow)
    J[s + "Hand"] = arm(side, a.wrist)
    J[s + "HandEnd"] = arm(side, 0.985)
    up = leg(side, a.hips)
    J[s + "UpLeg"] = up
    J[s + "Leg"] = leg(side, a.knee)
    J[s + "Foot"] = leg(side, a.ankle + 0.02)
    # Toes: the front-most point of the foot at the ankle's side.
    foot = [v for v in V if v.z < z_at(0.05) and side * (v.x - cx) > 0]
    tip = min(foot, key=lambda v: v.y) if foot else J[s + "Foot"] + Vector((0, -0.12, 0))
    J[s + "ToeBase"] = Vector((J[s + "Foot"].x, J[s + "Foot"].y + (tip.y - J[s + "Foot"].y) * 0.6, z_at(0.015)))
    J[s + "Toe_End"] = Vector((J[s + "Foot"].x, tip.y, z_at(0.015)))

# Symmetry: trunk joints on the centre line, each left/right pair mirrored to the mean of the two measurements.
for k in ("Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "HeadTop_End"):
    J[k].x = cx
for k in [k[4:] for k in J if k.startswith("Left")]:
    l, r = J["Left" + k], J["Right" + k]
    x = (abs(l.x - cx) + abs(r.x - cx)) / 2; y = (l.y + r.y) / 2; z = (l.z + r.z) / 2
    J["Left" + k] = Vector((cx + x, y, z)); J["Right" + k] = Vector((cx - x, y, z))

# Armature.
arm_data = bpy.data.armatures.new("Armature")
rig = bpy.data.objects.new("Armature", arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, connect=False):
    b = eb.new("mixamorig:" + name)
    b.head, b.tail = head, tail
    if (b.tail - b.head).length < 1e-4:
        b.tail = b.head + Vector((0, 0, 0.02))
    if parent:
        b.parent = eb["mixamorig:" + parent]
        b.use_connect = connect
    return b


bone("Hips", J["Hips"], J["Spine"])
bone("Spine", J["Spine"], J["Spine1"], "Hips", True)
bone("Spine1", J["Spine1"], J["Spine2"], "Spine", True)
bone("Spine2", J["Spine2"], J["Neck"], "Spine1", True)
bone("Neck", J["Neck"], J["Head"], "Spine2", True)
bone("Head", J["Head"], J["HeadTop_End"], "Neck", True)
for s in ("Left", "Right"):
    bone(s + "Shoulder", J[s + "Shoulder"], J[s + "Arm"], "Spine2")
    bone(s + "Arm", J[s + "Arm"], J[s + "ForeArm"], s + "Shoulder", True)
    bone(s + "ForeArm", J[s + "ForeArm"], J[s + "Hand"], s + "Arm", True)
    bone(s + "Hand", J[s + "Hand"], J[s + "HandEnd"], s + "ForeArm", True)
    bone(s + "UpLeg", J[s + "UpLeg"], J[s + "Leg"], "Hips")
    bone(s + "Leg", J[s + "Leg"], J[s + "Foot"], s + "UpLeg", True)
    bone(s + "Foot", J[s + "Foot"], J[s + "ToeBase"], s + "Leg", True)
    bone(s + "ToeBase", J[s + "ToeBase"], J[s + "Toe_End"], s + "Foot", True)
# Rolls: knees and elbows bend the natural way (bone Z axis forward for legs, back for arms).
for b in eb:
    if "Leg" in b.name or "Foot" in b.name or "Toe" in b.name:
        b.align_roll(Vector((0, -1, 0)))
    elif "Arm" in b.name or "Hand" in b.name or "Shoulder" in b.name:
        b.align_roll(Vector((0, 0, 1)))
    else:
        b.align_roll(Vector((0, -1, 0)))
bpy.ops.object.mode_set(mode="OBJECT")
for k, v in J.items():
    print(f"joint {k:14s} {v.x:+.3f} {v.y:+.3f} {v.z:+.3f}")

# Weights through a watertight proxy.
proxy = mesh.copy(); proxy.data = mesh.data.copy(); proxy.name = "WeightProxy"
bpy.context.scene.collection.objects.link(proxy)
rm = proxy.modifiers.new("Voxel", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = a.voxel
bpy.context.view_layer.objects.active = proxy
bpy.ops.object.modifier_apply(modifier=rm.name)
print("proxy verts", len(proxy.data.vertices))
for o in bpy.data.objects:
    o.select_set(False)
proxy.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
used = {x.group for v in proxy.data.vertices for x in v.groups if x.weight > 0.01}
print("proxy groups", len(proxy.vertex_groups), "empty", [g.name for g in proxy.vertex_groups if g.index not in used])

for g in proxy.vertex_groups:
    mesh.vertex_groups.new(name=g.name)
dt = mesh.modifiers.new("Weights", "DATA_TRANSFER")
dt.object = proxy
dt.use_vert_data = True
dt.data_types_verts = {"VGROUP_WEIGHTS"}
dt.vert_mapping = "POLYINTERP_NEAREST"
dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.modifier_apply(modifier=dt.name)
bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
# Vertices the transfer missed (inside a crease) take the weights of the nearest weighted vertex.
from mathutils import kdtree
weighted = [v for v in mesh.data.vertices if v.groups]
kd = kdtree.KDTree(len(weighted))
for i, v in enumerate(weighted):
    kd.insert(v.co, i)
kd.balance()
missing = [v for v in mesh.data.vertices if not v.groups]
for v in missing:
    src = weighted[kd.find(v.co)[1]]
    for g in src.groups:
        mesh.vertex_groups[g.group].add([v.index], g.weight, "REPLACE")
print("unweighted verts fixed", len(missing))
bpy.data.objects.remove(proxy)
mesh.parent = rig
mod = mesh.modifiers.new("Armature", "ARMATURE"); mod.object = rig
mesh.name = os.path.splitext(os.path.basename(a.out))[0]

# Export (rest pose).
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.ops.export_scene.fbx(filepath=a.out, use_selection=True, add_leaf_bones=False, bake_anim=False,
                         armature_nodetype="NULL", apply_scale_options="FBX_SCALE_ALL", mesh_smooth_type="FACE")
print("written", a.out)

# Posed preview: arms down, left elbow and right knee bent, head turned, to see the skin deform.
if a.previews:
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    pb = rig.pose.bones

    def rot(name, axis, deg):
        b = pb["mixamorig:" + name]; b.rotation_mode = "XYZ"
        r = list(b.rotation_euler); r["XYZ".index(axis)] = math.radians(deg); b.rotation_euler = r

    rot("LeftArm", "Y", 0); rot("LeftArm", "X", 0)
    for s, sg in (("Left", 1), ("Right", -1)):
        rot(s + "Arm", "Z", -65 * sg)
    rot("LeftForeArm", "X", 70)
    rot("RightLeg", "X", 70)
    rot("RightUpLeg", "X", -45)
    rot("Head", "Z", 35)
    bpy.ops.object.mode_set(mode="OBJECT")
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
    scene.render.resolution_x = scene.render.resolution_y = 900
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = H * 1.15
    centre = Vector((cx, 0, zmin + H / 2))
    os.makedirs(a.previews, exist_ok=True)
    base = os.path.splitext(os.path.basename(a.out))[0]
    for name, d, r in (("front", Vector((0, -1, 0)), (math.pi / 2, 0, 0)), ("side", Vector((1, 0, 0)), (math.pi / 2, 0, math.pi / 2)),
                       ("three_quarter", Vector((0.7, -0.7, 0.15)), (math.radians(82), 0, math.radians(45)))):
        cam.location = centre + d * H * 2; cam.rotation_euler = r
        scene.render.filepath = os.path.join(a.previews, f"{base}_pose_{name}.png")
        bpy.ops.render.render(write_still=True)
    print("previews in", a.previews)
