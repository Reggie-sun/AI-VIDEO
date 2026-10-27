# Shizhen Reference Images

本目录仅集中存放《失帧》的图片参考素材归档副本，保留目录名 `referces`。

## Browse

- 新增 [第一季其余16名角色总览](shizhen/season-cast-20261027/index.html)：16张四视角身份合图，另为林晚、周竞、谢振宇、陆建平各补一张场次参考；[选用清单与记录](shizhen/season-cast-20261027/README.md)。
- 新增 [董文慧、罗敏、高峥、闻素芬四人总览](shizhen/character-packs-20261027/index.html)：每套独立存放人物身份底图和当前场次参考，取材、职业／性格依据及候选状态见 [说明](shizhen/character-packs-20261027/README.md)。
- 第一集快递员见 [简单三视图进度](shizhen/courier/three-views-20261027/README.md)：正面、侧面已返回；背面调用UNKNOWN，未重复提交。
- 本机前端：[参考素材库](http://127.0.0.1:5174/?view=references)，或点击左侧“素材”／顶部“参考素材”。支持文件名和目录搜索、分页、完整图片放大；直接读取本目录的 PNG/JPEG/WebP，新图片落盘后自动更新。只读浏览不建立 Shot 绑定或质量验收。
- 主角合板见 [林序人物参考板 PNG](shizhen/lin-xu/expanded-20261027/boards/lin-xu-identity-board-v2.png)；独立单图见 [图片总览](shizhen/lin-xu/expanded-20261027/index.html)，来源与状态见 [Lin Xu Reference Expansion](shizhen/lin-xu/expanded-20261027/README.md)。本组以已生成成片帧为身份依据。
- 图片按原来源目录结构存放在 `runs/shizhen-*/` 和 `outputs/shizhen-episode01/` 子目录下。
- [index.csv](index.csv) 列出每个原路径、当前副本相对路径、SHA-256、大小和收录原因；同一 SHA-256 的图片只保存一份，多个来源指向同一副本。
- [verification.json](verification.json) 保存本次整理的计数及完整性核验结果。

## Scope

本次仅收录《失帧》运行和输出目录中 Registry 登记的图片、明确的 reference/input/image 目录内图片，以及以角色或参考用途命名的图片。其他项目的归档副本已移除，原始素材未改动。未扫描仓库外目录，也不将所有视频抽帧作为参考素材收录。

收录不表示素材已通过质量审查或适用于当前镜头。相同 bytes 去重不合并其不同来源和用途，原始关联保留在索引中。

## Preservation

本次仅复制、核验，没有移动或删除原文件，没有修改已有项目引用、Registry 或 Manifest。已封存的 Production 仍引用其原路径；本目录不拥有生产资产身份或验收状态。这里是本次整理的快照，后续新增素材不会自动同步。

图片文件保持本地存储，遵循仓库既有媒体管理方式；Git 仅保存本目录说明、来源索引和核验记录。
