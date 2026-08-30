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
output="$final/青颜_苗家女孩T8动态广告_30s_9x16_v4.mp4"

mkdir -p "$work" "$final" "$review"

video_args=(-r 24 -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)
brand="drawtext=fontfile=${font}:text='青颜':fontcolor=white:fontsize=38:x=66:y=64:shadowcolor=black@0.72:shadowx=2:shadowy=2,drawbox=x=66:y=116:w=88:h=5:color=0xF5CE00:t=fill"
portrait="crop=756:1344:6:0,scale=1080:1920:flags=lanczos"

# SHOT 01 | 0-3 s | 72 frames
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/01_concern.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=0.666667,trim=duration=3,${brand},drawbox=x=62:y=1360:w=8:h=224:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='汗湿黏腻？':fontcolor=white:fontsize=74:x=96:y=1370:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='靠近不自在？':fontcolor=white:fontsize=70:x=96:y=1475:shadowcolor=black@0.85:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 72 "${video_args[@]}" "$work/01-hook.mp4"

# SHOT 02 | 3-6 s | 72 frames. Generated lift is a motion cue; source packshot is the readable truth.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/02_product_lift.mp4" -loop 1 -framerate 24 -t 3 -i "$packshot" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=0.666667,trim=duration=3,${brand}[bg];[1:v]scale=390:390[pack];[bg]drawbox=x=625:y=1220:w=415:h=475:color=white@0.93:t=fill[card];[card][pack]overlay=638:1242,drawbox=x=64:y=1425:w=535:h=145:color=0xF5CE00@0.94:t=fill,drawtext=fontfile=${font}:text='出门前，带上青颜':fontcolor=0x171717:fontsize=54:x=92:y=1466[v]" \
  -map '[v]' -an -frames:v 72 "${video_args[@]}" "$work/02-product-lift.mp4"

# SHOT 03 | 6-9 s | 72 frames. No literal spray or nozzle claim.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/03_preuse_hint.mp4" -loop 1 -framerate 24 -t 3 -i "$packshot" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=0.666667,trim=duration=3,${brand}[bg];[1:v]scale=330:330[pack];[bg]drawbox=x=690:y=1260:w=355:h=400:color=white@0.93:t=fill[card];[card][pack]overlay=702:1282,drawbox=x=62:y=1410:w=600:h=155:color=white@0.90:t=fill,drawtext=fontfile=${font}:text='抑汗净味':fontcolor=0x171717:fontsize=58:x=94:y=1434,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x5B4B00:fontsize=47:x=96:y=1505[v]" \
  -map '[v]' -an -frames:v 72 "${video_args[@]}" "$work/03-preuse.mp4"

# SHOT 04 | 9-13 s | 96 frames
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 4 -i "$fluid" \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1+0.00030*on,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=24,drawtext=fontfile=${font}:text='帮助减少汗湿困扰':fontcolor=0x171717:fontsize=72:x=78:y=260,drawtext=fontfile=${font}:text='保持清爽自在':fontcolor=0x4A4A40:fontsize=58:x=82:y=380,drawbox=x=82:y=480:w=360:h=8:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=42:x=82:y=1640[v]" \
  -map '[v]' -an -frames:v 96 "${video_args[@]}" "$work/04-benefit.mp4"

# SHOT 05 | 13-18 s | 120 frames
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/04_walk_forward.mp4" -i "$runtime/05_walk_smile.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait}[a];[1:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop=8[b];[a][b]concat=n=2:v=1:a=0,trim=duration=5,${brand},drawbox=x=64:y=1425:w=8:h=205:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=76:x=98:y=1435:shadowcolor=black@0.84:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='步步从容':fontcolor=white:fontsize=76:x=98:y=1535:shadowcolor=black@0.84:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 120 "${video_args[@]}" "$work/05-state-change.mp4"

# SHOT 06 | 18-22 s | 96 frames
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_social_turn.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=1.666667,trim=duration=4,${brand},drawbox=x=62:y=1390:w=790:h=230:color=white@0.90:t=fill,drawtext=fontfile=${font}:text='通勤 · 出游 · 约会':fontcolor=0x171717:fontsize=58:x=94:y=1428,drawtext=fontfile=${font}:text='自在切换':fontcolor=0x5B4B00:fontsize=65:x=94:y=1510[v]" \
  -map '[v]' -an -frames:v 96 "${video_args[@]}" "$work/06-scenes.mp4"

# SHOT 07 | 22-26 s | 96 frames. Source product pixels own the hero shot.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 4 -i "$packshot" \
  -filter_complex "color=c=0xFFFBF0:s=1080x1920:r=24:d=4[bg];[0:v]scale=980:980,zoompan=z='min(1+0.00028*on,1.027)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=980x980:fps=24[pack];[bg][pack]overlay=50:240,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=82:x=(w-text_w)/2:y=1260,drawtext=fontfile=${font}:text='氯化羟铝抑汗净味喷雾':fontcolor=0x4A4A40:fontsize=48:x=(w-text_w)/2:y=1382,drawbox=x=360:y=1485:w=360:h=8:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 96 "${video_args[@]}" "$work/07-hero.mp4"

# SHOT 08 | 26-30 s | 96 frames
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_social_turn.mp4" -loop 1 -framerate 24 -t 4 -i "$packshot" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},tpad=stop_mode=clone:stop_duration=1.666667,trim=duration=4,boxblur=12:2,eq=brightness=-0.11:saturation=0.76[bg];[1:v]scale=560:560[pack];[bg]drawbox=x=230:y=720:w=620:h=760:color=white@0.95:t=fill[card];[card][pack]overlay=260:745,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=78:x=68:y=225:shadowcolor=black@0.88:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='自信不用藏':fontcolor=white:fontsize=78:x=68:y=335:shadowcolor=black@0.88:shadowx=3:shadowy=3,drawbox=x=70:y=455:w=330:h=8:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=72:x=(w-text_w)/2:y=1325,drawbox=x=305:y=1515:w=470:h=116:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='出门前，带上青颜':fontcolor=0x171717:fontsize=50:x=(w-text_w)/2:y=1546[v]" \
  -map '[v]' -an -frames:v 96 "${video_args[@]}" "$work/08-close.mp4"

printf '%s\n' \
  "file '$work/01-hook.mp4'" \
  "file '$work/02-product-lift.mp4'" \
  "file '$work/03-preuse.mp4'" \
  "file '$work/04-benefit.mp4'" \
  "file '$work/05-state-change.mp4'" \
  "file '$work/06-scenes.mp4'" \
  "file '$work/07-hero.mp4'" \
  "file '$work/08-close.mp4'" > "$work/concat.txt"

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$work/concat.txt" \
  -vf 'fps=24' -an -frames:v 720 -r 24 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
  -movflags +faststart "$work/picture-track.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -stream_loop -1 -i "$bgm" \
  -i "$whoosh" -i "$fluid_sfx" -i "$chime" \
  -filter_complex "[1:a]atrim=0:30,asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=0.5,afade=t=out:st=28.5:d=1.5[bgm];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.28,adelay=3000|3000[w1];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.25,adelay=6000|6000[w2];[3:a]atrim=0:1.4,asetpts=PTS-STARTPTS,volume=0.20,adelay=9000|9000[fluid];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.23,adelay=13000|13000[w3];[2:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.22,adelay=18000|18000[w4];[4:a]atrim=0:1.7,asetpts=PTS-STARTPTS,volume=0.30,adelay=22000|22000[chime];[bgm][w1][w2][fluid][w3][w4][chime]amix=inputs=7:duration=longest,volume=3.5,alimiter=limit=0.90[a]" \
  -map 0:v -map '[a]' -t 30 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家女孩T8动态广告_30s_9x16_v4.sha256"

ffmpeg -hide_banner -loglevel error -y -i "$output" \
  -vf 'fps=1,scale=270:-1,tile=6x5' -frames:v 1 "$review/contact.jpg"

ffprobe -v error \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,duration \
  -show_entries format=duration,size,bit_rate \
  -of json "$output" > "$review/ffprobe.json"

ffmpeg -hide_banner -i "$output" -af volumedetect -f null - \
  2> "$review/volumedetect.txt" || true

echo "$output"
