# Shizhen Reference Images

本目录仅集中存放《失帧》的图片参考素材归档副本，保留目录名 `referces`。

## Browse

- 新补主角参考见 [Lin Xu Reference Expansion](shizhen/lin-xu/expanded-20261027/README.md)，可打开 [图片总览](shizhen/lin-xu/expanded-20261027/index.html)；本组以已生成成片帧为身份依据，独立保留生成记录。
- 图片按原来源目录结构存放在 `runs/shizhen-*/` 和 `outputs/shizhen-episode01/` 子目录下。
- [index.csv](index.csv) 列出每个原路径、当前副本相对路径、SHA-256、大小和收录原因；同一 SHA-256 的图片只保存一份，多个来源指向同一副本。
- [verification.json](verification.json) 保存本次整理的计数及完整性核验结果。

## Scope

本次仅收录《失帧》运行和输出目录中 Registry 登记的图片、明确的 reference/input/image 目录内图片，以及以角色或参考用途命名的图片。其他项目的归档副本已移除，原始素材未改动。未扫描仓库外目录，也不将所有视频抽帧作为参考素材收录。

收录不表示素材已通过质量审查或适用于当前镜头。相同 bytes 去重不合并其不同来源和用途，原始关联保留在索引中。

## Preservation

本次仅复制、核验，没有移动或删除原文件，没有修改已有项目引用、Registry 或 Manifest。已封存的 Production 仍引用其原路径；本目录不拥有生产资产身份或验收状态。这里是本次整理的快照，后续新增素材不会自动同步。

图片文件保持本地存储，遵循仓库既有媒体管理方式；Git 仅保存本目录说明、来源索引和核验记录。
