#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
old_root='/home/reggie/电商图片/青颜/青颜视频_20260824'
source_root='/home/reggie/电商图片/青颜'
work="$task_root/work"
final="$task_root/final"
review="$task_root/review"
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
underarm="$source_root/jpeg_m_109f749e83800196821bac4a7d271411_sx_404981_www1440-1440~tplv-5mmsx3fupr-resize_q_1080_1080_q90.png"
pack="$old_root/edit/product_cutout.png"

mkdir -p "$work" "$final" "$review"

video_args=(-r 24 -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)
brand="drawtext=fontfile=${font}:text='青颜 氯化羟铝抑汗净味喷雾':fontcolor=white:fontsize=30:x=62:y=62:shadowcolor=black@0.9:shadowx=2:shadowy=2,drawbox=x=62:y=108:w=86:h=4:color=0xF7D000:t=fill"
lower="drawbox=x=56:y=920:w=6:h=150:color=0xF7D000:t=fill"

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 4.6 -i "$underarm" \
  -f lavfi -t 4.6 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v]crop=356:744:683:283,split=2[fg][bg];[bg]scale=720:1504,crop=720:1280:0:112,boxblur=30:2[bg2];[fg]scale=720:1504,crop=720:1280:0:112,zoompan=z='min(1+0.0012*on,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=720x1280:fps=24[fg2];[bg2][fg2]overlay=0:0,drawbox=x='420-55*t':y='430+18*sin(5*t)':w=270:h=112:color=0x9AA84D@0.78:t=fill:enable='between(t,0.15,2.25)',drawtext=fontfile=${font}:text='尴尬气味？  >>>':fontcolor=0x20230D:fontsize=40:x='438-55*t':y='458+18*sin(5*t)':enable='between(t,0.15,2.25)',drawbox=x=80:y=385:w=560:h=230:color=0xF7D000@0.90:t=fill:enable='between(t,2.1,4.0)',drawtext=fontfile=${font}:text='清爽随身':fontcolor=0x171717:fontsize=82:x=(w-text_w)/2:y=455:enable='between(t,2.1,4.0)',${brand},${lower},drawtext=fontfile=${font}:text='腋下小剧场':fontcolor=white:fontsize=62:x=90:y=925:shadowcolor=black@0.9:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='尴尬，退场！':fontcolor=white:fontsize=70:x=90:y=995:shadowcolor=black@0.9:shadowx=3:shadowy=3[v]" \
  -map '[v]' -map 1:a -t 4.6 "${video_args[@]}" "${audio_args[@]}" "$work/01_hook.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 3.2 -i "$pack" \
  -f lavfi -t 3.2 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "color=c=0xFFFBEF:s=720x1280:r=24:d=3.2[bg];[0:v]scale=530:-1,format=rgba[p];[bg][p]overlay=(W-w)/2:210,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=88:x=(w-text_w)/2:y=820,drawtext=fontfile=${font}:text='氯化羟铝抑汗净味喷雾':fontcolor=0x171717:fontsize=38:x=(w-text_w)/2:y=930,drawtext=fontfile=${font}:text='清爽随身':fontcolor=0x171717:fontsize=66:x=(w-text_w)/2:y=1020,drawbox=x=260:y=1115:w=200:h=7:color=0xF7D000:t=fill,zoompan=z='min(1+0.0007*on,1.055)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=720x1280:fps=24[v]" \
  -map '[v]' -map 1:a -t 3.2 "${video_args[@]}" "${audio_args[@]}" "$work/02_product.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$old_root/raw/shot03_seed240803.mp4" \
  -vf "crop=432:768:(iw-432)/2:0,scale=720:1280,${brand},${lower},drawtext=fontfile=${font}:text='运动尽兴':fontcolor=white:fontsize=64:x=90:y=925:shadowcolor=black@0.9:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='尴尬退场':fontcolor=white:fontsize=64:x=90:y=995:shadowcolor=black@0.9:shadowx=3:shadowy=3" \
  -af "volume=0,aresample=48000" -t 4.6 "${video_args[@]}" "${audio_args[@]}" "$work/03_gym.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$old_root/raw/shot04_seed240804.mp4" \
  -vf "crop=432:768:(iw-432)/2:0,scale=720:1280,${brand},${lower},drawtext=fontfile=${font}:text='通勤 · 运动 · 约会':fontcolor=white:fontsize=52:x=90:y=925:shadowcolor=black@0.9:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='清爽随身':fontcolor=white:fontsize=66:x=90:y=995:shadowcolor=black@0.9:shadowx=3:shadowy=3" \
  -af "volume=0,aresample=48000" -t 4.6 "${video_args[@]}" "${audio_args[@]}" "$work/04_commute.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$old_root/raw/shot06_seed240806.mp4" -loop 1 -framerate 24 -i "$pack" \
  -filter_complex "[0:v]split=2[fg][bg];[bg]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,boxblur=24:2[bg2];[fg]scale=720:-2[fg2];[bg2][fg2]overlay=(W-w)/2:(H-h)/2[base];[1:v]scale=390:-1,format=rgba,fade=t=in:st=1.0:d=0.22:alpha=1[p];[base][p]overlay=(W-w)/2:410:enable='gte(t,1.0)',${brand},${lower},drawtext=fontfile=${font}:text='看看青颜':fontcolor=white:fontsize=70:x=90:y=925:shadowcolor=black@0.9:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='日常外用 · 按说明使用':fontcolor=white:fontsize=40:x=90:y=1005:shadowcolor=black@0.9:shadowx=3:shadowy=3[v]" \
  -map '[v]' -map 0:a -af "volume=0,aresample=48000" -t 5.0 "${video_args[@]}" "${audio_args[@]}" "$work/05_close.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$work/01_hook.mp4" -i "$work/02_product.mp4" -i "$work/03_gym.mp4" -i "$work/04_commute.mp4" -i "$work/05_close.mp4" \
  -f lavfi -t 22.0 -i "aevalsrc=0.320*sin(2*PI*72*t)*exp(-18*mod(t\,0.535714))+0.110*sin(2*PI*180*t)*exp(-30*mod(t+0.267857\,0.535714)):s=48000" \
  -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a][3:v][3:a][4:v][4:a]concat=n=5:v=1:a=1[v][a];[5:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=2.50[beat];[a][beat]amix=inputs=2:duration=first:weights='1 1',alimiter=limit=0.92[aout]" \
  -map '[v]' -map '[aout]' -r 24 -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart \
  "$final/青颜_腋下POV轻夸张广告_22s_candidate.mp4"

sha256sum "$final/青颜_腋下POV轻夸张广告_22s_candidate.mp4" > "$final/青颜_腋下POV轻夸张广告_22s_candidate.mp4.sha256"

ffmpeg -hide_banner -loglevel error -y -i "$final/青颜_腋下POV轻夸张广告_22s_candidate.mp4" \
  -vf "fps=1,scale=240:-1,tile=6x4" -frames:v 1 "$review/contact.jpg"

ffprobe -v error -show_entries stream=index,codec_name,width,height,r_frame_rate,duration -show_entries format=duration,size \
  -of json "$final/青颜_腋下POV轻夸张广告_22s_candidate.mp4" > "$review/ffprobe.json"
