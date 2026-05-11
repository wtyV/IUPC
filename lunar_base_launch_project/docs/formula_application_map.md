# 数学建模在项目中的应用映射

本文档对照 [formula_summary_v1.md](formula_summary_v1.md)，逐个说明每章的数学建模在项目中**具体用在哪里**、**起什么作用**。

---

## 第一章 数值积分方法

### 1.1 RK4（经典四阶 Runge-Kutta）

- **代码位置**: [integrators.py:28-46](../src/integrators.py#L28-L46)
- **调用位置**: [ascent_full.py:364](../src/ascent_full.py#L364) — `simulate_ascent_full()` 中每步调用 `rk4_step`
- **作用**: 积分上升段 6 维 ECI 运动方程（位置+速度），以 0.5 s 固定步长推进轨迹。RK4 在计算精度和速度间取平衡——每步 4 次右端函数求值，全局误差 O(Δt⁴)，对百秒量级的火箭上升轨迹足够精确。

### 1.2 RK45（Dormand-Prince 5(4) 自适应）

- **代码位置**: [integrators.py:114-196](../src/integrators.py#L114-L196)
- **调用位置**: [integrators.py:199-244](../src/integrators.py#L199-L244) — `rk45_integrate` 为自适应积分的高精度需求提供接口
- **作用**: 提供更高精度备选。当前上升段主仿真用固定步长 RK4，但 RK45 可用于参数敏感性分析或长时间轨道传播（如 lambert.py 中隐式依赖的 Kepler 传播）。PI 步长控制器在精度和效率之间自适应调节。

---

## 第二章 标准大气模型

### 2.1-2.6 九层标准大气（杨炳蔚教材）

- **代码位置**: [atmosphere_full.py:53-63](../src/atmosphere_full.py#L53-L63)（分层表）、[atmosphere_full.py:110-149](../src/atmosphere_full.py#L110-L149)（层内温压密计算）、[atmosphere_full.py:191-257](../src/atmosphere_full.py#L191-L257)（`standard_atmosphere` 入口）
- **调用链**:
  - `simulate_ascent_full()` → RHS 中 `density_kg_m3_full(altitude)` 获取密度 → 计算气动阻力
  - `_build_state()` → `standard_atmosphere(altitude)` → 同时获取密度、温度、压强、声速 → 填入 `AscentStateFull` 的 `density_kg_m3`、`temperature_K`、`pressure_Pa` 字段
- **作用**: 提供 0–120 km 的实时大气参数（ρ, p, T, a），是**气动阻力计算、动压约束、马赫数计算、驻点热流估算**的物理基础。位势高度转换（§2.2）修正了高空重力减弱对大气分层的影响。

### 2.7 Sutherland 粘性公式

- **代码位置**: [atmosphere_full.py:282-293](../src/atmosphere_full.py#L282-L293)
- **调用位置**: `standard_atmosphere()` 的 `dynamic_viscosity_Pa_s` 字段
- **作用**: 提供空气动力粘性 μ(T)。当前项目中粘性为非主要输出量（存入 `AtmoState` 备查），未来若加入边界层传热或摩阻分析则会直接参与计算。

### 2.8 热层延伸模型（H ≥ 120 km）

- **代码位置**: [atmosphere_full.py:217-236](../src/atmosphere_full.py#L217-L236)
- **作用**: 当飞行器超过 120 km 仍提供合理的大气密度衰减，防止密度在边界处截断为零导致数值不连续。实际上升段在 ~300 km 入轨时 ρ 已低于 10⁻¹¹ kg/m³，气动力可忽略。

---

## 第三章 地球引力场模型

### 3.4 球形二体引力

- **代码位置**: [gravity_full.py:58-70](../src/gravity_full.py#L58-L70) — `spherical_gravity()`
- **作用**: 地球引力场的主导项，贡献 >99% 的引力加速度。a = −μ/r³·r，是所有上升段轨迹计算的基础。

### 3.5 J2 摄动加速度

- **代码位置**: [gravity_full.py:75-102](../src/gravity_full.py#L75-L102) — `j2_acceleration()`
- **作用**: 地球扁率摄动（~10⁻³ 量级）。对 300 km LEO 入轨速度产生 **~+41 m/s 的系统性偏移**（如 [formula_summary_v1.md L1147](formula_summary_v1.md#L1147) 所载）。上升段仿真中 **必须包含** J2 才能得到正确的入轨精度评估。

### 3.6-3.7 J3、J4 摄动

- **代码位置**: [gravity_full.py:107-149](../src/gravity_full.py#L107-L149) — `j3_acceleration()`、[gravity_full.py:154-197](../src/gravity_full.py#L154-L197) — `j4_acceleration()`
- **作用**: J3（梨形不对称，~10⁻⁶）和 J4（高阶扁率修正，~10⁻⁶）相对于 J2 的贡献约 **10⁻³**。在当前工程精度要求下引入它们是为了**展示模型完备性和可扩展性**。可以通过 `GravityConfig` 的布尔开关按需启用。

### 3.8 总引力加速度合成

- **代码位置**: [gravity_full.py:202-251](../src/gravity_full.py#L202-L251) — `gravity_acceleration_ecef()` / `gravity_acceleration_eci()`
- **调用位置**: [ascent_full.py:431](../src/ascent_full.py#L431) — `_ascent_rhs_6dof()` 中每步调用
- **作用**: 将所有引力分量叠加为总引力加速度，作为上升段运动方程右端函数的引力项 `g(r)`。

---

## 第四章 上升段质点动力学

### 4.2-4.3 六维 ECI 运动方程

- **代码位置**: [ascent_full.py:396-480](../src/ascent_full.py#L396-L480) — `_ascent_rhs_6dof()`
- **方程**:
  - dr/dt = v
  - dv/dt = **g**(r) + (T/m)·**û** − (D/m)·**v̂_rel** − 2**ω**×**v**
  - dm/dt = −T/(I_sp·g₀)
- **作用**: **项目核心动力学引擎**。每一步 RK4 子步都调用此 RHS 函数，将引力、推力、气动阻力、Coriolis 力四项叠加得到总加速度。质量消耗在 RK4 外层单独更新。

### 4.4 初始条件

- **代码位置**: [ascent_full.py:265-285](../src/ascent_full.py#L265-L285)
- **作用**: 将文昌发射场（19.614°N, 110.951°E, 50 m）的地理坐标转为 ECI 初始位置，加上地球自转赋予的初始切向速度（~438 m/s 向东）。这一步确定了整个仿真轨迹的起点。

### 4.5 推力方向（ENU 坐标基）

- **代码位置**: [ascent_full.py:485-554](../src/ascent_full.py#L485-L554) — `_compute_thrust_direction_eci()`
- **作用**: 将"天-东-北"坐标基 + 发射方位角 + 程序角 ϕ 合成为 ECI 系下的推力单位矢量 **û_T** = sinϕ·**û** + cosϕ·(cosA·**n̂** + sinA·**ê**)。这是推力加速度 (T/m)·**û_T** 的关键输入。

### 4.6 分段光滑俯仰转弯程序角

- **代码位置**: [ascent_full.py:133-188](../src/ascent_full.py#L133-L188) — `PitchProgramFull.pitch_deg()`
- **作用**: 定义火箭推力方向的时变规律——垂直上升阶段（ϕ=90°）→ 幂律平滑下压（控制转弯剧烈程度）→ 终端固定俯仰角 ϕ_f。四个参数 {t_v, t_end, ϕ_f, s} 即为后续**优化的设计变量**。备选双线性切线制导律也在同函数中实现。

### 4.7 推力和比冲的大气反压修正

- **代码位置**: [ascent_full.py:336-343](../src/ascent_full.py#L336-L343)
- **作用**: 按环境压强 p_amb(h) 线性插值修正推力和比冲：T(h) = T_vac − (T_vac − T_sl)·p_amb/p₀。对海平面推力 26.25 MN → 真空推力 29.34 MN 的过渡建模至关重要，直接决定低空段加速度和推进剂消耗率的精度。

### 4.8 质量消耗与分级

- **代码位置**: [ascent_full.py:345-369](../src/ascent_full.py#L345-L369)（质量更新）、[ascent_full.py:324-332](../src/ascent_full.py#L324-L332)（级间分离）
- **作用**: 每步按 ṁ = T/(I_sp·g₀) 消耗推进剂；推进剂耗尽后抛掉该级干质量。S1（1420 t 推进剂 + 260 t 干重）→ S2（285 t 推进剂 + 45 t 干重）两级模型。200 s 抛整流罩（减 4 t）。

---

## 第五章 气动力模型

### 5.1-5.3 大气相对速度、动压、气动阻力

- **代码位置**: [ascent_full.py:443-463](../src/ascent_full.py#L443-L463)（RHS 中的阻力计算）、[ascent_full.py:592-607](../src/ascent_full.py#L592-L607)（状态快照中的动压与马赫数）
- **公式**:
  - **v_rel** = v − **v_atm**（减掉地球自转带起的大气速度）
  - q = ½ρV_rel²
  - D = ½ρV_rel²·C_D·S_ref
  - **a_drag** = −(D/m)·**v̂_rel**
- **作用**: 气动阻力是低空段最大的耗散力（Max-Q 附近可达 MN 级），直接决定峰值动压和轴向过载，是两个关键约束条件（§12.4, §12.5）的来源。

### 5.4 驻点热流密度（Sutton-Graves）

- **代码位置**: [objectives_full.py:247-251](../src/objectives_full.py#L247-L251)
- **作用**: q̇_s = k·√(ρ/R_n)·V_rel³ 估算飞行器鼻锥驻点对流热流。作为优化问题中的热防护约束（§12.6）：峰值热流超过 500 kW/m² 时触发惩罚。

### 5.5-5.6 马赫数、轴向过载

- **代码位置**: [ascent_full.py:602-617](../src/ascent_full.py#L602-L617)
- **作用**: Ma = V_rel / a 是轨迹分析标量输出；n_x = (T−D)/(m·g₀) 以 g 为单位直接参与加速度约束判定。

---

## 第六章 LEO 入轨条件

### 6.1-6.4 目标圆轨道速度、飞行路径角、注入点判定

- **代码位置**: [objectives_full.py:192-215](../src/objectives_full.py#L192-L215)（注入点搜索）、[ascent_full.py:578-583](../src/ascent_full.py#L578-L583)（飞行路径角计算）
- **作用**: 在仿真轨迹上搜索**第一个同时满足 h ≥ 300 km 且 v ≥ 0.95·v_circ 的点**作为入轨注入点。飞行路径角 γ = arctan(v_r/v_h) 衡量速度矢量的"水平程度"，入轨目标 γ≈0°。这是优化目标 J_orbit 的三个评价量（h, v, γ）的基础。

---

## 第七章 轨道力学

### 7.1-7.3 活力公式、TLI 注入、C3

- **代码位置**: [transfer_full.py:66-183](../src/transfer_full.py#L66-L183) — `tli_injection()`
- **调用位置**: [mass_budget.py:49](../src/mass_budget.py#L49) — `solve_tli_mass_budget()` 中获取 Δv_TLI
- **作用**: 从 300 km 圆轨道出发，计算转移椭圆参数：
  - a = (r₁+r₂)/2, e = 1−r₁/a
  - v_p = √(μ(2/r₁−1/a)), Δv_TLI = v_p − v_c ≈ 3.108 km/s
  - TOF = π√(a³/μ) ≈ 4.98 d
  - C3 ≈ 0（椭圆转移不逃逸）
  
  这些参数是 **TLI 级质量预算**的直接输入：质量比 MR = exp(Δv/(I_sp·g₀)) → 推进剂需求 49 t。

### 7.4 Hohmann 圆轨道间转移

- **代码位置**: [rendezvous.py:36-49](../src/rendezvous.py#L36-L49) — `hohmann_delta_v_between_circular_orbits()`
- **作用**: 计算 LEO 交会对接中从调相轨道（如 280 km）到目标轨道（300 km）的转移 Δv。采用两脉冲 Hohmann 公式，用于估算交会过程的燃料消耗。

### 7.5 LEO 相位交会

- **代码位置**: [rendezvous.py:29-34](../src/rendezvous.py#L29-L34)（平均角速度）、[rendezvous.py:52-83](../src/rendezvous.py#L52-L83)（`estimate_rendezvous`）
- **作用**: 用 Kepler 第三定律计算圆轨道平均角速度 n = √(μ/r³)，根据两轨道间的角速度差估算追逐模块追赶目标所需的等待时间 t_wait = Δθ/|n_phase − n_target|。用于工期评估和发射窗口规划。

### 7.6 载荷-燃料快速交会（新增）

- **代码位置**: [rendezvous.py:103-194](../src/rendezvous.py#L103-L194) — `estimate_fast_rendezvous()` / `fast_rendezvous_sweep()`
- **作用**: 为载荷+燃料分开发射架构专门设计。载荷（Launch A）已在 300 km 目标轨道等待，燃料罐（Launch B）以低调相轨道（250–295 km）快速追赶。核心权衡：
  - 轨道越低 → 角速度差越大 → 追赶越快，但 Hohmann 上调 Δv 也越大
  - 250 km 调相：漂移率 2.71 deg/h，最差 44 h 等 120°，Δv 44 m/s
  - 280 km 调相：漂移率 1.08 deg/h，最差 111 h 等 120°，Δv 27 m/s
  - 通过精确发射时刻控制可将初始相位角压至 30° 以内，实现 1–2 天内交会
- **发射窗口**: B 必须在文昌发射场穿越 A 轨道面时发射（每日 2 次 ~5–10 min 窗口），保证两轨道共面以消除平面修正 Δv。

---

## 第八章 齐奥尔科夫斯基火箭方程与质量预算

### 8.1-8.2 理想火箭方程与 TLI 级质量反解（对称两发）

- **代码位置**: [mass_budget.py:31-76](../src/mass_budget.py#L31-L76) — `solve_tli_mass_budget()`
- **作用**: 从 Δv_TLI 反推 TLI 级推进剂需求：
  - MR = exp(Δv/(I_sp·g₀))
  - m_prop = (MR−1)·m_fixed / [1−(MR−1)·ε]
  - 结合结构系数 ε = 8%，得 m_prop = 49.0 t, m_dry = 3.9 t
  - LEO 组合体总质量 96.9 t → 每发需送入 LEO 48.5 t
  
  确认两发 CZ-10 各自有充足运力余量。

### 8.4 非对称发射质量预算（新增 —— 载荷+燃料分开发射）

- **代码位置**: [mass_budget.py:104-214](../src/mass_budget.py#L104-L214) — `solve_split_mass_budget()` / `split_mass_budget_sweep()`
- **作用**: 计算载荷+燃料分离架构下的各发 LEO 湿质量需求。
  - 固定质量 m_fixed = 40 t（月球基地物资）+ 4 t（对接适配器）= 44 t
  - TLI 级推进剂反解与对称方案完全相同：MR = 2.0225 → m_prop = 49.0 t, m_dry = 3.92 t
  - **分配**（与对称方案的关键区别）：
    - Launch A（载荷先发）: m_LEO,A = m_fixed + m_dry = **47.9 t**（载荷 + TLI 发动机结构）
    - Launch B（燃料后发）: m_LEO,B = m_prop = **49.0 t**（纯推进剂）
  - 两发均在 CZ-10 ~70 t 运力范围内，各自余量 20+ t
  - TLI 质量比 MR = 96.9/47.9 = 2.0225，Δv = 3.108 km/s，与对称方案完全相同
- **架构优势**: (1) 载荷不需拆分；(2) 燃料为纯推进剂，发射失败可重发；(3) 低轨快速交会

---

## 第九章 发射几何与地球自转

### 9.1-9.5 ECEF 坐标、自转速度增益、倾角关系

- **代码位置**: [launch_geometry.py:18-21](../src/launch_geometry.py#L18-L21)（自转线速度）、[launch_geometry.py:24-33](../src/launch_geometry.py#L24-L33)（倾角-方位角关系）、[launch_geometry.py:36-39](../src/launch_geometry.py#L36-L39)（自转增益分量）、[frames.py:21-31](../src/frames.py#L21-L31)（ECEF 坐标转换）
- **作用**:
  - 文昌 19.6°N 自转线速度 ~438 m/s，正东发射全额利用 → Δv 节省约 0.44 km/s
  - cos i ≈ cos φ·sin A → 正东发射最小倾角 i_min ≈ 19.6°，低倾角有利于后续 TLI 的轨道面匹配
  - ECEF ↔ 球坐标转换用于轨迹后处理中的经纬高输出

---

## 第十章 可靠性模型

### 10.1 发动机簇可靠性

- **代码位置**: [reliability.py:8-30](../src/reliability.py#L8-L30) — `engine_cluster_reliability()`
- **作用**: 评估 21 台 YF-100K 并联的发动机簇在允许 0 或 1 台失效时的成功概率。全串联 (k=0) 时 R = r²¹ 极低，允许 1 台失效时 R = r²¹ + 21(1−r)r²⁰ 显著提高。这为"发动机冗余"设计决策提供量化支持。

### 10.2 多发任务可靠性

- **代码位置**: [reliability.py:33-48](../src/reliability.py#L33-L48) — `at_least_k_successes()`
- **作用**: 两发全成功 (N=2, K=2) 和"三发二中二"备选方案的量化对比。若单发可靠度 R_L=0.95，两发全成功概率 0.9025，三发至少两发成功概率 0.9928——为是否增加第三枚备选火箭提供决策参数。

### 10.3 总任务串联可靠性链

- **代码位置**: [reliability.py:59-70](../src/reliability.py#L59-L70) — `two_launch_leo_tli_success()`
- **作用**: R_total = R_L² · R_rendezvous · R_TLI。基线值 0.95²×0.98×0.985 = 0.871。若交会对接可靠度降至 0.94 则总可靠度降至 0.797——识别出交会对接是当前方案可靠性的最大风险点。

### 10.4 非对称发射可靠性（新增 —— 载荷+燃料分离架构）

- **代码位置**: [reliability.py:76-121](../src/reliability.py#L76-L121) — `payload_fuel_split_reliability()` / `asymmetric_launch_sensitivity()`
- **作用**: 载荷+燃料分离架构下两发角色不同，可靠性结构有本质区别：
  - Launch A（载荷）失败 = 任务失败（载荷不可替代）
  - Launch B（燃料）失败 = 可补救——载荷在轨等待燃料重发
  - 不可重发：R = R_L² · R_rend · R_TLI = 0.871（与对称方案相同）
  - 可重发：R = R_L · [R_L + (1−R_L)·R_L] · R_rend · R_TLI = **0.915**（提升 ~0.044）
  - 核心优势不在公式而在操作灵活性——燃料失败不需重建整个 40 t 载荷模块
- **调用**: `asymmetric_launch_sensitivity()` 一次性输出对称/非对称/可重发三种方案的可靠性对比表。

---

## 第十一章 优化算法

### 11.1 粒子群优化 (PSO)

- **代码位置**: [optimizers.py:62-154](../src/optimizers.py#L62-L154) — `particle_swarm_optimization()`
- **作用**: 40 个粒子在四维设计空间 {t_end, ϕ_f, s, t_v} 中搜索最优俯仰程序。惯性权重从 0.9 线性衰减至 0.4（前期全局探索 → 后期局部开发），c₁=c₂=2.0 平衡个体认知与群体共享。连续 20 代无改进则早停。PSO 不依赖梯度，适合上升段轨迹这种高度非线性的"黑箱"目标函数。

### 11.2 遗传算法 (GA)

- **代码位置**: [optimizers.py:178-264](../src/optimizers.py#L178-L264) — `genetic_algorithm()`
- **作用**: 60 种群，实数编码，锦标赛选择 (k=3)，BLX-α 混合交叉 (α=0.25)，高斯变异 (σ=8%·搜索范围)。精英保留 4 个最优个体。作为 PSO 之外的第二全局搜索方案，用于交叉验证优化结果的一致性。

### 11.3 模拟退火 (SA)

- **代码位置**: [optimizers.py:284-344](../src/optimizers.py#L284-L344) — `simulated_annealing()`
- **作用**: 从 PSO 粗解出发做局部精调。Metropolis 准则以概率 exp(−ΔE/T) 接受劣解，温度以 0.95 倍指数衰减。自适应步长 ∝ T/T₀ 使高温时大步跳出局部最优，低温时小步收敛。温度降到 0.01T₀ 时重启至 0.5T₀，最多 3 次。

### 11.4 混合优化策略

- **代码位置**: [optimizers.py:349-377](../src/optimizers.py#L349-L377) — `hybrid_pso_sa()`
- **作用**: Stage 1 PSO（50 粒子 × 80 代）全局粗搜 → Stage 2 SA（T₀=50，200 代）局部精搜。两阶段互补：PSO 快速定位全局最优区域，SA 在该区域内精细收敛。这是项目优化的推荐方案。

---

## 第十二章 多目标代价函数

### 12.1-12.7 完整加权代价函数

- **代码位置**: [objectives_full.py:108-331](../src/objectives_full.py#L108-L331) — `evaluate_ascent_objective()`
- **设计变量**: u = [t_end, ϕ_f, s, t_v]，搜索范围见 §12.1
- **代价函数结构**:

| 项 | 权重 | 含义 | 作用 |
|----|------|------|------|
| J_orbit | 10 | (Δh/5km)² + (Δv/50m/s)² + (γ/0.5°)² | **主导项**——驱动轨迹精确入轨 |
| J_q | 5 | [max(0, q_max−60kPa)/20kPa]² | 动压超限惩罚，防止结构过载 |
| J_accel | 3 | [max(0, n_max−6g)/1g]² | 轴向过载约束，保护载荷 |
| J_heating | 2 | [max(0, q̇_max−500kW/m²)/100]² | 热流约束，保护热防护系统 |
| J_control | 0.1 | ∫(dϕ/dt)²dt / 1000 | 惩罚剧烈转弯，保证姿态可控 |

- **作用**: 将物理约束转化为数学优化问题的目标函数。优化器通过最小化 J(u) 来找到"既能精确入轨、又不违反工程约束、转弯还不过猛"的最优俯仰程序。

---

## 第十三章 坐标变换

### 13.1-13.2 ECI/ECEF/球坐标

- **代码位置**: [frames.py:21-48](../src/frames.py#L21-L48)（ECEF ↔ 球坐标互转）
- **作用**:
  - `geodetic_to_ecef_spherical()`：将发射场经纬高转为 ECEF 位置向量 → 进而作为 ECI 初始位置（t=0 时 ECI=ECEF）
  - `ecef_to_geodetic_spherical()`：将轨迹点的 ECI 位置转为经纬高用于输出和可视化
  - ECI 与 ECEF 的 z 轴同向（沿自转轴），故引力加速度的 ECI 表达式与 ECEF 完全相同——简化了引力模块的实现

---

## 第十四章 Lambert 问题（备用）

### 14.2-14.3 Stumpff 函数与通用变量法

- **代码位置**: [lambert.py:71-103](../src/lambert.py#L71-L103)（Stumpff C/S 函数）、[lambert.py:107-411](../src/lambert.py#L107-L411)（`solve_lambert`）
- **作用**: **备用模块**。当前方案用 Hohmann + 相位角模型（§7.4-7.5）处理 LEO 交会。Lambert 求解器作为高精度扩展——给定两个位置矢量和飞行时间，直接确定开普勒轨道的初始与终端速度。未来若需精确计算非共面交会或多圈 Lambert 转移，可替换简化的 Hohmann 模型。

---

## 第十五章 上升段轨迹状态计算

### 15.1-15.2 飞行路径角与完整状态诊断

- **代码位置**: [ascent_full.py:559-639](../src/ascent_full.py#L559-L639) — `_build_state()`
- **作用**: 从 RK4 积分的原始状态向量 [r, v, m] 计算 15 个导出物理量——地心距、高度、速度、大气参数、动压、马赫数、阻力、飞行路径角、轴向过载等。**这是仿真输出和优化评估的数据来源**，每个量的计算方法严格对应 formula_summary_v1 中第十五章所列的公式。

---

## 第十六章 公式与代码对照表

已内嵌于上述各小节。完整的文件级对照见 [formula_summary_v1.md 第十六章](formula_summary_v1.md#L1076-L1120)。

---

## 综合数据流示意

```
┌─────────────────────────────────────────────────────────────────┐
│              上升段轨迹优化（两发通用，§4–§12）                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  设计变量 u = [t_end, φ_f, s, t_v]                               │
│           │                                                     │
│           ▼                                                     │
│    PitchProgramFull.pitch_deg(t)    ← §4.6 俯仰程序角            │
│           │                                                     │
│           ▼                                                     │
│    simulate_ascent_full()           ← §4.2-4.3 ECI 运动方程      │
│      ├─ rk4_step()                  ← §1.1 RK4 积分             │
│      ├─ gravity_acceleration_eci()  ← §3.4-3.8 总引力           │
│      ├─ density_kg_m3_full(h)       ← §2.3-2.6 标准大气         │
│      ├─ thrust + back-pressure      ← §4.7 推力修正             │
│      ├─ drag + dynamic pressure     ← §5.1-5.3 气动力           │
│      ├─ Coriolis term               ← §4.3 Coriolis             │
│      └─ mass depletion + staging    ← §4.8 质量/分级            │
│           │                                                     │
│           ▼                                                     │
│    trajectory → AscentStateFull[]   ← §15 轨迹状态快照           │
│           │                                                     │
│           ▼                                                     │
│    evaluate_ascent_objective()      ← §12 多目标代价函数         │
│      ├─ J_orbit (h, v, γ)          ← §6 入轨条件                │
│      ├─ J_q (q_max penalty)        ← §5.2 动压约束              │
│      ├─ J_accel (n_x penalty)      ← §5.6 过载约束              │
│      ├─ J_heating (q̇_s penalty)    ← §5.4 热流约束              │
│      └─ J_control (pitch rate)     ← §12.7 控制平滑             │
│           │                                                     │
│           ▼                                                     │
│    PSO / GA / SA / Hybrid          ← §11 优化算法               │
│           │                                                     │
│           ▼                                                     │
│    最优设计 u* → 最优上升段轨迹                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│          LEO 组装与 TLI（§7–§8）—— 载荷+燃料分开发射              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  上升段轨迹仿真 → Launch A & B 各自入轨 LE0 (~300 km)             │
│           │                                                     │
│           ├─ solve_split_mass_budget()  ← §8.4 非对称质量预算   │
│           │   · Launch A: 47.9 t (40 t 载荷 + 4 t 适配器         │
│           │               + 3.9 t TLI 发动机/结构)               │
│           │   · Launch B: 49.0 t (纯 TLI 推进剂)                 │
│           │                                                     │
│           ├─ estimate_fast_rendezvous()  ← §7.6 快速交会        │
│           │   · B 以低调相轨追赶 A（280 km: 1.08 deg/h 漂移）    │
│           │   · Hohmann 上调 Δv ~27 m/s                         │
│           │   · 发射窗口: 每日 2 次 ~5-10 min                    │
│           │                                                     │
│           ├─ tli_injection()             ← §7.1-7.3 TLI Δv     │
│           │   · Δv_TLI = 3.108 km/s, TOF = 4.98 d              │
│           │                                                     │
│           └─ payload_fuel_split_reliability() ← §10.4 可靠性    │
│               · 不可重发: R = 0.871                             │
│               · 可重发:  R = 0.915（燃料失败可补发）              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
