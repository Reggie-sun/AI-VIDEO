#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime="$task_root/runtime/t8_portrait_ad"
assets="$task_root/assets"
work="$task_root/work"
final="$task_root/final"
review="$task_root/review/final"
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
bgm="$assets/house-vibez.mp3"
whoosh="$assets/sweep-fast-small.mp3"
chime="$assets/chime-crystal.mp3"
packshot="$assets/product-packshot.jpg"
fluid="$assets/04-golden-fluid.png"
spoken="$runtime/03_spoken_recommendation.mp4"
output="$final/青颜_苗家女孩T8硬切顺滑广告_30s_9x16_v7.mp4"

mkdir -p "$work" "$final" "$review"

video_args=(-r 24 -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)
portrait="crop=756:1344:6:0,scale=1080:1920:flags=lanczos"
brand="drawtext=fontfile=${font}:text='青颜':fontcolor=white:fontsize=38:x=66:y=64:shadowcolor=black@0.72:shadowx=2:shadowy=2"

# SHOT 01 | No transition effect: the next Shot begins on a direct cut.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/01_concern.mp4" \
  -filter_complex "[0:v]trim=start_frame=8:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=62:y=1360:w=8:h=224:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='汗湿黏腻？':fontcolor=white:fontsize=74:x=96:y=1370:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='靠近不自在？':fontcolor=white:fontsize=70:x=96:y=1475:shadowcolor=black@0.85:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 48 "${video_args[@]}" "$work/01-concern.mp4"

# SHOT 02 | Remove the six-frame still start. The generated hand-held bottle is the only product.
ffmpeg -hide_banner -loglevel error -y \
  -i "$spoken" \
  -filter_complex "[0:v]trim=start_frame=6:end_frame=124,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=54:y=1375:w=820:h=230:color=0x171717@0.78:t=fill,drawtext=fontfile=${font}:text='出门前用青颜，':fontcolor=white:fontsize=60:x=84:y=1410,drawtext=fontfile=${font}:text='抑汗净味，清爽舒适。':fontcolor=0xFFE156:fontsize=54:x=84:y=1500[v]" \
  -map '[v]' -an -frames:v 118 "${video_args[@]}" "$work/02-spoken-presenter.mp4"

# SHOT 03 | Direct outdoor cut after dialogue.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/04_walk_forward.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=76:x=96:y=1450:shadowcolor=black@0.84:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='步步从容':fontcolor=white:fontsize=76:x=96:y=1550:shadowcolor=black@0.84:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/03-walk-forward.mp4"

# SHOT 04 | Starts from a closely matching walking pose; no dissolve or flash.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_walk_smile.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawtext=fontfile=${font}:text='轻盈出发':fontcolor=white:fontsize=76:x=96:y=1450:shadowcolor=black@0.84:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='从容靠近':fontcolor=white:fontsize=76:x=96:y=1550:shadowcolor=black@0.84:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/04-walk-smile.mp4"

# SHOT 05 | Initial still hold removed; direct social cut.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_social_turn.mp4" \
  -filter_complex "[0:v]trim=start_frame=8:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=62:y=1390:w=800:h=185:color=white@0.90:t=fill,drawtext=fontfile=${font}:text='近距离社交，更从容':fontcolor=0x171717:fontsize=64:x=94:y=1434[v]" \
  -map '[v]' -an -frames:v 48 "${video_args[@]}" "$work/05-social-turn.mp4"

# SHOT 06 | Image-free bridge. No product, fluid image, moving band, or transition flash.
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "color=c=0xFFFBF2:s=1080x1920:r=24:d=2.416667" \
  -filter_complex "[0:v]drawtext=fontfile=${font}:text='通勤 · 出游 · 约会':fontcolor=0x55554C:fontsize=58:x=(w-text_w)/2:y=760,drawtext=fontfile=${font}:text='自在切换':fontcolor=0x171717:fontsize=96:x=(w-text_w)/2:y=900:enable='gte(t,0.50)'[v]" \
  -map '[v]' -an -frames:v 58 "${video_args[@]}" "$work/06-lifestyle-copy.mp4"

# SHOT 07 | Golden-fluid visual appears once. The background is pixel-stable.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$fluid" \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,drawbox=x=70:y=170:w=940:h=470:color=white@0.88:t=fill,drawtext=fontfile=${font}:text='帮助减少汗湿困扰':fontcolor=0x171717:fontsize=68:x=110:y=270,drawtext=fontfile=${font}:text='保持清爽自在':fontcolor=0x4A4A40:fontsize=58:x=112:y=405:enable='gte(t,0.60)'[v]" \
  -map '[v]' -an -frames:v 168 "${video_args[@]}" "$work/07-golden-fluid-benefit.mp4"

# SHOT 08 | Source packshot appears once and owns the final closure. No yellow band behind it.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$packshot" \
  -f lavfi -i "color=c=0xFFFCF6:s=1080x1920:r=24:d=7" \
  -filter_complex "[0:v]scale=960:960:flags=lanczos[pack];[1:v][pack]overlay=60:170[hero];[hero]drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=104:x=(w-text_w)/2:y=1230:enable='gte(t,0.40)',drawtext=fontfile=${font}:text='氯化羟铝抑汗净味喷雾':fontcolor=0x4A4A40:fontsize=52:x=(w-text_w)/2:y=1385:enable='gte(t,0.80)',drawtext=fontfile=${font}:text='出门前，用青颜':fontcolor=0x171717:fontsize=68:x=(w-text_w)/2:y=1540:enable='gte(t,1.25)'[v]" \
  -map '[v]' -an -frames:v 168 "${video_args[@]}" "$work/08-product-hero-close.mp4"

printf '%s\n' \
  "file '$work/01-concern.mp4'" \
  "file '$work/02-spoken-presenter.mp4'" \
  "file '$work/03-walk-forward.mp4'" \
  "file '$work/04-walk-smile.mp4'" \
  "file '$work/05-social-turn.mp4'" \
  "file '$work/06-lifestyle-copy.mp4'" \
  "file '$work/07-golden-fluid-benefit.mp4'" \
  "file '$work/08-product-hero-close.mp4'" > "$work/concat.txt"

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$work/concat.txt" \
  -vf 'fps=24' -an -frames:v 720 -r 24 -c:v libx264 -preset slow -crf 16 \
  -pix_fmt yuv420p -movflags +faststart "$work/picture-track.mp4"

# BGM provides continuity across hard cuts. Only the final benefit and product pair get subtle cues.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -stream_loop -1 -i "$bgm" -i "$spoken" \
  -i "$whoosh" -i "$chime" \
  -filter_complex "[1:a]atrim=0:30,asetpts=PTS-STARTPTS,volume=0.11,afade=t=in:st=0:d=0.5,afade=t=out:st=28.5:d=1.5[bgm];[2:a]atrim=start=0.25:end=5.166667,asetpts=PTS-STARTPTS,highpass=f=90,acompressor=threshold=0.16:ratio=2.5:attack=8:release=140:makeup=1.25,volume=1.08,adelay=2000|2000[voice];[3:a]atrim=0:0.4,asetpts=PTS-STARTPTS,volume=0.08,adelay=16000|16000[benefit_cue];[4:a]atrim=0:1.5,asetpts=PTS-STARTPTS,volume=0.14,adelay=23000|23000[hero_cue];[bgm][voice][benefit_cue][hero_cue]amix=inputs=4:duration=longest,volume=3.5,alimiter=limit=0.92[a]" \
  -map 0:v -map '[a]' -t 30 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家女孩T8硬切顺滑广告_30s_9x16_v7.sha256"

ffmpeg -hide_banner -loglevel error -y -i "$output" \
  -vf 'fps=1,scale=270:-1,tile=6x5' -frames:v 1 "$review/contact.jpg"

ffprobe -v error \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,duration \
  -show_entries format=duration,size,bit_rate \
  -of json "$output" > "$review/ffprobe.json"

echo "$output"
