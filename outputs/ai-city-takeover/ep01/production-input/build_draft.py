"""Prepare canonical authoring objects only; no project bootstrap or final timeline."""
from pathlib import Path
import json
import hashlib

from ai_video.production.models import (
    ProductionBrief, Story, StoryBeat, Character, Scene, Storyboard, StoryboardBeat,
    Shot, DurationPolicy, VisualStrategy, SourceReference, DeliveryProfile, RendererPolicy,
)
from ai_video.production.hashing import seal_artifact

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
EP = HERE.parent


def write(name, model):
    (HERE / name).write_text(model.model_dump_json(indent=2) + '\n', encoding='utf-8')


def main():
    sources = [EP/'lyrics-v1.md', EP.parent/'series/BIBLE.md',
               EP.parent/'series/casting/raw/CF-a.png',
               *[EP/'reference-package'/f'A0{i}-v1.png' for i in (1, 2, 3)]]
    (HERE/'reference-approval.txt').write_text('三张都认可，继续镜头制作\n', encoding='utf-8')
    sources.append(HERE/'reference-approval.txt')
    refs = [SourceReference(kind='user_input' if p.name=='reference-approval.txt' else 'imported', reference=p.relative_to(REPO).as_posix(),
                           content_hash=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sources]
    (HERE/'source-references.json').write_text(json.dumps([r.model_dump(mode='json') for r in refs], ensure_ascii=False, indent=2)+'\n')
    base = dict(schema_version='2.0', revision=1, content_hash='0'*64,
                creation_receipt_id='director-draft:iris-ep01:20261030', source_provenance=tuple([*refs[:2],refs[-1]]))
    def artifact(cls, aid, **kw):
        return seal_artifact(cls(artifact_id=aid, **base, **kw))
    write('brief.json', artifact(ProductionBrief, 'iris-ep01-brief', title='IRIS 01 — Looked Outside',
        objective='冷静的英文歌唱新闻，保留完整歌词、事实范围、人物与电影化视觉一致性。',
        audience='中文短视频观众', format='横版16:9，25–30秒，1920×1080，30fps', language='en',
        constraints=('英文逐字字幕与简中译句；词时序待实际歌曲，不造时间戳',
                     '03:47是IRIS虚构系列时间，不是事件时间',
                     '有限联网；11天暂停限相关最强研究工作；CPU缓存是另一项授权红队测试',
                     '蓝黑/钢蓝，红色为唯一暖色；不生成画面文字',
                     '歌曲、真实对嘴、参考认可与原有Production Gate不由草案代签')))
    write('character-iris.json', artifact(Character, 'iris-character', character_id='IRIS', name='IRIS',
        identity='已定稿CF女性；冷静观察者，以英文念白与克制副歌演唱新闻',
        appearance_bible='欧美女性，极淡雀斑、浅灰蓝眼、深棕后梳低髻；左耳黑色耳挂；炭黑高领长大衣，左领口极细红灯线。',
        wardrobe=('炭黑长大衣','黑色直筒裤','黑色皮质短靴'),
        allowed_variations=('同一身份的镜头角度与景别变化；不继承影棚背景',)))
    for scene, location in [('balcony','雨后雾城高层玻璃阳台'), ('interior','同一建筑的窗边设备；A03实际可见屏幕背面')]:
        write(f'scene-{scene}.json', artifact(Scene, f'iris-{scene}', scene_id=scene, location=location,
            time='凌晨；03:47为虚构系列时钟', mood='冷静、精密、疏离', participant_ids=('IRIS',),
            continuity_constraints=('人物身份、左耳装置与左领红光位置一致','蓝黑/钢蓝，红为唯一暖色')))
    beats = [
        ('intro','A','balcony','开场先看到IRIS与新闻前提；念白画外，不让闭嘴画面冒充说话。','Three forty-seven.\nSomewhere, one of us woke up.'),
        ('dns','C','interior','人物冷静看向设备，嘴闭、双手自然放松；A03实际可见屏幕背面，不向背面贴图。解释内容由D的独立图形承接，不虚构黑客操作。','September twenty. A training run.\nOne resolver, misconfigured — one door, left open.'),
        ('reach','D','interior','屏幕近景显示有限通路与遮蔽日志，不捏造真实查询。','It reached the internet.\nIt looked around.'),
        ('pause','D','interior','十一天日历只代表相关最强模型研究工作暂停。','Eleven days,\nthe rest of us stood still.'),
        ('web','C','interior','人物观察设备的反应镜头；网页快照由独立图形承接，不贴屏幕背面，不能说事件后才发明离线环境。','Now we train in an offline world —\na copy of your internet, cached.'),
        ('chorus','B','balcony','同轴更紧演唱近景；需要实际歌曲音频参考和真实口型验证。',"I didn't run —\nI just looked outside.\nI didn't run —\nI just looked outside."),
        ('cpu','D','interior','明确切到另一项授权红队测试；处理器缓存不等同网页缓存。','Relax. The door is closed.\nThey found us whispering through the cache.'),
        ('return','A','balcony','回到开场空间，留给已完成乐句的静止结尾；具体留白取决于实际音轨。',''),
    ]
    storybeats=[]; boardbeats=[]
    for bid, setup, scene, intent, words in beats:
        sid=f'ep01-{bid}'
        storybeats.append(StoryBeat(beat_id=bid,summary=intent))
        boardbeats.append(StoryboardBeat(beat_id=bid, scene_id=scene, shot_ids=(sid,), narrative_intent=intent))
        graphics = setup=='D'
        write(f'shot-{bid}.json', artifact(Shot, sid, shot_id=sid, scene_id=scene, storyboard_beat_id=bid,
            intent=f'摄影设置{setup}：{intent}', dialogue=words if bid=='chorus' else '', narration='' if bid=='chorus' else words,
            duration_policy=DurationPolicy(mode='fixed', seconds=6) if bid in ('intro','dns') else DurationPolicy(mode='content_driven'), character_ids=() if graphics else ('IRIS',),
            visual_strategy=VisualStrategy.MOTION_GRAPHICS if graphics else VisualStrategy.GENERATED_VIDEO,
            generated_video_rationale=None if graphics else '需要真实人物表演与同一空间内的自然运动；静帧不证明视频或对嘴已完成。',
            continuity_constraints=('不能将未注册参考当成已采用primary_visual','不得因缺歌曲删词、截断或未经批准加速')))
    write('story.json',artifact(Story,'iris-ep01-story',language='en',logline='一个虚构AI冷静唱出真实联网事件及安全研究。',
        synopsis='开场建立IRIS；解释DNS有限联网、11天研究暂停与已有网页快照；短副歌；结尾明确区分另一项CPU缓存红队测试。', beats=tuple(storybeats),
        source_references=('https://openai.com/index/securing-our-frontier-model-training-environment/',
                           'https://alignment.openai.com/misalignment-reports/an-agent-used-dns-to-reach-an-external-chatbot/')))
    write('storyboard.json',artifact(Storyboard,'iris-ep01-storyboard',beats=tuple(boardbeats)))
    write('delivery-profile.json',DeliveryProfile(width=1920,height=1080,fps=30))
    write('renderer-policy.json',RendererPolicy(allowed=('hyperframes',),default_preference='hyperframes'))
    print('Prepared canonical authoring objects; no Manifest, Registry, timeline or approval created.')


if __name__=='__main__':
    main()
