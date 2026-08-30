#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$task_root/../.." && pwd)"
v10="$repo_root/artifacts/qingyan-miao-ad-20260826-v10"
v8="$repo_root/artifacts/qingyan-miao-ad-20260826-v8"
assets="$task_root/assets"
audio="$task_root/audio"
work="$task_root/work"
final="$task_root/final"
font="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

treatment="$v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.mp4"
bridge="$v10/runtime/t8_portrait_ad/01_recap_elder_enters_v2.mp4"
dialogue="$v8/runtime/t8_portrait_ad/02_elder_dialogue_repair.mp4"
leave="$v8/runtime/t8_portrait_ad/03_leave_together.mp4"
demo_start="$assets/demo-keyframe-start.png"
demo_spray="$assets/demo-keyframe-spray.png"
demo_end="$assets/demo-keyframe-end.png"
hook="$assets/visible-sweat-hook.png"
packshot="$assets/product-packshot.jpg"

mkdir -p "$work" "$final"

video_args=(-c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -r 24 -g 48 -movflags +faststart)

# 00 / 0.000-1.500 / 36 frames: one fast visual pain beat.
ffmpeg -hide_banner -loglevel error -y -loop 1 -i "$hook" \
  -vf "scale=1080:1920,zoompan=z='min(zoom+0.0015,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=36:s=1080x1920:fps=24,drawbox=x=50:y=120:w=980:h=230:color=black@0.50:t=fill,drawtext=fontfile='$font':text='腋下一出汗':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=155,drawtext=fontfile='$font':text='就不敢靠太近？':fontcolor=0xFFD83D:fontsize=72:x=(w-text_w)/2:y=245" \
  -an -frames:v 36 "${video_args[@]}" "$work/00-hook.mp4"

# 01 / 1.500-3.500 / 48 frames: live product lift plus exact packshot.
# The solid brand panel replaces the source's lower yellow haze; no haze is shown as spray.
ffmpeg -hide_banner -loglevel error -y -i "$treatment" -loop 1 -i "$packshot" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=48,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=0:y=1380:w=1080:h=540:color=0xF5CE21:t=fill,drawbox=x=55:y=105:w=500:h=230:color=black@0.42:t=fill,drawtext=fontfile='$font':text='青颜':fontcolor=white:fontsize=84:x=95:y=130,drawtext=fontfile='$font':text='抑汗｜净味':fontcolor=0xFFD83D:fontsize=58:x=95:y=235[bg];[1:v]scale=450:450[product];[bg][product]overlay=600:1435:shortest=1[v]" \
  -map "[v]" -an -frames:v 48 "${video_args[@]}" "$work/01-product-intro.mp4"

# 02 / 3.500-6.500 / 72 frames: start -> diffuse colorless mist -> clean end.
ffmpeg -hide_banner -loglevel error -y -loop 1 -i "$demo_start" -loop 1 -i "$demo_spray" -loop 1 -i "$demo_end" \
  -filter_complex "[0:v]scale=1080:1920,fps=24,settb=AVTB,trim=duration=1.25,setpts=PTS-STARTPTS[d0];[1:v]scale=1080:1920,fps=24,settb=AVTB,trim=duration=1.25,setpts=PTS-STARTPTS[d1];[2:v]scale=1080:1920,fps=24,settb=AVTB,trim=duration=1.25,setpts=PTS-STARTPTS[d2];[d0][d1]xfade=transition=fade:duration=0.35:offset=0.90[x1];[x1][d2]xfade=transition=fade:duration=0.35:offset=1.80,trim=duration=3,setpts=PTS-STARTPTS,drawbox=x=85:y=1570:w=910:h=165:color=black@0.42:t=fill,drawtext=fontfile='$font':text='透明细雾  轻轻一喷':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=1615[v]" \
  -map "[v]" -an -frames:v 72 "${video_args[@]}" "$work/02-demonstration.mp4"

# 03 / 6.500-9.000 / 60 frames: natural relief rather than exaggerated excitement.
ffmpeg -hide_banner -loglevel error -y -i "$bridge" \
  -vf "trim=start_frame=0:end_frame=60,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=245:y=1580:w=590:h=145:color=black@0.40:t=fill,drawtext=fontfile='$font':text='清爽舒适':fontcolor=white:fontsize=70:x=(w-text_w)/2:y=1612" \
  -an -frames:v 60 "${video_args[@]}" "$work/03-result.mp4"

# 04 / 9.000-11.667 / 64 frames: the elder approaches and she no longer withdraws.
ffmpeg -hide_banner -loglevel error -y -i "$bridge" \
  -vf "trim=start_frame=60:end_frame=124,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=120:y=1580:w=840:h=130:color=black@0.35:t=fill,drawtext=fontfile='$font':text='靠近，也不用下意识躲开':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=1610" \
  -an -frames:v 64 "${video_args[@]}" "$work/04-social.mp4"

# 05 / 11.667-15.667 / 96 frames: truthful native dialogue, compressed to four seconds.
ffmpeg -hide_banner -loglevel error -y -i "$dialogue" \
  -vf "trim=start_frame=0:end_frame=96,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=85:y=1480:w=910:h=245:color=black@0.52:t=fill,drawtext=fontfile='$font':text='姑娘，喷的什么？':fontcolor=white:fontsize=54:x=(w-text_w)/2:y=1515:enable='lt(t,1.42)',drawtext=fontfile='$font':text='青颜抑汗净味喷雾':fontcolor=0xFFD83D:fontsize=54:x=(w-text_w)/2:y=1610:enable='gte(t,1.42)'" \
  -an -frames:v 96 "${video_args[@]}" "$work/05-dialogue.mp4"

# 06 / 15.667-19.667 / 96 frames: close social benefit.
ffmpeg -hide_banner -loglevel error -y -i "$leave" \
  -vf "trim=start_frame=0:end_frame=96,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=145:y=1570:w=790:h=150:color=black@0.38:t=fill,drawtext=fontfile='$font':text='近距离社交，更从容':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=1607" \
  -an -frames:v 96 "${video_args[@]}" "$work/06-walk.mp4"

# 07 / 19.667-25.000 / 128 frames: exact product hero.
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "color=c=0xF8F4E8:s=1080x1920:r=24:d=5.333334" -loop 1 -i "$packshot" \
  -filter_complex "[0:v]drawbox=x=0:y=0:w=1080:h=250:color=0xF5CE21:t=fill,drawtext=fontfile='$font':text='青颜':fontcolor=0x202020:fontsize=96:x=(w-text_w)/2:y=65,drawtext=fontfile='$font':text='氯化羟铝抑汗净味喷雾':fontcolor=0x202020:fontsize=50:x=(w-text_w)/2:y=1320,drawtext=fontfile='$font':text='抑汗｜净味':fontcolor=0x202020:fontsize=66:x=(w-text_w)/2:y=1435[bg];[1:v]scale=850:850[product];[bg][product]overlay=115:350:shortest=1[v]" \
  -map "[v]" -an -frames:v 128 "${video_args[@]}" "$work/07-hero.mp4"

# 08 / 25.000-30.000 / 120 frames: direct-response close, without unsupported promises.
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "color=c=0x1F1F1F:s=1080x1920:r=24:d=5" -loop 1 -i "$packshot" \
  -filter_complex "[0:v]drawbox=x=0:y=0:w=1080:h=220:color=0xF5CE21:t=fill,drawtext=fontfile='$font':text='近距离，更从容':fontcolor=0x202020:fontsize=76:x=(w-text_w)/2:y=72,drawtext=fontfile='$font':text='青颜 氯化羟铝抑汗净味喷雾':fontcolor=white:fontsize=46:x=(w-text_w)/2:y=1220,drawbox=x=210:y=1425:w=660:h=150:color=0xF5CE21:t=fill,drawtext=fontfile='$font':text='点击了解青颜':fontcolor=0x202020:fontsize=64:x=(w-text_w)/2:y=1463[bg];[1:v]scale=780:780[product];[bg][product]overlay=150:330:shortest=1[v]" \
  -map "[v]" -an -frames:v 120 "${video_args[@]}" "$work/08-cta.mp4"

# Picture lock: exactly 720 frames.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/00-hook.mp4" -i "$work/01-product-intro.mp4" -i "$work/02-demonstration.mp4" \
  -i "$work/03-result.mp4" -i "$work/04-social.mp4" -i "$work/05-dialogue.mp4" \
  -i "$work/06-walk.mp4" -i "$work/07-hero.mp4" -i "$work/08-cta.mp4" \
  -filter_complex "[0:v][1:v][2:v][3:v][4:v][5:v][6:v][7:v][8:v]concat=n=9:v=1:a=0[v]" \
  -map "[v]" -an -frames:v 720 "${video_args[@]}" "$work/picture-locked-v11.mp4"

# Deterministic soft spray foley: short filtered pink noise, not source dialogue.
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "anoisesrc=color=pink:duration=0.58:amplitude=0.16:r=48000" \
  -af "highpass=f=1000,lowpass=f=9500,afade=t=in:st=0:d=0.04,afade=t=out:st=0.38:d=0.20" \
  -ar 48000 -ac 2 "$audio/soft-spray.wav"

# BGM + SFX mix. The BGM ducks beneath the truthful four-second native dialogue.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-locked-v11.mp4" -i "$audio/bgm-tech-house.mp3" -i "$audio/cloth-hook.mp3" \
  -i "$audio/cap-click.mp3" -i "$audio/soft-spray.wav" -i "$audio/sweep-fast-small.mp3" \
  -i "$audio/sparkle-touch.mp3" -i "$dialogue" \
  -filter_complex "[1:a]asplit=3[b0][b1][b2];[b0]atrim=0:11.55,asetpts=PTS-STARTPTS,volume=0.105,afade=t=in:st=0:d=0.15,afade=t=out:st=11.25:d=0.30[bgm0];[b1]atrim=11.25:16.05,asetpts=PTS-STARTPTS,volume=0.055,afade=t=in:st=0:d=0.30,afade=t=out:st=4.50:d=0.30,adelay=11250|11250[bgm1];[b2]atrim=15.75:30,asetpts=PTS-STARTPTS,volume=0.105,afade=t=in:st=0:d=0.30,afade=t=out:st=13.25:d=1.0,adelay=15750|15750[bgm2];[2:a]atrim=0:0.70,asetpts=PTS-STARTPTS,volume=0.32,adelay=50|50[cloth];[3:a]atrim=0:0.45,asetpts=PTS-STARTPTS,volume=0.36,adelay=2450|2450[cap];[4:a]asetpts=PTS-STARTPTS,volume=0.88,adelay=4250|4250[spray];[5:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.18,adelay=6420|6420[lift];[6:a]atrim=0:1.0,asetpts=PTS-STARTPTS,volume=0.11,adelay=25000|25000[sting];[7:a]atrim=0:4,asetpts=PTS-STARTPTS,highpass=f=110,lowpass=f=9000,afftdn=nf=-28,afade=t=in:st=0:d=0.05,afade=t=out:st=3.75:d=0.25,loudnorm=I=-18:LRA=8:TP=-2,adelay=11667|11667[dialogue];[bgm0][bgm1][bgm2][cloth][cap][spray][lift][sting][dialogue]amix=inputs=9:duration=longest:dropout_transition=0,acompressor=threshold=0.12:ratio=2.5:attack=12:release=160:makeup=1.6,loudnorm=I=-13.5:LRA=7:TP=-3.5,alimiter=limit=0.68:attack=5:release=80:level=false[a]" \
  -map 0:v:0 -map "[a]" -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 -t 30 -movflags +faststart \
  "$final/青颜_苗家腋下止汗转化广告_30s_9x16_v11.mp4"

# No-BGM review variant retains the same dialogue and SFX contract.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-locked-v11.mp4" -i "$audio/cloth-hook.mp3" -i "$audio/cap-click.mp3" \
  -i "$audio/soft-spray.wav" -i "$audio/sweep-fast-small.mp3" -i "$audio/sparkle-touch.mp3" \
  -i "$dialogue" \
  -filter_complex "[1:a]atrim=0:0.70,asetpts=PTS-STARTPTS,volume=0.32,adelay=50|50[cloth];[2:a]atrim=0:0.45,asetpts=PTS-STARTPTS,volume=0.36,adelay=2450|2450[cap];[3:a]asetpts=PTS-STARTPTS,volume=0.88,adelay=4250|4250[spray];[4:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.18,adelay=6420|6420[lift];[5:a]atrim=0:1.0,asetpts=PTS-STARTPTS,volume=0.11,adelay=25000|25000[sting];[6:a]atrim=0:4,asetpts=PTS-STARTPTS,highpass=f=110,lowpass=f=9000,afftdn=nf=-28,afade=t=in:st=0:d=0.05,afade=t=out:st=3.75:d=0.25,loudnorm=I=-18:LRA=8:TP=-2,adelay=11667|11667[dialogue];[cloth][cap][spray][lift][sting][dialogue]amix=inputs=6:duration=longest:dropout_transition=0,acompressor=threshold=0.10:ratio=2.2:attack=12:release=160:makeup=1.5,loudnorm=I=-16:LRA=8:TP=-1.5,apad,atrim=0:30[a]" \
  -map 0:v:0 -map "[a]" -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 -t 30 -movflags +faststart \
  "$final/青颜_苗家腋下止汗转化广告_30s_9x16_v11_no-bgm.mp4"
