#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime="$task_root/runtime/t8_portrait_ad"
assets="$task_root/assets"
work="$task_root/work"
final="$task_root/final"
review="$task_root/review/final"
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
shot1="$runtime/01_underarm_deodorizing_repair.mp4"
shot2="$runtime/02_elder_dialogue_repair.mp4"
shot3="$runtime/03_leave_together.mp4"
fluid="$assets/04-golden-fluid.png"
packshot="$assets/product-packshot.jpg"
bgm="$assets/house-vibez.mp3"
whoosh="$assets/sweep-fast-small.mp3"
chime="$assets/chime-crystal.mp3"
output="$final/青颜_苗家双人腋下止汗对话广告_30s_9x16_v8.mp4"

mkdir -p "$work" "$final" "$review"

video_args=(-r 24 -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)
portrait="crop=756:1344:6:0,scale=1080:1920:flags=lanczos"

# Shot 01: one continuous T8 clip; no product overlay or transition effect.
ffmpeg -hide_banner -loglevel error -y -i "$shot1" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=175,setpts=PTS-STARTPTS,${portrait},drawbox=x=64:y=1510:w=760:h=176:color=0x121212@0.72:t=fill,drawtext=fontfile=${font}:text='汗湿异味？一喷散开':fontcolor=white:fontsize=62:x=96:y=1558[v]" \
  -map '[v]' -an -frames:v 175 "${video_args[@]}" "$work/01-underarm-deodorizing.mp4"

# Shot 02: the only promotional dialogue window. Captions follow measured ASR boundaries.
ffmpeg -hide_banner -loglevel error -y -i "$shot2" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=155,setpts=PTS-STARTPTS,${portrait},drawbox=x=50:y=1490:w=980:h=250:color=0x121212@0.74:t=fill:enable='between(t,0,6.2)',drawtext=fontfile=${font}:text='阿婆：姑娘，喷的什么？':fontcolor=white:fontsize=54:x=82:y=1542:enable='between(t,0,1.68)',drawtext=fontfile=${font}:text='女孩：青颜抑汗净味喷雾':fontcolor=0xFFE156:fontsize=50:x=82:y=1522:enable='between(t,1.68,4.74)',drawtext=fontfile=${font}:text='清爽舒适':fontcolor=white:fontsize=58:x=82:y=1605:enable='between(t,1.68,4.74)',drawtext=fontfile=${font}:text='阿婆：难怪这么自在':fontcolor=white:fontsize=56:x=82:y=1542:enable='between(t,4.74,6.20)'[v]" \
  -map '[v]' -an -frames:v 155 "${video_args[@]}" "$work/02-elder-dialogue.mp4"

# Shot 03: optical retime of one continuous T8 walk to avoid introducing another generated seam.
ffmpeg -hide_banner -loglevel error -y -i "$shot3" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=175,setpts=PTS-STARTPTS,minterpolate=fps=72:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,setpts=(269.0/174.0)*PTS,fps=24,${portrait},drawtext=fontfile=${font}:text='一起出门，靠近也自在':fontcolor=white:fontsize=62:x=(w-text_w)/2:y=1540:shadowcolor=black@0.82:shadowx=3:shadowy=3:enable='between(t,1.0,7.0)',drawtext=fontfile=${font}:text='通勤 · 出游 · 约会':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=1540:shadowcolor=black@0.82:shadowx=3:shadowy=3:enable='between(t,7.0,11.15)'[v]" \
  -map '[v]' -an -frames:v 270 "${video_args[@]}" "$work/03-leave-together.mp4"

# Shot 04: the benefit visual appears once and remains pixel-stable for exactly 2.5s.
ffmpeg -hide_banner -loglevel error -y -loop 1 -framerate 24 -i "$fluid" \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,drawbox=x=70:y=170:w=940:h=390:color=white@0.88:t=fill,drawtext=fontfile=${font}:text='帮助减少汗湿困扰':fontcolor=0x171717:fontsize=68:x=110:y=260,drawtext=fontfile=${font}:text='保持清爽自在':fontcolor=0x4A4A40:fontsize=58:x=112:y=395[v]" \
  -map '[v]' -an -frames:v 60 "${video_args[@]}" "$work/04-golden-fluid-benefit.mp4"

# Shot 05: source packshot appears once and remains pixel-stable for exactly 2.5s. No yellow band.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$packshot" \
  -f lavfi -i "color=c=0xFFFCF6:s=1080x1920:r=24:d=2.5" \
  -filter_complex "[0:v]scale=960:960:flags=lanczos[pack];[1:v][pack]overlay=60:160[hero];[hero]drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=104:x=(w-text_w)/2:y=1240,drawtext=fontfile=${font}:text='氯化羟铝抑汗净味喷雾':fontcolor=0x4A4A40:fontsize=52:x=(w-text_w)/2:y=1390,drawtext=fontfile=${font}:text='清爽自信，不用藏':fontcolor=0x171717:fontsize=68:x=(w-text_w)/2:y=1545[v]" \
  -map '[v]' -an -frames:v 60 "${video_args[@]}" "$work/05-product-hero.mp4"

printf '%s\n' \
  "file '$work/01-underarm-deodorizing.mp4'" \
  "file '$work/02-elder-dialogue.mp4'" \
  "file '$work/03-leave-together.mp4'" \
  "file '$work/04-golden-fluid-benefit.mp4'" \
  "file '$work/05-product-hero.mp4'" > "$work/concat.txt"

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$work/concat.txt" \
  -vf 'fps=24' -an -frames:v 720 -r 24 -c:v libx264 -preset slow -crf 16 \
  -pix_fmt yuv420p -movflags +faststart "$work/picture-track.mp4"

# Only Shot 01/02 native audio is used. Shot 03 native audio is discarded; continuous BGM bridges hard cuts.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -i "$shot1" -i "$shot2" -stream_loop -1 -i "$bgm" \
  -i "$whoosh" -i "$chime" \
  -filter_complex "[1:a]atrim=0:7.291667,asetpts=PTS-STARTPTS,volume=0.82,afade=t=out:st=7.16:d=0.13[a1];[2:a]atrim=0:6.458333,asetpts=PTS-STARTPTS,volume=1.05,adelay=7292|7292[a2];[3:a]atrim=0:30,asetpts=PTS-STARTPTS,volume=0.05,afade=t=in:st=0:d=0.4,afade=t=out:st=28.8:d=1.2[bgm];[4:a]atrim=0:0.40,asetpts=PTS-STARTPTS,volume=0.07,adelay=25000|25000[sweep];[5:a]atrim=0:1.50,asetpts=PTS-STARTPTS,volume=0.12,adelay=27500|27500[chime];[a1][a2][bgm][sweep][chime]amix=inputs=5:duration=longest:dropout_transition=0,volume=1.8,alimiter=limit=0.92[a]" \
  -map 0:v -map '[a]' -t 30 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家双人腋下止汗对话广告_30s_9x16_v8.sha256"
echo "$output"
