#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
assets="$task_root/assets"
runtime="$task_root/runtime/t8_portrait_ad"
work="$task_root/work_t8_dynamic"
final="$task_root/final"
review="$task_root/review/t8_dynamic"
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
bgm="$assets/house-vibez.mp3"
whoosh="$assets/sweep-fast-small.mp3"
fluid_sfx="$assets/water-bubble.mp3"
chime="$assets/chime-crystal.mp3"
output="$final/青颜_苗家女孩T8动态广告_28s_9x16.mp4"

mkdir -p "$work" "$final" "$review"

video_args=(-r 24 -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)
brand="drawtext=fontfile=${font}:text='青颜 氯化羟铝抑汗净味喷雾':fontcolor=white:fontsize=32:x=64:y=62:shadowcolor=black@0.70:shadowx=2:shadowy=2,drawbox=x=64:y=108:w=92:h=5:color=0xF5CE00:t=fill"
portrait="crop=756:1344:6:0,scale=1080:1920:flags=lanczos"

ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/01_concern.mp4" \
  -f lavfi -t 3 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=36,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=1.5,${brand},drawbox=x=62:y=1370:w=8:h=224:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='汗湿黏腻？':fontcolor=white:fontsize=74:x=96:y=1380:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='异味尴尬？':fontcolor=white:fontsize=74:x=96:y=1480:shadowcolor=black@0.85:shadowx=3:shadowy=3[v]" \
  -map '[v]' -map 1:a -t 3 "${video_args[@]}" "${audio_args[@]}" "$work/01-hook.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/02_product_lift.mp4" \
  -f lavfi -t 3 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=48,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=1,${brand},drawbox=x=72:y=1410:w=720:h=150:color=0xF5CE00@0.92:t=fill,drawtext=fontfile=${font}:text='出门前，先喷青颜':fontcolor=0x161616:fontsize=68:x=102:y=1445[v]" \
  -map '[v]' -map 1:a -t 3 "${video_args[@]}" "${audio_args[@]}" "$work/02-intro.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 3 -i "$assets/product-packshot.jpg" \
  -f lavfi -t 3 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "color=c=0xFFFBF0:s=1080x1920:r=24:d=3[bg];[0:v]scale=980:980[pack];[bg][pack]overlay=50:220,drawtext=fontfile=${font}:text='青颜抑汗净味喷雾':fontcolor=0x171717:fontsize=76:x=(w-text_w)/2:y=1260,drawtext=fontfile=${font}:text='抑汗净味 · 清爽舒适':fontcolor=0x4A4A40:fontsize=46:x=(w-text_w)/2:y=1380,drawbox=x=340:y=1480:w=400:h=7:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -map 1:a -t 3 "${video_args[@]}" "${audio_args[@]}" "$work/03-packshot.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 4 -i "$assets/04-golden-fluid.png" \
  -f lavfi -t 4 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1+0.00038*on,1.038)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=24,drawtext=fontfile=${font}:text='抑汗净味':fontcolor=0x171717:fontsize=84:x=80:y=215,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x171717:fontsize=84:x=80:y=330,drawtext=fontfile=${font}:text='帮助减少汗湿困扰':fontcolor=0x4A4A40:fontsize=50:x=84:y=470,drawbox=x=82:y=550:w=330:h=7:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -map 1:a -t 4 "${video_args[@]}" "${audio_args[@]}" "$work/04-benefit.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/04_walk_forward.mp4" \
  -i "$runtime/05_walk_smile.mp4" \
  -loop 1 -framerate 24 -t 2 -i "$assets/05-walk.png" \
  -f lavfi -t 5 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=42,setpts=PTS-STARTPTS,${portrait}[a];[1:v]trim=start_frame=0:end_frame=30,setpts=PTS-STARTPTS,${portrait}[b];[2:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1+0.00035*on,1.020)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=24,trim=duration=2,setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0,${brand},drawbox=x=64:y=1450:w=8:h=190:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=78:x=96:y=1460:shadowcolor=black@0.82:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='自信靠近':fontcolor=white:fontsize=78:x=96:y=1560:shadowcolor=black@0.82:shadowx=3:shadowy=3[v]" \
  -map '[v]' -map 3:a -t 5 "${video_args[@]}" "${audio_args[@]}" "$work/05-walk.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/06_social_turn.mp4" \
  -loop 1 -framerate 24 -t 2 -i "$assets/06-social.png" \
  -f lavfi -t 4 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=48,setpts=PTS-STARTPTS,${portrait}[a];[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1+0.00035*on,1.020)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=24,trim=duration=2,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0,${brand},drawbox=x=60:y=1430:w=820:h=145:color=white@0.86:t=fill,drawtext=fontfile=${font}:text='近距离社交，更从容':fontcolor=0x171717:fontsize=66:x=92:y=1468[v]" \
  -map '[v]' -map 2:a -t 4 "${video_args[@]}" "${audio_args[@]}" "$work/06-social.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 4 -i "$assets/product-packshot.jpg" \
  -f lavfi -t 4 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "color=c=0xFFF9E9:s=1080x1920:r=24:d=4[bg];[0:v]scale=900:900[pack];[bg][pack]overlay=60:170,drawtext=fontfile=${font}:text='通勤 · 出游 · 运动 · 约会':fontcolor=0x45453F:fontsize=50:x=(w-text_w)/2:y=1170,drawtext=fontfile=${font}:text='都自在':fontcolor=0x171717:fontsize=92:x=(w-text_w)/2:y=1270,drawtext=fontfile=${font}:text='青颜 氯化羟铝抑汗净味喷雾':fontcolor=0x171717:fontsize=46:x=(w-text_w)/2:y=1450,drawbox=x=375:y=1540:w=330:h=8:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -map 1:a -t 4 "${video_args[@]}" "${audio_args[@]}" "$work/07-hero.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 2 -i "$assets/06-social.png" \
  -loop 1 -framerate 24 -t 2 -i "$assets/product-packshot.jpg" \
  -f lavfi -t 2 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=12:2,eq=brightness=-0.10:saturation=0.78[bg];[1:v]scale=500:500[pack];[bg]drawbox=x=440:y=920:w=540:h=600:color=white@0.94:t=fill[card];[card][pack]overlay=460:945,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=78:x=70:y=250:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='自信不用藏':fontcolor=white:fontsize=78:x=70:y=360:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawbox=x=72:y=480:w=300:h=8:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=72:x=660:y=1430[v]" \
  -map '[v]' -map 2:a -t 2 "${video_args[@]}" "${audio_args[@]}" "$work/08-close.mp4"

printf '%s\n' \
  "file '$work/01-hook.mp4'" \
  "file '$work/02-intro.mp4'" \
  "file '$work/03-packshot.mp4'" \
  "file '$work/04-benefit.mp4'" \
  "file '$work/05-walk.mp4'" \
  "file '$work/06-social.mp4'" \
  "file '$work/07-hero.mp4'" \
  "file '$work/08-close.mp4'" > "$work/concat.txt"

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$work/concat.txt" \
  -vf 'fps=24' -an -t 28 -r 24 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
  -movflags +faststart "$work/picture-track.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -stream_loop -1 -i "$bgm" \
  -i "$whoosh" -i "$fluid_sfx" -i "$chime" \
  -filter_complex "[1:a]atrim=0:28,asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=0.5,afade=t=out:st=26.7:d=1.3[bgm];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.32,adelay=3000|3000[w1];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.28,adelay=6000|6000[w2];[3:a]atrim=0:1.4,asetpts=PTS-STARTPTS,volume=0.20,adelay=9000|9000[fluid];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.25,adelay=13000|13000[w3];[4:a]atrim=0:1.7,asetpts=PTS-STARTPTS,volume=0.30,adelay=22000|22000[chime];[bgm][w1][w2][fluid][w3][chime]amix=inputs=6:duration=longest,volume=3.5,alimiter=limit=0.90[a]" \
  -map 0:v -map '[a]' -t 28 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家女孩T8动态广告_28s_9x16.sha256"

ffmpeg -hide_banner -loglevel error -y -i "$output" \
  -vf 'fps=1,scale=270:-1,tile=7x4' -frames:v 1 "$review/contact.jpg"

ffprobe -v error \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,duration \
  -show_entries format=duration,size,bit_rate \
  -of json "$output" > "$review/ffprobe.json"

ffmpeg -hide_banner -i "$output" -af volumedetect -f null - \
  2> "$review/volumedetect.txt" || true

echo "$output"
