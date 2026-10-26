"""Image-led title: absent left field, then time on the next living scene."""
from ai_video.production.text_design import TextDesign,TextVisualNode,TextRun,MotionPose
from ai_video.production.commercial_graphics import GraphicTreatment,GraphicRole

def wrap(key,sid,n,nodes,fonts):
 d=TextDesign(intent='人物继续日常，观众记住缺席；文字不作为画内灵异实体',hierarchy='行动与对白先于片名；时间提示在新场景第一句之前结束',reference_width_px=1920,reference_height_px=1080,fonts=fonts,nodes=tuple(nodes))
 return GraphicTreatment(graphic_id=key,role=GraphicRole.HEADLINE,text=d.text,shot_id=sid,start_frame_offset=0,duration_frames=n,x_milli=0,y_milli=0,width_milli=1000,font_size_px=126,font_weight=400,text_color='#E7E0D2',z_index=100,text_design=d)
def graphics(font):
 nodes=[]
 # Same rain-glass negative field. No white portrait, moving matte or dark rectangle.
 for char,x,y,size in [('失',140,350,152),('帧',340,414,126)]:
  nodes.append(TextVisualNode(node_id='title-'+char,purpose='Absent left field carries the title while the person continues talking at right',x_px=x,y_px=y,width_px=230,height_px=220,runs=(TextRun(text=char,font_family=font.family,font_size_px=size,color='#E7E0D2'),),motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=49,opacity_milli=0),MotionPose(frame=61),MotionPose(frame=119))))
 title=wrap('name-in-unacknowledged-space','CO-A3',120,nodes,(font,))
 night=TextVisualNode(node_id='next-night',purpose='Time changes with the actual picture cut, outside faces and hands; leave before first S01 dialogue',x_px=735,y_px=100,width_px=360,height_px=145,runs=(TextRun(text='翌夜',font_family=font.family,font_size_px=72,tracking_px=15,color='#E7E0D2'),),motion=(MotionPose(frame=0),MotionPose(frame=30),MotionPose(frame=42,opacity_milli=0)))
 return (title,wrap('next-night-in-living-scene','S01',43,(night,),(font,)))
