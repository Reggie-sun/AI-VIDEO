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
fluid_sfx="$assets/water-bubble.mp3"
chime="$assets/chime-crystal.mp3"
packshot="$assets/product-packshot.jpg"
fluid="$assets/04-golden-fluid.png"
spoken="$runtime/03_spoken_recommendation.mp4"
output="$final/青颜_苗家女孩T8自然转场广告_30s_9x16_v6.mp4"

mkdir -p "$work" "$final" "$review"

video_args=(-r 24 -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)
portrait="crop=756:1344:6:0,scale=1080:1920:flags=lanczos"
brand="drawtext=fontfile=${font}:text='青颜':fontcolor=white:fontsize=38:x=66:y=64:shadowcolor=black@0.72:shadowx=2:shadowy=2,drawbox=x=66:y=116:w=88:h=5:color=0xF5CE00:t=fill"

# 01 | 48 real source frames. The outgoing image reaches white before the state changes.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/01_concern.mp4" \
  -filter_complex "[0:v]trim=start_frame=8:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=62:y=1360:w=8:h=224:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='汗湿黏腻？':fontcolor=white:fontsize=74:x=96:y=1370:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='靠近不自在？':fontcolor=white:fontsize=70:x=96:y=1475:shadowcolor=black@0.85:shadowx=3:shadowy=3,fade=t=out:st=1.875:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 48 "${video_args[@]}" "$work/01-concern.mp4"

# 02 | 24-frame neutral bridge. No bottle and no packshot.
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "color=c=0xFFFBF2:s=1080x1920:r=24:d=1" \
  -filter_complex "[0:v]drawbox=x=70:y=610:w=940:h=520:color=white:t=fill,drawbox=x=70:y=610:w=18:h=520:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='出门前':fontcolor=0x171717:fontsize=94:x=132:y=710,drawtext=fontfile=${font}:text='给自己多一点从容':fontcolor=0x4A4A40:fontsize=64:x=132:y=850,drawbox=x=132:y=970:w=390:h=8:color=0xF5CE00:t=fill,fade=t=out:st=0.875:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 24 "${video_args[@]}" "$work/02-neutral-bridge.mp4"

# 03 | One continuous presenter Shot. The hand-held bottle is the only product in-frame.
ffmpeg -hide_banner -loglevel error -y \
  -i "$spoken" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=124,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=54:y=1375:w=760:h=230:color=0x171717@0.78:t=fill,drawtext=fontfile=${font}:text='出门前用青颜，':fontcolor=white:fontsize=60:x=84:y=1410,drawtext=fontfile=${font}:text='抑汗净味，清爽舒适。':fontcolor=0xFFE156:fontsize=54:x=84:y=1500,fade=t=in:st=0:d=0.125:color=white,fade=t=out:st=5.041667:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 124 "${video_args[@]}" "$work/03-spoken-presenter.mp4"

# 04 | Fixed copy over a one-direction background light pass; no still-image transform.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$fluid" \
  -f lavfi -i "color=c=white:s=280x1920:r=24:d=3.5" \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[base];[1:v]format=rgba,colorchannelmixer=aa=0.16[light];[base][light]overlay=x='-280+18*n':y=0:eval=frame[bg];[bg]drawbox=x=54:y=180:w=900:h=410:color=white@0.82:t=fill,drawtext=fontfile=${font}:text='帮助减少汗湿困扰':fontcolor=0x171717:fontsize=72:x=84:y=255,drawtext=fontfile=${font}:text='保持清爽自在':fontcolor=0x4A4A40:fontsize=60:x=86:y=380,drawbox=x=86:y=490:w=360:h=8:color=0xF5CE00:t=fill,fade=t=in:st=0:d=0.125:color=white,fade=t=out:st=3.375:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 84 "${video_args[@]}" "$work/04-benefit-card.mp4"

# 05 | One continuous live-action step.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/04_walk_forward.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=64:y=1425:w=8:h=205:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=76:x=98:y=1435:shadowcolor=black@0.84:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='步步从容':fontcolor=white:fontsize=76:x=98:y=1535:shadowcolor=black@0.84:shadowx=3:shadowy=3,fade=t=in:st=0:d=0.125:color=white,fade=t=out:st=2.208333:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/05-walk-forward.mp4"

# 06 | Text-only scene reset. No repeated product image.
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "color=c=0xFFFBF2:s=1080x1920:r=24:d=1.5" \
  -f lavfi -i "color=c=0xF5CE00:s=240x1920:r=24:d=1.5" \
  -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.12[light];[0:v][light]overlay=x='-240+38*n':y=0:eval=frame[bg];[bg]drawbox=x=110:y=590:w=860:h=640:color=white@0.94:t=fill,drawtext=fontfile=${font}:text='通勤 · 出游 · 约会':fontcolor=0x4A4A40:fontsize=58:x=(w-text_w)/2:y=760,drawtext=fontfile=${font}:text='自在切换':fontcolor=0x171717:fontsize=92:x=(w-text_w)/2:y=900,drawbox=x=365:y=1040:w=350:h=8:color=0xF5CE00:t=fill,fade=t=in:st=0:d=0.125:color=white,fade=t=out:st=1.375:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 36 "${video_args[@]}" "$work/06-scenario-bridge.mp4"

# 07 | Independent outdoor walking beat.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_walk_smile.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=62:y=1405:w=8:h=205:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='轻盈出发':fontcolor=white:fontsize=76:x=96:y=1415:shadowcolor=black@0.84:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='从容靠近':fontcolor=white:fontsize=76:x=96:y=1515:shadowcolor=black@0.84:shadowx=3:shadowy=3,fade=t=in:st=0:d=0.125:color=white,fade=t=out:st=2.208333:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/07-walk-smile.mp4"

# 08 | Skip the source's initial 8-frame still hold; enter from white with real motion.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_social_turn.mp4" \
  -filter_complex "[0:v]trim=start_frame=8:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=62:y=1390:w=800:h=185:color=white@0.90:t=fill,drawtext=fontfile=${font}:text='近距离社交，更从容':fontcolor=0x171717:fontsize=64:x=94:y=1434,fade=t=in:st=0:d=0.125:color=white,fade=t=out:st=1.875:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 48 "${video_args[@]}" "$work/08-social-turn.mp4"

# 09 | The source packshot appears exactly once and remains pixel-stable.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$packshot" \
  -f lavfi -i "color=c=0xFFFBF2:s=1080x1920:r=24:d=6" \
  -f lavfi -i "color=c=0xF5CE00:s=320x1920:r=24:d=6" \
  -filter_complex "[0:v]scale=930:930[pack];[2:v]format=rgba,colorchannelmixer=aa=0.22[light];[1:v][light]overlay=x='-320+10*n':y=0:eval=frame[bg];[bg]drawbox=x=40:y=155:w=1000:h=1510:color=white@0.92:t=fill[card];[card][pack]overlay=75:250,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=86:x=(w-text_w)/2:y=1250,drawtext=fontfile=${font}:text='氯化羟铝抑汗净味喷雾':fontcolor=0x4A4A40:fontsize=48:x=(w-text_w)/2:y=1375,drawbox=x=360:y=1485:w=360:h=8:color=0xF5CE00:t=fill,fade=t=in:st=0:d=0.125:color=white,fade=t=out:st=5.875:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 144 "${video_args[@]}" "$work/09-product-hero.mp4"

# 10 | Text-only brand closure. No second packshot.
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "color=c=0xF5CE00:s=1080x1920:r=24:d=4.166667" \
  -f lavfi -i "color=c=white:s=360x1920:r=24:d=4.166667" \
  -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.20[light];[0:v][light]overlay=x='-360+13*n':y=0:eval=frame[bg];[bg]drawbox=x=90:y=520:w=900:h=850:color=white@0.92:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=132:x=(w-text_w)/2:y=680,drawtext=fontfile=${font}:text='抑汗净味 · 清爽舒适':fontcolor=0x4A4A40:fontsize=58:x=(w-text_w)/2:y=890,drawbox=x=340:y=1015:w=400:h=8:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='出门前，用青颜':fontcolor=0x171717:fontsize=68:x=(w-text_w)/2:y=1110,fade=t=in:st=0:d=0.125:color=white[v]" \
  -map '[v]' -an -frames:v 100 "${video_args[@]}" "$work/10-text-end-card.mp4"

printf '%s\n' \
  "file '$work/01-concern.mp4'" \
  "file '$work/02-neutral-bridge.mp4'" \
  "file '$work/03-spoken-presenter.mp4'" \
  "file '$work/04-benefit-card.mp4'" \
  "file '$work/05-walk-forward.mp4'" \
  "file '$work/06-scenario-bridge.mp4'" \
  "file '$work/07-walk-smile.mp4'" \
  "file '$work/08-social-turn.mp4'" \
  "file '$work/09-product-hero.mp4'" \
  "file '$work/10-text-end-card.mp4'" > "$work/concat.txt"

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$work/concat.txt" \
  -vf 'fps=24' -an -frames:v 720 -r 24 -c:v libx264 -preset slow -crf 16 \
  -pix_fmt yuv420p -movflags +faststart "$work/picture-track.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -stream_loop -1 -i "$bgm" -i "$spoken" \
  -i "$whoosh" -i "$fluid_sfx" -i "$chime" \
  -filter_complex "[1:a]atrim=0:30,asetpts=PTS-STARTPTS,volume=0.11,afade=t=in:st=0:d=0.5,afade=t=out:st=28.5:d=1.5[bgm];[2:a]atrim=0:5.166667,asetpts=PTS-STARTPTS,highpass=f=90,acompressor=threshold=0.16:ratio=2.5:attack=8:release=140:makeup=1.25,volume=1.08,adelay=3000|3000[voice];[3:a]atrim=0:0.4,asetpts=PTS-STARTPTS,volume=0.11,adelay=2000|2000[w1];[3:a]atrim=0:0.4,asetpts=PTS-STARTPTS,volume=0.10,adelay=8167|8167[w2];[4:a]atrim=0:1.2,asetpts=PTS-STARTPTS,volume=0.10,adelay=8167|8167[fluid];[3:a]atrim=0:0.4,asetpts=PTS-STARTPTS,volume=0.10,adelay=14000|14000[w3];[3:a]atrim=0:0.4,asetpts=PTS-STARTPTS,volume=0.10,adelay=19833|19833[w4];[5:a]atrim=0:1.5,asetpts=PTS-STARTPTS,volume=0.16,adelay=19833|19833[chime];[bgm][voice][w1][w2][fluid][w3][w4][chime]amix=inputs=8:duration=longest,volume=3.5,alimiter=limit=0.92[a]" \
  -map 0:v -map '[a]' -t 30 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家女孩T8自然转场广告_30s_9x16_v6.sha256"

ffmpeg -hide_banner -loglevel error -y -i "$output" \
  -vf 'fps=1,scale=270:-1,tile=6x5' -frames:v 1 "$review/contact.jpg"

ffprobe -v error \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,duration \
  -show_entries format=duration,size,bit_rate \
  -of json "$output" > "$review/ffprobe.json"

echo "$output"
