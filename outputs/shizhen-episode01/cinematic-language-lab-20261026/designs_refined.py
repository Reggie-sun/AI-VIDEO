"""Refinement after actual review: a portrait, not a generic whole-body icon."""
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.areaPen import AreaPen
from fontTools.svgLib.path import parse_path
from ai_video.production.text_design import TextDesign,TextVisualNode,TextRun,MotionPose
from ai_video.production.commercial_graphics import GraphicTreatment,GraphicRole
from designs import make_nodes,poses,typeface,RECT,INK,PAPER


def portrait_path(reverse=False):
    # Artist-redrawn profile from CO-A1's actual 0.5s sample (1280x720).
    # It is a graphic portrait boundary, not a pixel matte or tracked subject.
    source=('M435 105 L435 96 L440 96 L440 89 L449 87 L450 80 '
            'L462 77 L467 73 L482 76 L489 75 L501 81 L510 88 '
            'L516 100 L518 116 L513 129 L511 139 L502 151 '
            'L494 158 L500 173 L516 178 L525 181 L544 190 '
            'L557 201 L568 224 L577 255 L581 292 L588 348 '
            'L600 405 L365 405 L376 335 L384 289 L384 246 '
            'L394 218 L408 196 L426 182 L446 171 L454 163 '
            'L450 151 L441 147 L438 140 L434 138 L437 133 '
            'L429 129 L429 124 L434 118 L434 112 Z')
    matrix=(3.85,0,0,3.85,-1348,-199)
    area=AreaPen(typeface().getGlyphSet());parse_path(source,TransformPen(area,matrix))
    pen=SVGPathPen(typeface().getGlyphSet())
    target=ReverseContourPen(pen) if reverse and area.value>0 else pen
    parse_path(source,TransformPen(target,matrix))
    return pen.getCommands()


def refined_nodes(start,frames,font):
    nodes=list(make_nodes('C',start,frames,font))
    # Replace the rejected pictogram-shaped boundary with the source-led profile.
    for i,n in enumerate(nodes):
        if n.node_id=='city-body':
            nodes[i]=n.model_copy(update={'path':RECT+' '+portrait_path(True),'fill':'#D6D8D0F7',
                'purpose':'A hand-redrawn source-led portrait carries the moving city; not a diegetic ghost'})
        elif n.node_id=='body-border':
            nodes[i]=n.model_copy(update={'path':portrait_path(),'stroke_width_px':1})
        elif n.node_id=='body-interval':
            nodes[i]=n.model_copy(update={'path':'M0 758 H1040 V775 H0 Z',
                'purpose':'One material cut across the remembered portrait, no repeated flicker'})
    return tuple(nodes)


def graphics(variant,font):
    assert variant=='C'
    out=[]
    for shot,start,n in [('CO-A2',0,96),('CO-A3',96,120)]:
        d=TextDesign(intent='A remembered ordinary worker is made of the city that continues without him',
            hierarchy='Portrait aperture, offset film title, then a different temporal plane',
            reference_width_px=1920,reference_height_px=1080,fonts=(font,),
            nodes=refined_nodes(start,n,font))
        out.append(GraphicTreatment(graphic_id='refined-portrait-'+shot,role=GraphicRole.HEADLINE,
            text=d.text,shot_id=shot,start_frame_offset=0,duration_frames=n,x_milli=0,y_milli=0,
            width_milli=1000,font_size_px=236,font_weight=700,text_color=PAPER,z_index=100,text_design=d))
    return tuple(out)


def context_title(font):
    def path(identity,purpose,value,fill,motion=()):
        return TextVisualNode(node_id=identity,purpose=purpose,x_px=0,y_px=0,width_px=1920,
            height_px=1080,path=value,fill=fill,motion=motion)
    # The full-context cut uses a photographic still as an expressly frozen
    # title plate. The original scene remains moving and its audio unchanged.
    nodes=[path('portrait-exposure','A source-led portrait aperture, not an independent black title card',
        RECT+' '+portrait_path(True),'#D6D8D0F7',
        (MotionPose(frame=0,opacity_milli=0),MotionPose(frame=8),MotionPose(frame=83))),
        path('remembered-cut','One erased interval belongs to the portrait',
        'M0 758 H1040 V775 H0 Z',PAPER,
        (MotionPose(frame=0,opacity_milli=0),MotionPose(frame=14,opacity_milli=0),MotionPose(frame=15),MotionPose(frame=83)))]
    for text,x,y,size in [('失',1045,350,236),('帧',1330,611,170)]:
        nodes.append(TextVisualNode(node_id='title-'+text,purpose='Legible title anchor with deliberately broken baseline',
            x_px=x,y_px=y,width_px=380,height_px=360,
            runs=(TextRun(text=text,font_family=font.family,font_size_px=size,font_weight=700,color=INK),),
            motion=(MotionPose(frame=0,opacity_milli=0,reveal_right_milli=1000),
                    MotionPose(frame=9,opacity_milli=0,reveal_right_milli=1000),
                    MotionPose(frame=20),MotionPose(frame=83))))
    nodes.append(path('next-exposure','An exposure change carries the next night; the city remains as a thin interval',
        RECT+' M0 522 V552 H1920 V522 Z',INK,
        (MotionPose(frame=0,opacity_milli=0,reveal_left_milli=1000),
         MotionPose(frame=40,opacity_milli=0,reveal_left_milli=1000),
         MotionPose(frame=41,reveal_left_milli=1000),MotionPose(frame=52),MotionPose(frame=83))))
    for text,x,y,delay in [('翌',205,267,47),('夜',1350,634,51)]:
        nodes.append(TextVisualNode(node_id='next-'+text,purpose='Temporal separation occupies the frame, not a corner footnote',
            x_px=x,y_px=y,width_px=340,height_px=336,
            runs=(TextRun(text=text,font_family=font.family,font_size_px=224,font_weight=700,color=PAPER),),
            motion=(MotionPose(frame=0,opacity_milli=0,reveal_bottom_milli=1000),
                MotionPose(frame=delay,opacity_milli=0,reveal_bottom_milli=1000),
                MotionPose(frame=delay+8),MotionPose(frame=83))))
    d=TextDesign(intent='The ordinary answer becomes a remembered portrait, then the next-night exposure leads into original S01',
        hierarchy='Portrait and offset film title first; temporal field second, with at least one second of full legibility',
        reference_width_px=1920,reference_height_px=1080,fonts=(font,),nodes=tuple(nodes))
    return GraphicTreatment(graphic_id='portrait-title-in-context',role=GraphicRole.HEADLINE,text=d.text,
        shot_id='TITLE',start_frame_offset=0,duration_frames=84,x_milli=0,y_milli=0,width_milli=1000,
        font_size_px=236,font_weight=700,text_color=PAPER,z_index=100,text_design=d)
