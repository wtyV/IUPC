# 多智能体协作流程 v0.6

## 1. 协作原则

每个智能体只改自己拥有的文件；需要跨文件修改时，先在交接记录中说明原因。所有数值结果必须能由 `python src/run_baseline.py` 或后续对应脚本复现。

## 2. 标准交接格式

每个智能体完成任务后，输出以下信息：

```text
Agent:
Changed files:
Assumptions added:
Generated outputs:
Validation:
Open issues:
Next suggested step:
```

## 3. 当前执行链

```text
A_problem_sources
  -> B_architecture
  -> C_reliability
  -> D_transfer
  -> E_launch_geometry
  -> F_ascent
  -> G_optimization
  -> H_review
```

## 4. 检查清单

- 公开参数与假设参数是否分开。
- 所有质量单位统一为 t 或 kg，表格中标注清楚。
- 所有速度单位统一为 m/s 或 km/s，表格中标注清楚。
- 可靠性公式是否区分发动机簇、单发火箭和多发任务。
- 图表是否能从代码重新生成。
- 结论是否超过公开资料能支持的范围。

## 5. 可见目录

每个智能体都有自己的目录：

```text
agents/A_problem_sources
agents/B_architecture
agents/C_reliability
agents/D_transfer
agents/E_launch_geometry
agents/F_ascent
agents/G_optimization
agents/H_review
```

每个目录至少包含：

- `README.md`：职责、拥有文件、性能状态。
- `handoff.md`：最近一次交付和下一步问题。
