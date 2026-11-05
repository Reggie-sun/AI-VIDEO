#!/usr/bin/env python3
"""Root's observed tail layers. Analysis only, S0144–S0153 sole-writer handoff."""
import copy
import json
import sys
from pathlib import Path


def main(root):
    root = Path(root)
    for number in range(144,154):
        p = root / f"shots/shot_{number:04d}.json"
        s = json.loads(p.read_text()); a,b=s["start_frame"],s["end_frame"]; sid=s["shot_id"]
        backup=root/f"work/root_review/before_{sid}.json"
        if not backup.exists(): backup.write_bytes(p.read_bytes())
        template=copy.deepcopy(s["elements"][0]); elements=[]

        def add(kind, desc, box, z, text=None, keys=(), start=None, end=None, height=None):
            first=max(a,a if start is None else start);last=min(b,b if end is None else end)
            e=copy.deepcopy(template);x,y,w,h=box
            e.update(element_id=f"{sid}-E{len(elements)+1:02d}",shot_id=sid,type=kind,description=desc,
                     start_frame=first,end_frame=last,bounding_box=dict(x=x/1920,y=y/1080,w=w/1920,h=h/1080,space="frame_norm_top_left"),z_index=z,
                     appearance=dict(color_hex=None,opacity=None,blend_mode="normal",details=desc),
                     motion=dict(path=desc,easing="step/typewriter for text; observed continuous drift for source cloth/hair; source curve unknown",
                                 entrance=f"observed at/about f{first}; +/-3f unless inherited at cut",exit=f"last observed within shot f{last}"),
                     keyframes=[dict(frame=first,state="first visible state"),*[dict(frame=f,**v) for f,v in keys if first<=f<=last],dict(frame=last,state="last within shot")],
                     effects=["shared print pass; layer split inferred"],reference_frames=sorted({first,last,*[f for f,v in keys if first<=f<=last]}),
                     confidence=.73,uncertainties=["bbox visual estimate, typical/max extent +/-0.02 normalized; not author source coordinates",
                                                  "sampled timing bounds +/-3f; hidden alpha, font identity and exact curves unknown"],
                     reconstruction_hint="Separate this observed semantic layer; follow measured frame states and shared visual system; no claim of recovered author code")
            e.pop("text",None);e.pop("asset_id",None)
            if text is not None:
                e["text"]=dict(content=text,case="as observed",typography=dict(font_identity="unknown",candidate_only=True,
                    description="monospaced HUD or condensed numeric; bold grotesque lyric; compare actual frame glyphs",
                    cap_height_px_estimate=height,alignment="left unless ring/centred board",stroke="none separately observed",shadow="none separately observed",confidence=.72))
            elements.append(e);return e

        base_description=s["scene_description"].split(" Geometry and typography")[0].split(" 独立图层、时序与屏幕坐标")[0]
        add("background_media",base_description,(0,0,1920,1080),0)
        if number==144:
            add("prop","White rectangular woven barcode tag hangs on cord, rotates about-15deg over black pleats",(330,70,1210,865),5)
            add("prop","Narrow dark barcode bands printed into right half of physical tag; no decoded data inferred",(895,245,445,395),6)
            add("text_label","Tag header and fine-print fibre test details rotate with cloth",(375,300,450,500),22,
                "CARE LABEL 01 · EV-27-0000 / FIBRE CONTENT BY WEIGHT / TEST METHOD ISO 1833 · SS27 / SHELL 100% / LINING 100% / THIS SIDE OUT",height=14)
            add("text_lyric","SHELL types in orange then turns black on tag;100% appears on following line late",(410,400,350,265),23,
                "SHELL: / 100%",[(6585,dict(text="SHE")),(6588,dict(text="SHELL:")),(6594,dict(state="black text")),(6633,dict(text="SHELL: 100%"))],start=6584,height=78)
            add("hud_gauge","Right ring progress advances0→25→50→75→100, orange arc over grey track",(1600,260,240,270),30,
                "SHELL · ANALYSIS / 0 / 25 / 50 / 75",[(6586,dict(value=0)),(6603,dict(value=25)),(6615,dict(value=50)),(6624,dict(value=75)),(6636,dict(value=100))],start=6585,height=60)
            add("text_label","Weaving status below progress, then settled pending-weft text",(1568,558,310,65),31,
                "Weaving… / (1s · 2.3k tokens) / Woven. Result pending.",[(6616,dict(text="Weaving…")),(6636,dict(text="Woven. Result pending."))],start=6590,height=18)
            add("deco_graphic","Fine probe leader to barcode and orange vertical registration rule across tag",(840,120,560,590),18)
            add("transition_graphic","Incoming tag overlays previous full-body frame through horizontal tear at first two frames",(0,350,1920,450),60,end=6580)
        elif number in (145,146):
            add("character","Dark bob model holds white tag near face; portrait differs across hard cut, hand and collar remain plate regions",(315,0,1605,1080),5)
            add("prop","Blank/reversed physical white tag held in fingers, tracked by thin black bracket",(1250,140,650,640) if number==145 else (820,650,500,380),6)
            add("hud_panel","Upper-left FIG.11 construction paper; wearer/shell/lining exploded planes",(94,140,500,470),30,
                "FIG. 11 · CONSTRUCTION / 01 · SHELL · OUTSIDE / 100% OPTIMISM / 02 · LINING · INSIDE / 100% / 03 · WEARER / MODEL 01 / EXPLODED VIEW · 2 OF 2 LAYERS" if number==146 else
                "FIG. 11 · CONSTRUCTION / 01 · SHELL · OUTSIDE / 100% OPTIMISM / 03 · WEARER / MODEL 01 / EXPLODED VIEW · 1 OF 2 LAYERS",height=13)
            add("deco_graphic","Three parallelogram layer diagrams connected vertically; orange hatching shell, empty lining, dotted wearer; only1layer resolved in145",(315,228,260,287),31)
            add("tag_card","Lower-left fibre-content cream card, thin rules, barcode and EV identifier",(72,652,560,320),30,
                "CARE LABEL 01 · FIBRE CONTENT / L62 · 04:34:07 / EV-27-0000 · WOVEN · MADE TO ORDER",height=12)
            add("text_lyric","SHELL: optimism. typed orange with cursor then settles black; LINING: starts in last3frames of145 and persists146",(92,735,520,166),32,
                "SHELL: optimism. / LINING:",[(6656,dict(text="SHELL: opti")),(6659,dict(text="SHELL: optimism.")),(6664,dict(state="optimism now black")),(6670,dict(text="LINING starts")),(6673,dict(text="SHELL: optimism. / LINING:"))],height=67)
            add("hud_bracket","Face/tag corner marks follow model and tag; FACE DEADPAN label, TAG FACE→REVERSE as shot changes",(500,85,1250,720),18,
                "FACE · DEADPAN 0.96 / TAG · FACE 0.90" if number==145 else "FACE · DEADPAN 0.96 / TAG · REVERSE 0.90",height=12)
            if number==145:
                add("flash","Single faded incoming tilted portrait is overprinted at6670 then previous portrait returns6671 before real cut6673",(0,0,1920,1080),60,start=6670,end=6670)
            else:
                add("text_label","Cream nose-adjacent callout with leader types TURNED180deg",(1355,616,145,56),23,"TURNED 180°",[(6679,dict(state="blank note")),(6691,dict(text="TURNED 180°"))],start=6678,height=13)
                add("transition_graphic","Whole composition collapses sideways as3D card turn, revealing black tag behind at end",(0,0,1920,1080),60,start=6704)
        elif number==147:
            add("prop","Long black hanging label angled down-left against white cloth; bottom white barcode remains physical texture",(625,0,780,1080),5)
            add("text_title","Orange100% and small lining warning printed on black label",(830,70,400,290),22,
                "LINING · INSIDE / 100% / DO NOT SHOW OUTSIDE / WEAR SHELL SIDE OUT",height=122)
            add("tag_card","Black lower-left fibre card inverts former cream card; same barcode and identifier",(72,652,560,320),30,
                "CARE LABEL 01 · FIBRE CONTENT / SHELL: optimism. / LINING: doom. / EV-27-0000 · WOVEN · MADE TO ORDER",height=12)
            add("text_lyric","LINING doom types with orange first word then settles white on black card",(92,830,480,73),32,
                "LINING: doom.",[(6710,dict(text="LINING: do")),(6714,dict(text="LINING: doom.")),(6720,dict(state="white doom"))],height=66)
            add("hud_panel","Right cream SECTION A-A sleeve cross-section paper",(1310,200,500,560),30,"SECTION A-A · SLEEVE / FIG. 12",height=12)
            add("hud_gauge","Concentric section: orange outer shell complete, inner grey ring progressively fills black clockwise, centre MODEL01 WEARER",(1405,276,310,310),31,
                "MODEL 01 / (WEARER)",[(6712,dict(state="grey inner ring")),(6720,dict(state="black arc aboutquarter")),(6732,dict(state="black arc aboutthreequarters")),(6746,dict(state="inner black ring complete"))],height=14)
            add("text_label","Two legend lines type independently under ring",(1338,603,400,70),32,
                "SHELL · OUTSIDE · 100% OPTIMISM / LINING · INSIDE · 100% DOOM",[(6712,dict(text="SH / LI")),(6732,dict(text="100%")),(6738,dict(state="full words"))],start=6712,height=14)
            for f in (6719,6729,6740):add("glitch","Brief magenta/cyan edge fringe/RGB separation on tag border",(0,0,1920,1080),60,start=f,end=f+1)
        elif number==148:
            add("prop","White stitched care label with textile seams fills frame, black/grey flowing contour lines cross cloth",(230,100,1450,850),5)
            add("text_label","Care header and two dashed instruction placeholders",(340,190,1180,380),22,
                "CARE INSTRUCTIONS · ISO [typing] / INSTRUCTION 02 · PENDING / INSTRUCTION 03 · PENDING",height=14)
            add("text_lyric","Wash then cold type orange and settle black",(460,292,490,68),23,
                "Wash cold.",[(6753,dict(text="Was")),(6755,dict(text="Wash")),(6763,dict(text="Wash co")),(6765,dict(text="Wash cold.")),(6771,dict(state="all black"))],start=6753,height=66)
            add("icon","Wash-tub30 icon appears with cold word",(340,298,85,65),24,start=6762)
            add("counter","Large black30degree temperature at right with small orange max-wash note",(1217,360,360,190),23,
                "30° / MAX WASH · °C · MILD PROCESS",[(6763,dict(state="pale30")),(6765,dict(state="black30"))],start=6762,height=200)
            add("hud_gauge","Lower temperature rule and ticks30/40/60/95 with orange pointer at30 and COLD30C tag",(359,620,1110,105),25,
                "WASH TEMPERATURE · °C · MAX / COLD · 30°C / 30 / 40 / 60 / 95",start=6762,height=13)
            add("deco_graphic","Thin black wavy contour strands move across white fabric at intervals, independent of text",(0,0,1920,1000),18,
                keys=[(6755,dict(state="wave rises from lower-left")),(6765,dict(state="wave falls over30")),(6777,dict(state="next wave enters")),(6789,dict(state="third wave"))])
        elif number==149:
            add("character","Tilted direct portrait, hand holds tag at mouth; orange sleeve insert at shoulder",(420,0,1500,1080),5)
            add("prop","White care tag in fingers near lips, crossed-iron icon stamped over it during care instructions",(810,550,440,320),6)
            add("hud_panel","Upper-left care checklist paper inherits Washcold, then types Donotiron and Donotnerf",(72,104,600,320),30,
                "CARE INSTRUCTIONS · ISO 3758 / Wash cold. / Do not iron. / Do not nerf.",[(6805,dict(text="Do no")),(6814,dict(text="Do not iron.")),(6849,dict(text="Do")),(6858,dict(text="Do not")),(6864,dict(text="Do not nerf."))],end=6879,height=48)
            add("icon","Washtub30, crossed iron and crossed agent/nerf icon stack into independent checklist rows",(94,180,65,202),31,end=6879)
            add("hud_panel","PATCH NOTES model01 V11.2 paper opens below care panel",(72,449,440,178),30,
                "PATCH NOTES · MODEL 01 V11.2 / CHANGELOG",start=6848,end=6879,height=12)
            add("hud_chart","Three reasoning/capability/charm bars:100/70/100; orange capability loses30percent, diagonal REVERTED stamp",(86,503,420,97),31,
                "REASONING 100% / CAPABILITY 70% / CHARM 100% / -30% NERF / REVERTED",[(6858,dict(state="capability70")),(6864,dict(state="REVERTED stamped"))],start=6852,end=6879,height=12)
            add("text_title","Lower-left giant DO→NOT→NERF. changes whole word in cream box",(50,790,440,224),24,
                "DO / NOT / NERF.",[(6850,dict(text="DO")),(6856,dict(text="NOT")),(6861,dict(text="NERF."))],start=6848,end=6879,height=194)
            add("hud_bracket","Face and TAG CARE0.93 corner boxes; hand tag corner line moves with the object",(805,320,510,400),18,"FACE · TO LENS 0.97 / TAG · CARE 0.93",height=12)
            add("tag_card","Cream ESCAPE VELOCITY full garment card appears over chest after care panels clear",(1394,700,310,265),30,
                "LOOK 00 · TAG BACK / SS27 / ESCAPE VELOCITY / SHELL 100% OPTIMISM / LINING 100% DOOM / WASH COLD · 30 / IRON DO NOT / NERF DO NOT / MADE IN SAN FRANCISCO / EV-27-0000",start=6887,height=12)
            add("hud_panel","Blank FIG13 origin-map paper expands from left after cleanup",(72,120,500,540),30,
                "FIG. 13 · ORIGIN OF THE COLLECTION / SF",start=6914,height=12)
        elif number==150:
            add("character","Same tilted close portrait but new hand pose lifts tag beside mouth, black hair and orange strand crisp under coarse dots",(630,0,1290,1080),5)
            add("prop","White rectangular tag with small L-like mark and dot, held horizontally to lens",(960,540,290,190),6)
            add("hud_panel","FIG13 San Francisco map paper inherited blank grid from prior shot",(72,120,500,540),30,"FIG. 13 · ORIGIN OF THE COLLECTION / SF",height=12)
            add("hud_chart","City outline draws, then landmark circles, leader labels and orange MADEHERE star",(115,185,430,435),31,
                "GOLDEN GATE / 20 STRANDED · PRESIDIO / 00 · THE BILLBOARD · MASONIC AVE / LOOK 04 · SHOES OFF · NORTH BEACH / LOOK 05 · FIREWORK · MISSION / US-101 · BILLBOARDS / MADE HERE ✱",[(6926,dict(state="outline begins")),(6932,dict(state="outline complete; locations start")),(6940,dict(state="orange star and MADEHERE"))],height=12)
            add("text_lyric","Left headline builds Made/in/San thenFrancisco on second line; incoming word orange then black",(72,730,500,112),23,
                "Made in San / Francisco.",[(6924,dict(text="Made")),(6930,dict(text="Made in")),(6934,dict(text="Made in San")),(6940,dict(text="Made in San Francisco.")),(6954,dict(state="all words black"))],height=62)
            add("text_label","Map latitude ticks and typed city-coordinate/footer line",(72,855,500,45),22,
                "L64 · CARE LABEL / 37.7749° N · 122.4194° W",start=6944,height=12)
            add("tag_card","Chest ESCAPE VELOCITY tag-back full care/composition table stays from preceding shot",(1394,700,310,265),30,
                "LOOK 00 · TAG BACK / ESCAPE VELOCITY / SHELL 100% OPTIMISM / LINING 100% DOOM / WASH COLD · 30 / IRON DO NOT / NERF DO NOT / MADE IN SAN FRANCISCO / EV-27-0000",height=12)
            add("hud_bracket","Head/tag face-to-lens corner brackets",(1010,260,550,440),18,"FACE · TO LENS 0.97",height=12)
        elif number==151:
            add("character","Full-body model turns from side to back, black skirt and tall boots, centre white studio with soft floor shadow",(805,200,260,740),5)
            add("prop","Small solid black square board/void floats just left of model head; stays after other overlays clear",(690,265,145,165),6)
            add("hud_bracket","Thin circle and coordinate labels around black board and model, removed after7094",(640,230,420,705),18,
                "MODEL 01 · RING-OUT / BOARD 01",end=7094,height=12)
            add("hud_panel","Upper-right cream ring-out board grows open and holds large two-line flap",(1120,120,700,400),30,
                "BOARD 01 · THE WALL · RING-OUT",start=6971,end=7094,height=12)
            add("split_flap","Ring-out board THEREISNOUNDERCLASS flips to ENDOFSHOW by about7034, with orange SHOW and smallerLOOKS11/11 MONTHS00",(1150,160,640,305),31,
                "THERE IS NO / UNDERCLASS / END OF / SHOW. / LOOKS 11/11 / MONTHS 00",[(6974,dict(text="THERE IS NO UNDERCLASS")),(7014,dict(state="new flip begins")),(7034,dict(text="END OF SHOW."))],start=6974,end=7094,height=75)
            add("hud_panel","Left lower SHOW01 credits/status paper types lines progressively before clearing",(72,600,470,225),30,
                "SHOW 01 · REPORT / SS27 / LOOKS SHOWN 11/11 / MONTHS TO ESCAPE 00 / UNDERCLASS NONE / FRONT ROW AGENTS / RUNTIME 05:06 / STATUS LIVE [later terminal state not resolved]",start=6977,end=7094,height=13)
            add("text_label","Right SHOW NOTES LOOKBOOK INDEX list types from top down after main panels disappear; later coarsening makes glyphs ambiguous",(1205,230,600,590),22,
                "SHOW NOTES · LOOKBOOK INDEX / LOOK01 AGI ERA 00:26 / LOOK02 13 MAC MINIS 00:33 / LOOK03 DAD CAP 00:40 / LOOK04 SHOES OFF 00:47 / LOOK05 FIREWORK 00:55 / LOOK06 THE SINGULARITY 01:02 / LOOK07 IMPOSSIBLE PUZZLES 01:53 / LOOK08 HUGGING-FACE PIN 02:04 / LOOK09 SHEER 02:07 / LOOK10 STAFF BADGE 02:15 / LOOK11 THE IMMORTALS 02:25 / MUSIC · VOICE SUNO V6 / LOOKS MIDJOURNEY / MOTION SEEDANCE 2.5 / GRAPHICS CLAUDE · CODE / MADE IN SAN FRANCISCO",start=7095,height=13)
            add("hud_panel","Lower-left print-pass diagnostic box, dotted scale and changing pitch readout",(72,640,420,250),30,
                "SCREEN · DOT PITCH / HALFTONE / 07 PX → 60 PX / 7 PX → 60 PX · 45° · INK ON PAPER / STEP 05 / 12",[(7110,dict(value=7)),(7130,dict(value=8)),(7140,dict(value=10)),(7154,dict(value=12)),(7166,dict(value=16)),(7178,dict(value=21)),(7190,dict(value=27)),(7194,dict(value=36)),(7210,dict(value=47)),(7214,dict(value=60))],start=7107,height=50)
            add("texture_overlay","Halftone dots visibly grow from small grid to large separated circles, washing out details and fragmenting lookbook glyphs",(0,0,1920,1080),50,
                keys=[(7142,dict(state="model facial detail still partly clear")),(7180,dict(state="large dot grid covers whole frame")),(7214,dict(state="very coarse black/white cells"))],start=7140)
            add("text_label","Cream pointer note by model waist types a dot/ink-paper statement",(592,380,270,70),23,
                "MODEL 01 · 1 DOT / CLAY [continuation unresolved]",start=7202,height=14)
            add("transition_graphic","Orange flat radial burst grows from model centre in last few frames, black/white petals reveal next hair macro",(0,0,1920,1080),60,start=7221)
            add("flash","Brief grey paper/block over waist at very first frame; removed within first few frames",(820,420,230,170),60,end=6969)
        elif number==152:
            add("prop","Nine-point orange dimensional star clip dominates black hair; count9 verified by tips and on-screen annotation, despite8-point author canon",(540,110,850,850),6)
            add("deco_graphic","Thin circumscribed circle, radial spokes R1–R9, diameter rule and corner/anchor handles align to star",(465,95,1000,870),18,
                "R1 / R2 / R3 / R4 / R5 / R6 / R7 / R8 / R9",height=12)
            add("text_label","Star point-count annotation on cream strip at right",(1425,565,285,29),23,
                "9-PT STAR · 9 × 40° · CLAY #D97757",start=7279,height=12)
            add("text_label","Diameter note animates with hair/clip scale rather than staying a fixed841PX source measurement",(1425,595,270,28),24,
                "Ø 841 PX → Ø 839 PX · MEASURED ON THE PLATE",[(7285,dict(value=841)),(7290,dict(value=839))],start=7279,height=12)
            add("text_label","Separate upper angle annotation attached to the R7–R8 construction",(1227,83,207,26),23,
                "∠ 38° · R7–R8 · MEASURED",start=7279,height=12)
            add("text_lyric","Whispered ad-lib written vertically at left, word-by-word orange then black",(72,305,155,170),23,
                "we / are / so / back",[(7277,dict(text="we")),(7283,dict(state="are begins")),(7285,dict(text="we are")),(7286,dict(state="we black")),(7289,dict(state="so begins")),(7291,dict(text="we are so")),(7294,dict(state="are black")),(7300,dict(state="so black; back begins")),(7303,dict(text="we are so back")),(7311,dict(state="all black"))],start=7275,height=31)
            add("text_label","Cream leader label types right-aligned over two lines, then holds; source-native wording recovered from per-frame crops",(292,233,178,55),23,
                "THE LAST MARK / WORN SINCE LOOK 00",[(7289,dict(state="typing begins")),(7297,dict(text="THE LAST")),(7301,dict(text="THE LAST MARK / W")),(7317,dict(text="THE LAST MARK / WORN SINCE LOOK 00"))],start=7289,height=12)
            add("text_label","Ad-lib mode and timecode at left below words",(72,510,290,45),22,"AD-LIB · WHISPERED / 05:03:02",start=7275,height=12)
            add("tag_card","Cream ESCAPE VELOCITY end label slides up from left-lower edge, at full height by about7317; symbol row and barcode at bottom",(72,688,418,308),30,
                "LOOK 00 / 11 / END / ESCAPE VELOCITY / SHOW 01 · SS27 / LOOKS 11 / 11 / EV-27-0000",start=7312,height=12)
            add("transition_graphic","Inherited opening radial petals retract, then closing black geometric petals enter from frame edges",(0,0,1920,1080),60,
                keys=[(7225,dict(state="opening petals visible")),(7233,dict(state="opening reveal complete")),(7333,dict(state="closing black wedges enter")),(7345,dict(state="black sectors cover much of frame"))])
            add("texture_overlay","Coarse opening screen dots resolve to fine hair texture by about7270; orange star retains lit3D bevels",(0,0,1920,1080),50,
                keys=[(7225,dict(state="coarse dots")),(7270,dict(state="fine hair resolved"))])
        else:
            add("transition_graphic","Black radial iris covers prior hair shot during7346–7347, all chrome disappears7348",(0,0,1920,1080),60,end=7347)
            add("prop","Single isolated orange star briefly remains centred on near-black at7348 then disappears",(850,420,230,230),61,start=7348,end=7348)
            add("background_media","Near-black terminal frames7349–7352; decoded image not guaranteed mathematically RGB0 due compression",(0,0,1920,1080),62,start=7349)
        s["elements"]=elements
        s["animations"]=[dict(anim_id=f"{sid}-A{i+1:02d}",target_element_ids=[e["element_id"]],description=e["description"],
            start_frame=e["start_frame"],end_frame=e["end_frame"],easing=e["motion"]["easing"],audio_sync="candidate temporal relations only; no direct listening proof") for i,e in enumerate(elements) if len(e["keyframes"])>2]
        s["analysis_status"]="DETAILED_VISUAL_REVIEW"
        s["detail_review"]=dict(reviewer="root",method="whole filmstrip, native1920 midpoint and independent1–4f regional/whole-shot second pass",timing_precision_frames=3,
            reference_sheet=f"work/root_review/tail_micro_{sid}.jpg" if number<=150 else f"contactsheets/{sid}.jpg",
            pending=[])
        s["uncertainties"]=["Unknown font files, physical plate/overlay decomposition, original curve, alpha and random flip seed",
            "Measured visual boxes +/-0.02 normalized; event start bounds +/-3f; precise audio alignment still requires listening",
            "Author eight-point star statement does not override observed nine-point ending; uncounted clips remain unknown"]
        s["scene_description"]=base_description+" 独立图层、时序与屏幕坐标已根据实际参考帧复核；隐藏原参数保留unknown。"
        s["observed_text_inventory"]=[e["text"]["content"] for e in elements if "text" in e]
        mid=(a+b)//2;rp=f"work/full_batch/{mid:05d}.jpg"
        s["reference_frames"]=[e for e in s["reference_frames"] if not (e["role"]=="detail" and e["path"]==rp)]
        s["reference_frames"].append(dict(frame=mid,path=rp,role="detail",note="root viewed native1920 reference"))
        for f in ({151:[6980,7050,7140,7210],152:[7290]}.get(number,[])):
            extra=f"work/root_review/native/f{f}.jpg"
            if not any(e["path"]==extra for e in s["reference_frames"]):
                s["reference_frames"].append(dict(frame=f,path=extra,role="detail",note="root independently read native overlay fine text"))
        s["confidence"]=.73;p.write_text(json.dumps(s,indent=1,ensure_ascii=False)+"\n")
        print(sid,len(elements),s["analysis_status"])


if __name__=="__main__": main(sys.argv[1])
