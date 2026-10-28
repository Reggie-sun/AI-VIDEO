"""Export the known saved proxy scene after Blender 5.2 media-type diagnosis."""
import bpy
import json
from pathlib import Path
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'MC00-city-v3.blend'))
sc=bpy.data.scenes['MC00_LOCAL_PREVIS']
bpy.context.window.scene=sc
sc.camera=sc.objects['CAM_MC00_continuous']
sc.frame_set(1)
sc.render.image_settings.media_type='VIDEO'
sc.render.image_settings.file_format='FFMPEG'
sc.render.ffmpeg.format='MPEG4'
sc.render.ffmpeg.codec='H264'
sc.render.ffmpeg.constant_rate_factor='MEDIUM'
sc.render.filepath=str(root/'MC00-previs-v3.mp4')
assert not (root/'MC00-previs-v3.mp4').exists()
bpy.ops.render.render(animation=True)
print(json.dumps({'ok':True,'frames':sc.frame_end,'fps':sc.render.fps,'purpose':'proxy spatial rehearsal; no photographic match claim'}))
