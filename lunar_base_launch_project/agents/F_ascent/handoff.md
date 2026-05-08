Agent: F_ascent
Changed files: src/ascent_3dof.py, src/ascent_eci.py, src/atmosphere.py, src/frames.py
Assumptions added: 分段常推力、程序角、简化气动阻力。
Generated outputs: ascent_baseline.csv, ascent_eci_baseline.csv, gravity_model_comparison.csv
Validation: v0.6 ECI 基线末端高度约 306.9 km，惯性速度约 7.723 km/s，飞行路径角约 -0.02 deg，动压峰值约 21.9 kPa；J2 相对球形引力末端高度差约 -2.27 km。
Open issues: 分级质量仍为占位参数，需要结合公开运力约束校准。
Next suggested step: 对球形引力与 J2 的末端差异做对照表。
