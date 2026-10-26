"""Source-led title: missing position stays visible through Chinese letterforms."""
from pathlib import Path
import importlib.util
from fontTools.ttLib import TTFont
from ai_video.production.text_design import TextDesign, TextVisualNode, TextRun, MotionPose
from ai_video.production.commercial_graphics import GraphicTreatment, GraphicRole
ROOT=Path.cwd()
spec=importlib.util.spec_from_file_location('existing_letter_aperture',ROOT/'outputs/shizhen-episode01/cinematic-language-lab-20261026/designs.py')
lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
FONT='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
f=TTFont(FONT,fontNumber=2)
lab.typeface=lambda:f
PARTS=[('失',165,648,490),('帧',640,927,340)]

def graphics(font):
    # Only the empty side withdraws; survivor, source AI label and clock remain visible.
    mask='M0 88 H1060 V1080 H0 Z '+' '.join(lab.glyph(*p,reverse=True) for p in PARTS)
    nodes=[TextVisualNode(node_id='retained-empty-place',purpose='后期左侧曝光平面退出，空位的活动影像留在字内；不表示第二次人物或现实删除',x_px=0,y_px=0,width_px=1920,height_px=1080,path=mask,fill='#080D10',motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=9,opacity_milli=0),MotionPose(frame=31,opacity_milli=940),MotionPose(frame=71,opacity_milli=940)))]
    ascent=f['hhea'].ascent;descent=-f['hhea'].descent;upm=f['head'].unitsPerEm
    for char,x,baseline,size in PARTS:
        offset=size*((ascent/upm)+(1-(ascent+descent)/upm)/2)
        y=round(baseline-offset)
        nodes.append(TextVisualNode(node_id='title-'+char,purpose='原生中文完整字形提供轻微银盐密度，保留字内雨和路面反射，无随机错位或缺笔',x_px=x,y_px=y,width_px=size+30,height_px=size+70,line_height_milli=1000,runs=(TextRun(text=char,font_family=font.family,font_size_px=size,font_weight=700,color='#D8D8CF'),),motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=17,opacity_milli=0),MotionPose(frame=31,opacity_milli=240),MotionPose(frame=71,opacity_milli=240))))
    d=TextDesign(intent='观众知道这里少了一个人：片名从该空位的活动雨夜中显现，右侧幸存者仍无察觉。只做一次后期曝光分离。',hierarchy='先空位，后完整失帧；失更大、帧下沉，留出人与字之间的距离；无翌夜或S01',reference_width_px=1920,reference_height_px=1080,fonts=(font,),nodes=tuple(nodes))
    return (GraphicTreatment(graphic_id='empty-place-title',role=GraphicRole.HEADLINE,text=d.text,shot_id='CO-TAIL',start_frame_offset=0,duration_frames=72,x_milli=0,y_milli=0,width_milli=1000,font_size_px=490,font_weight=700,text_color='#D8D8CF',z_index=100,text_design=d),)
