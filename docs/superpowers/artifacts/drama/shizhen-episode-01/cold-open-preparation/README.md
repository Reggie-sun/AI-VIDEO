# Lost Frames EP01 — Cold Open Preparation

## Current Revision — Rhythm 02

当前推荐改为[Rhythm Revision 02](rhythm-revision-02/director-revision.md)：约22秒、20–28秒弹性，同一固定构图提前呈现“两位→一位”，无新付费生成。[当前coverage](rhythm-revision-02/director-coverage.json)取代下方37秒coverage的后续制作指导；人物、世界观、主题与S01保护继续继承。revision-02是创作准备，不激活Production。

以下各文件与37秒说明保留为Revision 01历史，不再作为最新镜头顺序／时长／spotting入口。旧验证回执绑定原commit `aabb9a3`；本README的版本入口更新不回填旧回执。既有音乐设计／静态素材可按revision-02明确列出的继承范围复用，不从旧shot-cards直接submit。

## Previous Director Decision — Revision 01

**《两位》：雨站里有两个人，十一秒过去，连“一起等车”这件事也只剩观众记得。**

这是一场约37秒、可随表演调整至约32–45秒的冷开场，不是城市宣传片。先看见普通人的生活关系，再看见空位，最后听见留下的人平静地说“就我一个”。片名之后回到翌夜的便利店，完整保留已认可的S01，让观众等待：这次消失，会有人记得吗？

视频路线已按用户最新指令锁定 **Jimeng / `seedance_2.5`、1080p、16:9**。音乐按用户补充的《爱，死亡和机器人》方向提炼冷峻、电子与室内乐混合、空间感及悬疑张力；这是审美参照，不仿制某集旋律、Logo或音效。

## Review Package

- [Director treatment](director-treatment.md)：整集审读、原创冷开场剧本、人物／空间、摄影和取舍。
- [Director coverage](director-coverage.json)：唯一的v4有序coverage，37秒是方案预算，不给对白排秒。
- [Shot and art preparation](shot-cards.md)：四个摄影／生成准备单元、中文语义稿、参考职责和前置缺口。
- [Music and sound](music-and-sound.md)：现有Music Director的spotting、原创主题、Suno准备和片尾延续。
- [Composition handoff](composition-handoff.md)：精确时间、矢量片名、字幕、声音分轨、S01保护和验收。
- `music/briefs.json`、`music/directions.json`、`music/*/dry-run.argv.json`：消费现有音乐API的离线产物；所有argv都含`--dry-run`，不是live入口。
- `assets/title-shizhen.paths.svg`：以实际CJK字体轮廓制作的透明静态片名字形资产；仍需P4排版与动态审看。
- `verification/preparation-receipt.json`：本包与源文件的实际身份、验证结果及证据边界。

## Current Delivery Boundary

本轮交付完整导演设计与离线制作准备。尚未生成冷开场视频、角色新美术或Suno音乐；没有新增Production revision、Registry asset、Manifest指针、permit或Final Acceptance。新人物美术、站台首帧、exact native profile／实际附件绑定仍待制作，`shot-cards.md`不是可直接POST的request。

当前S01原片与双语字幕版都只是输入引用，不编辑、不重生、不覆盖。旧Suno两个尝试的`auth_expired`与项目UNKNOWN保留；认证窗口独占修复，本窗口不生成、不解验证码、不改变旧请求或计数。配乐准备完成不等于Suno生产已恢复。
