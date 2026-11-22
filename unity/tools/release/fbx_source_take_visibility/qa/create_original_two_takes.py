"""Original first-party Blender animated FBX with two separately authored Actions.

Only exports a fresh private path; the retail source copy is made after
independent verification. Never downloads third-party files or textures.
"""
import bpy
import os
from pathlib import Path

root='/data/var/marketplace-account-setup/unity-20261122-wave54/original-fbx-fixture/'
destination=os.environ.get('HPR_TAKE_SOURCE_FBX_OUT','')
if not destination.startswith(root) or not destination.endswith('.fbx') or Path(destination).exists():
    raise RuntimeError('A fresh original FBX destination within owner private test root is required')
Path(destination).parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1.0)
cube=bpy.context.active_object
cube.name='HPR_Original_Two_Take_Cube'
cube.animation_data_create()
count = os.environ.get('HPR_SOURCE_TAKE_ACTION_COUNT', '2')
if count not in ('1', '2'):
    raise RuntimeError('First-party source test supports one or two Actions only')
for action_name, coordinate in [('HPR_Original_Sway',0),('HPR_Original_Hop',2)][:int(count)]:
    action=bpy.data.actions.new(action_name)
    action.use_fake_user=True
    cube.animation_data.action=action
    cube.location=(0,0,0)
    cube.keyframe_insert(data_path='location',frame=1,group=action_name)
    if coordinate==0:cube.location=(1,0,0)
    else:cube.location=(0,0,2)
    cube.keyframe_insert(data_path='location',frame=13,group=action_name)
    cube.location=(0,0,0)
    cube.keyframe_insert(data_path='location',frame=25,group=action_name)
    print('HPR_ORIGINAL_ACTION',action_name,len(action.fcurves))
bpy.context.scene.frame_start=1
bpy.context.scene.frame_end=25
bpy.ops.object.select_all(action='DESELECT')
cube.select_set(True)
bpy.context.view_layer.objects.active=cube
bpy.ops.export_scene.fbx(filepath=destination, use_selection=True, object_types={'MESH'},
    bake_anim=True, bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,
    add_leaf_bones=False,path_mode='AUTO')
if not Path(destination).is_file() or Path(destination).stat().st_size<6000:
    raise RuntimeError('Native original Blender FBX with two Actions was not exported')
print('HPR_ORIGINAL_BLENDER_ACTION_COUNT',count, 'FBX_BYTES',Path(destination).stat().st_size)
