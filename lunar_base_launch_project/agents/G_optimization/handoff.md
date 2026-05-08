Agent: G_optimization
Changed files: src/objectives.py, src/optimize.py
Assumptions added: 以末端高度、速度、飞行路径角、TLI Delta-v、交会 Delta-v 构成目标；ECI 目标速度取 300 km 圆轨道速度；程序角 shape 参与搜索。
Generated outputs: optimization_summary.csv, optimization_scores.svg
Validation: 可由 run_baseline.py 复现。
Open issues: 后续需加入连续优化和 Monte Carlo。
Next suggested step: 引入 scipy differential_evolution，如果允许依赖。
