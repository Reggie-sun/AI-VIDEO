#!/usr/bin/env bash
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
previous="$task_root/../qingyan-miao-ad-20260826-regenerated"
source_root="$task_root/../qingyan-miao-ad-20260825"
runtime="$previous/runtime/t8_portrait_ad"
voice="$task_root/runtime/voice"
assets="$source_root/assets"
inputs="$source_root/runtime/inputs"
work="$task_root/work"
final="$task_root/final"
review="$task_root/review/final"
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
output="$final/青颜_苗家女孩广告_v3_有声多人流畅版_27.9s_9x16_60fps.mp4"

mkdir -p "$work" "$final" "$review"

video_args=(-r 60 -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -movflags +faststart)
portrait_native="crop=756:1344:6:0"
portrait_final="scale=1080:1920:flags=lanczos"
smooth="minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
brand="drawtext=fontfile=${font}:text='青颜 氯化羟铝抑汗净味喷雾':fontcolor=white:fontsize=30:x=62:y=62:shadowcolor=black@0.75:shadowx=2:shadowy=2,drawbox=x=62:y=108:w=90:h=5:color=0xF5CE00:t=fill"

# Real generated motion is slowed before motion-compensated interpolation; no end-frame hold.
ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/01_concern.mp4" \
  -vf "${portrait_native},setpts=1.7*PTS,${smooth},trim=duration=3.6,setpts=PTS-STARTPTS,${portrait_final},${brand},drawbox=x=64:y=1260:w=8:h=205:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='天气一热':fontcolor=white:fontsize=78:x=96:y=1270:shadowcolor=black@0.88:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='小尴尬就来了':fontcolor=white:fontsize=70:x=96:y=1370:shadowcolor=black@0.88:shadowx=3:shadowy=3" \
  -an -frames:v 216 "${video_args[@]}" "$work/01-concern.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/02_product_lift.mp4" \
  -vf "${portrait_native},setpts=1.7*PTS,${smooth},trim=duration=3.6,setpts=PTS-STARTPTS,${portrait_final},${brand},drawbox=x=70:y=1270:w=760:h=140:color=0xF5CE00@0.94:t=fill,drawtext=fontfile=${font}:text='出门前，先用青颜':fontcolor=0x161616:fontsize=66:x=102:y=1306" \
  -an -frames:v 216 "${video_args[@]}" "$work/02-product-lift.mp4"

# Exact source packshot; subtle floating movement instead of a frozen full frame.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 60 -t 3.3 -i "$assets/product-packshot.jpg" \
  -filter_complex "color=c=0xFFFAEC:s=1080x1920:r=60:d=3.3[bg];[0:v]scale=990:990[pack];[bg][pack]overlay=x=45:y='205+10*sin(1.35*t)',drawtext=fontfile=${font}:text='青颜抑汗净味喷雾':fontcolor=0x171717:fontsize=74:x=(w-text_w)/2:y=1280,drawtext=fontfile=${font}:text='黄色包装 · 白色瓶盖':fontcolor=0x4A4A40:fontsize=44:x=(w-text_w)/2:y=1385,drawbox=x=360:y=1475:w=360:h=7:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 198 "${video_args[@]}" "$work/03-packshot.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 60 -t 3.3 -i "$assets/04-golden-fluid.png" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1+0.00022*on,1.044)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=60,drawtext=fontfile=${font}:text='抑汗净味':fontcolor=0x171717:fontsize=86:x=80:y=230,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x171717:fontsize=86:x=80:y=345,drawtext=fontfile=${font}:text='帮助减少汗湿困扰':fontcolor=0x45453F:fontsize=50:x=84:y=490,drawbox=x=82:y=572:w=330:h=7:color=0xF5CE00:t=fill" \
  -an -frames:v 198 "${video_args[@]}" "$work/04-benefit.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$runtime/04_walk_forward.mp4" \
  -vf "${portrait_native},setpts=1.7*PTS,${smooth},trim=duration=3.6,setpts=PTS-STARTPTS,${portrait_final},${brand},drawbox=x=64:y=1250:w=8:h=205:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=78:x=96:y=1260:shadowcolor=black@0.85:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='步步从容':fontcolor=white:fontsize=78:x=96:y=1360:shadowcolor=black@0.85:shadowx=3:shadowy=3" \
  -an -frames:v 216 "${video_args[@]}" "$work/05-walk.mp4"

# A full six-second multi-person beat: establish all three women, then continue into generated turn motion.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 60 -t 1.5 -i "$inputs/social-936x1664.png" \
  -i "$runtime/05_social_turn.mp4" \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1+0.00012*on,1.011)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=60,trim=duration=1.5,setpts=PTS-STARTPTS[a];[1:v]${portrait_native},setpts=2.2*PTS,${smooth},trim=duration=4.5,setpts=PTS-STARTPTS,${portrait_final}[b];[a][b]concat=n=2:v=1:a=0,${brand},drawbox=x=60:y=1240:w=830:h=140:color=white@0.88:t=fill,drawtext=fontfile=${font}:text='朋友在身边，靠近也自在':fontcolor=0x171717:fontsize=59:x=92:y=1277[v]" \
  -map '[v]' -an -frames:v 360 "${video_args[@]}" "$work/06-social-three-women.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 60 -t 3 -i "$assets/product-packshot.jpg" \
  -filter_complex "color=c=0xFFF7D9:s=1080x1920:r=60:d=3[bg];[0:v]scale=820:820[pack];[bg][pack]overlay=x=130:y='220+8*sin(1.4*t)',drawtext=fontfile=${font}:text='通勤 · 出游 · 运动 · 约会':fontcolor=0x171717:fontsize=55:x=(w-text_w)/2:y=1180,drawtext=fontfile=${font}:text='都能轻松一点，自信一点':fontcolor=0x45453F:fontsize=48:x=(w-text_w)/2:y=1300,drawbox=x=380:y=1405:w=320:h=8:color=0xF5CE00:t=fill[v]" \
  -map '[v]' -an -frames:v 180 "${video_args[@]}" "$work/07-scenarios.mp4"

# End card keeps the complete three-woman group visible behind the exact product packshot.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 60 -t 3.6 -i "$inputs/social-936x1664.png" \
  -loop 1 -framerate 60 -t 3.6 -i "$assets/product-packshot.jpg" \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(1+0.00010*on,1.022)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=60,boxblur=8:2,eq=brightness=-0.08:saturation=0.82[bg];[1:v]scale=580:580[pack];[bg]drawbox=x=230:y=650:w=620:h=780:color=white@0.94:t=fill[card];[card][pack]overlay=x=250:y='690+5*sin(1.5*t)',drawtext=fontfile=${font}:text='清爽自在':fontcolor=white:fontsize=78:x=70:y=230:shadowcolor=black@0.88:shadowx=3:shadowy=3,drawtext=fontfile=${font}:text='自信不用藏':fontcolor=white:fontsize=78:x=70:y=335:shadowcolor=black@0.88:shadowx=3:shadowy=3,drawbox=x=72:y=455:w=300:h=8:color=0xF5CE00:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=72:x=(w-text_w)/2:y=1315[v]" \
  -map '[v]' -an -frames:v 216 "${video_args[@]}" "$work/08-close.mp4"

# 300 ms dissolves remove the hard-cut montage cadence; total picture length is 27.9 s.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/01-concern.mp4" -i "$work/02-product-lift.mp4" \
  -i "$work/03-packshot.mp4" -i "$work/04-benefit.mp4" \
  -i "$work/05-walk.mp4" -i "$work/06-social-three-women.mp4" \
  -i "$work/07-scenarios.mp4" -i "$work/08-close.mp4" \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.3:offset=3.3[x1];[x1][2:v]xfade=transition=fade:duration=0.3:offset=6.6[x2];[x2][3:v]xfade=transition=fade:duration=0.3:offset=9.6[x3];[x3][4:v]xfade=transition=fade:duration=0.3:offset=12.6[x4];[x4][5:v]xfade=transition=fade:duration=0.3:offset=15.9[x5];[x5][6:v]xfade=transition=fade:duration=0.3:offset=21.6[x6];[x6][7:v]xfade=transition=fade:duration=0.3:offset=24.3,drawbox=x=60:y=1460:w=960:h=170:color=black@0.48:t=fill:enable='between(t,0.15,4.25)+between(t,4.65,8.35)+between(t,8.35,12.65)+between(t,15.75,17.45)+between(t,18.35,20.95)+between(t,24.0,27.35)',drawtext=fontfile=${font}:text='天气一热，汗湿黏腻，异味尴尬':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=1502:enable='between(t,0.15,4.25)',drawtext=fontfile=${font}:text='出门前，我会先用青颜抑汗净味喷雾':fontcolor=white:fontsize=43:x=(w-text_w)/2:y=1504:enable='between(t,4.65,8.35)',drawtext=fontfile=${font}:text='抑汗净味，清爽舒适，帮助减少汗湿困扰':fontcolor=white:fontsize=43:x=(w-text_w)/2:y=1504:enable='between(t,8.35,12.65)',drawtext=fontfile=${font}:text='朋友说 · 今天状态真好！':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=1502:enable='between(t,15.75,17.45)',drawtext=fontfile=${font}:text='她说 · 出门前，我用了青颜。':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=1502:enable='between(t,18.35,20.95)',drawtext=fontfile=${font}:text='青颜，清爽自在，自信不用藏':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=1502:enable='between(t,24.0,27.35)'[v]" \
  -map '[v]' -an -frames:v 1674 -r 60 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart "$work/picture-track.mp4"

# Native H3 speech is kept as foreground speech; BGM is deliberately quiet and the final bus is normalized.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -stream_loop -1 -i "$assets/house-vibez.mp3" \
  -i "$voice/vo01_hook.mp4" -i "$voice/vo02_product.mp4" \
  -i "$voice/vo03_benefit.mp4" -i "$voice/vo04_dialogue.mp4" \
  -i "$voice/vo05_close.mp4" -i "$assets/chime-crystal.mp3" \
  -filter_complex "[1:a]atrim=0:27.9,asetpts=PTS-STARTPTS,volume=0.075,afade=t=in:st=0:d=0.5,afade=t=out:st=26.7:d=1.2[bgm];[2:a]aresample=48000,asetpts=PTS-STARTPTS,volume=1.25[v1];[3:a]aresample=48000,asetpts=PTS-STARTPTS,volume=1.25,adelay=4100|4100[v2];[4:a]aresample=48000,asetpts=PTS-STARTPTS,volume=1.25,adelay=8200|8200[v3];[5:a]aresample=48000,asetpts=PTS-STARTPTS,volume=1.30,adelay=15800|15800[v4];[6:a]aresample=48000,asetpts=PTS-STARTPTS,volume=1.30,adelay=24000|24000[v5];[7:a]atrim=0:1.7,asetpts=PTS-STARTPTS,volume=0.16,adelay=24300|24300[chime];[bgm][v1][v2][v3][v4][v5][chime]amix=inputs=7:duration=longest,loudnorm=I=-16:LRA=9:TP=-1.5[a]" \
  -map 0:v -map '[a]' -t 27.9 -c:v copy -c:a aac -b:a 224k -ar 48000 -ac 2 "$output"

sha256sum "$output" > "$final/青颜_苗家女孩广告_v3_有声多人流畅版_27.9s_9x16_60fps.sha256"
ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,duration -show_entries format=duration,size,bit_rate -of json "$output" > "$review/ffprobe.json"
ffmpeg -hide_banner -loglevel error -y -i "$output" -vf 'fps=1,scale=270:-1,tile=7x4' -frames:v 1 "$review/contact.jpg"

echo "$output"
