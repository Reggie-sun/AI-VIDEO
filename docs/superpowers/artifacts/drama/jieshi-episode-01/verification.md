# Verification

## Scope

本轮是完整Episode创作与提示草稿交付。源内容为 `episode-01.proposed.json`；
`episode-01.md` 是人读分镜，`creative-artifacts.json` 是派生的现有模型快照。
不把文档、Pydantic验证或Harness当作Production loading、媒体验收或留存实测。

## Focused Evidence

- Director coverage schema v3：`passed`，16个节拍，300秒，`multi_shot`。
- 当前Production模型：69个artifact（Brief、Story、11个Character、3个Scene、Storyboard、52个Shot）。
- 17个Storyboard分组：剧情Beat跨Scene时按同一beat分开，仍保持52镜顺序。
- 逐镜连续时间、台词窗口、角色/Scene引用、3秒原句钩子、最后15秒、24fps素材裁切均已检查。
- 66个素材component：65个候选生成素材与1个末帧复用；最少计划源时长337秒，剪辑300秒。
  该数量不是已发生调用，不含首帧准备、重试或可执行预算。
- 选择的当前capability：`seedance-2-0-260128-image_to_video`，
  `doubao-seedance-2-0-260128`，`seedance-2026-08-19`。
  当前本地profile允许4–15秒，选择1080p、24fps、I2V ratio=9:16；不支持seed或negative_prompt参数。
  这是仓库capability事实，不证明账号权限、实时价格或模型质量。

## Reproduce

从仓库root运行：

```bash
python .agents/skills/open-video/scripts/validate_director_coverage.py docs/superpowers/artifacts/drama/jieshi-episode-01/director-coverage.json
```

以下检查只读离线创作文件，并调用现有模型/hash verifier；不调用Production loader：

```python
import hashlib
import json
import math
from pathlib import Path
from ai_video.production import models
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.hashing import canonical_sha256
from ai_video.production.seedance_capabilities import select_seedance_capabilities

r = Path('docs/superpowers/artifacts/drama/jieshi-episode-01')
p = json.loads((r / 'episode-01.proposed.json').read_text())
a = json.loads((r / 'creative-artifacts.json').read_text())
sha = hashlib.sha256((r / 'episode-01.proposed.json').read_bytes()).hexdigest()
assert sha == a['source_sha256']
cap = next(c for c in select_seedance_capabilities('doubao-seedance-2-0-260128')
           if c.variant.mode.value == 'image_to_video')
t = p['selected_authoring_target']
assert t['model_id'] == cap.variant.model_id
assert t['capability_id'] == cap.variant.capability_id
assert t['capability_content_sha256'] == canonical_sha256(cap)
assert t['ratio'] == '9:16' and t['resolution_label'] == '1080p' and t['fps'] == 24
assert any(x.resolution_label == '1080p' and x.ratio == '9:16'
           and x.width == 1080 and x.height == 1920 for x in cap.output_rasters)
types = {'brief': models.ProductionBrief, 'story': models.Story,
         'characters': models.Character, 'scenes': models.Scene,
         'storyboard': models.Storyboard, 'shots': models.Shot}
count = 0
for key, cls in types.items():
    rows = a['artifacts'][key]
    for row in rows if isinstance(rows, list) else [rows]:
        obj = cls.model_validate(row)
        assert verify_artifact_hash(obj)
        assert obj.source_provenance[0].content_hash == sha
        count += 1
assert count == 69
shots = p['ordered_shots']
scenes = {s['scene_id']: s for s in p['scenes']}
characters = {c['character_id'] for c in p['characters']}
assert len(shots) == 52 and sum(s['duration_seconds'] for s in shots) == 300
assert len({s['shot_id'] for s in shots}) == 52
typed = a['artifacts']['shots']
for i, s in enumerate(shots):
    assert s['start_seconds'] == (shots[i-1]['end_seconds'] if i else 0)
    assert s['end_seconds'] - s['start_seconds'] == s['duration_seconds']
    assert set(s['character_ids']) <= set(scenes[s['scene_id']]['participant_ids'])
    assert typed[i]['shot_id'] == s['shot_id']
    assert typed[i]['intent'] == s['title'] + '：' + s['action_and_performance']
    assert typed[i]['duration_policy']['seconds'] == s['duration_seconds']
    assert math.isclose(sum(c['edited_seconds'] for c in s['generation_components']), s['duration_seconds'])
    for c in s['generation_components']:
        assert math.isclose(c['edited_seconds'] * 24, round(c['edited_seconds'] * 24))
        assert set(c['visible_character_ids']) <= set(s['character_ids'])
        assert c['prompt_draft'] and c['camera_intent'] and c['first_frame_preparation']
        assert c['kind'] != 'seedance_i2v_draft' or 4 <= c['requested_source_seconds'] <= 15
    for d in s['dialogue']:
        assert 0 <= d['start_seconds'] < d['end_seconds'] <= s['duration_seconds']
        assert d['speaker_id'] in characters
ordered = [sid for b in a['artifacts']['storyboard']['beats'] for sid in b['shot_ids']]
assert ordered == [s['shot_id'] for s in shots]
assert shots[0]['duration_seconds'] == 3
assert shots[0]['dialogue'][0]['text'] == '林砚，请在终点站下车。'
assert '可这条地铁，没有终点站。' in shots[0]['on_screen_text']
assert shots[49]['start_seconds'] == 285 and shots[51]['end_seconds'] == 300
assert all('LY' not in c['visible_character_ids'] for s in shots[50:] for c in s['generation_components'])
print({'status': 'passed', 'typed_models': count, 'shots': 52, 'seconds': 300, 'frames': 7200})
```

## Harness

2026-09-05用户改选Seedance 2.0后的proposal SHA-256：
`433434377d96a14fa3dc4efce4428acfa1b599d3c81db6afedfd26a2ddf459e8`。
本次仅更新模型选择、画幅参数、用户约束及派生provenance/hash；52个Shot内容与时长逐项保持一致。
下述独立审读属于前一创作版本，不作为本次模型选择的review证据。

Native `reviewer_high`独立审读后修正原阻断，同tier scoped re-review最终为`accept`，
没有剩余Blocking issues。改名前复核proposal SHA-256为
`48ec205ef97e4df55744dec3f80d4fc77a2cdc2e59920a53c26278aa87ddab3f`。
用户要求改用中文姓名后的SHA-256为
`6f1bdb6d8f0f42cb3a9f3d41ffc1db2206f991330dfdbcac17d14c8b790143ee`。
已逐镜对比暂存前版，台词原文、时长、角色ID、镜头顺序、component与生成目标未改变；
正文及所有prompt无裸角色字母，机器ID继续稳定用于引用。
姓名修改亦经同一native reviewer_high scoped re-review，结果`accept`，无阻断。

真实路径归入documentation；exact staged snapshot的mandatory checks由当时的
`.agent/harness/policy.yaml`决定。最终receipt预定位置：
`.agent/harness/runs/jieshi-e01-seedance20-20260905/receipt.json`。
是否通过和freshness以实际receipt及本轮交付为准，本文不预写成功结果。

```bash
python scripts/agent_harness.py inspect --base-ref <task-commit-parent> --head-ref <task-commit>
python scripts/agent_harness.py verify --base-ref <task-commit-parent> --head-ref <task-commit> --run-id jieshi-e01-seedance20-20260905
python scripts/agent_harness.py verify-receipt .agent/harness/runs/jieshi-e01-seedance20-20260905/receipt.json
```

## Remaining Evidence

没有Provider调用、参考图生成、MP4、voice生成、字形渲染、口型或全速媒体观看证据。
逐镜生成提示中的首帧均是待制作需求；没有伪造Asset Registry ID、上传引用或执行profile。
媒体执行仍须现有Paid Provider、source audio、continuity、per-Shot video-analysis与P6 gates。
没有发布抖音，未取得平台审核结果或观众留存数据。
