# Bakes every node's transform into its mesh and drops the hierarchy, so a model whose parts sit under rotated
# parent nodes (Sketchfab GLBs) comes out as it looks. The game-3d-assets optimizer joins the meshes without their
# parents' transforms: the Sketchfab door came out in pieces turned 90 degrees from each other (03/10).
# Skinned GLBs (an armature, even a trivial one) keep their raw vertices in glTF Y-up and leave the Y-up to Z-up
# conversion in the armature's rest pose, so the modifiers are applied first (convert to mesh); otherwise the mesh
# comes out lying down once the optimizer drops the armature (22/10, Sketchfab "Mid-poly Wooden Door with Animations").
# Run: blender -b --factory-startup --python flatten_model.py -- <in.glb|.fbx> <out.glb>
import sys, bpy
args = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
if args[0].lower().endswith((".glb", ".gltf")):
    bpy.ops.import_scene.gltf(filepath=args[0])
else:
    bpy.ops.import_scene.fbx(filepath=args[0])
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.convert(target='MESH')  # applies modifiers (armature in rest pose, mirrors, subdivision) in place
for o in meshes:
    m = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = m
for o in [o for o in bpy.data.objects if o.type != 'MESH']:
    bpy.data.objects.remove(o)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
lo = [min((o.matrix_world @ v.co)[i] for o in meshes for v in o.data.vertices) for i in range(3)]
hi = [max((o.matrix_world @ v.co)[i] for o in meshes for v in o.data.vertices) for i in range(3)]
print("[flatten]", len(meshes), "meshes, size", tuple(round(h - l, 3) for l, h in zip(lo, hi)))
bpy.ops.export_scene.gltf(filepath=args[1], export_format='GLB')
