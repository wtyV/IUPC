Agent: D_transfer
Changed files: src/transfer.py, src/mass_budget.py
Assumptions added: LEO 停泊后 Hohmann 型 TLI；名义 TLI 级 Isp=450 s，结构系数=0.08。
Generated outputs: delta_v_budget.csv, tli_mass_budget.csv, tli_delta_v.svg, tli_mass_budget.svg
Validation: 300 km LEO 的 TLI Delta-v 约 3.108 km/s；名义 LEO 初始组合体约 96.9 t。
Open issues: 后续需要加入月球相位和三体近似。
Next suggested step: 与优化智能体连接，选择 LEO 高度。
