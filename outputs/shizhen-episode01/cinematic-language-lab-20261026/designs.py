"""Three source-specific compositions using existing typed vector/motion primitives."""
from functools import lru_cache
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.areaPen import AreaPen
from ai_video.production.text_design import TextDesign, TextVisualNode, TextRun, MotionPose
from ai_video.production.commercial_graphics import GraphicTreatment, GraphicRole

W, H, END = 1920, 1080, 216
INK, PAPER, CHALK = '#0A1115', '#D6D8D0', '#DAD9CF'
RECT = 'M0 0 H1920 V1080 H0 Z'


@lru_cache
def typeface():
    return TTFont('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', fontNumber=2)


def glyph(text, x, baseline, size, *, reverse=False):
    f = typeface()
    gs = f.getGlyphSet()
    name = f.getBestCmap()[ord(text)]
    scale = size / f['head'].unitsPerEm
    matrix = (scale, 0, 0, -scale, x, baseline)
    area = AreaPen(gs)
    gs[name].draw(TransformPen(area, matrix))
    pen = SVGPathPen(gs)
    # An outer clockwise rectangle plus counterclockwise glyphs is a genuine
    # video aperture. Inner counters retain their correct opposite winding.
    target = ReverseContourPen(pen) if reverse and area.value > 0 else pen
    gs[name].draw(TransformPen(target, matrix))
    return pen.getCommands()


def holes(parts):
    return RECT + ' ' + ' '.join(glyph(*p, reverse=True) for p in parts)


def poses(keys, start, frames):
    """Slice one authored motion trajectory at the resolved Shot boundary."""
    keys = sorted(keys)
    fields = {'opacity_milli', 'translate_x_px', 'translate_y_px',
              'reveal_top_milli', 'reveal_right_milli', 'reveal_bottom_milli', 'reveal_left_milli'}
    defaults = {x: (1000 if x == 'opacity_milli' else 0) for x in fields}
    states = []
    current = defaults.copy()
    for t, update in keys:
        current = {**current, **update}
        states.append((t, current.copy()))
    def at(t):
        if t <= states[0][0]:
            return states[0][1]
        for (a, va), (b, vb) in zip(states, states[1:]):
            if a <= t <= b:
                return {k: round(va[k] + (vb[k] - va[k]) * (t-a)/(b-a)) for k in fields}
        return states[-1][1]
    times = sorted({start, start+frames-1, *(t for t,_ in keys if start < t < start+frames-1)})
    return tuple(MotionPose(frame=t-start, **at(t), easing=(333,333,667,667)) for t in times)


def make_nodes(variant, start, frames, font):
    nodes = []
    def vector(identity, purpose, path, fill, keys=None, stroke='none', sw=0, box=(0,0,W,H)):
        x,y,w,h = box
        nodes.append(TextVisualNode(node_id=identity, purpose=purpose, x_px=x,y_px=y,
            width_px=w,height_px=h,path=path,fill=fill,stroke=stroke,stroke_width_px=sw,
            motion=poses(keys or [(0,{})],start,frames)))
    def label(identity, text, x,y,size, keys, color=CHALK, width=500):
        nodes.append(TextVisualNode(node_id=identity,purpose='A complete readable anchor within an experimental image',
            x_px=x,y_px=y,width_px=width,height_px=round(size*1.5),
            runs=(TextRun(text=text,font_family=font.family,font_size_px=size,font_weight=700,color=color),),
            motion=poses(keys,start,frames)))

    if variant == 'A':
        # Cropped shapes are deliberate: a giant 失 is outside a neat baseline,
        # while 帧 is lower and smaller. Real motion lives inside the strokes.
        parts=[('失',-108,970,1100),('帧',1100,1050,710)]
        vector('letter-aperture','Rain and the occluding truck remain moving inside oversized broken type',
            holes(parts),INK,[(0,{'opacity_milli':0}),(18,{'opacity_milli':1000}),
                             (145,{'opacity_milli':1000}),(169,{'opacity_milli':1000})])
        vector('etched-boundary','A sparse edge records the letter boundary without a glow',
            ' '.join(glyph(*p) for p in parts),'none',[(0,{'opacity_milli':0}),(24,{'opacity_milli':450})],CHALK,1)
        vector('missing-column','One column of visual time is absent, no repeated digital flicker',
            'M878 0 H934 V1080 H878 Z',INK,
            [(0,{'opacity_milli':0}),(46,{'opacity_milli':0}),(47,{'opacity_milli':1000})])
        label('readable-shi','失',1320,158,108,[(0,{'opacity_milli':0}),(76,{'opacity_milli':0}),
             (89,{'opacity_milli':1000}),(154,{'opacity_milli':1000})],width=180)
        label('readable-zhen','帧',1490,280,148,[(0,{'opacity_milli':0}),(86,{'opacity_milli':0}),
             (99,{'opacity_milli':1000}),(154,{'opacity_milli':1000})],width=230)

    elif variant == 'B':
        vector('retained-street','Keep the physical world legible, with a quiet printed-black density',
            RECT,'#0A111560',[(0,{'opacity_milli':0}),(40,{'opacity_milli':1000})])
        # A physical letter fragment follows the truck direction once; the upper
        # fragment stays put. This is a missing piece, not a glitch oscillator.
        p=glyph('失',0,420,460)
        vector('fixed-half','One half of the remembered title keeps its place',p,CHALK,
            [(0,{'opacity_milli':0,'reveal_bottom_milli':490}),(20,{'opacity_milli':1000}),
             (143,{'opacity_milli':1000}),(162,{'opacity_milli':0})],box=(140,105,480,480))
        vector('displaced-half','A single displaced lower half uses the same left-to-right screen direction as the truck',
            p,CHALK,[(0,{'opacity_milli':0,'reveal_top_milli':510}),
                     (20,{'opacity_milli':1000}),(65,{'translate_x_px':0}),
                     (104,{'translate_x_px':145}),(143,{'opacity_milli':1000}),
                     (162,{'opacity_milli':0})],box=(140,105,480,480))
        label('boundary-zhen','帧',1190,595,254,[(0,{'opacity_milli':0,'reveal_left_milli':1000}),
              (43,{'opacity_milli':0}),(67,{'opacity_milli':1000,'reveal_left_milli':0}),
              (143,{'opacity_milli':1000}),(162,{'opacity_milli':0})],width=400)
        vector('empty-place-rule','The line belongs to the empty left-hand position, not a decorative frame',
            'M690 875 H960 V878 H690 Z',CHALK,
            [(0,{'opacity_milli':0,'reveal_right_milli':1000}),(80,{'opacity_milli':0}),
             (110,{'opacity_milli':1000,'reveal_right_milli':0}),(156,{'opacity_milli':1000})])

    elif variant == 'C':
        # A deliberately abstract contour based on Gao's actual bag/coat/stance.
        # It is a title metaphor, never a claim that a ghost is visible in-scene.
        body=('M657 28 C610 25 574 68 575 118 C575 163 591 185 607 198 '
              'L594 230 C533 244 493 279 474 342 L453 555 L468 637 '
              'L484 666 L479 742 L517 759 L540 1030 L511 1066 '
              'L644 1066 L659 1017 L659 784 L678 784 L705 1026 '
              'L705 1066 L841 1066 L805 1021 L806 743 L841 683 '
              'L841 611 L861 543 L844 351 C835 282 789 246 725 228 '
              'L713 201 C743 176 757 149 752 109 C746 59 712 27 657 28 Z')
        # Reverse the explicit contour to make the body a hole in the pale field.
        from fontTools.svgLib.path import parse_path
        gs=typeface().getGlyphSet(); pen=SVGPathPen(gs); area=AreaPen(gs)
        parse_path(body, area)
        parse_path(body, ReverseContourPen(pen) if area.value > 0 else pen)
        vector('city-body','The missing ordinary worker becomes an aperture containing continuing city motion',
            RECT+' '+pen.getCommands(),PAPER,
            [(0,{'opacity_milli':0}),(28,{'opacity_milli':1000}),
             (152,{'opacity_milli':1000})])
        vector('body-border','An ink edge separates memory from the world without an electric outline',
            body,'none',[(0,{'opacity_milli':0}),(34,{'opacity_milli':550})],INK,1)
        label('body-shi','失',1060,358,236,[(0,{'opacity_milli':0,'reveal_right_milli':1000}),
             (44,{'opacity_milli':0}),(72,{'opacity_milli':1000,'reveal_right_milli':0})],INK,width=360)
        label('body-zhen','帧',1324,614,170,[(0,{'opacity_milli':0,'reveal_top_milli':1000}),
             (66,{'opacity_milli':0}),(95,{'opacity_milli':1000,'reveal_top_milli':0})],INK,width=300)
        vector('body-interval','A single broad missing slice refers to absence instead of a digital error effect',
            'M445 554 H864 V578 H445 Z',PAPER,
            [(0,{'opacity_milli':0}),(81,{'opacity_milli':0}),
             (82,{'opacity_milli':1000})])
    else:
        raise ValueError(variant)

    # Temporal transition has a different job: a material plane replaces the
    # title, leaving one slit of wet-city motion. No small corner label.
    field = PAPER if variant != 'C' else INK
    ink = INK if variant != 'C' else PAPER
    vector('night-plane','A new exposure crosses the image; a narrow strip keeps the city alive',
        RECT+' M0 522 V552 H1920 V522 Z',field,
        [(0,{'opacity_milli':0,'reveal_left_milli':1000}),
         (163,{'opacity_milli':0}),(164,{'opacity_milli':1000}),
         (187,{'reveal_left_milli':0}),(215,{'reveal_left_milli':0})])
    label('next-yi','翌',205,267,224,[(0,{'opacity_milli':0,'reveal_bottom_milli':1000}),
          (181,{'opacity_milli':0}),(194,{'opacity_milli':1000,'reveal_bottom_milli':0})],ink,width=340)
    label('next-ye','夜',1350,634,224,[(0,{'opacity_milli':0,'reveal_top_milli':1000}),
          (189,{'opacity_milli':0}),(202,{'opacity_milli':1000,'reveal_top_milli':0})],ink,width=340)
    return tuple(nodes)


def graphics(variant, embedded_font):
    out=[]
    for shot,start,n in [('CO-A2',0,96),('CO-A3',96,120)]:
        d=TextDesign(intent='Source-specific cinematic language study '+variant+'; abstract titles, no new supernatural rule',
            hierarchy='Image and absence first; complete readable title anchors; then a separate temporal exposure',
            reference_width_px=W,reference_height_px=H,fonts=(embedded_font,),
            nodes=make_nodes(variant,start,n,embedded_font))
        out.append(GraphicTreatment(graphic_id='language-'+variant+'-'+shot,role=GraphicRole.HEADLINE,
            text=d.text,shot_id=shot,start_frame_offset=0,duration_frames=n,x_milli=0,y_milli=0,
            width_milli=1000,font_size_px=236,font_weight=700,text_color=CHALK,z_index=100,text_design=d))
    return tuple(out)
