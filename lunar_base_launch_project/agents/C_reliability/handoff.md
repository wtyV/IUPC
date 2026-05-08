Agent: C_reliability
Changed files: src/reliability.py
Assumptions added: 发动机独立失效；两发任务需两发均成功；总链路乘上交会对接和 TLI 可靠性。
Generated outputs: reliability_sweep.csv, mission_chain_reliability.csv, mission_chain_sensitivity.csv, engine_cluster_sweep.csv
Validation: R_launch=0.95, R_rendezvous=0.98, R_TLI=0.985 时，总可靠性为 0.87118325。
Open issues: 交会对接和 TLI 可靠性不应写成确定真值。
Next suggested step: 将敏感性图纳入最终图表清单。
