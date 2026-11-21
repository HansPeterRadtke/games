"""Blender-only disposable original animated model for Unity native QA."""
import bpy
import os
from pathlib import Path

path = os.environ.get('HPR_FBX_FIXTURE_OUT','')
if not path.startswith('/data/var/marketplace-account-setup/unity-20261121-evening/') or not path.endswith('.fbx'):
    raise RuntimeError('Fresh private QA destination is mandatory')
if Path(path).exists():
    raise RuntimeError('No replacing existing fixture')
Path(path).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1.0)
cube = bpy.context.active_object
cube.name='HPR_Original_Motion_Cube'
cube.location=(0,0,0)
cube.keyframe_insert('location',frame=1,group='OriginalMove')
cube.location=(0,0,1)
cube.keyframe_insert('location',frame=12,group='OriginalMove')
cube.location=(0,0,0)
cube.keyframe_insert('location',frame=24,group='OriginalMove')
bpy.context.scene.frame_start=1
bpy.context.scene.frame_end=24
bpy.ops.object.select_all(action='DESELECT')
cube.select_set(True)
bpy.context.view_layer.objects.active=cube
bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'},
    bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
    add_leaf_bones=False, path_mode='AUTO')
if not Path(path).is_file() or Path(path).stat().st_size < 4000:
    raise RuntimeError('Native FBX exporter did not create a nontrivial original animation')
print('HPR_ORIGINAL_FBX_CREATED_BYTES',Path(path).stat().st_size)
