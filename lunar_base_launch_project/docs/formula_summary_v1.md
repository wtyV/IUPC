# 完整数学物理建模公式汇总 v1.0

本文档汇总了月球基地运载方案建模中使用的全部公式。任务目标：两发长征十号将总计40t载荷送入地月转移轨道（TLI），不涉及月球到达。

---

## 一、数值积分方法

### 1. RK4 四阶 Runge-Kutta（`integrators.py`）

```
k1 = f(t_n, x_n)
k2 = f(t_n + dt/2,  x_n + dt·k1/2)
k3 = f(t_n + dt/2,  x_n + dt·k2/2)
k4 = f(t_n + dt,    x_n + dt·k3)

x_{n+1} = x_n + (dt/6)·(k1 + 2·k2 + 2·k3 + k4)
```

局部截断误差 O(dt⁵)，全局误差 O(dt⁴)。

### 2. RK45 Dormand-Prince 5(4) 自适应（`integrators.py`）

七级五阶嵌入四阶，步长 PI 控制：`h_new = h·min(2, max(0.5, 0.9·error^(-0.2)))`

---

## 二、标准大气模型 — 杨炳蔚教材（`atmosphere_full.py`）

### 2.1 位势高度

```
H = R_E · h / (R_E + h)
```

`R_E = 6371000 m`, `g0 = 9.80665 m/s²`, `R_air = 287.05287 J/(kg·K)`, `γ = 1.4`

### 2.2 大气九层分层（0–120 km）

| 层 | H 范围 (km) | L (K/km) | T_base (K) |
|----|------------|----------|------------|
| 0 对流层 | 0–11 | -6.5 | 288.15 |
| 1 对流层顶 | 11–20 | 0 | 216.65 |
| 2 平流层下 | 20–32 | +1.0 | 216.65 |
| 3 平流层上 | 32–47 | +2.8 | 228.65 |
| 4 平流层顶 | 47–51 | 0 | 270.65 |
| 5 中间层 | 51–71 | -2.8 | 270.65 |
| 6 中间层上 | 71–84.852 | -2.0 | 214.65 |
| 7 中间层顶 | 84.852–92 | 0 | 186.87 |
| 8 热层底 | 92–120 | +4.0 | 186.87 |

### 2.3 非等温层 (L ≠ 0)

```
T(H) = T_base + L·(H - H_base)
p(H) = p_base · [T_base / T(H)]^(g0 / (R·L))
ρ(H) = p(H) / (R·T(H))
```

### 2.4 等温层 (L = 0)

```
T(H) = T_base
p(H) = p_base · exp[-g0·(H - H_base) / (R·T_base)]
ρ(H) = p(H) / (R·T_base)
```

### 2.5 声速与粘性

```
a = √(γ·R·T)
μ = μ_ref·(T/T_ref)^(3/2)·(T_ref + S)/(T + S)
```

`μ_ref = 1.716e-5 Pa·s`, `T_ref = 273.15 K`, `S = 110.4 K`

---

## 三、地球引力场（`gravity_full.py`）

`μ_E = 3.986004418e14 m³/s²`, `R_E = 6371000 m`

### 3.1 球形二体引力

```
a = -(μ_E / r³) · r
```

### 3.2 J2 带谐项（扁率，~10⁻³）

`J2 = 1.08262668e-3`

```
P2(x) = (3x² - 1)/2

a_x = (-3·J2·μ·R²·x / 2r⁵) · (1 - 5z²/r²)
a_y = (-3·J2·μ·R²·y / 2r⁵) · (1 - 5z²/r²)
a_z = (-3·J2·μ·R²·z / 2r⁵) · (3 - 5z²/r²)
```

### 3.3 J3 带谐项（梨形不对称，~10⁻⁶）

`J3 = -2.53265649e-6`

```
P3(x) = (5x³ - 3x)/2
```

### 3.4 J4 带谐项（~10⁻⁶）

`J4 = -1.61962159e-6`

```
P4(x) = (35x⁴ - 30x² + 3)/8
```

### 3.5 总引力

```
a_total = a_spherical + a_J2 + a_J3 + a_J4
```

**J2 对入轨的影响**：Δh ≈ -0.01 km，Δv ≈ +41 m/s（相对于纯球形引力）。J3/J4 的影响比 J2 小约 1000 倍。

---

## 四、上升段动力学（`ascent_full.py`）

### 4.1 状态向量（ECI 坐标系）

```
x = [rx, ry, rz, vx, vy, vz]ᵀ    （质量 m 单独代数更新）
```

### 4.2 6-DOF 运动方程

```
dr/dt = v

dv/dt = g(r)                           ← 引力（球形 + J2 + J3 + J4）
      + (T/m)·û_T                       ← 推力
      - (D/m)·(v_rel / |v_rel|)         ← 气动阻力
      - 2·ω_E × v                       ← Coriolis

dm/dt = -T / (I_sp·g0)                 ← 质量消耗
```

`ω_E = 7.2921159e-5 rad/s`

### 4.3 推力方向（ECI 中 ENU 坐标基）

```
û_up    = r / |r|
û_east  = (ω_E × r) / |ω_E × r|
û_north = û_up × û_east

û_h = cos(A)·û_north + sin(A)·û_east          （发射方位角 A）
û_T = sin(φ)·û_up + cos(φ)·û_h                （程序角 φ）
```

### 4.4 程序角 — 分段光滑俯仰转弯

设计变量：`t_v`（垂直上升时间）、`t_end`（转弯结束时间）、`φ_f`（终端程序角）、`s`（形状指数）

```
φ(t) = 90°                                                    t ≤ t_v
φ(t) = 90° - [(t-t_v)/(t_end-t_v)]^s · (90° - φ_f)          t_v < t < t_end
φ(t) = φ_f                                                    t ≥ t_end
```

### 4.5 推力大气反压修正

```
T(h) = T_vac - (T_vac - T_sl) · p(h)/p0
I_sp(h) = I_sp,vac - (I_sp,vac - I_sp,sl) · p(h)/p0
```

### 4.6 分级模型

长征十号两级入轨（第三级为独立 TLI 级，不在上升段内）：

| 级 | 推进剂 (t) | 干重 (t) | 推力真空 (MN) | 推力海平面 (MN) | I_sp 真空 (s) | I_sp 海平面 (s) |
|----|----------|---------|-------------|---------------|-------------|---------------|
| S1 助推+芯级 | 1420 | 260 | 29.34 | 26.25 | 338.2 | 301.8 |
| S2 上面级 | 285 | 45 | 5.59 | 5.59 | 340.0 | 340.0 |

载荷：20 t/发，整流罩：4 t

---

## 五、气动力（`ascent_full.py`）

### 5.1 大气相对速度

```
v_atm = ω_E × r
v_rel = v - v_atm
```

### 5.2 动压

```
q = (1/2) · ρ(h) · |v_rel|²
```

### 5.3 阻力

```
D = (1/2) · ρ(h) · |v_rel|² · C_D · S_ref
```

`C_D = 0.30`, `S_ref = 78.5 m²`

### 5.4 驻点热流（Sutton-Graves）

```
q_dot = k · √(ρ/R_n) · V³
```

`k ≈ 1.83e-4`, `R_n ≈ 1.0 m`

---

## 六、LEO 入轨条件（`objectives_full.py`）

### 6.1 目标轨道

```
r_target = R_E + h_target
v_circular = √(μ_E / r_target)
```

### 6.2 飞行路径角

```
γ = arctan(v_radial / v_horizontal)
v_radial = v · r̂
v_horizontal = √(v² - v_radial²)
```

**理想入轨**：`h ≈ 300 km`, `v ≈ 7.73 km/s`, `γ ≈ 0°`

---

## 七、轨道力学

### 7.1 活力公式 Vis-Viva（`transfer_full.py`, `rendezvous.py`）

```
v² = μ · (2/r - 1/a)
```

### 7.2 TLI 注入 Δv（`transfer_full.py`）

```
r1 = R_E + h_LEO,   r2 = 384400000 m（地月距离）

a = (r1 + r2) / 2                    ← 转移椭圆半长轴
v_c = √(μ_E / r1)                    ← LEO 圆轨道速度
v_p = √(μ_E·(2/r1 - 1/a))           ← 近地点速度（活力公式）
v_a = √(μ_E·(2/r2 - 1/a))           ← 远地点速度

Δv_TLI = v_p - v_c                   ← TLI 冲量
```

| h_LEO | Δv_TLI | TOF |
|-------|--------|-----|
| 200 km | 3.133 km/s | 4.98 d |
| 300 km | 3.108 km/s | 4.98 d |
| 400 km | 3.084 km/s | 4.98 d |
| 500 km | 3.060 km/s | 4.98 d |

### 7.3 C3 发射能量（`transfer_full.py`）

```
E = v_p²/2 - μ_E/r1 = -μ_E/(2a)     ← 轨道能量
C3 = v_inf² = 2E  (E > 0 时，椭圆转移时 C3 ≈ 0)
```

### 7.4 飞行时间（`transfer_full.py`）

```
TOF = π · √(a³ / μ_E)
```

### 7.5 Hohmann 圆轨道间转移（`rendezvous.py`）

```
a = (r1 + r2)/2
v1 = √(μ/r1),   v2 = √(μ/r2)
v_t1 = √(μ·(2/r1 - 1/a)),   v_t2 = √(μ·(2/r2 - 1/a))
Δv = |v_t1 - v1| + |v2 - v_t2|
```

### 7.6 LEO 相位交会（`rendezvous.py`）

```
n = √(μ / r³)                        ← 圆轨道角速度
θ_rel = n_phase - n_target           ← 相对漂移角速度
t_wait = Δθ / |θ_rel|               ← 等待时间
```

---

## 八、齐奥尔科夫斯基火箭方程（`mass_budget.py`）

### 8.1 理想火箭方程

```
Δv = I_sp · g0 · ln(m0/mf)
MR = m0/mf = exp(Δv / (I_sp·g0))
```

### 8.2 TLI 级质量预算

给定 `m_fixed = m_cargo + m_adapter = 44 t`, `ε = m_dry/m_prop = 0.08`:

```
MR = exp(Δv_TLI / (I_sp·g0))
m_prop = (MR-1)·m_fixed / (1 - (MR-1)·ε)
m_dry  = ε·m_prop
m_stack,LEO = m_fixed + m_prop + m_dry
m_LEO,per_launch = m_stack,LEO / 2
```

**300 km LEO 基线**：MR = 2.022，m_prop = 49.0 t，m_stack,LEO = 96.9 t，per_launch = 48.5 t

---

## 九、发射几何（`launch_geometry.py`, `frames.py`）

### 9.1 ECEF 坐标

```
r = [(R_E+h)·cos(φ)·cos(λ),  (R_E+h)·cos(φ)·sin(λ),  (R_E+h)·sin(φ)]ᵀ
```

### 9.2 地球自转

```
v_rot(φ) = ω_E · R_E · cos(φ)                      ← 文昌 ≈ 438 m/s
Δv_rot(A) = v_rot · sin(A)                          ← 沿发射方向增益
v0 = ω_E × r0                                       ← 惯性初速
```

### 9.3 倾角与方位角

```
cos(i) ≈ cos(φ) · sin(A)
```

正东发射 (A = 90°)：`i_min ≈ φ = 19.6°`

---

## 十、可靠性（`reliability.py`）

### 10.1 发动机簇

```
R_cluster = Σ(k=0→f) C(N,k) · (1-r)^k · r^(N-k)
```

### 10.2 k-out-of-N 多发任务

```
P(N,K;R) = Σ(s=K→N) C(N,s) · R^s · (1-R)^(N-s)
```

两发全成功：`P2 = R²`
三发至少两发：`P3,2 = 3R² - 2R³`

### 10.3 总可靠性链

```
R_total = R_launch² × R_rendezvous × R_TLI
```

**基线**（`R_launch=0.95`, `R_rendezvous=0.98`, `R_TLI=0.985`）：
`R_total = 0.95² × 0.98 × 0.985 ≈ 0.871`

---

## 十一、优化算法（`optimizers.py`）

### 11.1 PSO 粒子群优化

```
v_i ← w·v_i + c1·r1·(pbest_i - x_i) + c2·r2·(gbest - x_i)
x_i ← x_i + v_i
w(k) = w_start - (w_start - w_end)·k/K_max
```

`c1=c2=2.0`, `w_start=0.9`, `w_end=0.4`, 种群 40-50, 迭代 80-100

### 11.2 GA 遗传算法

锦标赛选择 + 混合交叉 (BLX-α, α=0.25) + 高斯变异 + 精英保留

### 11.3 SA 模拟退火

```
P(accept) = min(1, exp(-ΔE/T))
T_{k+1} = α·T_k,   α = 0.92-0.95
```

---

## 十二、多目标代价函数（`objectives_full.py`）

### 12.1 总代价

```
J = w1·J_orbit + w2·J_q + w3·J_accel + w4·J_heating + w5·J_control
```

`w1=10`, `w2=5`, `w3=3`, `w4=2`, `w5=0.1`

### 12.2 入轨误差

```
J_orbit = (h_f-h*)²/σh² + (v_f-v*)²/σv² + γ_f²/σγ²
```

`h*=300 km`, `v*=7.73 km/s`, `γ*=0°`, `σh=5 km`, `σv=50 m/s`, `σγ=0.5°`

### 12.3 路径约束（软惩罚）

```
J_q     = max(0, q_max - 60 kPa)² / (20 kPa)²
J_accel = max(0, n_max - 6g)² / (1g)²
J_heating = max(0, q_dot_max - 500 kW/m²)² / (100 kW/m²)²
```

---

## 十三、Lambert 问题（`lambert.py`）

### 13.1 问题描述

给定 `r1, r2, TOF, μ`，求解 `v1, v2`

### 13.2 Stumpff 函数

```
C(z) = (1-cos√z)/z  (z>0),  (cosh√(-z)-1)/(-z)  (z<0),  1/2  (z=0)
S(z) = (√z-sin√z)/z^(3/2)  (z>0),  (sinh√(-z)-√(-z))/(-z)^(3/2)  (z<0),  1/6  (z=0)
```

### 13.3 通用变量时间方程

```
√μ·t = χ³·S(αχ²) + A·√y
y = r1 + r2 + A·(αχ²·S(αχ²)-1)/√C(αχ²)
```

（Lambert 求解器当前作为备用，LEO 交会主要使用 Hohmann+相位追赶模型）

---

## 十四、公式与代码对照

| 章节 | 公式 | 代码文件 |
|------|------|---------|
| 一 | RK4 / RK45 | `integrators.py` |
| 二 | 杨炳蔚标准大气（位势高度、九层分层、温度/压强/密度、声速、粘性） | `atmosphere_full.py` |
| 三 | 球形引力 + J2 + J3 + J4 | `gravity_full.py` |
| 四 | 6-DOF ECI 运动方程、ENU 推力方向、程序角、推力反压修正 | `ascent_full.py` |
| 五 | 动压、阻力、Sutton-Graves 热流 | `ascent_full.py` |
| 六 | 圆轨道速度、飞行路径角 | `objectives_full.py` |
| 七 | Vis-Viva、TLI Δv、C3、TOF、Hohmann、相位交会 | `transfer_full.py`, `rendezvous.py` |
| 八 | 火箭方程、TLI 质量预算 | `mass_budget.py` |
| 九 | ECEF 坐标、自转速度、倾角-方位角 | `launch_geometry.py`, `frames.py` |
| 十 | k-out-of-N 可靠性、串联链 | `reliability.py` |
| 十一 | PSO、GA、SA | `optimizers.py` |
| 十二 | 多目标代价函数、入轨误差、路径约束 | `objectives_full.py` |
| 十三 | Lambert 通用变量法、Stumpff 函数 | `lambert.py` |

---

## 十五、关键数值汇总

| 指标 | 数值 |
|------|------|
| 推荐架构 | 两发 CZ-10 → LEO 交会对接 → 组合 TLI |
| 每发载荷 | 20 t |
| 300 km LEO TLI Δv | 3.108 km/s |
| TLI 飞行时间 | 4.98 d |
| TLI 转移偏心率 | 0.9659 |
| LEO 组合体初始质量 | 96.9 t |
| TLI 推进剂 | 49.0 t |
| 每发 LEO 湿质量需求 | 48.5 t |
| 每发模拟入轨质量 | ~65 t（含 20 t 载荷） |
| 文昌自转速度增益 | ~438 m/s（正东发射） |
| 最低轨道倾角 | ~19.6° |
| 可靠性链 (R_launch=0.95) | 0.871 |
| J2 对入轨高度影响 | ≈ 0 km（正负抵消） |
| J2 对入轨速度影响 | ≈ +41 m/s |
