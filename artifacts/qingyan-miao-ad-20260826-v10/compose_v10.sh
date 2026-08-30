#!/usr/bin/env bash
set -euo pipefail

repo='/home/reggie/vscode_folder/AI-VIDEO'
root="$repo/artifacts/qingyan-miao-ad-20260826-v10"
v8="$repo/artifacts/qingyan-miao-ad-20260826-v8"
runtime="$root/runtime/t8_portrait_ad"
work="$root/work"
final="$root/final"
audio="$root/audio"
mkdir -p "$work" "$final" "$audio"

problem="$runtime/00_problem_discovery_sniff_recoil_v2.mp4"
treatment="$runtime/01_problem_open_cap_spray.mp4"
bridge="$runtime/01_recap_elder_enters_v2.mp4"
dialogue="$v8/runtime/t8_portrait_ad/02_elder_dialogue_repair.mp4"
leave="$v8/runtime/t8_portrait_ad/03_leave_together.mp4"
fluid="$v8/assets/04-golden-fluid.png"
packshot="$v8/assets/product-packshot.jpg"
bgm="$v8/assets/house-vibez.mp3"
chime="$v8/assets/chime-crystal.mp3"
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
output="$final/青颜_苗家腋下止汗完整广告_30s_9x16_v10.mp4"

portrait='crop=756:1344:6:0,scale=1080:1920:flags=lanczos'
video_args=(-r 24 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)

# Reuse speech from the exact accepted elder-dialogue artifact. These two clips make
# the last promotional cards audible without introducing a new voice identity.
ffmpeg -hide_banner -loglevel error -y -ss 3.35 -to 4.45 -i "$dialogue" -vn \
  -af 'highpass=f=120,lowpass=f=8000,afftdn=nf=-30' -ar 48000 -ac 2 "$audio/benefit-phrase.wav"
ffmpeg -hide_banner -loglevel error -y -ss 1.42 -to 4.40 -i "$dialogue" -vn \
  -af 'highpass=f=120,lowpass=f=8000,afftdn=nf=-30,atempo=1.3' -ar 48000 -ac 2 "$audio/product-line-fast.wav"

# 00 / 0.000-5.875s / 141 frames: first show the underarm sweat/odor problem and a clear sniff recoil.
ffmpeg -hide_banner -loglevel error -y -i "$problem" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=141,setpts=PTS-STARTPTS,${portrait},drawbox=x=62:y=1460:w=956:h=276:color=0x111111@0.72:t=fill:enable='between(t,0.35,5.45)',drawbox=x=88:y=1500:w=206:h=76:color=0xFFD400@0.96:t=fill:enable='between(t,0.35,5.45)',drawtext=fontfile=${font}:text='使用前':fontcolor=0x111111:fontsize=46:x=113:y=1513:enable='between(t,0.35,5.45)',drawtext=fontfile=${font}:text='汗湿黏腻？异味尴尬？':fontcolor=white:fontsize=59:x=92:y=1610:enable='between(t,0.35,5.45)'[v]" \
  -map '[v]' -an -frames:v 141 "${video_args[@]}" "$work/00-problem.mp4"

# 01A / 5.875-10.167s / 103 frames: problem is already established; now open the cap and spray the underarm.
# Source frames 141-174 are retired because they contain a near-static hold after the spray action.
ffmpeg -hide_banner -loglevel error -y -i "$treatment" \
  -filter_complex "[0:v]trim=start_frame=38:end_frame=141,setpts=PTS-STARTPTS,${portrait},drawbox=x=62:y=1492:w=956:h=214:color=0x111111@0.70:t=fill:enable='between(t,0.30,4.05)',drawtext=fontfile=${font}:text='取下瓶盖  对准腋下轻喷':fontcolor=white:fontsize=57:x=(w-text_w)/2:y=1548:enable='between(t,0.30,4.05)'[v]" \
  -map '[v]' -an -frames:v 103 "${video_args[@]}" "$work/01a-treatment.mp4"

# 01B / 10.167-15.333s / 124 frames: recap in one continuous action, then the elder enters from screen right.
ffmpeg -hide_banner -loglevel error -y -i "$bridge" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=124,setpts=PTS-STARTPTS,${portrait},drawbox=x=64:y=1518:w=952:h=174:color=0x111111@0.68:t=fill:enable='between(t,2.30,4.85)',drawtext=fontfile=${font}:text='使用后 · 清爽舒适':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=1565:enable='between(t,2.30,4.85)'[v]" \
  -map '[v]' -an -frames:v 124 "${video_args[@]}" "$work/01b-recap-elder-enters.mp4"

# 02 / 15.333-21.542s / 149 frames: the only dialogue window; captions use the measured speech timing.
ffmpeg -hide_banner -loglevel error -y -i "$dialogue" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=149,setpts=PTS-STARTPTS,${portrait},drawbox=x=48:y=1478:w=984:h=270:color=0x111111@0.74:t=fill:enable='between(t,0,6.20)',drawtext=fontfile=${font}:text='阿婆：姑娘，喷的什么？':fontcolor=white:fontsize=53:x=82:y=1535:enable='between(t,0,1.68)',drawtext=fontfile=${font}:text='女孩：青颜抑汗净味喷雾':fontcolor=0xFFE156:fontsize=49:x=82:y=1518:enable='between(t,1.68,4.74)',drawtext=fontfile=${font}:text='清爽舒适':fontcolor=white:fontsize=57:x=82:y=1605:enable='between(t,1.68,4.74)',drawtext=fontfile=${font}:text='阿婆：难怪这么自在':fontcolor=white:fontsize=55:x=82:y=1540:enable='between(t,4.74,6.20)'[v]" \
  -map '[v]' -an -frames:v 149 "${video_args[@]}" "$work/02-dialogue.mp4"

# 03 / 21.542-25.000s / 83 frames: native motion only; no optical retime and no extra product image.
ffmpeg -hide_banner -loglevel error -y -i "$leave" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=83,setpts=PTS-STARTPTS,${portrait},drawtext=fontfile=${font}:text='近距离社交  更从容':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=1540:shadowcolor=black@0.86:shadowx=3:shadowy=3:enable='between(t,0.20,3.15)'[v]" \
  -map '[v]' -an -frames:v 83 "${video_args[@]}" "$work/03-leave.mp4"

# 04 / 25.000-27.500s / 60 frames: the golden-fluid benefit visual appears exactly once and is pixel-stable.
ffmpeg -hide_banner -loglevel error -y -loop 1 -framerate 24 -i "$fluid" \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,drawbox=x=70:y=170:w=940:h=310:color=white@0.90:t=fill,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x171717:fontsize=82:x=(w-text_w)/2:y=250,drawtext=fontfile=${font}:text='保持自在':fontcolor=0x555550:fontsize=58:x=(w-text_w)/2:y=370[v]" \
  -map '[v]' -an -frames:v 60 "${video_args[@]}" "$work/04-benefit.mp4"

# 05 / 27.500-30.000s / 60 frames: the clean packshot appears exactly once. No yellow strip or inset duplicate.
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -i "$packshot" \
  -f lavfi -i 'color=c=0xFFFCF6:s=1080x1920:r=24:d=2.5' \
  -filter_complex "[0:v]scale=960:960:flags=lanczos[pack];[1:v][pack]overlay=60:150[hero];[hero]drawtext=fontfile=${font}:text='青颜':fontcolor=0x171717:fontsize=104:x=(w-text_w)/2:y=1235,drawtext=fontfile=${font}:text='氯化羟铝抑汗净味喷雾':fontcolor=0x4A4A40:fontsize=52:x=(w-text_w)/2:y=1385,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x171717:fontsize=68:x=(w-text_w)/2:y=1535[v]" \
  -map '[v]' -an -frames:v 60 "${video_args[@]}" "$work/05-product-hero.mp4"

printf '%s\n' \
  "file '$work/00-problem.mp4'" \
  "file '$work/01a-treatment.mp4'" \
  "file '$work/01b-recap-elder-enters.mp4'" \
  "file '$work/02-dialogue.mp4'" \
  "file '$work/03-leave.mp4'" \
  "file '$work/04-benefit.mp4'" \
  "file '$work/05-product-hero.mp4'" > "$work/concat.txt"

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$work/concat.txt" \
  -vf 'fps=24' -an -frames:v 720 -r 24 -c:v libx264 -preset slow -crf 16 \
  -pix_fmt yuv420p -movflags +faststart "$work/picture-track.mp4"

# Native action/dialogue audio follows the exact visual trims. Continuous low BGM masks no seam;
# it only provides one acoustic bed. The last two cards reuse the accepted woman's exact voice.
ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" \
  -i "$problem" -i "$treatment" -i "$bridge" -i "$dialogue" \
  -stream_loop -1 -i "$bgm" -i "$chime" \
  -i "$audio/benefit-phrase.wav" -i "$audio/product-line-fast.wav" \
  -filter_complex "[1:a]atrim=0:5.856,asetpts=PTS-STARTPTS,volume=0.74,afade=t=out:st=5.70:d=0.15[a0];[2:a]atrim=1.583333:5.875,asetpts=PTS-STARTPTS,volume=0.76,afade=t=in:st=0:d=0.08,afade=t=out:st=4.14:d=0.15,adelay=5875|5875[a1];[3:a]atrim=0:5.152,asetpts=PTS-STARTPTS,volume=0.76,afade=t=in:st=0:d=0.08,afade=t=out:st=5.00:d=0.15,adelay=10167|10167[a1b];[4:a]atrim=0:6.208333,asetpts=PTS-STARTPTS,volume=1.04,afade=t=in:st=0:d=0.06,afade=t=out:st=6.06:d=0.14,adelay=15333|15333[a2];[5:a]atrim=0:30,asetpts=PTS-STARTPTS,volume=0.042,afade=t=in:st=0:d=0.35,afade=t=out:st=29.0:d=1.0[bgm];[6:a]atrim=0:1.5,asetpts=PTS-STARTPTS,volume=0.10,adelay=27500|27500[chime];[7:a]volume=1.08,adelay=25120|25120[benefit_voice];[8:a]volume=1.10,adelay=27570|27570[product_voice];[a0][a1][a1b][a2][bgm][chime][benefit_voice][product_voice]amix=inputs=8:duration=longest:dropout_transition=0,volume=2.15,alimiter=limit=0.94[a]" \
  -map 0:v -map '[a]' -t 30 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家腋下止汗完整广告_30s_9x16_v10.sha256"
echo "$output"
