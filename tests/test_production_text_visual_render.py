"""Opt-in exact local production comparisons; no paid/model generation."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from ai_video.production.commercial_graphics import GraphicTreatment, GraphicRole, GraphicAnimation
from ai_video.production.models import CaptionSegment, CaptionWord
from ai_video.production.subtitle_ass import SubtitleDesign, SubtitleLineStyle, libass_version
from ai_video.production.text_design import TextDesign, TextVisualNode, TextRun, MotionPose
from text_visual_pilot_support import REPO, FFMPEG, render_case, subset_font


pytestmark = pytest.mark.skipif(os.environ.get("AI_VIDEO_TEXT_PILOT") != "1", reason="explicit real local media pilot")


def _fonts(text):
    fonts = Path("/usr/share/fonts/opentype/noto")
    return (
        subset_font(fonts/"NotoSansCJK-Regular.ttc",text,family="Noto Sans CJK SC",face=2),
        subset_font(fonts/"NotoSerifCJK-Regular.ttc",text,family="Noto Serif CJK SC",face=2),
    )


def _node(identity, text, font, size, x, y, w, h, *, color="#302B20", motion=(), tracking=0, purpose=None):
    return TextVisualNode(node_id=identity,purpose=purpose or identity,x_px=x,y_px=y,width_px=w,height_px=h,
        runs=(TextRun(text=text,font_family=font.family,font_size_px=size,color=color,tracking_px=tracking),),motion=motion)


def _graphic(design,frames, *, x=70,y=70,width=860):
    return GraphicTreatment(graphic_id="typography",role=GraphicRole.HEADLINE,text=design.text,shot_id="sample",
        start_frame_offset=0,duration_frames=frames,x_milli=x,y_milli=y,width_milli=width,
        font_size_px=48,text_color="#FFFFFF",z_index=10,text_design=design)


def _reveal(delay=0):
    if delay:
        return (MotionPose(frame=0,opacity_milli=0,reveal_right_milli=1000),
                MotionPose(frame=delay,opacity_milli=0,reveal_right_milli=1000),
                MotionPose(frame=delay+24))
    return (MotionPose(frame=0,opacity_milli=0,reveal_right_milli=1000),MotionPose(frame=24))


def _advert_design():
    text="LUMA  /  EDITION 01轻，一点。THE ART OF EVERYDAY把光，带回日常¥29950mL概念设计演示 · 非真实商品或售价"
    sans,serif=_fonts(text)
    nodes=(
        _node("brand","LUMA  /  EDITION 01",sans,22,0,0,660,50,tracking=3,motion=_reveal()),
        _node("headline","轻，一点。",serif,92,0,130,660,150,motion=_reveal(12),purpose="primary; quiet editorial headline in negative space"),
        _node("eyebrow","THE ART OF EVERYDAY",sans,16,0,330,640,40,tracking=4,motion=_reveal(24)),
        _node("promise","把光，带回日常",sans,30,0,392,650,65,motion=_reveal(30)),
        TextVisualNode(node_id="rule",purpose="align supporting price block with the reading axis",x_px=0,y_px=850,
            width_px=600,height_px=3,path="M0 1 L600 1",fill="none",stroke="#8C774E",stroke_width_px=1,motion=_reveal(48)),
        TextVisualNode(node_id="price",purpose="secondary information with subordinate unit",x_px=0,y_px=900,width_px=650,height_px=130,
            runs=(TextRun(text="¥299",font_family=serif.family,font_size_px=84,color="#302B20"),
                  TextRun(text="  50mL",font_family=sans.family,font_size_px=22,color="#51452F")),motion=_reveal(54)),
        _node("disclaimer","概念设计演示 · 非真实商品或售价",sans,17,0,1080,660,50,color="#5C574B",motion=_reveal(60)),
    )
    return TextDesign(intent="An imaginary premium lifestyle brand; fluid image stays full bleed, hierarchy grows from quiet editorial typography.",
        hierarchy="Brand first, large serif promise second, price later; no solid card; copied facts are marked fictional.",
        reference_width_px=660,reference_height_px=1160,fonts=(sans,serif),nodes=nodes)


def _title_design():
    sans,serif=_fonts("余 温A LITTLE LONGER序章 · 此刻，留下")
    nodes=(
        _node("chapter","序章 · 此刻，留下",sans,17,12,0,570,35,color="#D8CCB5",tracking=3,
              motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=18))),
        _node("title","余 温",serif,100,0,55,580,135,color="#F6EEDB",tracking=16,
              motion=(MotionPose(frame=0,opacity_milli=0,blur_milli_px=7000,reveal_right_milli=1000),
                      MotionPose(frame=42,opacity_milli=1000),MotionPose(frame=160,opacity_milli=1000),
                      MotionPose(frame=185,opacity_milli=0,blur_milli_px=3000))),
        _node("english","A LITTLE LONGER",sans,15,14,204,570,34,color="#DBC9AB",tracking=6,
              motion=(MotionPose(frame=0,opacity_milli=0),MotionPose(frame=24,opacity_milli=0),MotionPose(frame=58))),
    )
    return TextDesign(intent="Film title emerges gently over the empty sofa, preserving both faces and the physical invitation.",
        hierarchy="Chinese serif title; small restrained chapter and English line; the room's blue/amber light remains dominant.",
        reference_width_px=600,reference_height_px=250,fonts=(sans,serif),nodes=nodes)


@pytest.mark.parametrize("case",["dialogue","advert","title","word"])
def test_real_production_text_comparison(case):
    output=Path(os.environ["AI_VIDEO_TEXT_PILOT_ROOT"]).resolve()/case
    if case in {"dialogue","word"}:
        source=REPO/"artifacts/qingyan-miao-ad-20260826-v8/runtime/t8_portrait_ad/02_elder_dialogue_repair.mp4"
        texts=("姑娘，喷的什么？\nWhat are you spraying?", "青颜抑汗净味喷雾，清爽舒适。\nQingyan spray. Fresh and comfortable.", "难怪这么自在。\nNo wonder you look so at ease.")
        intervals=((.08,1.58),(1.70,4.65),(4.78,6.15))
        segments=tuple(CaptionSegment(segment_id=f"line-{i}",text=t,start_sample=round(a*48000),end_sample=round(b*48000))
                       for i,(t,(a,b)) in enumerate(zip(texts,intervals)))
        if case == "word":
            partitions=(("姑娘，","喷的","什么？"),("青颜","抑汗净味","喷雾，","清爽舒适。"),("难怪","这么","自在。"))
            boundaries=((.08,.60,1.05,1.58),(1.70,2.16,3.15,3.65,4.65),(4.78,5.14,5.55,6.15))
            segments=tuple(CaptionSegment(segment_id=f"line-{i}",text="".join(parts),start_sample=round(times[0]*48000),
                end_sample=round(times[-1]*48000),words=tuple(CaptionWord(text=t,start_sample=round(a*48000),end_sample=round(b*48000))
                for t,a,b in zip(parts,times,times[1:]))) for i,(parts,times) in enumerate(zip(partitions,boundaries)))
        sans,_=_fonts("".join(texts))
        new=SubtitleDesign(libass_version=libass_version(),fonts=(sans,),font_family=sans.family,font_size_px=46,
            outline_px=1.4,shadow_px=0.5,margin_vertical_px=100,margin_left_px=35,margin_right_px=35,
            word_highlight=case == "word",
            line_styles=(SubtitleLineStyle(line_index=1,font_size_px=30,primary_color="#E0DDD6",outline_px=1.0),) if case == "dialogue" else (),
            intent="Dialogue follows turn-taking, never touches faces; Chinese carries meaning and English stays subordinate.").model_dump(mode="json")
        old=dict(schema_version="1",font_family="sans-serif",font_size_px=34,bottom_margin_px=100,max_width_milli=910,
                 outline_width_px=2,text_color="#FFFFFF",outline_color="#101820")
        kwargs=dict(source=source,profile=dict(width=768,height=1344,fps=24),duration_seconds=7,segments=segments,preserve_audio=True)
        reports=[render_case(output/"before",style=old,**kwargs),render_case(output/"after",style=new,**kwargs)]
    else:
        d=_advert_design() if case == "advert" else _title_design()
        seconds=6 if case == "advert" else 8
        args={} if case == "advert" else dict(x=65,y=470,width=440)
        new=_graphic(d,seconds*24,**args)
        old=GraphicTreatment.model_validate({**new.model_dump(),"text_design":None,"font_size_px":36,
            "text_color":"#302B20" if case == "advert" else "#F6EEDB","entrance":GraphicAnimation.FADE,"exit":GraphicAnimation.FADE})
        source=REPO/("artifacts/qingyan-miao-ad-20260826-v8/assets/04-golden-fluid.png" if case == "advert"
                     else "runs/director-stay-a-moment-20261021-001/stay-a-moment-8s.mp4")
        if case == "advert":
            output.mkdir(parents=True, exist_ok=True)
            moving=output/"shared-source.mp4"
            subprocess.run([str(FFMPEG),"-v","error","-loop","1","-i",str(source),
                "-vf","scale=1536:-2,zoompan=z='1+on*0.0003':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=144:s=768x1344:fps=24",
                "-t","6","-an","-c:v","libx264","-pix_fmt","yuv420p",str(moving)],check=True)
            source=moving
        kwargs=dict(source=source,profile=dict(width=768,height=1344,fps=24) if case == "advert" else dict(width=1344,height=768,fps=24),
                    duration_seconds=seconds)
        reports=[render_case(output/"before",graphics=(old,),**kwargs),render_case(output/"after",graphics=(new,),**kwargs)]
    (output/"comparison.json").write_text(json.dumps(reports,indent=2))
    assert reports[0]["source_sha256"]==reports[1]["source_sha256"]
    assert reports[0]["output_sha256"]!=reports[1]["output_sha256"]
