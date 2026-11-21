# 技术笔记：把 MMD 模型替换进《龙之剑：觉醒》

> 成品下载：**[Releases · latest](https://github.com/xpjlhxhkh/DragonSword-Aria-Hanser-Mod/releases/latest)**
> （直接下文件：https://github.com/xpjlhxhkh/DragonSword-Aria-Hanser-Mod/releases/latest/download/zzzzDS_HanserFinal_P.pak）
> 安装/卸载/文件校验见 [README](../README.md)。

本文记录这次替换的完整链路和踩过的坑，尽量写成“照着做就能复现”的形式。

## 0. 环境与工具

| 用途 | 工具 / 路径 |
|---|---|
| 游戏 | 《龙之剑：觉醒》UE 5.3，Windows |
| 引擎 | Unreal Engine 5.3（`UnrealEditor-Cmd.exe`、`UnrealPak.exe`） |
| 建模 | Blender 4.5（MMD 模型用 mmd_tools 导入） |
| 读游戏 pak | CUE4Parse（游戏本体 pak 是 version 101，`UnrealPak -List` 读不了） |
| 解密 | AES key + 游戏 `.usmap`（映射文件），CUE4Parse 里先设 `MappingsContainer` 再 `Initialize()`，然后 `SubmitKey` → `Mount()` |

## 1. 资产路径与结构

```
DS\Content\Art\Character\Player\DS_Aria\
├─ Meshs\        ch_aria_mesh_body（主体网格，183 骨）、ch_aria_mesh_face / ingame_face / glasses（眼睛/脸/眼镜，做替换时可压成空网格）
│                M_body / M_skin / M_hair / M_wp（自建材质，放在 Meshs 而不是 Materials！）
├─ Materials\    ch_aria_base_{hair,wp,skin,body}_mi（游戏自己的材质实例）
├─ Textures\     T_hanser_atlas（自建图集，4096²）
└─ outline\      ch_aria_outline_hair_mi 等（游戏描边材质）
```

Mod 只需放到 `DS\Content\Paks\~mods\xxx_P.pak`，包内路径用 `../../../DS/Content/Art/...` 的挂载相对路径。

## 2. 关键机制：游戏按“槽位顺序”套材质

游戏在运行时创建 4 个 `MaterialInstanceDynamic`，**按槽位顺序**套它自己的材质表：

```
槽位 0 → ch_aria_base_hair_mi   （Unlit + Masked）
槽位 1 → ch_aria_base_wp_mi     （武器材质）
槽位 2 → ch_aria_base_skin_mi   （带 Matcap 的皮肤/脸材质）
槽位 3 → ch_aria_base_body_mi   （身体/衣服）
```

⇒ **我们网格的 4 个 section 必须按同样的语义排序**：

```
sec0 = 头发          (hair + 后发饰)
sec1 = 饰品          (手环/飘带/耳环/项圈…)
sec2 = 皮肤          (body/face/腿/脚趾甲/眼睛)
sec3 = 衣服 + 袜子   (连衣裙/腰带/领巾/袜子…)
```

顺序错了的典型症状：

- 皮肤被套上 hair MI（Masked）→ **皮肤一片黑**（遮罩不通过处被丢弃，露出黑色描边壳）
- 头发被套上 skin MI（带 Matcap）→ **头发反光**
- 衣服被套上 hair MI（Unlit）→ **一片死白**

## 3. 网格构建链路

```
ad_phys2.blend（MMD 导入 + 摆 A-pose + 材质分桶）
   │  dump_*.py：删 ARMATURE 修改器、按材质名分 4 桶、双面裙补反向三角
   ▼
mesh_src.npz（pos / uv / 顶点色无 / 骨索引+权重 / 三角+桶）
   │  glb_uv.py：拼 183 骨 glb（骨用游戏 refpose），posG=(x,z,y)，uvG=(u,1-v)
   ▼
xxx.glb（4 prim = 4 section）
   │  UE Python：导入 → 改骨架名 → 改网格名 → 4 槽挂自建材质
   ▼
UnrealEditor-Cmd -run=Cook -CookAll -TargetPlatform=Windows
   │
   ▼
UnrealPak <out> "-Create=rsp.txt" -compress=False      # rsp 每行 "<绝对路径> "../../../DS/Content/Art/…"
```

### 3.1 必须翻 V

`uvG = (u, 1 - v)`。漏了这一步的典型症状是“整身乌漆嘛黑 / 颜色错位”：我们的图集是稀疏 tile 图集（大量黑底），V 反了正好采到黑底。

### 3.2 三角绕序必须与原始网格一致（本项目的最大坑）

从 Blender 重新导出网格后，如果三角绕序与原始网格相反，UE 重新计算的**顶点法线会朝内**：

- 游戏 toon 材质按 NdotL 着色 → **皮肤算成纯黑**
- 而走 Unlit 材质的段（衣服）不受影响 → 依旧白
- 于是表现为“**皮肤黑、衣服白**”，非常容易被误判成贴图/材质问题

验证方法（离线、不需要进游戏）：读 cooked 网格的 `VertsFloat[i].Normal`，它是 `FPackedNormal[3]`：

```
[0] 切线基础
[1] 未使用（全 0）
[2] 法线
```

**三个通道的原始字节都要逐顶点比**。若 `[2]` 与参考网格逐字节互补，就是法线反了。

修法：导出时翻转绕序（`(v0,v1,v2) → (v2,v1,v0)`），重新导入、cook。修复后三个 packed normal 与参考网格逐字节一致。

### 3.3 自建材质必须开使用标记

脚本用 `unreal.MaterialFactoryNew` 新建的 `UMaterial`，`used_with_skeletal_mesh` 默认是 **False**，cook 出来不带蒙皮变体 → 挂到骨骼网格上时引擎回退默认灰材质（只有剧情/过场能看出来，因为正常游玩是 MID 覆盖槽位）。

必须设：

```python
mat.set_editor_property("used_with_skeletal_mesh", True)
mat.set_editor_property("used_with_morph_targets", True)
mat.set_editor_property("used_with_clothing", True)
```

重新编译后 cooked `M_*.uexp` 会从 ~170KB 涨到 ~369KB，uasset 里出现 `bUsedWithSkeletalMesh` 标记。

### 3.4 不要用 Unlit 覆盖游戏材质槽位

为了让颜色显示出来而把 `ch_aria_base_{hair,skin,body}_mi` 全部替换成自建 Unlit 材质，会把**游戏自带的明暗 + 描边**一起去掉，结果永远是“平板白 / 看不清细节”，再怎么调色偏和假明暗都救不回来。

正确做法：**保留游戏材质链**，只覆盖必要的 MI（本项目只覆盖了 `ch_aria_base_skin_mi` 一处来压掉头发高光）。

## 4. 手指权重

- 原模型的手是“掌 + 四指融合薄片”，且所有手指顶点权重都并进了 `hand_l/r`（指骨权重为 0），所以游戏里有手指轨道也不动。
- 做法：取 `hand_*` 权重 ≥0.5 的手区顶点（每侧约 1,317 个），按到 5 条指链（index/middle/ring/pinky/thumb × 01~03）骨段的距离，取最近 2 条链混合，指根 2cm 过渡带，最大指权重 0.95，其余权重乘 (1-F)，最后取 top-4 归一化。
- 离线弯曲测试（45°×3 节）：index 715 顶点位移 >2mm（最大 9.1cm）、pinky 112 顶点、非手部顶点位移 >2cm 的为 0（手掌不会被拽走）。

## 5. pak 组装与自检

- rsp 里每行 `"<绝对路径>" "../../../DS/Content/Art/..."`，`-Create` 整体加引号，不传 `-mount_point`。
- 包里**不要带 `*_Skeleton`**（否则游戏用自己的动画会失效），让游戏用它自己的骨架。
- 出包后回读自检：文件数、大小、SHA256、`4 段 tri 非空`、`材质槽指向正确`、`无 Skeleton`。

## 6. 目录/脚本说明

`tools/` 下是本项目实际用到的关键脚本（路径已脱敏，需按自己机器改）：

| 脚本 | 作用 |
|---|---|
| `aria_finger_weights2.py` | Blender：给手区加指骨权重 |
| `dump_aria_fing2.py` | Blender：导出网格数据（pos/uv/权重/三角+桶）到 npz |
| `glb_uv_fing3.py` | Blender：拼 183 骨 glb（含翻 V；绕序由上游 npz 决定） |
| `ue_aria_fing3.py` | UE：导入 glb、改名、挂 4 个材质槽 |

> 说明：这些脚本里写死了本机的盘符与工程路径，使用前请改成本机路径。
