#!/usr/bin/env bash
set -euo pipefail

repo='/home/reggie/vscode_folder/AI-VIDEO'
v8="$repo/artifacts/qingyan-miao-ad-20260826-v8"
root="$repo/artifacts/qingyan-miao-ad-20260826-v9"
work="$root/work"
final="$root/final"
mkdir -p "$work" "$final" "$root/audio"

shot1="$v8/runtime/t8_portrait_ad/01_underarm_deodorizing_repair.mp4"
shot2="$v8/runtime/t8_portrait_ad/02_elder_dialogue_repair.mp4"
shot3="$v8/runtime/t8_portrait_ad/03_leave_together.mp4"
fluid="$v8/assets/04-golden-fluid.png"
packshot="$v8/assets/product-packshot.jpg"
bgm="$v8/assets/house-vibez.mp3"
whoosh="$v8/assets/sweep-fast-small.mp3"
chime="$v8/assets/chime-crystal.mp3"
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
output="$final/青颜_苗家腋下使用前后对比广告_30s_9x16_v9.mp4"

portrait='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920'
video_args=(-r 24 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart)
audio_args=(-c:a aac -b:a 192k -ar 48000 -ac 2)

# Recovered voice phrases from the exact accepted H3 dialogue bytes.
ffmpeg -hide_banner -loglevel error -y -ss 3.35 -to 4.45 -i "$shot2" -vn \
  -af 'highpass=f=120,lowpass=f=8000,afftdn=nf=-30' -ar 48000 -ac 2 "$root/audio/benefit-phrase.wav"
ffmpeg -hide_banner -loglevel error -y -ss 4.98 -to 6.28 -i "$shot2" -vn \
  -af 'highpass=f=120,lowpass=f=8000,afftdn=nf=-30' -ar 48000 -ac 2 "$root/audio/elder-approval.wav"
ffmpeg -hide_banner -loglevel error -y -ss 1.42 -to 4.40 -i "$shot2" -vn \
  -af 'highpass=f=120,lowpass=f=8000,afftdn=nf=-30,atempo=1.3' -ar 48000 -ac 2 "$root/audio/product-line-fast.wav"

# Opening starts on visible motion; source frames 0-24 are intentionally retired.
ffmpeg -hide_banner -loglevel error -y -i "$shot1" \
  -filter_complex "[0:v]trim=start_frame=25:end_frame=175,setpts=PTS-STARTPTS,${portrait},drawbox=x=64:y=1510:w=720:h=176:color=0x121212@0.72:t=fill:enable='between(t,0,4.8)',drawtext=fontfile=${font}:text='腋下闷热？一喷散开':fontcolor=white:fontsize=58:x=96:y=1558:enable='between(t,0,4.8)'[v]" \
  -map '[v]' -an -frames:v 150 "${video_args[@]}" "$work/01-underarm-motion-hook.mp4"

ffmpeg -hide_banner -loglevel error -y -i "$shot2" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=155,setpts=PTS-STARTPTS,${portrait},drawbox=x=50:y=1490:w=980:h=250:color=0x121212@0.74:t=fill:enable='between(t,0,6.2)',drawtext=fontfile=${font}:text='阿婆：姑娘，喷的什么？':fontcolor=white:fontsize=54:x=82:y=1542:enable='between(t,0,1.68)',drawtext=fontfile=${font}:text='女孩：青颜抑汗净味喷雾':fontcolor=0xFFE156:fontsize=50:x=82:y=1522:enable='between(t,1.68,4.74)',drawtext=fontfile=${font}:text='清爽舒适':fontcolor=white:fontsize=58:x=82:y=1605:enable='between(t,1.68,4.74)',drawtext=fontfile=${font}:text='阿婆：难怪这么自在':fontcolor=white:fontsize=56:x=82:y=1542:enable='between(t,4.74,6.20)'[v]" \
  -map '[v]' -an -frames:v 155 "${video_args[@]}" "$work/02-elder-dialogue.mp4"

# Same-subject before/after sources. No package asset is used in this comparison.
ffmpeg -hide_banner -loglevel error -y -i "$shot1" -vf "select='eq(n,12)',${portrait}" -vsync vfr -frames:v 1 "$work/before.png"
ffmpeg -hide_banner -loglevel error -y -i "$shot1" -vf "select='eq(n,60)',${portrait}" -vsync vfr -frames:v 1 "$work/after.png"

# Adapted from video-shotcraft before-after-slider-scrub: conventional before-left / after-right,
# fast reveal then slow evidence scrub. The divider moves; the images themselves never jitter.
p_blend="if(lt(T,0.583333),0.92,if(lt(T,1.083333),0.92-(T-0.583333)/0.5*0.68,if(lt(T,1.583333),0.24+(T-1.083333)/0.5*0.06,if(lt(T,2.333333),0.30,if(lt(T,4.333333),0.30+(T-2.333333)/2*0.30,0.60)))))"
p_overlay="if(lt(t,0.583333),0.92,if(lt(t,1.083333),0.92-(t-0.583333)/0.5*0.68,if(lt(t,1.583333),0.24+(t-1.083333)/0.5*0.06,if(lt(t,2.333333),0.30,if(lt(t,4.333333),0.30+(t-2.333333)/2*0.30,0.60)))))"
ffmpeg -hide_banner -loglevel error -y -loop 1 -framerate 24 -t 5 -i "$work/before.png" \
  -loop 1 -framerate 24 -t 5 -i "$work/after.png" -f lavfi -t 5 -i 'color=c=white:s=8x1920:r=24' \
  -filter_complex "[0:v]format=yuv444p[before];[1:v]format=yuv444p[after];[before][after]blend=all_expr='if(lt(X,W*${p_blend}),A,B)'[cmp];[2:v]format=yuva444p,colorchannelmixer=aa=0.94[bar];[cmp][bar]overlay=x='main_w*${p_overlay}-4':y=0:eval=frame,drawbox=x=52:y=92:w=442:h=116:color=0x161616@0.82:t=fill,drawtext=fontfile=${font}:text='使用前  汗湿闷热':fontcolor=white:fontsize=48:x=78:y=128,drawbox=x=584:y=92:w=444:h=116:color=0x2578A9@0.88:t=fill,drawtext=fontfile=${font}:text='使用后  清爽舒适':fontcolor=white:fontsize=48:x=610:y=128,drawbox=x=175:y=1560:w=730:h=144:color=0x111111@0.70:t=fill,drawtext=fontfile=${font}:text='同一腋下  使用前后对比':fontcolor=white:fontsize=54:x=222:y=1603[v]" \
  -map '[v]' -an -frames:v 120 "${video_args[@]}" "$work/03-before-after.mp4"

# Native 175-frame source timing. No minterpolate, setpts stretch, xfade, flash or synthetic seam.
ffmpeg -hide_banner -loglevel error -y -i "$shot3" \
  -filter_complex "[0:v]trim=start_frame=0:end_frame=175,setpts=PTS-STARTPTS,${portrait}[v]" \
  -map '[v]' -an -frames:v 175 "${video_args[@]}" "$work/04-leave-native.mp4"

ffmpeg -hide_banner -loglevel error -y -loop 1 -framerate 24 -t 2.5 -i "$fluid" \
  -vf "${portrait},drawbox=x=70:y=150:w=940:h=290:color=white@0.92:t=fill,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x171717:fontsize=72:x=122:y=220,drawtext=fontfile=${font}:text='难怪这么自在':fontcolor=0x535353:fontsize=54:x=122:y=330" \
  -an -frames:v 60 "${video_args[@]}" "$work/05-benefit.mp4"

ffmpeg -hide_banner -loglevel error -y -loop 1 -framerate 24 -t 2.5 -i "$packshot" \
  -vf "${portrait},drawbox=x=0:y=1390:w=1080:h=530:color=white@0.96:t=fill,drawtext=fontfile=${font}:text='青颜':fontcolor=0x111111:fontsize=86:x=(w-text_w)/2:y=1450,drawtext=fontfile=${font}:text='氯化羟铝抑汗净味喷雾':fontcolor=0x4A4A4A:fontsize=44:x=(w-text_w)/2:y=1580,drawtext=fontfile=${font}:text='清爽舒适':fontcolor=0x111111:fontsize=54:x=(w-text_w)/2:y=1690" \
  -an -frames:v 60 "${video_args[@]}" "$work/06-product-hero.mp4"

printf '%s\n' \
  "file '$work/01-underarm-motion-hook.mp4'" \
  "file '$work/02-elder-dialogue.mp4'" \
  "file '$work/03-before-after.mp4'" \
  "file '$work/04-leave-native.mp4'" \
  "file '$work/05-benefit.mp4'" \
  "file '$work/06-product-hero.mp4'" > "$work/concat.txt"

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$work/concat.txt" \
  -vf 'fps=24' -an -frames:v 720 -r 24 -c:v libx264 -preset slow -crf 16 \
  -pix_fmt yuv420p -movflags +faststart "$work/picture-track.mp4"

ffmpeg -hide_banner -loglevel error -y \
  -i "$work/picture-track.mp4" -i "$shot1" -i "$shot2" -stream_loop -1 -i "$bgm" \
  -i "$whoosh" -i "$chime" -i "$root/audio/benefit-phrase.wav" \
  -i "$root/audio/elder-approval.wav" -i "$root/audio/product-line-fast.wav" \
  -filter_complex "[1:a]atrim=1.041667:7.291667,asetpts=PTS-STARTPTS,volume=0.82,afade=t=out:st=6.12:d=0.13[a1];[2:a]atrim=0:6.458333,asetpts=PTS-STARTPTS,volume=1.05,adelay=6250|6250[a2];[3:a]atrim=0:30,asetpts=PTS-STARTPTS,volume=0.04,afade=t=in:st=0:d=0.35,afade=t=out:st=29:d=1[bgm];[4:a]asplit=2[w1][w2];[w1]atrim=0:0.40,asetpts=PTS-STARTPTS,volume=0.09,adelay=13292|13292[swipe];[w2]atrim=0:0.40,asetpts=PTS-STARTPTS,volume=0.06,adelay=25000|25000[benefit_sweep];[5:a]atrim=0:1.5,asetpts=PTS-STARTPTS,volume=0.10,adelay=27500|27500[chime];[6:a]asplit=2[b1][b2];[b1]volume=1.18,adelay=14150|14150[compare_voice];[b2]volume=1.18,adelay=25000|25000[benefit_voice];[7:a]volume=1.15,adelay=26075|26075[elder_voice];[8:a]volume=1.18,adelay=27620|27620[product_voice];[a1][a2][bgm][swipe][benefit_sweep][chime][compare_voice][benefit_voice][elder_voice][product_voice]amix=inputs=10:duration=longest:dropout_transition=0,volume=1.55,alimiter=limit=0.92[a]" \
  -map 0:v -map '[a]' -t 30 -c:v copy "${audio_args[@]}" "$output"

sha256sum "$output" > "$final/青颜_苗家腋下使用前后对比广告_30s_9x16_v9.sha256"
echo "$output"
