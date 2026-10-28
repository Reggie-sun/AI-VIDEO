"""Read saved rehearsal bytes, export geometry and camera facts, no media render."""
import hashlib
import json
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

root=Path(__file__).resolve().parent
asset=root/'MC00-city-v2.blend'
bpy.ops.wm.open_mainfile(filepath=str(asset))
sc=bpy.data.scenes['MC00_LOCAL_PREVIS']
bpy.context.window.scene=sc
cam=sc.objects['CAM_MC00_continuous']
names=['ENV_eave_building','ENV_residence','ENV_shelter_roof','ENV_gate','PRP_winch_plinth','PRP_return_base','PRP_control']
objects={}
for name in names:
    ob=sc.objects[name]
    corners=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    objects[name]={'position_m':list(ob.location),'dimensions_m':list(ob.dimensions),'min_m':[min(v[i] for v in corners) for i in range(3)],'max_m':[max(v[i] for v in corners) for i in range(3)]}
positions=[]
quats=[]
collisions=[]
side=[]
framing={}
for f in range(1,sc.frame_end+1):
    sc.frame_set(f)
    p=cam.matrix_world.translation.copy()
    positions.append(p)
    quats.append(cam.matrix_world.to_quaternion())
    side.append(10.5*(p.y+.15)+3.03*(p.x+3.5))
    for name in ('ENV_eave_building','ENV_residence'):
        box=objects[name]
        if all(box['min_m'][i]-.03 < p[i] < box['max_m'][i]+.03 for i in range(3)):
            collisions.append({'frame':f,'object':name})
    if f in (1,61,121,193,265,337,385,433,480):
        row={}
        for name in names:
            ob=sc.objects[name]
            uv=world_to_camera_view(sc,cam,ob.matrix_world.translation)
            row[name]={'u':uv.x,'v':uv.y,'depth':uv.z,'center_in_frame':0<uv.x<1 and 0<uv.y<1 and uv.z>0}
        framing[str(f)]=row
vel=[(b-a).length*24 for a,b in zip(positions,positions[1:])]
angular=[a.rotation_difference(b).angle*24*180/3.141592653589793 for a,b in zip(quats,quats[1:])]
sc.frame_set(480)
report={'authority':'LOCAL_STATIC_REFERENCE_AND_DESIGN_AUDIT_ONLY','asset':asset.name,'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'scene':sc.name,'fps':sc.render.fps,'frames':sc.frame_end,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'lens_mm':cam.data.lens,'camera_marker_count':len(sc.timeline_markers),'objects':objects,'camera_inside_named_building':collisions,'traction_outgoing_side_range': [min(side),max(side)],'camera_path_length_m':sum((b-a).length for a,b in zip(positions,positions[1:])),'speed_mps_max':max(vel),'speed_mps_last':vel[-1],'angular_degrees_per_second_first_2_5s_max':max(angular[:60]),'angular_degrees_per_second_max':max(angular),'sampled_center_projection_only':framing,'not_proven':['actual video motion','subject visibility between stills','occlusion-free entire camera volume','sound','model compliance','MC00-to-MC01 dynamic junction','human acceptance'],'new_mp4_count':len(list(root.glob('*.mp4')))}
(root/'scene-audit-v2.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:report[k] for k in ['camera_inside_named_building','traction_outgoing_side_range','camera_path_length_m','speed_mps_max','speed_mps_last','angular_degrees_per_second_first_2_5s_max','angular_degrees_per_second_max','new_mp4_count']}))
