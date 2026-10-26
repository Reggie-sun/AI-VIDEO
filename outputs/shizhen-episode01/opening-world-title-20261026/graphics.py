"""The city continues above a withdrawn image field; editorial, not diegetic lettering."""
from ai_video.production.text_design import TextDesign,TextVisualNode,TextRun,MotionPose
from ai_video.production.commercial_graphics import GraphicTreatment,GraphicRole

def graphics(font):
    # A single editorial field change after the passing taxi; no fake tracked obstacle.
    nodes=[TextVisualNode(node_id='withdrawn-field',purpose='画面退出下部，城市仍在上部正常运行；这是剪辑平面，不是画内物理变化',x_px=0,y_px=0,width_px=1920,height_px=1080,path='M0 750 H1920 V1080 H0 Z',fill='#070A0B',motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=71,opacity_milli=0),MotionPose(frame=72),MotionPose(frame=143)))]
    nodes.append(TextVisualNode(node_id='remembered-title',purpose='完整汉字跨越活动影像与撤去的影像；观众记忆成为唯一留存，字不扮演场景中的灵异实体',x_px=320,y_px=575,width_px=880,height_px=370,runs=(TextRun(text='失帧',font_family=font.family,font_size_px=266,font_weight=400,tracking_px=38,color='#DAD8CF'),),motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=71,opacity_milli=0),MotionPose(frame=72),MotionPose(frame=143))))
    d=TextDesign(intent='人群走开而世界照常运行；一次影像平面撤退留下标题。不是汉字随机错位、字形开洞或新的灵异事件。',hierarchy='先看完车流和空下的过街位置，再读完整片名；标题不压人物反应或对白',reference_width_px=1920,reference_height_px=1080,fonts=(font,),nodes=tuple(nodes))
    return (GraphicTreatment(graphic_id='world-remembers-title',role=GraphicRole.HEADLINE,text=d.text,shot_id='WORLD-OUT',start_frame_offset=0,duration_frames=144,x_milli=0,y_milli=0,width_milli=1000,font_size_px=266,font_weight=400,text_color='#DAD8CF',z_index=100,text_design=d),)
