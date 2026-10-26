"""One late film title in the space the scene no longer acknowledges."""
from pathlib import Path
import base64
import hashlib
import io
from fontTools import subset
from fontTools.ttLib import TTFont
from ai_video.production.text_fonts import EmbeddedFont
from ai_video.production.text_design import TextDesign,TextVisualNode,TextRun,MotionPose
from ai_video.production.commercial_graphics import GraphicTreatment,GraphicRole


def font():
    f=TTFont('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',fontNumber=2,recalcTimestamp=False)
    opts=subset.Options();opts.name_IDs=[0,1,2,3,4,5,6,13,14,16,17]
    s=subset.Subsetter(options=opts);s.populate(text='失帧动态预演素材未统一');s.subset(f)
    b=io.BytesIO();f.save(b);raw=b.getvalue()
    return EmbeddedFont(family='Noto Serif CJK SC',sha256=hashlib.sha256(raw).hexdigest(),
        data_base64=base64.b64encode(raw).decode(),license='Noto CJK / SIL OFL 1.1; system distribution subset')


def graphics():
    face=font()
    # The native closeup begins inside this9s source window. Wait until it is
    # established; the title must never explain the disappearance in advance.
    nodes=[TextVisualNode(node_id='glass-tone',purpose='Local exposure support for title, never a person matte',
        x_px=0,y_px=0,width_px=1920,height_px=1080,
        path='M0 0 H850 V1080 H0 Z',fill='#080F1678',
        motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=131,opacity_milli=0),
                MotionPose(frame=147),MotionPose(frame=215)))]
    for char,x,y in [('失',144,363),('帧',380,423)]:
        nodes.append(TextVisualNode(node_id='title-'+char,
            purpose='Original film title inhabits the negative image field after the event; nondiegetic typography',
            x_px=x,y_px=y,width_px=280,height_px=280,
            runs=(TextRun(text=char,font_family=face.family,font_size_px=184,font_weight=400,color='#E4DFD2'),),
            motion=(MotionPose(frame=0,opacity_milli=0,blur_milli_px=4500),
                    MotionPose(frame=139,opacity_milli=0,blur_milli_px=4500),
                    MotionPose(frame=155),MotionPose(frame=215))))
    d=TextDesign(intent='A relation was removed; the last title occupies compositional negative space, not a supernatural object',
        hierarchy='Event and sustained absence first; face and glass next; original Chinese title last',
        reference_width_px=1920,reference_height_px=1080,fonts=(face,),nodes=tuple(nodes))
    result=[GraphicTreatment(graphic_id='late-title-in-glass',role=GraphicRole.HEADLINE,text=d.text,
        shot_id='CO-A3',start_frame_offset=0,duration_frames=216,x_milli=0,y_milli=0,width_milli=1000,
        font_size_px=184,font_weight=400,text_color='#E4DFD2',z_index=100,text_design=d)]
    # Honest material status remains in the film, including when copied away
    # from its review page. It is secondary to the cinematic frame.
    for shot,n in [('CITY',126),('ROAD',66),('CO-A1',184),('CO-A2',96),('CO-A3',216)]:
        label=TextVisualNode(node_id='previs-status',purpose='Disclose material status independently of the review page',
            x_px=0,y_px=0,width_px=470,height_px=36,
            runs=(TextRun(text='动态预演  素材未统一',font_family=face.family,font_size_px=20,font_weight=400,color='#C5CFD8'),))
        ld=TextDesign(intent='Development status, not narrative exposition',hierarchy='Small secondary source status',
            reference_width_px=470,reference_height_px=36,fonts=(face,),nodes=(label,))
        result.append(GraphicTreatment(graphic_id='previs-'+shot,role=GraphicRole.HEADLINE,text=ld.text,shot_id=shot,
            start_frame_offset=0,duration_frames=n,x_milli=750,y_milli=30,width_milli=245,
            font_size_px=20,font_weight=400,text_color='#C5CFD8',z_index=110,text_design=ld))
    return tuple(result)
