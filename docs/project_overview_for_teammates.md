# 国际大物 Problem B 项目总览与交接说明

更新时间：2026-05-08  
项目根目录：`G:\国际大物`

本文档用于给同学快速了解当前项目已经完成了什么、每一部分在哪里、如何继续工作、如何在 VS Code 中保存/管理文件，以及如何打包发送项目。

---

## 1. 项目一句话概括

本项目解决的是 Problem B: Lunar Base Construction。当前主方案是：

```text
两发长征十号
每发约 20 t 月球基地货运模块
先进入近地轨道 LEO
两个模块在 LEO 交会对接
组合体执行 TLI
进入地月转移轨道
```

为什么不是单发？

```text
长征十号公开 TLI 运力约 >= 27 t
题目要求总计 40 t 载荷进入地月转移轨道
所以单发 40 t 直接 TLI 不可行
```

为什么可以两发？

```text
题目载荷是月球基地原材料，可拆分为两个约 20 t 模块。
两发方案更贴近工程可行性，也借鉴了中国载人登月“两次发射 + 在轨交会对接”的任务思想。
```

---

## 2. 原始资料在哪里

原始题目和前期说明仍在项目根目录的 `docs` 文件夹中：

```text
G:\国际大物\docs
```

重要文件：

| 文件 | 作用 |
|---|---|
| `docs/notes.md` | 原始 Problem B 题意和最初想法 |
| `docs/menu.md` | 项目大纲、建模路线、智能体分工的早期规划 |
| `docs/problem_day_1.md` | 昨天问题的解决思路，指出长征十号发动机参数和任务目标解释问题 |
| `docs/2026空天飞行力学-弹道学大作业要求.md` | 参考上升段、程序角、大气、J2、结果图表等建模风格 |

---

## 3. 当前正式工作区在哪里

当前所有新建模型、代码、结果、智能体、论文草稿都放在：

```text
G:\国际大物\lunar_base_launch_project
```

建议同学从这个文件夹开始看。

---

## 4. 推荐阅读顺序

建议按下面顺序阅读：

1. `lunar_base_launch_project\README.md`  
   看项目主结论和目录。

2. `lunar_base_launch_project\docs\modeling_v0.md`  
   看数学物理建模主线。

3. `lunar_base_launch_project\docs\assumptions_and_sources.md`  
   看公开资料、假设和引用来源。

4. `lunar_base_launch_project\results\tables\baseline_summary.json`  
   看当前最重要的数值结果。

5. `lunar_base_launch_project\paper_draft_v0\paper_skeleton.md`  
   看论文草稿骨架。

6. `lunar_base_launch_project\paper_draft_v0\figure_table_plan.md`  
   看论文图表编号和每张图/表的用途。

---

## 5. 工作区各部分说明

### 5.1 文档区

位置：

```text
G:\国际大物\lunar_base_launch_project\docs
```

文件说明：

| 文件 | 内容 |
|---|---|
| `assumptions_and_sources.md` | 假设、公开资料来源、长征十号/Starship/中国登月方案引用 |
| `modeling_v0.md` | 当前数学物理建模主文档 |
| `next_steps.md` | 下一阶段建议 |

当前建模文档已经覆盖：

- 单发不可行性分析。
- 两发 LEO 交会对接主方案。
- LEO 到 TLI 的 Hohmann 型估算。
- LEO 交会对接模型。
- ECI/J2 上升段代理模型。
- 可靠性链。
- TLI 质量预算。
- J2 与球形引力对照。

---

### 5.2 智能体区

位置：

```text
G:\国际大物\lunar_base_launch_project\agents
```

这里的智能体不是后台运行程序，而是项目协作分工目录。每个 Agent 都有自己的职责说明和交接文件。

| Agent | 位置 | 职责 |
|---|---|---|
| A_problem_sources | `agents\A_problem_sources` | 题目解析、资料来源、假设边界 |
| B_architecture | `agents\B_architecture` | 任务架构、两发/三发/单体方案比较、LEO 交会 |
| C_reliability | `agents\C_reliability` | 发动机簇、多发任务、可靠性链 |
| D_transfer | `agents\D_transfer` | TLI 速度增量、TLI 质量预算 |
| E_launch_geometry | `agents\E_launch_geometry` | 文昌发射点、自转收益、方位角-倾角关系 |
| F_ascent | `agents\F_ascent` | 上升段 2D/ECI/J2 模型 |
| G_optimization | `agents\G_optimization` | 程序角、交会轨道等粗网格优化 |
| H_review | `agents\H_review` | 自检、单位、复现检查 |

总注册表：

```text
lunar_base_launch_project\agents\agent_registry.yaml
```

协作流程：

```text
lunar_base_launch_project\agents\workflow.md
```

每个 Agent 文件夹里一般有：

```text
README.md   # 职责和当前性能
handoff.md  # 当前交接状态和下一步
```

---

### 5.3 代码区

位置：

```text
G:\国际大物\lunar_base_launch_project\src
```

主要代码文件：

| 文件 | 功能 |
|---|---|
| `run_baseline.py` | 主运行脚本，生成所有表格和 SVG 图 |
| `self_check.py` | 自检脚本，检查关键公式和结果数量级 |
| `architecture.py` | 任务架构比较 |
| `rendezvous.py` | LEO 交会对接一阶模型 |
| `transfer.py` | LEO 到 TLI 的 Hohmann 型估算 |
| `mass_budget.py` | LEO 组合体 TLI 质量预算 |
| `reliability.py` | 发动机簇、多发任务、可靠性链模型 |
| `launch_geometry.py` | 文昌发射几何、自转收益 |
| `ascent_3dof.py` | 2D 上升段代理模型 |
| `ascent_eci.py` | ECI 三维点质点上升段模型，含 J2 选项 |
| `atmosphere.py` | 简化大气密度模型 |
| `frames.py` | 坐标和地球自转工具 |
| `objectives.py` | 优化目标函数 |
| `optimize.py` | 粗网格优化 |
| `svg_charts.py` | 无第三方依赖的 SVG 曲线图生成工具 |

---

### 5.4 结果区

位置：

```text
G:\国际大物\lunar_base_launch_project\results
```

里面分为：

```text
results\figures       # SVG 图
results\tables        # CSV/JSON 表格
results\trajectories  # 轨迹 CSV
```

重要图：

| 图文件 | 内容 |
|---|---|
| `launch_geometry.svg` | 文昌发射方位角、倾角、自转收益 |
| `rendezvous_plan.svg` | LEO 交会相位轨道估算 |
| `tli_delta_v.svg` | LEO 高度与 TLI delta-v |
| `tli_mass_budget.svg` | TLI 质量预算 |
| `ascent_eci_altitude_speed.svg` | ECI 上升段高度和速度 |
| `ascent_mass_q.svg` | 质量和动压 |
| `mission_reliability.svg` | 两发/三发可靠性对比 |
| `mission_chain_reliability.svg` | 两发 + 对接 + TLI 总可靠性链 |
| `mission_chain_sensitivity.svg` | 对接可靠性和 TLI 可靠性的敏感性 |
| `engine_cluster_reliability.svg` | 发动机簇可靠性 |
| `optimization_scores.svg` | 优化评分 |

重要表：

| 表文件 | 内容 |
|---|---|
| `baseline_summary.json` | 当前最重要结果汇总 |
| `architecture_summary.csv` | 四种任务架构比较 |
| `rendezvous_plan.csv` | LEO 交会对接估算 |
| `delta_v_budget.csv` | TLI delta-v 表 |
| `tli_mass_budget.csv` | TLI 质量预算 |
| `gravity_model_comparison.csv` | J2 与球形引力对照 |
| `mission_chain_reliability.csv` | 总可靠性链 |
| `mission_chain_sensitivity.csv` | 可靠性敏感性 |
| `optimization_summary.csv` | 程序角和交会轨道优化结果 |

---

### 5.5 论文草稿区

位置：

```text
G:\国际大物\lunar_base_launch_project\paper_draft_v0
```

这是论文草稿骨架，不是最终正文。

文件说明：

| 文件 | 内容 |
|---|---|
| `README.md` | 论文草稿文件夹说明 |
| `paper_skeleton.md` | 论文标题、摘要占位、章节骨架 |
| `figure_table_plan.md` | 论文图表编号和每张图/表的用途 |
| `reproduction_notes.md` | 如何复现结果 |
| `writing_todo.md` | 后续写正文前的任务清单 |

手工画的论文架构图在：

```text
G:\国际大物\lunar_base_launch_project\paper_draft_v0\figures\fig2_architecture.svg
```

这张图是论文中的 Fig. 2，用来说明：

```text
Launch 1 -> Module A in LEO
Launch 2 -> Module B in phasing LEO
LEO rendezvous and docking
Combined stack
TLI
Earth-Moon transfer orbit
```

---

## 6. 当前关键结果

当前推荐方案：

```text
Architecture B: two Long March 10 launches with LEO rendezvous and combined TLI
```

关键数值：

| 项目 | 当前结果 |
|---|---:|
| 单发长征十号公开 TLI 运力 | >= 27 t |
| 题目要求总载荷 | 40 t |
| 每发货运模块 | 约 20 t |
| 300 km LEO 到 TLI delta-v | 约 3.108 km/s |
| LEO 交会示例等待时间 | 约 18.5 h |
| LEO 交会总 delta-v | 约 43 m/s |
| 名义 LEO 初始组合体质量 | 约 96.9 t |
| 每发 LEO 湿质量需求 | 约 48.5 t |
| ECI 上升段末端高度 | 约 306.9 km |
| ECI 上升段末端惯性速度 | 约 7.723 km/s |
| ECI 末端飞行路径角 | 约 -0.02 deg |
| 名义任务可靠性链 | 约 0.871 |
| J2 相对球形引力末端高度差 | 约 -2.27 km |

---

## 7. 如何运行和复现结果

进入：

```powershell
G:\国际大物\lunar_base_launch_project
```

运行：

```powershell
python .\src\run_baseline.py
python .\src\self_check.py
```

如果 VS Code 终端工作目录有问题，也可以在 `G:\国际大物` 下运行绝对路径：

```powershell
python G:\国际大物\lunar_base_launch_project\src\run_baseline.py
python G:\国际大物\lunar_base_launch_project\src\self_check.py
```

正常输出应包含：

```text
self_check passed
```

---

## 8. 接下来可以做什么

建议下一步工作：

1. 把 `paper_draft_v0\paper_skeleton.md` 扩写成正式论文正文。
2. 检查 Fig. 2 架构图是否需要美化。
3. 把所有 SVG 图统一成论文格式。
4. 对长征十号/YF-100K 参数做更保守的引用说明。
5. 加入月球相位、发射窗口或更真实星历模型。
6. 把 LEO 交会对接可靠性和 TLI 可靠性写成敏感性分析，而不是固定真值。
7. 如允许使用第三方库，可以用 `scipy` 做更正式的优化。

---

## 9. VS Code 中怎么保存文件

### 9.1 保存当前文件

快捷键：

```text
Ctrl + S
```

菜单：

```text
File -> Save
```

### 9.2 保存所有打开的文件

快捷键：

```text
Ctrl + K，然后按 S
```

注意这是一个组合快捷键：先按 `Ctrl+K`，松开后再按 `S`。

菜单：

```text
File -> Save All
```

### 9.3 自动保存

可以打开：

```text
File -> Auto Save
```

打开后，VS Code 会自动保存正在编辑的文件。

### 9.4 我刚才生成的文件需要手动保存吗？

不需要。  
由我通过工具创建或修改的文件已经直接写入磁盘，不是 VS Code 里的“未保存草稿”。你只需要在 VS Code 里刷新或重新打开文件即可看到。

---

## 10. VS Code 左侧“源代码管理”是什么

左侧的“源代码管理”就是 Git 管理界面。

它的作用不是“保存文件”，而是“记录项目版本”。

它可以做：

- 查看哪些文件被修改了。
- 查看每个文件改了什么。
- 暂存文件。
- 写提交信息。
- 提交 commit。
- 如果连接了远程仓库，还可以 push/pull。

常见概念：

| 操作 | 含义 |
|---|---|
| Save | 保存文件到硬盘 |
| Stage | 选择哪些修改准备进入下一次 commit |
| Commit | 记录一个项目版本 |
| Push | 上传到远程仓库 |
| Pull | 从远程仓库拉取更新 |
| Discard | 丢弃修改，慎用 |

注意：

```text
不要随便点 Discard Changes
```

它会丢掉文件修改。

当前项目中还有一些原始文件状态，比如：

```text
docs/problem_day_1.md
docs/~$menu.docx
```

这些不是本次新项目核心文件，提交或打包时要留意。

---

## 11. 这个项目可以整体打包发给别人吗

可以。

推荐打包这个文件夹：

```text
G:\国际大物\lunar_base_launch_project
```

这个文件夹已经包含：

- 模型文档。
- 智能体分工。
- Python 代码。
- 结果表格。
- SVG 图。
- 轨迹数据。
- 论文草稿。

如果同学还需要看原始题目和老师给的材料，也可以打包整个：

```text
G:\国际大物
```

但一般推荐先发：

```text
lunar_base_launch_project
```

这样更干净。

### 11.1 Windows 资源管理器打包

右键：

```text
lunar_base_launch_project
```

选择：

```text
发送到 -> 压缩(zipped)文件夹
```

### 11.2 PowerShell 打包命令

可以在 `G:\国际大物` 下运行：

```powershell
Compress-Archive -Path .\lunar_base_launch_project -DestinationPath .\lunar_base_launch_project.zip -Force
```

生成：

```text
G:\国际大物\lunar_base_launch_project.zip
```

### 11.3 打包时可忽略的文件

可以忽略：

```text
__pycache__
*.pyc
```

当前项目里已经有：

```text
lunar_base_launch_project\.gitignore
```

用于避免 Python 缓存文件进入版本管理。

---

## 12. 给同学的最短说明

如果只给同学一句话：

```text
请先打开 G:\国际大物\lunar_base_launch_project\README.md，
再看 docs\modeling_v0.md 和 paper_draft_v0\paper_skeleton.md。
运行 src\run_baseline.py 可以复现所有结果图表。
```

