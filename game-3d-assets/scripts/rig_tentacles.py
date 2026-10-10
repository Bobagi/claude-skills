# Rigs a tentacle, or a radial creature with arms in a star (octopus), with a chain of bones along each arm that
# follows the arm's own centre line, curled tips included.
#   blender -b --factory-startup --python rig_tentacles.py -- --src <mesh.fbx> --out <rigged.fbx> [--previews <dir>]
#          --arms 1            a single tentacle (the chain starts at the thick end)
#          --arms 8            radial: the arms lie in a plane around a body (the mantle), found by PCA
#          [--bones 12] [--core 0.2] [--samples 3000]
# How (and why not bone heat): heat weighting fails on meshes with loose detail (suckers, spikes), and ordering the
# arm by distance from the centre breaks where the tip curls back. Instead, each arm's surface is sampled into a
# neighbour graph and the geodesic distance from the arm's base ring is computed (Dijkstra): it grows steadily along
# the arm round any curl. Joints are the centroids of the bands of equal geodesic distance; each vertex is weighted
# between the two bones whose middles bracket its distance (smooth, no heat solve). Radial: the arms are told apart
# by their angle in the star plane, the mantle is what lies inside --core (fraction of the star's radius) and gets a
# two-bone chain along the plane normal, toward the side it bulges to. Writes posed previews (arms curled, the
# tentacle in an S) to check the deformation.
import argparse
import heapq
import math
import os
import random
import sys

import bpy
from mathutils import Vector, kdtree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--previews")
ap.add_argument("--arms", type=int, default=1)
ap.add_argument("--bones", type=int, default=12, help="bones per arm")
ap.add_argument("--core", type=float, default=0.2, help="radial: arms start this far from the mouth (fraction of the star radius)")
ap.add_argument("--path-tol", type=float, default=0.12, help="radial: how far off the mouth-to-tip path (fraction of "
                "the star radius, as extra geodesic length) a vertex may be and still be arm, not mantle")
ap.add_argument("--samples", type=int, default=3000, help="graph points per arm")
ap.add_argument("--neighbours", type=int, default=10)
ap.add_argument("--debug-csv", help="radial: writes x, y (star plane), height and arm of every vertex, to plot")
a = ap.parse_args(argv)
a.src, a.out = os.path.abspath(a.src), os.path.abspath(a.out)
if a.previews:
    a.previews = os.path.abspath(a.previews)
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=a.src)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
for o in list(bpy.data.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o)
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

P = [v.co.copy() for v in mesh.data.vertices]
n_v = len(P)
centre = sum(P, Vector()) / n_v


def pca(points, c):
    m = [[0.0] * 3 for _ in range(3)]
    for p in points:
        d = p - c
        for i in range(3):
            for j in range(3):
                m[i][j] += d[i] * d[j]
    # Power iteration with deflation (no numpy dependency needed).
    vecs, vals = [], []
    mat = [row[:] for row in m]
    for _ in range(3):
        v = Vector((random.random(), random.random(), random.random())).normalized()
        for _ in range(200):
            w = Vector([sum(mat[i][j] * v[j] for j in range(3)) for i in range(3)])
            if w.length < 1e-12:
                break
            v = w.normalized()
        lam = sum(v[i] * sum(mat[i][j] * v[j] for j in range(3)) for i in range(3))
        vecs.append(v.copy()); vals.append(lam)
        for i in range(3):
            for j in range(3):
                mat[i][j] -= lam * v[i] * v[j]
    return vecs, vals  # largest first


axes, variances = pca(P, centre)
print("pca variances", [round(v / n_v, 4) for v in variances])

# ---- arms: which vertices, and where each starts --------------------------------------------------------------
arm_of = [-1] * n_v          # -1 = mantle (radial) / never for single
geo = [0.0] * n_v            # distance along the arm from its base
arm_len = []
starts = []                  # per arm: indices of the base ring
if a.arms == 1:
    axis = axes[0]
    t = [(p - centre).dot(axis) for p in P]
    lo, hi = min(t), max(t)
    span = hi - lo

    def spread(sel):
        pts = [P[i] for i in sel]
        c = sum(pts, Vector()) / len(pts)
        return sum(((p - c) - axis * (p - c).dot(axis)).length for p in pts) / len(pts)

    near_lo = [i for i in range(n_v) if t[i] < lo + span * 0.03]
    near_hi = [i for i in range(n_v) if t[i] > hi - span * 0.03]
    base_is_lo = spread(near_lo) >= spread(near_hi)
    arm_of = [0] * n_v
    starts.append(near_lo if base_is_lo else near_hi)
    normal = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((0, 1, 0))
    print(f"single tentacle: length {span:.3f}, base at {'low' if base_is_lo else 'high'} end")
else:
    normal = axes[2]
    e1, e2 = axes[0], axes[1]
    xs = [(p - centre).dot(e1) for p in P]
    ys = [(p - centre).dot(e2) for p in P]
    R = max(math.hypot(x, y) for x, y in zip(xs, ys))
    # Surface graph: the mesh's own edges (a kNN graph jumps between an arm and the mantle it passes behind), plus
    # one link from every loose island (a sucker) to the nearest vertex of the main body.
    adj = [[] for _ in range(n_v)]
    for e in mesh.data.edges:
        i, j = e.vertices
        w = (P[i] - P[j]).length
        adj[i].append((j, w)); adj[j].append((i, w))
    comp = [-1] * n_v
    sizes = []
    for s0 in range(n_v):
        if comp[s0] >= 0:
            continue
        cid = len(sizes); comp[s0] = cid; stack = [s0]; count = 0
        while stack:
            u = stack.pop(); count += 1
            for v, _ in adj[u]:
                if comp[v] < 0:
                    comp[v] = cid; stack.append(v)
        sizes.append(count)
    main = max(range(len(sizes)), key=lambda c: sizes[c])
    main_list = [i for i in range(n_v) if comp[i] == main]
    kdm = kdtree.KDTree(len(main_list))
    for n_, i in enumerate(main_list):
        kdm.insert(P[i], n_)
    kdm.balance()
    for i in range(n_v):
        if comp[i] != main:
            _, n_, w = kdm.find(P[i])
            j = main_list[n_]
            adj[i].append((j, w)); adj[j].append((i, w))
    print(f"surface graph: {len(sizes)} pieces, main {sizes[main]} of {n_v} verts")

    def dijkstra(sources):
        dist = [math.inf] * n_v
        heap = []
        for s_ in sources:
            dist[s_] = 0.0
            heap.append((0.0, s_))
        heapq.heapify(heap)
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        return dist

    # From the mouth (the vertices nearest the centre), then the arm tips by farthest-point sampling: each new tip
    # is the vertex farthest from the centre and from every tip found so far.
    kdc = kdtree.KDTree(n_v)
    for i, p in enumerate(P):
        kdc.insert(p, i)
    kdc.balance()
    d_centre = dijkstra([i for _, i, _ in kdc.find_n(centre, 20)])
    tips, d_tip = [], []
    nearest = d_centre[:]
    for k in range(a.arms):
        t_ = max(range(n_v), key=lambda i: nearest[i])
        tips.append(t_)
        d_tip.append(dijkstra([t_]))
        nearest = [min(nearest[i], d_tip[-1][i]) for i in range(n_v)]
    # An arm is the band of surface on the way from the mouth to its tip: centre-to-vertex plus vertex-to-tip is
    # about centre-to-tip. The mantle is off every such path, so it stays mantle even where an arm passes behind it.
    core_geo = a.core * R
    tol = a.path_tol * R
    for i in range(n_v):
        if d_centre[i] < core_geo:
            continue
        k = min(range(a.arms), key=lambda k: d_centre[i] + d_tip[k][i] - d_centre[tips[k]])
        if d_centre[i] + d_tip[k][i] - d_centre[tips[k]] < tol:
            arm_of[i] = k
            geo[i] = d_centre[i] - core_geo
    arm_len = [d_centre[tips[k]] - core_geo for k in range(a.arms)]
    for k in range(a.arms):
        print(f"arm {k}: {sum(1 for x in arm_of if x == k)} verts, length {arm_len[k]:.3f}")
    if sum((p - centre).dot(normal) for p in P if (p - centre).length < core_geo) < 0:
        normal = -normal
    head = [P[i] for i in range(n_v) if arm_of[i] < 0 and d_centre[i] >= core_geo]
    mantle_dir = (sum(head, Vector()) / len(head) - centre).normalized() if head else normal
    if a.debug_csv:
        with open(a.debug_csv, "w") as f:
            for i in range(n_v):
                f.write(f"{xs[i]:.4f},{ys[i]:.4f},{(P[i] - centre).dot(normal):.4f},{arm_of[i]}" + chr(10))
    print(f"radial: star radius {R:.3f}, arms start {core_geo:.3f} from the mouth, path tolerance {tol:.3f}, "
          f"mantle verts {sum(1 for x in arm_of if x < 0)}")

# ---- single tentacle: geodesic distance from the base ring over a neighbour graph --------------------------------
for k in (range(1) if a.arms == 1 else ()):
    idx = [i for i in range(n_v) if arm_of[i] == k]
    sample = idx if len(idx) <= a.samples else random.sample(idx, a.samples)
    sample = list(dict.fromkeys(sample + random.sample(starts[k], min(len(starts[k]), 60))))
    kd = kdtree.KDTree(len(sample))
    for j, i in enumerate(sample):
        kd.insert(P[i], j)
    kd.balance()
    dist = [math.inf] * len(sample)
    heap = []
    start_set = set(starts[k])
    for j, i in enumerate(sample):
        if i in start_set:
            dist[j] = 0.0
            heap.append((0.0, j))
    heapq.heapify(heap)
    while heap:
        d, j = heapq.heappop(heap)
        if d > dist[j]:
            continue
        for _, jj, w in kd.find_n(P[sample[j]], a.neighbours + 1):
            nd = d + w
            if nd < dist[jj]:
                dist[jj] = nd
                heapq.heappush(heap, (nd, jj))
    # Small clusters the neighbour graph did not join (a loose sucker): the nearest reached point's distance plus
    # the gap. Giving them the arm's length instead turned them into spikes thrown to the tip bone.
    reached = [j for j, d in enumerate(dist) if not math.isinf(d)]
    unreached = len(sample) - len(reached)
    if unreached:
        kr = kdtree.KDTree(len(reached))
        for n_, j in enumerate(reached):
            kr.insert(P[sample[j]], n_)
        kr.balance()
        for j in range(len(sample)):
            if math.isinf(dist[j]):
                _, n_, w = kr.find(P[sample[j]])
                dist[j] = dist[reached[n_]] + w
    for i in idx:
        _, j, w = kd.find(P[i])
        geo[i] = dist[j] + w
    L = max(geo[i] for i in idx)
    arm_len.append(L)
    print(f"arm {k}: {len(idx)} verts, {len(sample)} samples, unreached {unreached}, length {L:.3f}")

# ---- joints: centroids of equal-distance bands ------------------------------------------------------------------
N = a.bones
joints = []
for k in range(max(1, a.arms)):
    idx = [i for i in range(n_v) if arm_of[i] == k]
    L = arm_len[k]
    h = L / (2 * N)
    js = []
    for j in range(N + 1):
        tj = L * j / N
        band = [P[i] for i in idx if abs(geo[i] - tj) <= h]
        if j == N:
            far = sorted(idx, key=lambda i: -geo[i])[:max(3, len(idx) // 200)]
            band = [P[i] for i in far]
        if j == 0:
            band = [P[i] for i in idx if geo[i] <= h]
        js.append(sum(band, Vector()) / len(band) if band else (js[-1] if js else centre))
    joints.append(js)

# ---- armature ---------------------------------------------------------------------------------------------------
arm_data = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, connect=False):
    b = eb.new(name)
    b.head, b.tail = head, tail
    if (b.tail - b.head).length < 1e-4:
        b.tail = b.head + normal * 0.02
    if parent:
        b.parent = eb[parent]
        b.use_connect = connect
    b.align_roll(normal)
    return b


names = []   # per arm, bone names in order
if a.arms == 1:
    js = joints[0]
    for i in range(N):
        nm = f"Tentacle_{i:02d}"
        bone(nm, js[i], js[i + 1], f"Tentacle_{i - 1:02d}" if i else None, i > 0)
        names.append(nm)
    names = [names]
else:
    # The mantle chain runs from the centre toward the dome's centroid, as far as the mantle reaches that way.
    core_h = max(((P[i] - centre).dot(mantle_dir) for i in range(n_v) if arm_of[i] < 0), default=0.1)
    base = centre
    bone("Root", base, base + mantle_dir * core_h * 0.25)
    bone("Mantle_1", base + mantle_dir * core_h * 0.25, base + mantle_dir * core_h * 0.6, "Root", True)
    bone("Mantle_2", base + mantle_dir * core_h * 0.6, base + mantle_dir * core_h, "Mantle_1", True)
    for k in range(a.arms):
        js = joints[k]
        arm_names = []
        for i in range(N):
            nm = f"Arm{k}_{i:02d}"
            bone(nm, js[i], js[i + 1], f"Arm{k}_{i - 1:02d}" if i else "Root", i > 0)
            arm_names.append(nm)
        names.append(arm_names)
bpy.ops.object.mode_set(mode="OBJECT")

# ---- weights ----------------------------------------------------------------------------------------------------
groups = {}


def group(nm):
    if nm not in groups:
        groups[nm] = mesh.vertex_groups.new(name=nm)
    return groups[nm]


for nm in [b.name for b in arm_data.bones]:
    group(nm)
for i in range(n_v):
    k = arm_of[i]
    if k < 0:
        # Mantle: blended along the mantle's axis from the root to the end of the dome.
        hgt = max(0.0, (P[i] - centre).dot(mantle_dir)) / max(core_h, 1e-4)
        f = min(hgt, 1.0) * 3.0
        chain = ["Root", "Mantle_1", "Mantle_2"]
        k0 = min(int(f), 2); frac = f - k0
        group(chain[k0]).add([i], 1.0 - frac if k0 < 2 else 1.0, "REPLACE")
        if k0 < 2 and frac > 0:
            group(chain[k0 + 1]).add([i], frac, "REPLACE")
        continue
    L = arm_len[k]
    f = geo[i] / L * N - 0.5            # bone middles at integer f
    chain = names[k]
    if f <= 0:
        # Base of the arm: blend into the root (radial) or stay on the first bone (single).
        if a.arms > 1:
            w = min(1.0, -f * 2)
            group("Root").add([i], w, "REPLACE")
            group(chain[0]).add([i], 1.0 - w, "REPLACE")
        else:
            group(chain[0]).add([i], 1.0, "REPLACE")
        continue
    k0 = min(int(f), N - 1)
    frac = f - k0
    if k0 >= N - 1:
        group(chain[N - 1]).add([i], 1.0, "REPLACE")
    else:
        group(chain[k0]).add([i], 1.0 - frac, "REPLACE")
        group(chain[k0 + 1]).add([i], frac, "REPLACE")

mesh.parent = rig
mod = mesh.modifiers.new("Armature", "ARMATURE"); mod.object = rig
mesh.name = os.path.splitext(os.path.basename(a.out))[0]
print("bones", len(arm_data.bones), "verts", n_v, "arm lengths", [round(x, 3) for x in arm_len])

os.makedirs(os.path.dirname(a.out), exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True); rig.select_set(True)
bpy.ops.export_scene.fbx(filepath=a.out, use_selection=True, add_leaf_bones=False, bake_anim=False,
                         armature_nodetype="NULL", apply_scale_options="FBX_SCALE_ALL", mesh_smooth_type="FACE")
print("written", a.out)

# ---- posed previews ---------------------------------------------------------------------------------------------
if a.previews:
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    for k, chain in enumerate(names):
        for i, nm in enumerate(chain):
            pb = rig.pose.bones[nm]
            pb.rotation_mode = "XYZ"
            if a.arms == 1:
                pb.rotation_euler = (0, 0, math.radians(14 * math.sin(i / N * math.pi * 2)))
            else:
                # Curl out of the plane on alternate arms, sway in it on the others.
                pb.rotation_euler = (math.radians(9 if k % 2 == 0 else 0), 0, math.radians(0 if k % 2 == 0 else 7))
    bpy.ops.object.mode_set(mode="OBJECT")
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.render.resolution_x = scene.render.resolution_y = 900
    bb = [mesh.matrix_world @ Vector(c) for c in mesh.bound_box]
    size = max((max(v[i] for v in bb) - min(v[i] for v in bb)) for i in range(3))
    mid = sum(bb, Vector()) / 8
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = size * 1.5
    os.makedirs(a.previews, exist_ok=True)
    base = os.path.splitext(os.path.basename(a.out))[0]
    up_hint = Vector((0, 0, 1)) if abs(normal.z) < 0.9 else Vector((0, 1, 0))
    for name, d in (("normal", normal), ("edge", normal.cross(up_hint).normalized() if normal.cross(up_hint).length > 0.1 else Vector((1, 0, 0))),
                    ("three_quarter", (normal + normal.cross(up_hint).normalized()).normalized())):
        cam.location = mid + d * size * 3
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(a.previews, f"{base}_pose_{name}.png")
        bpy.ops.render.render(write_still=True)
    print("previews in", a.previews)
