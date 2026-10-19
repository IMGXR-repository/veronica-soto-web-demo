# 模型许可声明 / Model License Notice

本文件适用于本仓库中的 **`models/anatomy.glb`**。

This notice applies to **`models/anatomy.glb`** in this repository.

---

## 原始数据来源 / Original Data Source

本模型有**两层上游来源**，署名时请一并保留。
This model has **two upstream layers**; please credit both.

### 1. BodyParts3D —— 原始数据 / original data

Database Center for Life Science (DBCLS), 日本 / Japan

- 项目主页 / Project page: <https://dbarchive.biosciencedbc.jp/en/bodyparts3d/desc.html>
- 原始许可 / Original license: **Creative Commons Attribution-ShareAlike 2.1 Japan**
  (<https://creativecommons.org/licenses/by-sa/2.1/jp/deed.zh>)

BodyParts3D 是日本 DBCLS 基于人体 MRI 影像分割构建的三维解剖模型数据集，依
CC BY-SA 2.1 JP 许可公开发布。

BodyParts3D is a 3D anatomical model dataset built by DBCLS (Japan) from
segmented human MRI volumes, released under CC BY-SA 2.1 Japan.

### 2. Z-Anatomy —— 整理与分发 / curation and distribution

- 项目主页 / Project page: <https://www.z-anatomy.com/>
- 上游许可 / Upstream license: **CC BY-SA**（ShareAlike）

开源 3D 解剖图谱项目，对 BodyParts3D 等公开数据集做了整理、命名与再分发。
An open-source 3D anatomy atlas project that curates, names, and redistributes
public datasets such as BodyParts3D.

> 本仓库模型的具体获取渠道为 Z-Anatomy 整理后的版本。若上游署名要求有更细的
> 规定，以 Z-Anatomy 项目的声明为准。
>
> The model in this repository was sourced from a Z-Anatomy distribution. If the
> upstream project specifies stricter attribution, defer to Z-Anatomy's notice.

---

## 本仓库中的文件是衍生作品 / Derivative Work

`models/anatomy.glb` **不是** BodyParts3D 的原始分发文件，而是经过以下处理后的
衍生作品 / is a derivative work produced by the following modifications:

| 处理 / Modification | 说明 / Detail |
| --- | --- |
| 裁剪 / Cropping | 截取全身范围，剔除多余部分 |
| 坐标系变换 / Axis conversion | Z-up 转为 Y-up（`rotation.x = -π/2`） |
| 单位换算 / Unit scaling | 毫米制转为米制（比例 ≈ 0.0010774，身高归一为 1.780 m） |
| 网格重命名 / Mesh renaming | 网格名重写为肌肉 id，以与页面的数据表对齐 |
| 属性剔除 / Attribute stripping | 移除 NORMAL 属性以减小体积，运行时重算法线 |

因此，**该文件整体继续受 CC BY-SA 2.1 JP 许可约束**，不得以更宽松的许可再分发。
Therefore this file **remains licensed under CC BY-SA 2.1 JP** and may not be
redistributed under a more permissive license.

---

## 你需要做什么 / Your Obligations

若你使用、修改或再分发 `models/anatomy.glb`：

If you use, modify, or redistribute `models/anatomy.glb`:

1. **署名 / Attribution** —— 必须注明数据来自 BodyParts3D / DBCLS，并附原始许可链接。
   You must credit BodyParts3D / DBCLS and link to the original license.

2. **相同方式共享 / ShareAlike** —— 若你发布了修改后的版本，该版本必须同样以
   CC BY-SA 2.1 JP（或与之兼容的 ShareAlike 许可）发布。
   If you publish a modified version, it must be released under CC BY-SA 2.1 JP
   (or a compatible ShareAlike license).

3. **保留声明 / Keep notices** —— 不得移除本文件与本仓库 README 中的许可声明。
   Do not remove the license notices in this file or in the repository README.

### 署名范例 / Attribution template

> 解剖模型数据来自 BodyParts3D（Database Center for Life Science, Japan），
> 依 CC BY-SA 2.1 Japan 许可使用。
> Anatomical mesh data from BodyParts3D (Database Center for Life Science,
> Japan), used under CC BY-SA 2.1 Japan.

---

## 许可范围边界 / Scope Boundary

**ShareAlike 的传染性仅作用于模型及其衍生作品本身。**

The ShareAlike condition applies **only to the model and its derivatives**.

`index.html` 中的渲染代码、交互逻辑、UI 与样式是独立作品，以 **MIT** 许可发布
（见 [`LICENSE`](LICENSE)）——它们在运行时会*加载*模型，但本身不构成对模型的
改编。仅将其嵌入你的网页、改变其配色或展示方式，**不会**使你的页面受 ShareAlike
约束。

The rendering code, interaction logic, UI, and styles in `index.html` are an
independent work released under the **MIT** license (see [`LICENSE`](LICENSE)).
They *load* the model at runtime but do not themselves constitute an adaptation
of it. Embedding the model in your own page, or changing its colors or display,
does **not** subject your page to the ShareAlike condition.

> ⚠️ 以上为技术性说明，**不构成法律意见**。若用于商业产品，建议自行核对官方
> 许可条款或咨询法律专业人士。
>
> The above is a technical description and **does not constitute legal advice**.
> For commercial use, please verify the official license terms yourself or
> consult a legal professional.
