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
output="$final/青颜_苗家女孩T8对白修复广告_30s_9x16_v5.mp4"

mkdir -p "$work" "$final" "$review"

video_args=(-r 24 -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)
brand="drawtext=fontfile=${font}:text='青颜':fontcolor=white:fontsize=38:x=66:y=64:shadowcolor=black@0.72:shadowx=2:shadowy=2,drawbox=x=66:y=116:w=88:h=5:color=0xF5CE00:t=fill"
portrait="crop=756:1344:6:0,scale=1080:1920:flags=lanczos"

# 01 | 48 source frames. Skip the source's initial 8-frame still hold; no cloned-frame extension.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/01_concern.mp4" \
  -filter_complex "[0:v]trim=start_frame=8:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=62:y=1360:w=8:h=224:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='汗湿黏腻？':fontcolor=white:fontsize=74:x=96:y=1370:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='靠近不自在？':fontcolor=white:fontsize=70:x=96:y=1475:shadowcolor=black@0.85:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 48 "${video_args[@]}" "$work/01-concern.mp4"

# 02 | 56 source frames. Readable product pixels come from the source packshot.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/02_product_lift.mp4" -loop 1 -framerate 24 -i "$packshot" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand}[bg];[1:v]scale=370:370[pack];[bg]drawbox=x=650:y=1220:w=395:h=445:color=white@0.93:t=fill[card];[card][pack]overlay=662:1240,drawbox=x=64:y=1425:w=535:h=145:color=0xF5CE00@0.94:t=fill,drawtext=fontfile=${font}:text='出门前，带上青颜':fontcolor=0x171717:fontsize=54:x=92:y=1466[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/02-product-lift.mp4"

# 03 | 124 source frames with native T8 dialogue. Caption preserves exact product/claim spelling.
ffmpeg -hide_banner -loglevel error -y \
  -i "$spoken" -loop 1 -framerate 24 -i "$packshot" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=124,setpts=PTS-STARTPTS,${portrait},${brand}[bg];[1:v]scale=290:290[pack];[bg]drawbox=x=735:y=1240:w=315:h=355:color=white@0.94:t=fill[card];[card][pack]overlay=747:1260,drawbox=x=54:y=1375:w=650:h=230:color=0x171717@0.78:t=fill,drawtext=fontfile=${font}:text='出门前用青颜，':fontcolor=white:fontsize=60:x=84:y=1410,drawtext=fontfile=${font}:text='抑汗净味，清爽舒适。':fontcolor=0xFFE156:fontsize=54:x=84:y=1500[v]" \
  -map '[v]' -an -frames:v 124 "${video_args[@]}" "$work/03-spoken.mp4"

# 04 | 96 frames of continuous benefit motion graphics.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$fluid" \
  -filter_complex "[0:v]scale=1240:2100:force_original_aspect_ratio=increase,crop=1240:2100,zoompan=z='1.08+0.025*sin(on/19)':x='iw/2-(iw/zoom/2)+42*sin(on/23)':y='ih/2-(ih/zoom/2)+28*cos(on/29)':d=1:s=1080x1920:fps=24,drawbox=x=54:y=180:w=890:h=390:color=white@0.72:t=fill,drawtext=fontfile=${font}:text='帮助减少汗湿困扰':fontcolor=0x171717:fontsize=72:x=82:y=250,drawtext=fontfile=${font}:text='保持清爽自在':fontcolor=0x4A4A40:fontsize=60:x=84:y=370,drawbox=x=84:y=480:w=360:h=8:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=42:x=84:y=1640[v]" \
  -map '[v]' -an -frames:v 96 "${video_args[@]}" "$work/04-benefit.mp4"

# 05 | 56 source frames. One continuous live-action Shot.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/04_walk_forward.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=64:y=1425:w=8:h=205:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=76:x=98:y=1435:shadowcolor=black@0.84:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='步步从容':fontcolor=white:fontsize=76:x=98:y=1535:shadowcolor=black@0.84:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/05-walk-forward.mp4"

# 06 | 72 frames. Explicit animated scene-reset card separates independent outdoor actions.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$fluid" -loop 1 -framerate 24 -i "$packshot" \
  -filter_complex "[0:v]scale=1240:2100:force_original_aspect_ratio=increase,crop=1240:2100,zoompan=z='1.10+0.020*sin(on/17)':x='iw/2-(iw/zoom/2)-38*sin(on/21)':y='ih/2-(ih/zoom/2)+30*sin(on/27)':d=1:s=1080x1920:fps=24[bg];[1:v]scale=600:600,zoompan=z='1.02+0.0015*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=600x600:fps=24[pack];[bg]drawbox=x=160:y=405:w=760:h=1010:color=white@0.88:t=fill[card];[card][pack]overlay=240:475,drawtext=fontfile=${font}:text='通勤 · 出游 · 约会':fontcolor=0x4A4A40:fontsize=54:x=(w-text_w)/2:y=1160,drawtext=fontfile=${font}:text='自在切换':fontcolor=0x171717:fontsize=84:x=(w-text_w)/2:y=1260,drawbox=x=370:y=1380:w=340:h=8:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 72 "${video_args[@]}" "$work/06-scene-reset.mp4"

# 07 | 56 source frames. One continuous live-action Shot.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_walk_smile.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=62:y=1405:w=8:h=205:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='轻盈出发':fontcolor=white:fontsize=76:x=96:y=1415:shadowcolor=black@0.84:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='从容靠近':fontcolor=white:fontsize=76:x=96:y=1515:shadowcolor=black@0.84:shadowx=3:shadowy=3[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/07-walk-smile.mp4"

# 08 | 56 source frames. Dissolve establishes a new social beat instead of pretending action continuity.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/05_social_turn.mp4" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=56,setpts=PTS-STARTPTS,${portrait},${brand},drawbox=x=62:y=1390:w=800:h=185:color=white@0.90:t=fill,drawtext=fontfile=${font}:text='近距离社交，更从容':fontcolor=0x171717:fontsize=64:x=94:y=1434[v]" \
  -map '[v]' -an -frames:v 56 "${video_args[@]}" "$work/08-social-turn.mp4"

# 09 | 120 frames. Source packshot owns readable product truth; continuous motion avoids a freeze card.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$packshot" -loop 1 -framerate 24 -i "$fluid" \
  -filter_complex "[1:v]scale=1240:2100:force_original_aspect_ratio=increase,crop=1240:2100,zoompan=z='1.10+0.018*sin(on/21)':x='iw/2-(iw/zoom/2)+34*sin(on/25)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=24[bg];[0:v]scale=940:940,zoompan=z='1.03+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=940x940:fps=24[pack];[bg]drawbox=x=40:y=155:w=1000:h=1510:color=white@0.83:t=fill[card];[card][pack]overlay=70:250,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=86:x=(w-text_w)/2:y=1250,drawtext=fontfile=${font}:text='氯化羟铝抑汗净味喷雾':fontcolor=0x4A4A40:fontsize=48:x=(w-text_w)/2:y=1375,drawbox=x=360:y=1485:w=360:h=8:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 120 "${video_args[@]}" "$work/09-product-hero.mp4"

# 10 | 90 frames. Animated close; no copied live-action tail.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$fluid" -loop 1 -framerate 24 -i "$packshot" \
  -filter_complex "[0:v]scale=1240:2100:force_original_aspect_ratio=increase,crop=1240:2100,zoompan=z='1.10+0.022*sin(on/16)':x='iw/2-(iw/zoom/2)-35*sin(on/19)':y='ih/2-(ih/zoom/2)+28*cos(on/23)':d=1:s=1080x1920:fps=24[bg];[1:v]scale=650:650,zoompan=z='1.03+0.0011*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=650x650:fps=24[pack];[bg]drawbox=x=165:y=490:w=750:h=1050:color=white@0.91:t=fill[card];[card][pack]overlay=215:555,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x171717:fontsize=80:x=(w-text_w)/2:y=1250,drawtext=fontfile=${font}:text='自信更从容':fontcolor=0x4A4A40:fontsize=68:x=(w-text_w)/2:y=1360,drawbox=x=360:y=1465:w=360:h=8:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=54:x=(w-text_w)/2:y=1515[v]" \
  -map '[v]' -an -frames:v 90 "${video_args[@]}" "$work/10-end-card.mp4"

# Nine 6-frame dissolves make scene changes explicit and remove hard concat seams.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/01-concern.mp4" \
  -i "$work/02-product-lift.mp4" \
  -i "$work/03-spoken.mp4" \
  -i "$work/04-benefit.mp4" \
  -i "$work/05-walk-forward.mp4" \
  -i "$work/06-scene-reset.mp4" \
  -i "$work/07-walk-smile.mp4" \
  -i "$work/08-social-turn.mp4" \
  -i "$work/09-product-hero.mp4" \
  -i "$work/10-end-card.mp4" \
  -filter_complex "[0:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v0];[1:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v1];[2:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v2];[3:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v3];[4:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v4];[5:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v5];[6:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v6];[7:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v7];[8:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v8];[9:v]fps=24,settb=AVTB,setpts=PTS-STARTPTS[v9];[v0][v1]xfade=transition=fade:duration=0.25:offset=1.750000[x1];[x1][v2]xfade=transition=fade:duration=0.25:offset=3.833333[x2];[x2][v3]xfade=transition=fade:duration=0.25:offset=8.750000[x3];[x3][v4]xfade=transition=fade:duration=0.25:offset=12.500000[x4];[x4][v5]xfade=transition=fade:duration=0.25:offset=14.583333[x5];[x5][v6]xfade=transition=fade:duration=0.25:offset=17.333333[x6];[x6][v7]xfade=transition=fade:duration=0.25:offset=19.416667[x7];[x7][v8]xfade=transition=fade:duration=0.25:offset=21.500000[x8];[x8][v9]xfade=transition=fade:duration=0.25:offset=26.250000,trim=end_frame=720,setpts=PTS-STARTPTS[picture]" \
  -map '[picture]' -an -frames:v 720 -r 24 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart "$work/picture-track.mp4"

# The accepted native voice begins when segment 03 enters the timeline (3.833333 s).
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -stream_loop -1 -i "$bgm" -i "$spoken" \
  -i "$whoosh" -i "$fluid_sfx" -i "$chime" \
  -filter_complex "[1:a]atrim=0:30,asetpts=PTS-STARTPTS,volume=0.11,afade=t=in:st=0:d=0.5,afade=t=out:st=28.5:d=1.5[bgm];[2:a]atrim=0:5.166667,asetpts=PTS-STARTPTS,highpass=f=90,acompressor=threshold=0.16:ratio=2.5:attack=8:release=140:makeup=1.25,volume=1.08,adelay=3833|3833[voice];[3:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.16,adelay=1750|1750[w1];[3:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.13,adelay=8750|8750[w2];[4:a]atrim=0:1.4,asetpts=PTS-STARTPTS,volume=0.12,adelay=8750|8750[fluid];[3:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.13,adelay=14583|14583[w3];[3:a]atrim=0:0.55,asetpts=PTS-STARTPTS,volume=0.12,adelay=19417|19417[w4];[5:a]atrim=0:1.7,asetpts=PTS-STARTPTS,volume=0.18,adelay=26250|26250[chime];[bgm][voice][w1][w2][fluid][w3][w4][chime]amix=inputs=8:duration=longest,volume=3.5,alimiter=limit=0.92[a]" \
  -map 0:v -map '[a]' -t 30 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家女孩T8对白修复广告_30s_9x16_v5.sha256"

ffmpeg -hide_banner -loglevel error -y -i "$output" \
  -vf 'fps=1,scale=270:-1,tile=6x5' -frames:v 1 "$review/contact.jpg"

ffprobe -v error \
  -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,duration \
  -show_entries format=duration,size,bit_rate \
  -of json "$output" > "$review/ffprobe.json"

ffmpeg -hide_banner -i "$output" -af volumedetect -f null - \
  2> "$review/volumedetect.txt" || true

echo "$output"
