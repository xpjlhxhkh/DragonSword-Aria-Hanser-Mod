# 龙之剑：觉醒 · 阿莉娅（Aria）← hanser 模型替换 Mod

[![Download](https://img.shields.io/badge/⬇_下载成品-v1.0.0-2ea44f?style=for-the-badge)](https://github.com/xpjlhxhkh/DragonSword-Aria-Hanser-Mod/releases/latest)
[![Release](https://img.shields.io/github/v/release/xpjlhxhkh/DragonSword-Aria-Hanser-Mod?style=for-the-badge&label=Release)](https://github.com/xpjlhxhkh/DragonSword-Aria-Hanser-Mod/releases/latest)
[![Technotes](https://img.shields.io/badge/📘_技术笔记-docs/TECHNICAL.md-blue?style=for-the-badge)](docs/TECHNICAL.md)

> **快速入口**
> - ⬇️ 下载成品 pak：**[Releases · latest](https://github.com/xpjlhxhkh/DragonSword-Aria-Hanser-Mod/releases/latest)**（约 84.9 MB）
> - 📦 所有版本：**[Releases 列表](https://github.com/xpjlhxhkh/DragonSword-Aria-Hanser-Mod/releases)**
> - 📘 制作流程与踩坑：**[docs/TECHNICAL.md](docs/TECHNICAL.md)**
> - 🗂 关键脚本：**[tools/](tools/)**

把《龙之剑：觉醒》（DragonSword: Awakening，UE 5.3）里可操作角色 **阿莉娅 Aria** 的模型替换成 **hanser** 的 MMD 模型（白水手服 + 深蓝领 + 白袜、棕色短发那套）。

- ✅ 模型几何真的换了（不是换贴图）
- ✅ 骨骼用游戏原版 A-pose 骨架，动作 / 武器挂点 / 相机全部正常
- ✅ 剧情、过场、大世界、角色展示页外观一致（贴图方向、材质用法均已修正）
- ✅ 头发无高光（已按需求压掉 Matcap 反光）
- ✅ 五指会跟随动画弯曲（融合薄片整片弯曲，允许合理拉伸）
- ⚠️ 未做：布料/头发物理、换装（epic/rare）自带网格的替换

## 效果

| 大世界 / 角色页 | 剧情过场 |
|---|---|
| 皮肤、衣物、袜子、头发颜色与图集一致，带游戏自带描边与明暗 | 使用自建 Unlit 材质 + 烘焙图集，颜色与游戏内一致 |

（效果图可自行进游戏查看；本仓库不附带游戏截图。）

## 下载

成品 pak 在 Release 里（仓库本身只放文档与脚本，不放 89MB 的二进制）：

| 方式 | 地址 |
|---|---|
| 直接下载文件 | https://github.com/xpjlhxhkh/DragonSword-Aria-Hanser-Mod/releases/latest/download/zzzzDS_HanserFinal_P.pak |
| Release 页面 | https://github.com/xpjlhxhkh/DragonSword-Aria-Hanser-Mod/releases/tag/v1.0.0 |

| 项 | 值 |
|---|---|
| 文件 | `zzzzDS_HanserFinal_P.pak` |
| 大小 | 89,028,129 字节（约 84.9 MB） |
| SHA256 | `FCB3BC3C596A31ED90FEE4473E13F3697E737066E3669986885C9B8883DD8E00` |

## 安装

1. 找到游戏安装目录下的 Pak 目录，例如：

   ```
   <SteamLibrary>\steamapps\common\DragonSword  Awakening\DS\Content\Paks\
   ```

2. 在 `Paks` 下新建（或使用已有的）`~mods` 文件夹：

   ```
   ...\DS\Content\Paks\~mods\
   ```

3. 把 `zzzzDS_HanserFinal_P.pak` 放进 `~mods\`，重启游戏即可。

   ```
   ~mods\zzzzDS_HanserFinal_P.pak
   ```

> 文件名以 `zzzz` 开头是为了让本包在挂载顺序里靠后，覆盖游戏本体资产。

## 卸载

删除 `~mods\zzzzDS_HanserFinal_P.pak` 并重启游戏即可，不会改动任何游戏原文件。

## 文件信息

| 项 | 值 |
|---|---|
| 文件 | `zzzzDS_HanserFinal_P.pak` |
| 大小 | 89,028,129 字节（约 84.9 MB） |
| 文件数 | 85 |
| SHA256 | `FCB3BC3C596A31ED90FEE4473E13F3697E737066E3669986885C9B8883DD8E00` |
| 游戏版本 | 《龙之剑：觉醒》UE 5.3（Windows） |
| 安装位置 | `DS\Content\Paks\~mods\` |

## 已知限制

- 手指是“整片按指骨弯曲”，不是逐指完全独立：模型的手是掌 + 四指融合的薄片（最大连通块 1,411 顶点），要做到逐指独立必须先切缝改拓扑。
- 头发/裙摆没有物理（替换网格吃不到游戏的 KawaiiPhysics），只有骨骼刚性跟随。
- 如果游戏后续换装系统使用独立的 costume 网格，那套衣服不会被替换（本 Mod 只替换 `ch_aria_mesh_body`）。

## 技术要点（做同款 Mod 可以直接抄）

完整流程与踩过的坑见 [docs/TECHNICAL.md](docs/TECHNICAL.md)，核心几条：

1. **网格必须恰好 4 段且段顺序 = 游戏期望的槽位语义**（游戏按槽位顺序套它自己的材质表，顺序错了就会出现“皮肤发黑/头发反光”）。
2. **导出 glb 必须翻 V**（`uv[:,1] = 1-uv[:,1]`），否则整身颜色错位。
3. **重建网格时三角绕序必须与原始网格一致**，否则 UE 算出的顶点法线朝内，游戏 toon 材质会把皮肤算成全黑。
4. **自建材质必须打开 `used_with_skeletal_mesh`**，否则剧情/过场里会回退默认灰材质。
5. **不要用 Unlit 材质去覆盖游戏材质槽位**——会把游戏自带的明暗和描边全部去掉，观感变成“平板白”。

## 版本历史

| 版本 | 说明 |
|---|---|
| v1–v3 | 网格替换打通（4 槽、骨骼对齐、pak 结构） |
| v4 | 补材质 usage flag（修剧情“灰模型”） |
| v5 | 图集 V 翻转（修“贴图串色/全黑”） |
| v7 | 覆盖 `ch_aria_base_skin_mi` 压掉头发高光（验收版） |
| v8–v14 | 手指权重 / 段顺序重排 / 材质覆盖实验（均被回退） |
| **v15** | **最终版**：修复重建网格法线反向 + 五指权重（本仓库发布版） |

## 致谢与免责

- 模型：**hanser** 的 MMD 模型（版权归原作者；本仓库只做格式转换与骨骼适配，不再分发原始模型文件）。
- 游戏：《龙之剑：觉醒》，版权归其开发商 / 发行商所有。
- 本项目仅为个人学习与自用目的制作，**请勿用于商业用途**；如相关权利方认为不妥，请联系删除。
