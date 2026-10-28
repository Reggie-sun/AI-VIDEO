"""Task-local reproducible spatial rehearsal. Never writes Production state."""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT = Path(__file__).resolve().parent
FPS = 24
SECONDS = 20
FRAMES = FPS * SECONDS
NODES = [
    (0, (-18.6, -52, 18.3), (-23, -43, 17)),
    (2.5, (-17.8, -47, 18.2), (-22.2, -38, 16.9)),
    (5, (-15, -39, 17), (-5, 7, 5)),
    (8, (-12, -28, 13), (-3, 6, 3)),
    (11, (-9, -18, 8), (-1, 5, 2)),
    (14, (-3, -12, 4.5), (0, 3, 1.6)),
    (16, (3.5, -10, 2.8), (0.4, 3, 1.5)),
    (20, (9, -9, 2.6), (0.8, 3, 1.5)),
]
LOOKS = [(t, tuple((Vector(aim)-Vector(pos)).normalized())) for t,pos,aim in NODES]


def box(name, loc, dims, color):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.color = (*color, 1)
    return obj


def sphere(name, loc, radius, color):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.color = (*color, 1)
    return obj


def rod(name, a, b, radius, color):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius, depth=(b-a).length, location=(a+b)/2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    obj.color = (*color, 1)
    return obj


def smooth(table, t, column):
    """C1 cubic Hermite, time-aware tangents; ease-out endpoint velocity zero."""
    for i in range(len(table)-1):
        t0, t1 = table[i][0], table[i+1][0]
        if t <= t1:
            break
    p0, p1 = Vector(table[i][column]), Vector(table[i+1][column])
    if (p1-p0).length < 1e-5:
        return p0
    dt = t1-t0
    u = max(0, min(1, (t-t0)/dt))
    prev = max(0, i-1)
    nex = min(len(table)-1, i+2)
    m0 = (p1-Vector(table[prev][column]))/(t1-table[prev][0])
    if (p0-Vector(table[prev][column])).length < 1e-5:
        m0 = Vector((0,0,0))
    m1 = (Vector(table[nex][column])-p0)/(table[nex][0]-t0)
    if i == len(table)-2:
        m1 = Vector((0, 0, 0))
    return (2*u**3-3*u*u+1)*p0+(u**3-2*u*u+u)*dt*m0+(-2*u**3+3*u*u)*p1+(u**3-u*u)*dt*m1


def building(name, x, y, w, d, h, color):
    obj = box('ENV_'+name, (x, y, h/2), (w, d, h), color)
    box('ENV_'+name+'_roof', (x, y, h+.12), (w+.5, d+.5, .24), (.19,.23,.27))
    for z in range(2, int(h), 3):
        for a in range(1, int(w)-1, 3):
            col = (.8,.68,.38) if (a+z+int(x))%4 else (.22,.34,.41)
            box('ENV_'+name+'_window', (x-w/2+a,y-d/2-.025,z), (.85,.055,1.15),col)
    return obj


def make_scene():
    assert bpy.app.version >= (5,2,0), bpy.app.version_string
    sc = bpy.data.scenes.new('MC00_LOCAL_PREVIS')
    bpy.context.window.scene = sc
    sc.unit_settings.system = 'METRIC'
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = 1280,720
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1,FRAMES
    sc.world = bpy.data.worlds.new('MC00_world')
    sc.world.color = (.035,.045,.065)
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'OBJECT'
    sc.display.shading.show_shadows = True
    sc.display.shading.show_cavity = True
    sc.display.shading.cavity_type = 'BOTH'
    sc.display.shading.show_specular_highlight = True
    sc.display.shading.background_type = 'WORLD'
    sc.display.render_aa = '8'
    sc.view_settings.view_transform = 'Standard'
    box('ENV_ground',(0,35,-.2),(330,400,.3),(.19,.22,.25))
    box('ENV_main_road',(-14,35,-.025),(14,340,.05),(.08,.12,.16))
    box('ENV_cross_road',(0,34,-.02),(230,13,.055),(.08,.12,.16))
    for y in range(-100,185,7):
        box('ENV_road_dash',(-14,y,.01),(.12,3,.02),(.78,.75,.52))
    for x in (-21.2,-6.8):
        box('ENV_curb',(x,35,.08),(.25,340,.16),(.43,.46,.49))
    building('eave_building',-27,-59,14,18,18,(.39,.4,.43))
    # Northern exterior corner is x=-20,y=-50; no interior camera travel.
    rod('PRP_gutter',(-34.5,-49.65,18.0),(-19.5,-49.65,18.0),.11,(.64,.68,.7))
    for i in range(10):
        x=-20.0-i*.27
        dr=sphere('PRP_eave_drop', (x,-49.66,17.8),.045,(.7,.85,.92))
        for f in range(1,FRAMES+1):
            dr.location.z=17.85-((f+i*7)%38)/38*.85
            dr.keyframe_insert(data_path='location',frame=f)
    residence=building('residence',1,-30,10,14,12,(.48,.36,.3))
    # Distinct vertical stair glazing; exterior locator only, no stair action.
    box('ENV_residence_stair_glazing',(-4.07,-30,6),( .12,3,10),(.18,.48,.57))
    for z in range(2,12,2):
        box('ENV_residence_stair_mullion',(-4.15,-30,z),(.14,3.2,.12),(.7,.7,.65))
    for y in (-12,-6):
        for x in (-6.1,-4.3):
            rod('ENV_shelter_post',(x,y,.15),(x,y,2.65),.065,(.37,.53,.57))
    box('ENV_shelter_roof',(-5.2,-9,2.7),(2.3,6.6,.22),(.25,.63,.68))
    box('ENV_shelter_glass',(-4.25,-9,1.45),(.07,5.8,2.3),(.32,.47,.51))
    box('ENV_shelter_bench',(-4.75,-9,.55),(.5,4,.16),(.48,.41,.32))
    box('ENV_shelter_clock',(-5.4,-6.1,2.3),(.65,.18,.3),(.1,.2,.22))
    # Site has two actual line segments with a return pulley, from observed frame.
    box('ENV_gate', (1.8,4,1.7),(5.6,.16,3.4),(.29,.36,.42))
    box('ENV_gate_opening_back', (6.05,6.5,1.7),(2.4,.2,3.4),(.11,.15,.19))
    box('ENV_gate_opening_floor', (6.05,5.2,.04),(2.4,2.4,.08),(.22,.25,.27))
    for x in (-1,3,7.5):
        box('ENV_gate_post',(x,4,1.9),(.22,.32,3.8),(.2,.25,.3))
    box('ENV_gate_rail',(3.2,4,3.45),(9,.35,.17),(.5,.52,.54))
    box('PRP_limit',(7.6,3.6,.9),(.35,.5,1.8),(.68,.58,.27))
    box('PRP_winch_plinth',(-4,0,.25),(2.2,1.5,.5),(.42,.43,.41))
    rod('PRP_winch_drum',(-4.5,0,.95),(-3.5,0,.95),.49,(.46,.49,.52))
    rod('PRP_winch_motor',(-5.2,0,.82),(-4.7,0,.82),.3,(.3,.36,.39))
    box('PRP_return_base',(7,-3,.2),(1.1,1.1,.4),(.4,.42,.43))
    rod('PRP_return_pulley',(7,-3.18,.7),(7,-2.82,.7),.49,(.46,.49,.5))
    rod('PRP_cable_out',(-3.5,-.15,.8),(7,-3.18,.7),.045,(.7,.74,.76))
    rod('PRP_cable_return',(7,-2.82,.7),(3,3.8,1.2),.045,(.7,.74,.76))
    sphere('PRP_gate_lug',(3,3.8,1.2),.17,(.56,.6,.63))
    box('PRP_control',(-5.4,3,1.12),(.6,.42,2.24),(.64,.67,.65))
    sphere('PRP_stop_button',(-5.4,2.75,1.7),.075,(.8,.08,.04))
    box('PRP_worklight',(-6,3.1,2.8),(.55,.22,.4),(1,.8,.35))
    rod('PRP_light_stand',(-6,3.1,0),(-6,3.1,2.7),.035,(.55,.54,.45))
    for x in (-4.35,-3.95):
        rod('FIG_worker_leg',(x,3,.08),(x,3,.78),.11,(.08,.15,.25))
    box('FIG_worker_torso',(-4.15,3,1.06),(.6,.32,.67),(.09,.2,.34))
    box('FIG_worker_reflector',(-4.15,2.82,1.12),(.6,.025,.1),(.75,.76,.65))
    sphere('FIG_worker_head',(-4.15,3,1.57),.16,(.65,.5,.37))
    sphere('FIG_worker_helmet',(-4.15,3,1.71),.19,(.95,.65,.08))
    rod('FIG_worker_arm',(-4.48,3,1.3),(-4.62,2.97,.83),.085,(.08,.2,.34))
    rod('FIG_worker_arm',(-3.82,3,1.3),(-3.65,2.97,.83),.085,(.08,.2,.34))
    # Generic neighborhood masses: fixed seed; no source-grounded city claim.
    rng=random.Random(27)
    for y in (5,55,90,130,175):
        for x in (-65,-42,28,57,92):
            h=rng.choice((15,21,27,36,45))
            building(f'city_{x}_{y}',x,y,14,16,h,(.28+rng.random()*.12,.34,.4))
    for y in range(-65,135,18):
        for x in (-22.5,-5.7):
            if x>-10 and -17<y<10:
                continue
            rod('ENV_streetlight',(x,y,0),(x,y,6),.055,(.47,.52,.55))
            box('ENV_lamp',(x,y,6.1),(.5,.7,.16),(.88,.9,.7))
    for i,(x,y) in enumerate(((-17,40),(-11,70),(-17,-5),(-11,-65))):
        car=box('PRP_car_'+str(i),(x,y,.8),(1.9,4.6,1.4),(.35,.42,.45))
        for f in (1,FRAMES):
            car.location.y=y+(f-1)/FPS*(2 if i%2 else -2)
            car.keyframe_insert(data_path='location',frame=f)
    bpy.ops.object.camera_add()
    cam=bpy.context.object
    cam.name='CAM_MC00_continuous'
    cam.data.lens=28
    cam.data.sensor_width=36
    cam.data.clip_start=.03
    cam.data.clip_end=1000
    cam.rotation_mode='QUATERNION'
    sc.camera=cam
    samples=[]
    previous_q=None
    for f in range(1,FRAMES+1):
        t=(f-1)/FPS
        pos=smooth(NODES,t,1)
        direction=smooth(LOOKS,t,1).normalized()
        aim=pos+direction*40
        q=direction.to_track_quat('-Z','Y')
        if previous_q is not None and q.dot(previous_q)<0:
            q.negate()
        cam.location=pos
        cam.rotation_quaternion=q
        cam.keyframe_insert(data_path='location',frame=f)
        cam.keyframe_insert(data_path='rotation_quaternion',frame=f)
        previous_q=q.copy()
        samples.append({'frame':f,'seconds':t,'position_m':list(pos),'aim_m':list(aim),'quaternion':list(q)})
    # Per-frame samples are continuous baked motion; linear interpolation between them.
    for obj in sc.objects:
        if obj.animation_data and obj.animation_data.action:
            for layer in obj.animation_data.action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for fc in bag.fcurves:
                            for key in fc.keyframe_points:
                                key.interpolation='LINEAR'
    marker=sc.timeline_markers.new('MC00_ONLY_NO_INTERNAL_CUT',frame=1)
    marker.camera=cam
    OUT.mkdir(exist_ok=True)
    (OUT/'camera-samples-v2.json').write_text(json.dumps({'fps':FPS,'seconds':SECONDS,'nodes':NODES,'samples':samples},indent=2))
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MC00-city-v2.blend'))
    return sc,cam


def render_stills(sc,cam):
    dest=OUT/'views-v2'
    dest.mkdir(exist_ok=True)
    sc.render.image_settings.file_format='PNG'
    for f in (1,25,61,121,193,265,337,385,433,480):
        sc.frame_set(f)
        sc.render.filepath=str(dest/f'camera-{f:04d}.png')
        bpy.ops.render.render(write_still=True)
    # Separate inspection camera; never part of the continuous camera timeline.
    bpy.ops.object.camera_add(location=(70,-100,110))
    overview=bpy.context.object
    overview.name='CAM_INSPECTION_ONLY'
    overview.rotation_euler=(Vector((-5,8,0))-overview.location).to_track_quat('-Z','Y').to_euler()
    overview.data.type='ORTHO'
    overview.data.ortho_scale=145
    sc.camera=overview
    sc.timeline_markers[0].camera=None
    sc.render.filepath=str(dest/'city-overview.png')
    bpy.ops.render.render(write_still=True)
    sc.camera=cam
    sc.timeline_markers[0].camera=cam


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--stills',action='store_true')
    parser.add_argument('--animation',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    sc,cam=make_scene()
    if args.stills:
        render_stills(sc,cam)
    if args.animation:
        sc.render.image_settings.file_format='FFMPEG'
        sc.render.ffmpeg.format='MPEG4'
        sc.render.ffmpeg.codec='H264'
        sc.render.ffmpeg.constant_rate_factor='MEDIUM'
        sc.render.filepath=str(OUT/'MC00-previs-v2.mp4')
        bpy.ops.render.render(animation=True)
    print(json.dumps({'ok':True,'blender':bpy.app.version_string,'frames':FRAMES,'fps':FPS,'purpose':'local spatial previs only'}))
