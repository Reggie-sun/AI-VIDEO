# MC00 City Reference Revision

## Review

本轮承接用户认可的“城市总图＋连贯写实参考”方向，停止完整城市白模，不修饰或复用已退回的 proxy 视频。打开 [index.html](index.html) 查看屋檐、城市展开、下降接近与真实市政末态；[完整开场参考包](../full-opening-references-20261027/index.html) 继续保留 MC01–06 和完整 B6。

已将新图中横断接近路线的水泥围墙／高台移除，近处住宅回到站棚之前，市政前方改为开放连续铺地。照片只能支持这些可见空间判断，不能证明精确地坪高差、全城逐建筑对应或实际移动。当前为静态候选，未获用户新一轮接受、未绑定 Production 或正式视频请求。

## Layout And Source Duties

- [city-map.svg](city-map.svg) 是可编辑顶视设计，PNG 为 Chromium 直接渲染。它独立于退回白模，不来自该 blend。方向、高度和街区位置都是本轮新地理设计；图中轨迹是设计线，不是实测轨迹。
- `02-eave-start-v1.png`：屋檐、外转角及局部城市的起幅候选。旧起幅图仅提供湿墙和檐口取景，修订城市图提供城市氛围；不声称视差或摄影轨迹已得到模型保证。
- `01-city-reveal-v2.png`：城市展开后的主参考；修正 v1 的高台与围墙。道路、近处住宅、站棚与市政区的可见关系供审看，站棚不承担 B6 身份锚点。
- `03-descent-v1.png`：下降接近时的观察位置。与市政实拍锚点同侧，可见站棚北端开放地面；未作为精确市政入口、完整机械连接或动作参考通过。
- [MC01-normal.png](../full-opening-references-20261027/MC01-normal.png)：已认可市政原片第 0 帧，SHA `a2cef0e9ff42796e09e72105bb04ea336149b4551a20dc767ffdd3179910eeed`，仍是唯一末态锚点。新照片不覆盖它。原 MP4 SHA `b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d` 本轮重新核对一致。
- [B6-entry.png](../full-opening-references-20261027/B6-entry.png) 只给新城市图提供站棚形制，不允许把两人、钟读数或异常事件迁入 MC00。完整 B6 SHA `d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a` 重新核对一致。

## Generation And Review

本轮使用内置 `image_gen.imagegen` / `imagegen` Skill，纯中文实际提示词为本目录四份 `*-prompt.zh.txt`。新单元上限四次、45 分钟：城市展开、一次针对地坪／围墙和住宅纵深的修订、屋檐、下降；全部 known 返回，原始 PNG exact copy 留存。v1 高台版 `FAIL` 保留，不覆盖。未重抽、未换工具，未生成视频或音乐。具体模型和结算金额工具未暴露，标待确认，不推断免费。

四份实际输入顺序、SHA、提示词身份及输出见 [generation-intent.json](generation-intent.json)，文件规格与静态审查边界见 [verification.json](verification.json)。静态候选不等于一镜到底、声音、逐镜 Gate 或人工验收通过。

## Known Gaps

站棚仍有广告板／框体偏厚，与 B6 的通透玻璃形制存在偏差；下降图提示已要求修正，但不能据提示词假称执行成功。两张城市图仅承担道路与入口位置审看，不可升级为站棚身份母图。路灯比 MC01 整体更暖，远景机械索端细节仍不足。

住宅、站棚与市政在三张图中的逐构件对应和真实显露顺序没有动态证据；雨线、车流、工人手势、门速与尾帧如何连续衔接仍 `NOT_EVALUATED`。静态画面不能判定工人是否提前按停，更不能证明没有重复动作。未新增或延续白模视频，未伪造连续预演。下阶段需要先解决实际输入条件及必要的模型控制缺口，不能凭图漂亮就提交。

当前选定 2.5 首尾帧模式只实际接受首／尾两图，不能把城市中间图、位置图或失败 proxy 视频悄悄作为额外控制。新增图未消除既有 conditioning 的景别兼容性缺口；七项兼容性证据仍未签真，不修改共享 contract 绕过。楼梯原 FAIL 继续阻止后续正式视频推进。

## Verification Boundary

四次输入／输出 SHA、纯中文 prompt、21 项总览 exact 源与页面本地链接已核对；浏览器实际加载7／21张图，桌面与手机无横向溢出，文档 contract 通过。对本次 exact commit range 尝试 Harness focused 后，因 `referces/` 的提示词、SVG、HTML、JSON 无 module mapping 而在执行前拒绝，未取得该范围的 focused receipt。此项明确为验证映射缺口，不扩大运行无关全套测试、不调整 Gate 放行，也不冒称工程或媒体验收通过。实际已完成的素材／页面检查见本目录 verification 与 browser-review。
