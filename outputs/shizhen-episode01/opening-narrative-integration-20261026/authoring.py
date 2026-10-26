"""Task-local creative declarations; never Production acceptance."""
from pathlib import Path
import hashlib
import json
from ai_video.production.final_output_contracts import FinalOutputContract, FinalOutputRequirement
from ai_video.production.visual_quality import VisualDirection, visual_requirements

HERE = Path(__file__).resolve().parent
UNITS = [{'unit_id': 'CO-A1', 'duration_seconds': 7.666666666666667, 'beat_function': 'establish', 'objective': '先让观众记住两人彼此注意的普通关系，再完整被车厢遮住', 'open_state': '男人与打电话的女人在同一站棚', 'close_state': '男人对女人的关注已发生，货车覆盖两人', 'shot_scale': 'full', 'camera_treatment': 'static', 'camera_intent': '保留已生成双人表演原速和相互视线，不加剪影或片名分散注意', 'visible_change': '男人转向，女人回看，然后普通货车进入并完整遮挡'}, {'unit_id': 'CO-A2', 'duration_seconds': 2.75, 'beat_function': 'reveal', 'objective': '实体完全遮挡内切去1.25秒空车厢；车尾揭示原位只剩一人', 'open_state': '车身覆盖视野', 'close_state': '左侧空位与右侧继续打电话的女人同框', 'shot_scale': 'full', 'camera_treatment': 'static', 'camera_intent': '切口放在实体完全遮挡区，保留正常车身移动，不增加闪屏或消失特效', 'visible_change': '完全遮挡持续缩短，车身向右揭开无人站立的左侧'}, {'unit_id': 'CO-A3', 'duration_seconds': 8.0, 'beat_function': 'reaction', 'objective': '原位空缺可比较；司机核对一位，女人平静确认，继续生活；片名留给观众', 'open_state': '一人全景与空位继续存在', 'close_state': '近景中女人继续生活，失帧进入她身旁负空间', 'shot_scale': 'mixed_progression', 'camera_treatment': 'static', 'camera_intent': '只用原A3的后态和原生近景切镜；不使用历史FAIL的双人前段，不伪造新微距', 'visible_change': '一人全景继续约一秒后切近景，真实问答后仍保留两秒动态'}]

QUOTES = {
    'opening-only': '先别衔接了,我现在就是要前面的,跟s01没关系',
    'source-review': '先审看最新的 `失帧-视觉方向-C-概念片.mp4`、对应海报、现有 Shot、原音乐、剧本及导演设计。',
    'references': '请主动研究其片头的镜头组织、构图、节奏、音乐与文字结合方法。',
    'originality': '参考的是创作方法和艺术水准，不是复刻镜头、使用原作素材或照搬视觉风格。',
    'structure': '真正的问题是：观众看到了设计，却没有经历一个正在发生的异常。',
    'ordinary-world': '世界表面上依然正常运转，但现实正在悄无声息地发生某种不合理的变化。',
    'scale': '希望从更大的世界尺度，逐渐收束到具体空间和极其细微的异常。',
    'emotion': '让观众从感受到不协调，逐渐进入怀疑、困惑与不安。',
    'relations': '异常不仅需要被看见，还需要通过镜头前后的关系被感知。',
    'reveal-boundary': '请根据《失帧》的剧本与信息揭示边界，自主寻找更具有表现力的电影语言。',
    'freedom': '不再要求继续沿用白色背景、人物剪影、城市纹理、黑色宋体和水平线转场。',
    'type': '字体也应具有更强的电影美术品质，并与镜头事件、空间和剪辑节奏形成联系。',
    'type-restraint': '不必追求所有镜头都有文字，也不要为了展现 Typography Skill 而制造无意义的文字动画。',
    'music': '保留此前已确认的音乐，将其作为新版开场的核心声音素材。',
    'mix': '根据音乐的结构、情绪和节奏重新组织视觉内容，必要时进行合理延展、混音和环境音设计。',
    'reuse': '现有 Shot 与方向 C 概念片中的有效画面也应作为可复用素材，而非全部废弃。',
    'skills': '不要重新开发一套重复的 Skill，不要为了调用某个 Skill 而改变作品应该采用的视觉形式。',
    'explore': '随后探索具有明显艺术差异的视觉方案，选出最符合《失帧》的方向，实际推进制作。',
    'timing': '不预设固定镜头数量、精确时长或必须使用的特效。',
    'dynamic': '请在既有素材及已授权工具范围内完成尽可能充分的动态预演、剪辑、字体合成、音乐组织及可观看样片。',
    'missing': '对于尚无素材的镜头，准备可生产的导演设计和生成输入。',
    'no-video-fee': '未经明确授权不要产生新的视频生成费用；预演和最终成片必须清楚区分。',
    'no-template': '是否出现静态海报堆叠、廉价特效或过于模板化的 AI 视频设计。',
    'art-review': '不得将技术测试通过、字体清晰或者渲染成功等同于艺术审查通过。',
}


def write(path, value):
    (HERE/path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    raw = (HERE/'creative-input.txt').read_text()
    digest = hashlib.sha256(raw.encode()).hexdigest()
    assert all(q in raw for q in QUOTES.values())
    constraints = [dict(constraint_id=k, scope='global', source_text=v) for k,v in QUOTES.items()]
    units = [{**u, 'transition_out':'end' if i == len(UNITS)-1 else 'cut',
              'constraint_ids':list(QUOTES)} for i,u in enumerate(UNITS)]
    coverage = dict(schema_version='4', request=dict(creative_input_kind='direction',
        creative_input_evidence=raw, creative_constraints=constraints,
        target_duration_seconds=sum(u['duration_seconds'] for u in units),
        coverage_strategy='multi_shot', strategy_source='agent_directed',
        director_decision_rationale='由尺度、关系、遮挡和后态比较分镜；镜长来自已有完整动作与观察需要，不按模型上限或固定镜数。缺正式同街宏观/微距素材继续保留，不以预演关闭最终目标。',
        strategy_request_evidence=None, director_skill='open-video'), coverage_units=units,
        intent_items=[dict(intent_item_id=k,statement=v,origin='explicit_user',
            source_refs=[dict(source_hash=digest, locator='creative-input.txt#'+k,
                intent_item_id=k,quote=v,origin='explicit_user')], related_intent_ids=[]) for k,v in QUOTES.items()],
        intent_groups={k:([dict(intent_item_id=i) for i in QUOTES] if k=='must_happen' else [])
                       for k in ['must_happen','must_not_happen','preferred_performance','timing_targets','acceptable_variation']})
    direction = VisualDirection(content_kind='drama',
        typography='片名只在异常和后态成立之后进入真实玻璃负空间；字形清楚但不能靠读字解释异常，无无意义级联/闪烁或每镜字幕。',
        palette='深蓝黑与原片局部钨灯暖光，保留暗部和雨夜层次；stock与旧CG只作清楚披露的预演，正式版须统一摄影。',
        layout='先完整看见两人，再同构图看见一人和空位；全景后态有时间比较，最后视线收近人物与玻璃，不以大量独立海报替代。',
        style='采用原创日常关系缺席机制，不使用参考片的镜头、素材或字体；无廉价glitch、随机粒子、身体残影或未经剧本建立的循环空间。',
        holistic='以正常速度完整听看：有意义的变化通过前后镜头成立，宏观到微观递进、悬疑情绪、字体和原音乐及关键对白形成整体；预演不能代签正式真人成片。')
    contract = FinalOutputContract(goal_id='shizhen-opening-reconstruction',goal_version='1',user_goal=raw,
        requirements=tuple([FinalOutputRequirement(requirement_id=k,observable=v,
            proof='human' if k in {'structure','emotion','relations','type','mix','art-review'} else 'evaluator')
            for k,v in QUOTES.items()]+list(visual_requirements(direction))))
    write('director-coverage.json',coverage)
    write('visual-direction.json',direction.model_dump(mode='json'))
    write('final-output-contract.json',contract.model_dump(mode='json'))
    def ref(path):return dict(path=path,sha256=hashlib.sha256((HERE/path).read_bytes()).hexdigest())
    write('goal-binding.json',dict(schema_version='creative-goal-binding/1',authority='development_only',
        creative_input=ref('creative-input.txt'),coverage=ref('director-coverage.json'),
        final_output_contract=ref('final-output-contract.json'),bindings=[dict(intent_item_id=k,
            constraint_ids=[k],unit_ids=[u['unit_id'] for u in units],requirement_ids=[k]) for k in QUOTES]))
    print(json.dumps(dict(intent_items=len(QUOTES),units=len(units),goal_hash=contract.contract_hash)))


if __name__=='__main__':main()
