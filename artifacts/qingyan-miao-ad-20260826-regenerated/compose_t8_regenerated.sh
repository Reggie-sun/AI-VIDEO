#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime="$task_root/runtime/t8_portrait_ad"
source_assets="$task_root/../qingyan-miao-ad-20260825/assets"
work="$task_root/work"
final="$task_root/final"
review="$task_root/review/final"
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
bgm="$source_assets/house-vibez.mp3"
whoosh="$source_assets/sweep-fast-small.mp3"
fluid_sfx="$source_assets/water-bubble.mp3"
chime="$source_assets/chime-crystal.mp3"
packshot="$source_assets/product-packshot.jpg"
fluid="$source_assets/04-golden-fluid.png"
output="$final/青颜_苗家女孩T8动态广告_重新生成_28s_9x16.mp4"

mkdir -p "$work" "$final" "$review"

video_args=(-r 24 -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)
brand="drawtext=fontfile=${font}:text='青颜 氯化羟铝抑汗净味喷雾':fontcolor=white:fontsize=32:x=64:y=62:shadowcolor=black@0.70:shadowx=2:shadowy=2,drawbox=x=64:y=108:w=92:h=5:color=0xF5CE00:t=fill"
portrait="crop=756:1344:6:0,scale=1080:1920:flags=lanczos"

# 60 frames / 2.5 s: restrained pain-point hook.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/01_concern.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=0.166667,trim=duration=2.5,${brand},drawbox=x=62:y=1360:w=8:h=224:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='汗湿黏腻？':fontcolor=white:fontsize=74:x=96:y=1370:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='异味尴尬？':fontcolor=white:fontsize=74:x=96:y=1470:shadowcolor=black@0.85:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 60 "${video_args[@]}" "$work/01-hook.mp4"

# 60 frames / 2.5 s: dynamic product lift.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/02_product_lift.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=0.166667,trim=duration=2.5,${brand},drawbox=x=72:y=1410:w=720:h=150:color=0xF5CE00@0.92:t=fill,drawtext=fontfile=${font}:text='出门前，先用青颜':fontcolor=0x161616:fontsize=68:x=102:y=1445[v]" \
  -map '[v]' -an -frames:v 60 "${video_args[@]}" "$work/02-product-lift.mp4"

# 60 frames / 2.5 s: clean pre-use implication, no generated spray claim.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/03_preuse_hint.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=0.166667,trim=duration=2.5,${brand},drawbox=x=62:y=1400:w=760:h=145:color=white@0.88:t=fill,drawtext=fontfile=${font}:text='轻轻一用，清爽出发':fontcolor=0x171717:fontsize=63:x=96:y=1438[v]" \
  -map '[v]' -an -frames:v 60 "${video_args[@]}" "$work/03-preuse.mp4"

# 72 frames / 3 s: exact source packshot for readable packaging truth.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 3 -i "$packshot" \
  -filter_complex "color=c=0xFFFBF0:s=1080x1920:r=24:d=3[bg];[0:v]scale=1000:1000[pack];[bg][pack]overlay=40:210,drawtext=fontfile=${font}:text='青颜抑汗净味喷雾':fontcolor=0x171717:fontsize=76:x=(w-text_w)/2:y=1280,drawtext=fontfile=${font}:text='黄色包装 · 白色瓶盖':fontcolor=0x4A4A40:fontsize=46:x=(w-text_w)/2:y=1390,drawbox=x=350:y=1490:w=380:h=7:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 72 "${video_args[@]}" "$work/04-packshot.mp4"

# 84 frames / 3.5 s: restrained benefit visualization.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 3.5 -i "$fluid" \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1+0.00038*on,1.034)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=24,drawtext=fontfile=${font}:text='抑汗净味':fontcolor=0x171717:fontsize=84:x=80:y=215,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x171717:fontsize=84:x=80:y=330,drawtext=fontfile=${font}:text='帮助减少汗湿困扰':fontcolor=0x4A4A40:fontsize=50:x=84:y=470,drawbox=x=82:y=550:w=330:h=7:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 84 "${video_args[@]}" "$work/05-benefit.mp4"

# 56 frames / 2.334 s: validated outdoor walking motion.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/04_walk_forward.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=64:y=1430:w=8:h=190:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=78:x=96:y=1440:shadowcolor=black@0.82:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='步步从容':fontcolor=white:fontsize=78:x=96:y=1540:shadowcolor=black@0.82:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/06-walk.mp4"

# 56 frames / 2.334 s: validated social turn.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_social_turn.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=60:y=1420:w=790:h=145:color=white@0.88:t=fill,drawtext=fontfile=${font}:text='近距离社交，更从容':fontcolor=0x171717:fontsize=63:x=92:y=1458[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/07-social.mp4"

# 80 frames / 3.334 s: scenario recall with exact product pixels.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 3.334 -i "$packshot" \
  -filter_complex "color=c=0xFFF8DD:s=1080x1920:r=24:d=3.334[bg];[0:v]scale=820:820[pack];[bg][pack]overlay=130:230,drawtext=fontfile=${font}:text='通勤 · 出游':fontcolor=0x171717:fontsize=64:x=(w-text_w)/2:y=1170,drawtext=fontfile=${font}:text='运动 · 约会':fontcolor=0x171717:fontsize=64:x=(w-text_w)/2:y=1270,drawtext=fontfile=${font}:text='都能自在一点':fontcolor=0x4A4A40:fontsize=50:x=(w-text_w)/2:y=1400,drawbox=x=390:y=1500:w=300:h=8:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 80 "${video_args[@]}" "$work/08-scenarios.mp4"

# 96 frames / 4 s: product hero.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 4 -i "$packshot" \
  -filter_complex "color=c=0xFFFBF0:s=1080x1920:r=24:d=4[bg];[0:v]scale=940:940[pack];[bg][pack]overlay=70:220,drawtext=fontfile=${font}:text='青颜抑汗净味喷雾':fontcolor=0x171717:fontsize=73:x=(w-text_w)/2:y=1260,drawtext=fontfile=${font}:text='清爽舒适 · 自信靠近':fontcolor=0x4A4A40:fontsize=49:x=(w-text_w)/2:y=1380,drawbox=x=365:y=1480:w=350:h=8:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 96 "${video_args[@]}" "$work/09-hero.mp4"

# 48 frames / 2 s: compact end card inside portrait UI-safe margins.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_social_turn.mp4" \
  -loop 1 -framerate 24 -t 2 -i "$packshot" \
  -filter_complex "[0:v]trim=start_frame=8:end_frame=56,setpts=PTS-STARTPTS,${portrait},boxblur=12:2,eq=brightness=-0.10:saturation=0.78[bg];[1:v]scale=570:570[pack];[bg]drawbox=x=230:y=740:w=620:h=760:color=white@0.94:t=fill[card];[card][pack]overlay=255:770,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=78:x=70:y=250:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='自信不用藏':fontcolor=white:fontsize=78:x=70:y=360:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawbox=x=72:y=480:w=300:h=8:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=72:x=(w-text_w)/2:y=1375[v]" \
  -map '[v]' -an -frames:v 48 "${video_args[@]}" "$work/10-close.mp4"

printf '%s\n' \
  "file '$work/01-hook.mp4'" \
  "file '$work/02-product-lift.mp4'" \
  "file '$work/03-preuse.mp4'" \
  "file '$work/04-packshot.mp4'" \
  "file '$work/05-benefit.mp4'" \
  "file '$work/06-walk.mp4'" \
  "file '$work/07-social.mp4'" \
  "file '$work/08-scenarios.mp4'" \
  "file '$work/09-hero.mp4'" \
  "file '$work/10-close.mp4'" > "$work/concat.txt"

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$work/concat.txt" \
  -vf 'fps=24' -an -frames:v 672 -r 24 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
  -movflags +faststart "$work/picture-track.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -stream_loop -1 -i "$bgm" \
  -i "$whoosh" -i "$fluid_sfx" -i "$chime" \
  -filter_complex "[1:a]atrim=0:28,asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=0.5,afade=t=out:st=26.7:d=1.3[bgm];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.30,adelay=2500|2500[w1];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.27,adelay=5000|5000[w2];[3:a]atrim=0:1.4,asetpts=PTS-STARTPTS,volume=0.20,adelay=10500|10500[fluid];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.24,adelay=14000|14000[w3];[4:a]atrim=0:1.7,asetpts=PTS-STARTPTS,volume=0.30,adelay=22000|22000[chime];[bgm][w1][w2][fluid][w3][chime]amix=inputs=6:duration=longest,volume=3.5,alimiter=limit=0.90[a]" \
  -map 0:v -map '[a]' -t 28 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家女孩T8动态广告_重新生成_28s_9x16.sha256"

ffmpeg -hide_banner -loglevel error -y -i "$output" \
  -vf 'fps=1,scale=270:-1,tile=7x4' -frames:v 1 "$review/contact.jpg"

ffprobe -v error \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,duration \
  -show_entries format=duration,size,bit_rate \
  -of json "$output" > "$review/ffprobe.json"

ffmpeg -hide_banner -i "$output" -af volumedetect -f null - \
  2> "$review/volumedetect.txt" || true

echo "$output"
