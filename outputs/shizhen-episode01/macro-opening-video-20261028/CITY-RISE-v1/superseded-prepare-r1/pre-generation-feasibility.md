# CITY-RISE v1 Pre-generation Feasibility

范围：仅前期作者审查，不是视频或接点验收。

- 首帧：已认可市政片最后一帧（第163帧）原样解码 `anchors/municipal-last-f163.png`，SHA `3d461331069e5505af70b6e18e36b0ec05098890f181146e775d8df90dae55fb`；市政片 SHA `b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d`。
- 尾帧：已认可B6所用事件源第0帧（无字幕层）`anchors/b6-event-render-f0.png`，SHA `6ab19dffab771f23fa82545c28eef2ccaa37d7c215b5c3475a9d30dab977e83c`；事件源 SHA `587352b307d19c995ba5f8f0de7f5bbe5de5e889e00dafd0d6339d99bd6323dc`。
- 两端都是固定机位：起点由静止急拉，终点刹停后静止，接B6稳定机位，避免v4末段漂移骤停。
- 首尾景别、地点完全不同，same_subject_scale=False；中段城市为新设计，不声称与已有素材测绘对应。
- 罗敏、高峥身份只由B6第0帧锚定，中段远景不另造面孔；市政工人只在首帧出现。
- 未证明：拉升/横掠/俯冲速度观感、建筑稳定、站棚与人物身份连续、刹停精度与声音，全部待exact MP4验证。
