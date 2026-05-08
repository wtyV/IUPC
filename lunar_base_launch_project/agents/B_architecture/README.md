# Agent B：任务架构智能体

## 职责

- 比较单发、两发 LEO 对接、三发冗余、40 t 单体 LEO 组合方案。
- 维护 `src/architecture.py` 和 `src/rendezvous.py`。
- 输出 `architecture_summary.csv` 和 `rendezvous_plan.csv`。

## 当前性能

状态：可用。  
主方案：两发长征十号，每发约 20 t，在 LEO 交会对接后组合 TLI。  
强项：能把“单发不可行”和“两发可行”讲清楚。  
短板：LEO 交会对接目前是一阶相位/速度增量模型，不是完整 GNC 仿真。

