#!/usr/bin/env python3
"""Persist root's actual image observations for the handed-over S0095–S0102.

Pixel boxes are bounded visual measurements, not recovered author coordinates.
Only the explicitly handed-over records are written. Raw drafts are retained.
"""
import json
import sys
from pathlib import Path


def main(root):
    root = Path(root)
    for number in range(95, 103):
        path = root / f"shots/shot_{number:04d}.json"
        s = json.loads(path.read_text())
        backup = root / f"work/root_review/before_S{number:04d}.json"
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
        a, b = s["start_frame"], s["end_frame"]
        sid = s["shot_id"]
        elements = []

        def add(kind, desc, box, z, start=None, end=None, text=None, keys=(), color=None, height=None, motion=None):
            first, last = max(a, a if start is None else start), min(b, b if end is None else end)
            eid = f"{sid}-E{len(elements)+1:02d}"
            x, y, w, h = box
            kf = [dict(frame=first, state="first observed/estimated visible state; onset uncertainty <=2 frames"),
                  *[dict(frame=f, **v) for f, v in keys if first <= f <= last],
                  dict(frame=last, state="continues to cut unless exit described")]
            e = dict(element_id=eid, shot_id=sid, type=kind, description=desc,
                     start_frame=first, end_frame=last,
                     bounding_box=dict(x=round(x/1920, 5), y=round(y/1080, 5),
                                       w=round(w/1920, 5), h=round(h/1080, 5), space="frame_norm_top_left"),
                     z_index=z, appearance=dict(color_hex=color, opacity=None, blend_mode="normal",
                                               details="Observed appearance after print pass; source alpha unknown. "+desc),
                     motion=dict(path=motion or desc, easing="snap/step for word and flap states; continuous underlying motion curve unknown",
                                 entrance=f"visible from about f{first}, +/-2f unless inherited at cut",
                                 exit=f"last visible within this shot f{last}; no inferred offscreen history"),
                     keyframes=kf, effects=["shared measured print pass"], reference_frames=sorted({first,last,*[f for f,v in keys if first<=f<=last]}),
                     confidence=0.74, uncertainties=["bbox is visual estimate of typical/max region, approx +/-0.02 normalized; static paper edges approximately +/-8px; not author source geometry",
                                                   "Visibility/word timing sampled every2f; bound +/-2f, not sample-accurate audio timing"],
                     reconstruction_hint="Use exact referenced frames for geometry, draw this layer independently, share global chrome from visual_system.json")
            if text is not None:
                e["text"] = dict(content=text, case="as observed", typography=dict(
                    font_identity="unknown", candidates=["DIN-like condensed sans" if kind in ("split_flap","counter","text_title") else "Helvetica-like grotesque / monospaced HUD"],
                    cap_height_px_estimate=height, weight="visual estimate; condensed regular for flap, regular sans for cream caption",
                    alignment="left unless board cell-centred", tracking="wide monospace on boards/HUD; normal in captions",
                    stroke="none observed", shadow="none separately resolved", method="visual_estimate", confidence=0.72))
            elements.append(e)
            return e

        # These regions are semantic plate regions, not a claim of independent
        # person masks or recovered source-layer z-order.
        add("background_media", s["scene_description"], (0,0,1920,1080), 0)
        if number == 95:
            add("character", "Dark bob model turns and approaches below three gantries, white puff blouse, black harness/skirt and hanging tag", (660,280,520,800), 5)
            add("split_flap", "Left gantry settles ESCAPE VELOCITY; lower row still random flip states before later speed number", (122,210,460,180), 20,
                text="ESCAPE VELOCITY", keys=[(4382,dict(state="random characters")),(4408,dict(state="ESCAPE VELOCITY; lower digits scrambling"))],height=43)
            add("split_flap", "Middle gantry changes independently into LONGEVITY E.V.; lower line random until YR/YR suffix", (630,198,500,180), 20,
                text="LONGEVITY E.V. / YR/YR", keys=[(4400,dict(text="LONGEVITY E.V.")),(4430,dict(state="YR/YR suffix visible"))], height=43)
            add("split_flap", "Right gantry turns from random letters into UNDERCLASS, then 06 MONTHS", (1230,190,500,190), 20,
                text="UNDERCLASS / 06 MONTHS",keys=[(4406,dict(text="UNDERCLASS")),(4428,dict(text="06 MONTHS"))],height=43)
            add("text_title", "Residual individual cream BACK! tiles flip vertically and disappear near shot opening", (1232,245,580,235), 22,
                end=4387,text="BACK!",keys=[(4386,dict(state="tile halves rotating; not a new lyric"))],height=130)
            add("hud_panel", "Cream PLAN · US-101 N · 06:40 1:4000 panel expands at lower left", (72,640,330,291), 30,
                start=4388,text="PLAN · US-101 N · 06:40 / 1:4000",keys=[(4388,dict(state="paper surface begins")),(4391,dict(state="panel filled"))],height=12)
            add("hud_chart", "Three horizontal gantry lanes G3/G2/G1; orange G3 top line, YOU orange dot below G1", (112,684,270,230),31,
                start=4390,text="G3 / G2 / G1 / YOU",keys=[(4408,dict(state="G3 orange; lower lanes black; YOU near x237 y878"))],height=11)
            add("text_label", "Upper-left cream ad-lib and bridge navigation note", (64,171,264,53),22,
                text="AD-LIB · BA-DA— / NEXT · THE BRIDGE · 3 BOARDS",height=13)
            for label, box in [("BOARD 01 · ROCKET",(350,440,146,25)),("BOARD 02 · LONGEVITY",(870,467,176,25)),("BOARD 03 · UNDERCLASS",(1480,475,188,25))]:
                add("text_label", "Black pointer-tag below corresponding gantry: "+label,box,23,start=4394,text=label,height=12)
            add("hud_bracket", "Model face/body corner brackets with MODEL 01 · TURNING 0.97 tag",(700,310,470,690),18,
                text="MODEL 01 · TURNING 0.97",height=12)
            add("transition_graphic", "Outgoing subject becomes ghosted with incoming closer portrait during dissolve",(0,0,1920,1080),60,start=4432,
                keys=[(4432,dict(state="incoming ghost starts")),(4435,dict(state="two subject positions visible"))])
        elif number == 96:
            add("character", "Model centred below gantries, head bowed; hair and hanging garment tag remain in plate", (710,310,480,770),5)
            for text,box in [("ESCAPE / VELOCITY / 8.8→10.7 KM/S",(40,100,530,190)),("LONGEVITY / E.V. / ---- YR/YR",(690,97,515,190)),("PERMANENT / UNDERCLASS / 06 MONTHS",(1350,97,530,190))]:
                add("split_flap","Separate gantry board with cell-grid numerals: "+text,box,20,text=text,height=46,
                    keys=[(4436,dict(state="inherited board state")),(4517,dict(state="rocket value about10.7; six-month board stable"))])
            add("text_title", "Very large low-opacity grey ESCAPE behind model and caption, aligned to road perspective",(100,420,780,200),19,text="ESCAPE",color="#808080",height=180)
            add("text_caption", "Cream caption grows by word; Escape readable f4442, velocity rotates/reveals f4454–4456",(72,392,390,65),22,start=4441,
                text="Escape velocity:", keys=[(4442,dict(text="Escape")),(4454,dict(state="velocity entering below baseline")),(4456,dict(text="Escape velocity:"))],height=49)
            add("hud_panel", "Right-lower FIG.1 paper panel reveals from top to full rectangle",(1190,560,620,390),30,start=4441,
                text="FIG. 1 · ESCAPE VELOCITY · EARTH / BOARD 01 · ROCKET",keys=[(4441,dict(state="faint header")),(4442,dict(state="panel shallow")),(4445,dict(state="full paper panel"))],height=12)
            add("hud_chart", "Earth circle, dashed7.9 orbit, solid ellipse and plotted launch-dot gradually draw; orbit opens upward into escaping trajectory",(1210,735,430,205),31,
                start=4447,text="7.9 · ORBIT / EARTH · R 6,371 KM",keys=[(4447,dict(state="Earth circle begins")),(4478,dict(state="ellipse orbit")),(4499,dict(state="escaping open curve"))],height=12)
            add("text_label", "Upper-right panel formulas and velocity readout; fall-back caption changes to escape near threshold",(1555,604,245,135),32,
                start=4447,text="V = √(2GM / R) / G 6.674 × 10⁻¹¹ / M 5.972 × 10²⁴ [unit partly resolved] / v 9.2 KM/S · FALLS BACK",
                keys=[(4478,dict(text="v 9.2 KM/S · FALLS BACK")),(4517,dict(state="near10.7 speed; formula unit not invented from a partial glyph"))],height=15)
            add("text_label", "Black micro labels track boards and model; lower-left road weather metadata",(72,875,300,72),18,
                text="SEGMENT · 3 GANTRIES · 400 M / US 101 N · FOG · 06:52 / VISIBILITY 40 M · WIND 22 KT",height=12)
            add("hud_bracket", "PAYLOAD 01 · LOOK 11 0.97 face/body bracket; TAG pointer to hanging label",(720,280,480,780),18,
                text="PAYLOAD 01 · LOOK 11 0.97 / TAG",height=12)
            add("text_label", "Small G1/G2/G3 labels below gantries, light/dark contrast differs",(295,315,1440,35),23,
                text="G1 · ROCKET / G2 · LONGEVITY / G3 · UNDERCLASS",height=12)
            add("transition_graphic", "Incoming eye close-up/fast crop overlaps face at end",(0,0,1920,1080),60,start=4519)
        elif number == 97:
            add("character", "Extreme eye/cheek crop; blue-white gantry reflected in iris, hair black and orange above",(0,0,1920,1080),5)
            add("hud_gauge", "White circular iris reticle with radial ticks and four longer crosshair arms, centred about(1205,530)",(952,280,505,500),18,
                text="Ø 11.8 MM",height=11)
            add("counter", "Projected white condensed speed in iris increases about10.8→11.2 KM/S; it is graphic reflection, not a physical readout",(1090,450,245,145),20,
                text="11.2 / KM/S",keys=[(4527,dict(value=10.8)),(4531,dict(value=11.0)),(4540,dict(value=11.2))],height=70)
            add("text_label", "Iris source annotation types letter-by-letter at upper-right",(1470,375,300,70),22,
                text="IRIS · REFLECTION / SRC · GANTRY 01 / OCR · 11.2 KM/S",keys=[(4548,dict(text="IRIS · REFLECTION / SRC · GANTRY 01 / OC")),(4575,dict(state="annotation fills further; source unit labels unchanged"))],height=13)
            add("text_caption", "Inherited cream Escape velocity: caption appends measured speed, first appearing as pale reveal",(72,392,650,65),22,
                text="Escape velocity: 11.2 KM/S.",keys=[(4524,dict(text="Escape velocity:")),(4544,dict(text="Escape velocity: 11.2 KM/S."))],height=49)
            add("text_title", "Very tall white left11.2 with KM/S. below; one-frame cream/black reveal precedes white text",(72,535,400,398),23,
                start=4543,text="11.2 / KM/S.",keys=[(4543,dict(state="cream reveal backing; digits invert")),(4546,dict(state="white digits without backing"))],height=270,color="#F5F4E9")
            add("text_label", "Small physical formula footer under big speed",(87,943,440,22),24,start=4544,
                text="v_esc = √(2GM/r) · EARTH · NO ATMOSPHERE",height=12)
            add("counter", "Black launch-speed number below iris with long underline, value matches its own numeric animation",(1248,823,440,106),21,
                text="v · LAUNCH SPEED · KM/S / 11.2",keys=[(4531,dict(value=11.0)),(4548,dict(value=11.2))],height=69)
            add("deco_graphic", "Thin horizontal iris-diameter measuring bar with end ticks and centred black micro-tag",(1035,738,340,35),19,text="Ø 11.8 MM",height=11)
        elif number == 98:
            add("character", "Small walking model centred on fog road, approx(884,550)-(1020,920)",(880,545,145,380),5)
            add("split_flap", "Left overhead board blanks then spells LONGEVITY ESCAPE VELOCITY over three rows",(145,120,725,280),20,
                text="LONGEVITY / ESCAPE / VELOCITY",keys=[(4576,dict(text="")),(4618,dict(state="first line scrambling")),(4620,dict(text="LONGEVITY")),(4638,dict(text="LONGEVITY ESCAPE")),(4650,dict(text="LONGEVITY ESCAPE VELOCITY"))],height=50)
            add("split_flap", "Right board initially----YR/YR, flips to+1YR/YR then PAST2029 on second row",(910,150,610,235),20,
                text="+1 YR/YR / PAST 2029",keys=[(4576,dict(text="---- YR/YR")),(4654,dict(text="+1 YR/YR / PAST 2029"))],height=68)
            add("text_caption", "Lower-left cream caption enters word-by-word over road",(72,850,670,66),22,start=4614,
                text="Longevity escape velocity:",keys=[(4616,dict(text="Longevity")),(4634,dict(text="Longevity escape")),(4644,dict(text="Longevity escape velocity:"))],height=49)
            add("hud_panel", "Lower-right FIG.2 cream paper expands downward, dark one-pixel border",(1180,520,640,410),30,start=4614,
                text="FIG. 2 · LONGEVITY ESCAPE VELOCITY / BOARD 02",keys=[(4614,dict(state="shallow header")),(4617,dict(state="full paper rectangle")),(4619,dict(state="plot headers drawn"))],height=12)
            add("hud_chart", "Life-expectancy gained per calendar-year curve rises; dashed1YR/YR threshold, endpoint moves to1.89",(1230,690,535,212),31,start=4619,
                text="LIFE EXPECTANCY GAINED / CALENDAR YEAR / 2000 / 2020 / 2040 / 1 YR/YR",
                keys=[(4620,dict(value=.16)),(4639,dict(value=.77)),(4646,dict(value=1.40)),(4650,dict(value=1.89))],height=12)
            add("counter", "Panel large numeric YR/YR readout increments with curve",(1215,610,190,45),32,start=4619,
                text="1.89 YR / YR",keys=[(4620,dict(value=.16)),(4628,dict(value=.29)),(4639,dict(value=.77)),(4646,dict(value=1.40)),(4650,dict(value=1.89))],height=22)
            add("hud_bracket", "Full body tracking box and black PAYLOAD header follows the small model",(855,510,235,415),18,
                text="PAYLOAD 01 · WALKING 0.95 / G1 + G2 · 11.5 M / PACE 1.4 M/S",height=12)
            add("text_label", "Small black label below overhead left board",(345,425,180,28),22,
                text="G2 · LONGEVITY · LIVE",height=12)
        elif number == 99:
            add("character", "Model low in frame, head tilted upward under black gantry truss, body cropped at hips",(735,540,390,540),5)
            add("environment", "Large black overhead steel truss crosses top; white fog opens behind, crash barriers converge on road",(0,0,1920,550),5)
            add("split_flap", "Four large calendar tiles alternate2025→2026 and later2027→2026; each digit has horizontal hinge",(84,300,440,160),20,
                text="2026",keys=[(4662,dict(value=2025)),(4669,dict(value=2026)),(4718,dict(value=2027)),(4726,dict(value=2026)),(4741,dict(value=2027)),(4748,dict(value=2026))],height=120)
            add("counter", "Smaller BIOLOGICAL AGE tiles beside year,34.0 then35.0 then34.0; keep displayed inconsistency rather than forcing calendar monotonicity",(552,300,195,72),20,
                text="34.0",keys=[(4662,dict(value=34.0)),(4718,dict(value=35.0)),(4726,dict(value=34.0)),(4741,dict(value=35.0)),(4748,dict(value=34.0))],height=50)
            add("text_label", "Calendar and age column headings, net-since line below age",(84,270,680,125),22,
                text="GANTRY 02 · CALENDAR · LOCAL / BIOLOGICAL AGE · YR / NET SINCE 2026 · 0.0",height=12)
            add("text_caption", "Inherited lower-left cream line appends one/year/back then wraps for/every/year",(72,850,830,125),23,
                text="Longevity escape velocity: one year back / for every year.",height=49,
                keys=[(4662,dict(text="Longevity escape velocity:")),(4714,dict(text="Longevity escape velocity: one")),(4718,dict(text="Longevity escape velocity: one year")),(4724,dict(state="back entering")),(4728,dict(text="Longevity escape velocity: one year back")),(4732,dict(state="for on second line")),(4738,dict(state="for every")),(4744,dict(state="for every year."))])
            add("hud_bracket", "Small face bracket gazes upward; black label connected by diagonal leader to overhead coordinate",(884,553,146,173),18,
                text="GAZE ↑ · G2 0.93",height=12)
            add("text_label", "Black upper leader tag near(998,405), diagonal stem ends on head",(940,402,235,160),19,
                text="G2 · OVERHEAD · 6.1 M",height=12)
        elif number == 100:
            add("character", "Direct lens gaze, dark bob with orange centre streak and star; enlarged face occupies left60%, raised shoulder lower right",(80,0,1090,1080),5)
            add("split_flap", "Right upper3-row grid scrambles then resolves35% DIE /43% LIVE /FOREVER",(1190,109,625,264),20,
                text="35% DIE / 43% LIVE / FOREVER",keys=[(4749,dict(text="")),(4765,dict(state="three rows scrambling")),(4775,dict(text="35% DIE / 43% LIVE")),(4784,dict(text="35% DIE / 43% LIVE / FOREVER"))],height=64)
            add("text_label", "Tiny heading above probability flap board",(1190,83,420,24),22,text="GANTRY 02 · THE ODDS · DECISION",height=12)
            add("text_lyric", "Right-centre black lyric appears word by word; incoming word is pale grey and below baseline for about2f before becoming black",(1225,469,480,136),23,start=4782,
                text="If it doesn't kill us / all first.",height=54,
                keys=[(4783,dict(text="If")),(4785,dict(state="it entering pale")),(4789,dict(text="If it doesn't")),(4797,dict(text="If it doesn't kill")),(4801,dict(text="If it doesn't kill us")),(4805,dict(state="all entering second line")),(4807,dict(text="If it doesn't kill us all")),(4811,dict(text="If it doesn't kill us all first."))])
            add("deco_graphic", "Thin black underline below lyric; types SOURCE · LESS after a short delay",(1228,608,470,35),24,start=4783,
                text="SOURCE · LESS",keys=[(4791,dict(text="S")),(4803,dict(text="SOURCE")),(4819,dict(text="SOURCE · LES"))],height=10)
            add("hud_chart", "N=100 waffle matrix fills row by row using black squares, outlined circles, outlined squares and dots for four categories",(1227,714,210,200),31,start=4782,
                text="IMMORTALITY OR DEATH BY AGI · BORN 2001 · N = 100",keys=[(4782,dict(state="first black cells")),(4791,dict(state="43percent circle category")),(4803,dict(state="10percent die before AGI")),(4806,dict(state="11percent live ageing unsolved"))],height=11)
            add("text_label", "Four outcome legend lines; printed rounded percentages sum99, do not invent a remainder category",(1453,713,340,140),32,start=4782,
                text="35% DIE FROM UNSAFE AGI / 43% LIVE · AGEING SOLVED / 10% DIE BEFORE AGI / 11% LIVE · AGEING UNSOLVED",height=16,
                keys=[(4782,dict(state="35% line")),(4791,dict(state="43% line")),(4803,dict(state="10% line")),(4806,dict(state="11% line"))])
            add("text_label", "Tiny source footer below waffle chart, independently read at native f4823; absent4807, present4810",(1227,918,535,22),32,start=4809,
                text='SOURCE · LESSWRONG, 21 DEC 2024 · "IMMORTALITY OR DEATH BY AGI"',height=10)
            add("hud_bracket", "Corner bracket encloses face; white-on-black label emphasises gaze at camera rather than board",(392,169,665,908),18,
                text="GAZE · LENS · NOT THE BOARD 0.98",height=12)
        elif number == 101:
            add("character", "Model in profile/three-quarter occupies left half, hands beside skirt; white hanging label points to TAG callout",(330,70,620,1010),5)
            add("split_flap", "Left board types PERMANENT then UNDERCLASS; each row flips independently",(0,170,520,165),20,
                text="PERMANENT / UNDERCLASS",keys=[(4824,dict(text="")),(4853,dict(text="PERMANENT")),(4870,dict(text="PERMANENT UNDERCLASS"))],height=58)
            add("split_flap", "Right board settles06 above widely spaced MONTHS; central third board stays unlettered/dark",(1260,148,555,198),20,
                text="06 / MONTHS",keys=[(4834,dict(state="digits scrambling")),(4840,dict(text="06 MONTHS"))],height=76)
            add("environment", "Dark empty central gantry and fog road form negative field between model and right board",(600,40,590,390),5)
            add("text_caption", "Cream caption to right begins Permanent then appends underclass, without forcing board typing timing to match",(1125,418,570,66),23,start=4846,
                text="Permanent underclass:",height=49,keys=[(4848,dict(text="Permanent")),(4866,dict(text="Permanent underclass:"))])
            add("hud_panel", "FIG.3 cream paper grows vertically at lower right; header and thin border appear before axes",(1140,560,680,380),30,start=4846,
                text="FIG. 3 · MONTHS TO ESCAPE THE PERMANENT UNDERCLASS / BOARD 03",height=12,
                keys=[(4846,dict(state="shallow header strip")),(4849,dict(state="full paper surface"))])
            add("hud_chart", "Step-down month chart from18 to0; x LOOK, y18/12/06/00, animated endpoint descends through L07/L08 toward current6 and finally0",(1188,610,602,280),31,start=4851,
                text="18 / 12 / 06 / 00 / LOOK → / L07 / L08 / L09 / L10 / L11",height=12,
                keys=[(4851,dict(state="axes and18 plateau")),(4861,dict(value=12)),(4876,dict(value=6)),(4889,dict(value=0))])
            add("deco_graphic", "Three small black square markers beneath right board, aligned horizontally above caption",(1480,469,185,20),19)
            add("hud_bracket", "Tall partial body bracket from head to frame bottom and leader toward clothing label",(328,66,622,1010),18,text="TAG",height=12)
        elif number == 102:
            add("character", "Eye/cheek extreme close-up; silver-blue reflection in iris, orange hair above, microphone part at lower right",(0,0,1920,1080),5)
            add("hud_gauge", "Thin iris circle, ticks/crosshairs and horizontal diameter line; diameter label reads11.7MM",(648,274,620,490),18,
                text="Ø 11.7 MM",height=11)
            add("counter", "White 06 MO initially in iris, changes03 by f4904, then02 in last2frames while large3. stays unchanged",(854,315,200,300),20,
                text="03 / MO",height=122,keys=[(4900,dict(value="06 MO")),(4904,dict(value="03 MO")),(4930,dict(value="02 MO"))])
            add("text_title", "Lower-left huge3. enters as white on black backing then inverts to black on image",(84,694,240,265),23,start=4910,
                text="3.",height=234,keys=[(4910,dict(state="white3 on black rectangle")),(4912,dict(state="black3 on bare cheek")),(4931,dict(state="black3 retained while iris says02"))])
            add("text_label", "Very small countdown explanation below3 numeral",(86,950,350,20),24,start=4912,
                text="PERMANENT UNDERCLASS · T-3",height=11)
            add("transition_graphic", "Incoming eye exposed through wide pale horizontal tear bands, thin horizontal registration lines, vanishes by4906",(0,50,1920,630),60,end=4906,
                keys=[(4900,dict(state="two bright horizontal wipe strips")),(4904,dict(state="thin central tear")),(4906,dict(state="underlying eye clean"))])
            s["persistent_layer_state"]["G-MONTHS-COUNTER"] = "06 initially,03 by4904,02 at4930–4931; exact mismatch to left3. retained"
        else:
            continue
        s["elements"] = elements
        s["animations"] = [dict(anim_id=f"{sid}-A{i+1:02d}", target_element_ids=[e["element_id"]],
                                description=e["motion"]["path"], start_frame=e["start_frame"],end_frame=e["end_frame"],
                                easing=e["motion"]["easing"],audio_sync="temporal candidates only; listening not evaluated")
                           for i,e in enumerate(elements) if len(e["keyframes"])>2]
        s["analysis_status"] = "DETAILED_VISUAL_REVIEW"
        panel_sheets = {95:"panels95.jpg",96:"panels96.jpg",98:"panels98.jpg",100:"panels100.jpg",101:"panels101.jpg"}
        s["detail_review"] = dict(reviewer="root", method="actual whole filmstrip + native1920 midpoint +2f crop sequence, followed by separate1f panel visibility review",
                                 sheet=f"work/root_review/micro_{sid}.jpg", timing_precision_frames=2,
                                 additional_sheets=[f"work/root_review/{panel_sheets[number]}"] if number in panel_sheets else [],
                                 visibility_note="continuous plate persists throughout; diagram/word starts use inspected1–2f bounds; hidden renderer and font identity remain unknown",
                                 pending=[])
        s["uncertainties"] = ["Original font files, random flap seed, alpha and easing code are unknown",
                              "Positions are bounded visual measurements; digit transition glyphs are reference-frame backed, not fully transcribed random sequences",
                              "Source assertions remain confirmed/inferred/unknown as in original layer hypotheses; inferred film-layer separation is not recovered author source code",
                              "No direct listening proof; audio linkage is candidate timing only"]
        s["observed_text_inventory"] = [e["text"]["content"] for e in elements if "text" in e]
        s["confidence"] = 0.73
        # Add precise reviewed source-frame references without overwriting
        # existing first/middle/last keyframe roles.
        mid = (a+b)//2
        s["reference_frames"] = [e for e in s["reference_frames"] if not (e["role"]=="detail" and e["path"]==f"work/full_batch/{mid:05d}.jpg")]
        s["reference_frames"].append(dict(frame=mid,path=f"work/full_batch/{mid:05d}.jpg",role="detail",note="root viewed native1920 frame"))
        path.write_text(json.dumps(s,ensure_ascii=False,indent=1)+"\n")
        print(sid, len(elements))


if __name__ == "__main__":
    main(sys.argv[1])
