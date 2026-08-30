#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$task_root/../.." && pwd)"
v10="$repo_root/artifacts/qingyan-miao-ad-20260826-v10"
v8="$repo_root/artifacts/qingyan-miao-ad-20260826-v8"
assets="$task_root/assets"
audio="$task_root/audio"
segments="$task_root/segments"
final="$task_root/final"
font="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

problem="$v10/runtime/t8_portrait_ad/00_problem_discovery_sniff_recoil_v2.mp4"
dialogue="$v8/runtime/t8_portrait_ad/02_elder_dialogue_repair.mp4"
treatment="$v10/runtime/t8_portrait_ad/01_problem_open_cap_spray.mp4"
bridge="$v10/runtime/t8_portrait_ad/01_recap_elder_enters_v2.mp4"
leave="$v8/runtime/t8_portrait_ad/03_leave_together.mp4"
packshot="$assets/product-packshot.jpg"

mkdir -p "$segments" "$final"

video_args=(-c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -r 24 -g 48 -movflags +faststart)

# Rebuild one recommendation line from already accepted native dialogue:
# elder address + one lower-pitched product phrase. No new voice or Provider call.
ffmpeg -hide_banner -loglevel error -y -i "$dialogue" -i "$audio/product-line-source.wav" \
  -filter_complex "[0:a]atrim=0.04:0.42,asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:st=0:d=0.02,afade=t=out:st=0.34:d=0.04[address];[1:a]asetrate=44160,aresample=48000,atempo=1.0869565,highpass=f=95,lowpass=f=8500,volume=1.05,afade=t=in:st=0:d=0.02,afade=t=out:st=2.20:d=0.06[product];[address][product]concat=n=2:v=0:a=1,apad,atrim=0:2.75,loudnorm=I=-18:LRA=7:TP=-2[a]" \
  -map "[a]" -ar 48000 -ac 2 "$audio/elder-recommendation.wav"

# 00 / 0.000-4.500 / 108 frames: make the problem readable and audible.
ffmpeg -hide_banner -loglevel error -y -i "$problem" \
  -vf "trim=start_frame=0:end_frame=108,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=70:y=115:w=940:h=250:color=black@0.52:t=fill,drawtext=fontfile='$font':text='汗湿黏腻？':fontcolor=white:fontsize=76:x=(w-text_w)/2:y=145,drawtext=fontfile='$font':text='一靠近，就下意识躲开':fontcolor=0xFFD83D:fontsize=52:x=(w-text_w)/2:y=255" \
  -an -frames:v 108 "${video_args[@]}" "$segments/00-problem.mp4"

# 01 / 4.500-7.250 / 66 frames: elder recommends before any spray action.
ffmpeg -hide_banner -loglevel error -y -i "$dialogue" \
  -vf "trim=start_frame=109:end_frame=175,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=70:y=1450:w=940:h=300:color=black@0.54:t=fill,drawtext=fontfile='$font':text='老人推荐':fontcolor=0xFFD83D:fontsize=44:x=(w-text_w)/2:y=1482,drawtext=fontfile='$font':text='姑娘，试试青颜':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=1555,drawtext=fontfile='$font':text='抑汗净味，清爽舒适':fontcolor=white:fontsize=54:x=(w-text_w)/2:y=1645" \
  -an -frames:v 66 "${video_args[@]}" "$segments/01-elder-recommends.mp4"

# 02 / 7.250-13.250 / 144 frames: one continuous open-cap-and-spray shot.
# The source's frozen tail is deliberately excluded.
ffmpeg -hide_banner -loglevel error -y -i "$treatment" \
  -vf "trim=start_frame=0:end_frame=144,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=105:y=1550:w=870:h=145:color=black@0.38:t=fill:enable='lt(t,5.7)',drawtext=fontfile='$font':text='听她的，旋开喷头':fontcolor=white:fontsize=54:x=(w-text_w)/2:y=1585:enable='lt(t,3.6)',drawtext=fontfile='$font':text='轻轻一喷':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=1580:enable='between(t,3.6,5.7)'" \
  -an -frames:v 144 "${video_args[@]}" "$segments/02-treatment.mp4"

# 03 / 13.250-17.042 / 91 frames: immediate, natural relief in gentle slow motion.
ffmpeg -hide_banner -loglevel error -y -i "$bridge" \
  -vf "trim=start_frame=0:end_frame=60,setpts=(PTS-STARTPTS)*91/60,crop=756:1344:6:0,scale=1080:1920,fps=24,drawbox=x=250:y=1570:w=580:h=145:color=black@0.40:t=fill,drawtext=fontfile='$font':text='清爽舒适':fontcolor=white:fontsize=70:x=(w-text_w)/2:y=1602" \
  -an -frames:v 91 "${video_args[@]}" "$segments/03-result.mp4"

# 04 / 17.042-24.333 / 175 frames: continuous social proof; 22s stays inside this shot.
ffmpeg -hide_banner -loglevel error -y -i "$leave" \
  -vf "trim=start_frame=0:end_frame=175,setpts=PTS-STARTPTS,crop=756:1344:6:0,scale=1080:1920,drawbox=x=185:y=1570:w=710:h=145:color=black@0.34:t=fill:enable='between(t,0.7,3.4)',drawtext=fontfile='$font':text='靠近，也更自在':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=1604:enable='between(t,0.7,3.4)'" \
  -an -frames:v 175 "${video_args[@]}" "$segments/04-walk.mp4"

# 05 / 24.333-30.000 / 136 frames: one moving hero, replacing two static cards.
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "color=c=0x1F1F1F:s=1080x1920:r=24:d=5.666667" -loop 1 -i "$packshot" \
  -filter_complex "[0:v]drawbox=x=0:y=0:w=1080:h=255:color=0xF5CE21:t=fill,drawtext=fontfile='$font':text='青颜':fontcolor=0x202020:fontsize=100:x=(w-text_w)/2:y=62,drawtext=fontfile='$font':text='氯化羟铝抑汗净味喷雾':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=1360,drawtext=fontfile='$font':text='抑汗｜净味':fontcolor=0xFFD83D:fontsize=70:x=(w-text_w)/2:y=1475[bg];[1:v]scale=870:870,zoompan=z='1.0+0.00055*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=136:s=870x870:fps=24,fade=t=in:st=0:d=0.35[product];[bg][product]overlay=105:330:shortest=1,fade=t=out:st=5.25:d=0.40[v]" \
  -map "[v]" -an -frames:v 136 "${video_args[@]}" "$segments/05-hero.mp4"

# Picture lock: exactly 720 frames, with hard cuts only at motivated action/state changes.
ffmpeg -hide_banner -loglevel error -y \
  -i "$segments/00-problem.mp4" -i "$segments/01-elder-recommends.mp4" \
  -i "$segments/02-treatment.mp4" -i "$segments/03-result.mp4" \
  -i "$segments/04-walk.mp4" -i "$segments/05-hero.mp4" \
  -filter_complex "[0:v][1:v][2:v][3:v][4:v][5:v]concat=n=6:v=1:a=0[v]" \
  -map "[v]" -an -frames:v 720 "${video_args[@]}" "$segments/picture-locked-v12.mp4"

# Full mix: low BGM, one recommendation line, concrete problem/action/result SFX.
ffmpeg -hide_banner -loglevel error -y \
  -i "$segments/picture-locked-v12.mp4" -i "$audio/bgm-tech-house.mp3" \
  -i "$audio/cloth-hook.mp3" -i "$audio/elder-recommendation.wav" \
  -i "$audio/cap-click.mp3" -i "$audio/soft-spray.wav" -i "$audio/sparkle-touch.mp3" \
  -filter_complex "[1:a]atrim=0:30,asetpts=PTS-STARTPTS,volume=0.095,afade=t=in:st=0:d=0.20,afade=t=out:st=29:d=1.0[bgm];[2:a]atrim=0:0.85,asetpts=PTS-STARTPTS,volume=0.48,adelay=80|80[cloth];[3:a]asetpts=PTS-STARTPTS,volume=1.0,adelay=4500|4500[elder];[4:a]atrim=0:0.48,asetpts=PTS-STARTPTS,volume=0.44,adelay=7800|7800[cap];[5:a]asetpts=PTS-STARTPTS,volume=0.95,adelay=11150|11150[spray];[6:a]atrim=0:1.25,asetpts=PTS-STARTPTS,volume=0.16,adelay=13250|13250,asplit=2[spark1][spark2pre];[spark2pre]adelay=11083|11083[spark2];[bgm][cloth][elder][cap][spray][spark1][spark2]amix=inputs=7:duration=longest:dropout_transition=0,acompressor=threshold=0.12:ratio=2.4:attack=12:release=160:makeup=1.5,loudnorm=I=-14:LRA=7:TP=-2.5,alimiter=limit=0.75:attack=5:release=80:level=false,volume=0.80,apad,atrim=0:30[a]" \
  -map 0:v:0 -map "[a]" -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 -t 30 -movflags +faststart \
  "$final/青颜_苗家腋下止汗完整广告_30s_9x16_v12.mp4"

# Review variant without music, retaining dialogue and concrete SFX.
ffmpeg -hide_banner -loglevel error -y \
  -i "$segments/picture-locked-v12.mp4" -i "$audio/cloth-hook.mp3" \
  -i "$audio/elder-recommendation.wav" -i "$audio/cap-click.mp3" \
  -i "$audio/soft-spray.wav" -i "$audio/sparkle-touch.mp3" \
  -filter_complex "[1:a]atrim=0:0.85,asetpts=PTS-STARTPTS,volume=0.48,adelay=80|80[cloth];[2:a]asetpts=PTS-STARTPTS,volume=1.0,adelay=4500|4500[elder];[3:a]atrim=0:0.48,asetpts=PTS-STARTPTS,volume=0.44,adelay=7800|7800[cap];[4:a]asetpts=PTS-STARTPTS,volume=0.95,adelay=11150|11150[spray];[5:a]atrim=0:1.25,asetpts=PTS-STARTPTS,volume=0.16,adelay=13250|13250,asplit=2[spark1][spark2pre];[spark2pre]adelay=11083|11083[spark2];[cloth][elder][cap][spray][spark1][spark2]amix=inputs=6:duration=longest:dropout_transition=0,acompressor=threshold=0.10:ratio=2.2:attack=12:release=160:makeup=1.5,loudnorm=I=-17:LRA=8:TP=-2,volume=0.80,apad,atrim=0:30[a]" \
  -map 0:v:0 -map "[a]" -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 -t 30 -movflags +faststart \
  "$final/青颜_苗家腋下止汗完整广告_30s_9x16_v12_no-bgm.mp4"

sha256sum "$final/青颜_苗家腋下止汗完整广告_30s_9x16_v12.mp4" \
  > "$final/青颜_苗家腋下止汗完整广告_30s_9x16_v12.sha256"
