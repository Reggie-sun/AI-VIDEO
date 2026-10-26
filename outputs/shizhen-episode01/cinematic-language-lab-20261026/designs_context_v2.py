"""Context-only repair: keep people out of the title plate and soften cut-paper corners."""
from fontTools.svgLib.path import parse_path
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.areaPen import AreaPen
from ai_video.production.text_design import MotionPose
from designs_refined import context_title as first_title,portrait_path
from designs import typeface,RECT


def smooth_profile(reverse=False):
    r=RecordingPen();parse_path(portrait_path(),r)
    points=[tuple(coords[0]) for op,coords in r.value if op in {'moveTo','lineTo'}]
    commands=[]
    for i,p in enumerate(points):
        a=points[i-1];b=points[(i+1)%len(points)]
        before=tuple(p[k]*.8+a[k]*.2 for k in (0,1))
        after=tuple(p[k]*.8+b[k]*.2 for k in (0,1))
        commands.append(('M' if i==0 else 'L')+f'{before[0]:.2f} {before[1]:.2f}')
        commands.append(f'Q{p[0]:.2f} {p[1]:.2f} {after[0]:.2f} {after[1]:.2f}')
    raw=' '.join(commands)+' Z'
    gs=typeface().getGlyphSet();a=AreaPen(gs);parse_path(raw,a)
    pen=SVGPathPen(gs);parse_path(raw,ReverseContourPen(pen) if reverse and a.value>0 else pen)
    return pen.getCommands()


def context_title(font):
    g=first_title(font);nodes=[]
    for n in g.text_design.nodes:
        if n.node_id=='portrait-exposure':
            n=n.model_copy(update={'path':RECT+' '+smooth_profile(True),'fill':'#D6D8D0EF',
                'motion':(MotionPose(frame=0),MotionPose(frame=83))})
        nodes.append(n)
    return g.model_copy(update={'text_design':g.text_design.model_copy(update={'nodes':tuple(nodes)})})
