# 论文解题顺序 —— 完整数学物理公式推导链

> **对应竞赛题目**："Lunar Base Construction: A Heavy-Lift Rocket Design Challenge"
> —— 基于中国现有火箭技术，设计将 40 t 载荷送入地月转移轨道的发射方案，
> 匹配 Starship 运输能力但可靠性更高。

本文档按**论文解题的推演顺序**重新组织全部数学公式。
从问题分析开始 → 选箭选场 → 定架构 → 建物理模型 → 优化求解 → 最终方案验证。

---

## Step 1 — 基本物理常数

所有计算的公理起点。

| 符号 | 数值 | 单位 | 含义 |
|------|------|------|------|
| $g_0$ | 9.80665 | m/s² | 标准重力加速度 |
| $\mu_E$ | $3.986004418 \times 10^{14}$ | m³/s² | 地球引力参数 |
| $R_E$ | $6\,371\,000$ | m | 地球平均半径 |
| $\omega_E$ | $7.2921159 \times 10^{-5}$ | rad/s | 地球自转角速度 |
| $R_a$ | 287.05287 | J/(kg·K) | 干空气气体常数 |
| $\gamma$ | 1.4 | — | 空气比热比 |
| $p_0$ | 101325 | Pa | 海平面标准气压 |
| $T_0$ | 288.15 | K | 海平面标准温度 |
| $\rho_0$ | 1.225 | kg/m³ | 海平面标准密度 |

引力场系数 (EGM2008):

| 系数 | 数值 |
|------|------|
| $J_2$ | $+1.0826266835531513 \times 10^{-3}$ |
| $J_3$ | $-2.5326564853322357 \times 10^{-6}$ |
| $J_4$ | $-1.6196215913672832 \times 10^{-6}$ |

---

## Step 2 — 运载火箭选型：长征十号参数

对比 Starship 33 台发动机单发高风险，选择中国最强火箭 CZ-10。

| 参数 | S1（助推+芯级） | S2（上面级） |
|------|-------------|----------|
| 推进剂质量 $m_{\text{prop}}$ | 1 420 t | 285 t |
| 干质量 $m_{\text{dry}}$ | 260 t | 45 t |
| 真空推力 $T_{\text{vac}}$ | 29.34 MN (21×YF-100K) | 5.59 MN (4×YF-100K) |
| 海平面推力 $T_{\text{sl}}$ | 26.25 MN | 5.59 MN |
| 真空比冲 $I_{\text{sp,vac}}$ | 338.2 s | 340.0 s |
| 海平面比冲 $I_{\text{sp,sl}}$ | 301.8 s | 340.0 s |
| 发动机数量 | 21 | 4 |
| 整流罩 $m_{\text{fairing}}$ | 4 t（200 s 抛离） | — |
| 参考面积 $S_{\text{ref}}$ | 78.5 m² | — |
| 阻力系数 $C_D$ | 0.30 | — |
| 公开 TLI 运力 | ≥27 t | — |
| 起飞质量 | ~2 189 t | — |

> **关键判断**: 单发 TLI 运力 27 t < 40 t 需求 → **单发不可行**，需要多发方案。

---

## Step 3 — 发射场选择：文昌

| 参数 | 数值 |
|------|------|
| 纬度 $\varphi$ | 19.614°N |
| 经度 $\lambda$ | 110.951°E |
| 高程 $h_0$ | 50 m |

### 3.1 发射点在 ECEF 中的位置

$$\boxed{\mathbf{r}_{\text{ECEF}} = \begin{bmatrix} (R_E + h_0)\cos\varphi \cos\lambda \\ (R_E + h_0)\cos\varphi \sin\lambda \\ (R_E + h_0)\sin\varphi \end{bmatrix}}$$

### 3.2 地球自转东向线速度（惯性速度增益）

$$\boxed{v_{\text{rot}}(\varphi, h_0) = \omega_E \cdot (R_E + h_0) \cdot \cos\varphi}$$

文昌数值：$v_{\text{rot}} \approx 438$ m/s。

### 3.3 沿发射方向的自转速度增益

$$\boxed{\Delta v_{\text{rot}}(A) = v_{\text{rot}} \cdot \sin A}$$

正东发射 ($A=90^\circ$)：$\Delta v_{\text{rot}} = 438$ m/s（全额利用）。

### 3.4 轨道倾角与发射方位角的关系

$$\boxed{\cos i \approx \cos\varphi \cdot \sin A}$$

正东发射最小倾角 $i_{\min} \approx \varphi = 19.6^\circ$，利于近赤道低倾角轨道，降低后续 TLI 能量代价。

---

## Step 4 — 任务架构决策

### 4.1 单发直接 TLI → 否决

TLI 运力 27 t < 40 t — 物理上不可行。

### 4.2 对称两发 (每发 20 t) → 备选

两发各载 20 t 模块→LEO→交会对接→组合体 TLI。需要拆分载荷。

### 4.3 载荷+燃料分开发射 → **推荐方案**

- **Launch A（载荷先发）**: 40 t 基地物资 + 4 t 对接适配器 + TLI 级发动机干质量 → 300 km LEO
- **Launch B（燃料后发）**: TLI 级推进剂 → 低轨调相，快速追赶 A
- **组合体 TLI** 点火 → 地月转移轨道

**架构优势**: 载荷不需拆分；燃料为纯推进剂，发射失败可重发；低轨快速交会。

---

## Step 5 — 坐标系与参考框架

### 5.1 ECI（地心惯性系）

采用 ECI，取 $t=0$ 时 ECI = ECEF。

$$\boldsymbol{\omega}_E = \begin{bmatrix} 0 \\ 0 \\ \omega_E \end{bmatrix}, \quad \omega_E = 7.2921159 \times 10^{-5} \text{ rad/s}$$

### 5.2 上升段状态向量（6 维 + 质量）

$$\mathbf{x}(t) = \begin{bmatrix} r_x \\ r_y \\ r_z \\ v_x \\ v_y \\ v_z \end{bmatrix}_{\text{ECI}}, \quad m(t) \text{（单独更新）}$$

### 5.3 ECI 初始条件

初始位置（ECI = ECEF at $t=0$）：
$$r_0 = R_E + h_0$$
$$\begin{bmatrix} r_{x0} \\ r_{y0} \\ r_{z0} \end{bmatrix} = \begin{bmatrix} r_0 \cos\varphi \cos\lambda \\ r_0 \cos\varphi \sin\lambda \\ r_0 \sin\varphi \end{bmatrix}$$

初始速度（地球自转）：
$$\boxed{\mathbf{v}_0 = \boldsymbol{\omega}_E \times \mathbf{r}_0 = \begin{bmatrix} -\omega_E \cdot y_0 \\ \omega_E \cdot x_0 \\ 0 \end{bmatrix}}$$

初始质量：
$$m_0 = \sum_{j} m_{\text{dry},j} + \sum_{j} m_{\text{prop},j} + m_{\text{payload}} + m_{\text{fairing}}$$

### 5.4 ECEF ↔ 球坐标

$$\varphi = \arcsin\left(\frac{z}{r}\right), \quad \lambda = \operatorname{atan2}(y, x), \quad h = r - R_E$$

---

## Step 6 — 地球引力场模型

### 6.1 球形二体引力（主导项 >99%）

$$r = \|\mathbf{r}\| = \sqrt{x^2 + y^2 + z^2}$$

$$\boxed{\mathbf{a}_{\text{spherical}} = -\frac{\mu_E}{r^3} \begin{bmatrix} x \\ y \\ z \end{bmatrix}}$$

### 6.2 J2 摄动（地球扁率，~10⁻³ 量级）

引力势：
$$U_{J2} = -\frac{\mu_E}{r} \cdot J_2 \cdot \left(\frac{R_E}{r}\right)^2 \cdot P_2(\sin\phi_g)$$
$$P_2(x) = \frac{1}{2}(3x^2 - 1)$$

取梯度 $\mathbf{a}_{J2} = -\nabla U_{J2}$，得 ECEF 笛卡尔分量：

$$\boxed{a_x^{J2} = -\frac{3}{2} \cdot \frac{\mu_E J_2 R_E^2}{r^5} \cdot x \cdot \left(1 - \frac{5z^2}{r^2}\right)}$$
$$\boxed{a_y^{J2} = -\frac{3}{2} \cdot \frac{\mu_E J_2 R_E^2}{r^5} \cdot y \cdot \left(1 - \frac{5z^2}{r^2}\right)}$$
$$\boxed{a_z^{J2} = -\frac{3}{2} \cdot \frac{\mu_E J_2 R_E^2}{r^5} \cdot z \cdot \left(3 - \frac{5z^2}{r^2}\right)}$$

### 6.3 J3 摄动（梨形不对称，~10⁻⁶）

$$U_{J3} = \frac{\mu_E}{r} \cdot J_3 \cdot \left(\frac{R_E}{r}\right)^3 \cdot P_3(\sin\phi_g), \quad P_3(x) = \frac{1}{2}(5x^3 - 3x)$$

令 $s = z/r$，链式法则求梯度：

$$\frac{\partial U_{J3}}{\partial r} = -4\mu_E J_3 \frac{R_E^3}{r^5} P_3(s), \quad \frac{\partial U_{J3}}{\partial s} = \mu_E J_3 \frac{R_E^3}{r^4} P_3'(s)$$
$$\frac{\partial s}{\partial x} = -\frac{xz}{r^3}, \quad \frac{\partial s}{\partial y} = -\frac{yz}{r^3}, \quad \frac{\partial s}{\partial z} = \frac{1}{r} - \frac{z^2}{r^3}$$

加速度分量：
$$a_x^{J3} = \frac{x}{r} \cdot \frac{\partial U_{J3}}{\partial r} + \frac{\partial U_{J3}}{\partial s} \cdot \frac{\partial s}{\partial x}$$

（$a_y^{J3}$, $a_z^{J3}$ 类同）

### 6.4 J4 摄动（高阶扁率修正，~10⁻⁶）

$$U_{J4} = -\frac{\mu_E}{r} \cdot J_4 \cdot \left(\frac{R_E}{r}\right)^4 \cdot P_4(\sin\phi_g), \quad P_4(x) = \frac{1}{8}(35x^4 - 30x^2 + 3)$$
$$\frac{\partial U_{J4}}{\partial r} = 5\mu_E J_4 \frac{R_E^4}{r^6} P_4(s), \quad \frac{\partial U_{J4}}{\partial s} = -\mu_E J_4 \frac{R_E^4}{r^5} P_4'(s)$$

（加速度分量推导同 J3）

### 6.5 总引力加速度

$$\boxed{\mathbf{a}_{\text{grav}}(\mathbf{r}) = \mathbf{a}_{\text{spherical}}(\mathbf{r}) + \mathbf{a}_{J2}(\mathbf{r}) + \mathbf{a}_{J3}(\mathbf{r}) + \mathbf{a}_{J4}(\mathbf{r})}$$

---

## Step 7 — 标准大气模型（杨炳蔚教材，9 层 0–120 km）

### 7.1 位势高度转换（修正重力随高度减弱）

$$\boxed{H = \frac{R_E \cdot h}{R_E + h}}$$

### 7.2 大气九层分层

| 层 | 名称 | $H_{\text{base}}$ (km) | $H_{\text{top}}$ (km) | $T_{\text{base}}$ (K) | $L_i$ (K/km) |
|----|------|------------------------|----------------------|----------------------|-------------|
| 0 | 对流层 | 0 | 11 | 288.15 | −6.5 |
| 1 | 对流层顶 | 11 | 20 | 216.65 | 0 |
| 2 | 平流层下部 | 20 | 32 | 216.65 | +1.0 |
| 3 | 平流层上部 | 32 | 47 | 228.65 | +2.8 |
| 4 | 平流层顶 | 47 | 51 | 270.65 | 0 |
| 5 | 中间层 | 51 | 71 | 270.65 | −2.8 |
| 6 | 中间层上部 | 71 | 84.852 | 214.65 | −2.0 |
| 7 | 中间层顶 | 84.852 | 92 | 186.87 | 0 |
| 8 | 热层底部 | 92 | 120 | 186.87 | +4.0 |

### 7.3 非等温层 ($L_i \neq 0$) — 推导

由流体静力学平衡 $dp/dH = -\rho g_0$ 与理想气体 $p = \rho R_a T$ 联立。

温度：
$$T(H) = T_{\text{base},i} + L_i \cdot (H - H_{\text{base},i})$$

代入 $dp/dH = -p g_0 / (R_a T)$，用 $dT = L_i dH$ 换元：

$$\frac{dp}{p} = -\frac{g_0}{R_a L_i} \cdot \frac{dT}{T}$$
$$\ln\frac{p(H)}{p_{\text{base},i}} = -\frac{g_0}{R_a L_i} \ln\frac{T(H)}{T_{\text{base},i}}$$

$$\boxed{p(H) = p_{\text{base},i} \cdot \left[\frac{T_{\text{base},i}}{T(H)}\right]^{\frac{g_0}{R_a L_i}}}$$

密度：
$$\boxed{\rho(H) = \frac{p(H)}{R_a \cdot T(H)}}$$

### 7.4 等温层 ($L_i = 0$) — 推导

$T(H) = T_{\text{base},i}$ = 常数。

$$\frac{dp}{p} = -\frac{g_0}{R_a T_{\text{base},i}} dH$$
$$\ln\frac{p(H)}{p_{\text{base},i}} = -\frac{g_0}{R_a T_{\text{base},i}}(H - H_{\text{base},i})$$

$$\boxed{p(H) = p_{\text{base},i} \cdot \exp\left[-\frac{g_0(H - H_{\text{base},i})}{R_a T_{\text{base},i}}\right]}$$

密度：
$$\boxed{\rho(H) = \frac{p(H)}{R_a \cdot T_{\text{base},i}}}$$

### 7.5 声速

$$\boxed{a(H) = \sqrt{\gamma \cdot R_a \cdot T(H)}}$$

### 7.6 热层延伸 ($H \ge 120$ km)

$$\boxed{\rho(H) = \rho_{120} \cdot \exp\left(-\frac{H - H_{120}}{H_{\text{scale}}}\right)}$$
$$\rho_{120} = 2.44 \times 10^{-8} \text{ kg/m³}, \quad H_{\text{scale}} = 15000 \text{ m}$$

---

## Step 8 — 气动力模型

### 8.1 大气相对速度（减掉地球自转引起的大气运动）

$$\boxed{\mathbf{v}_{\text{atm}} = \boldsymbol{\omega}_E \times \mathbf{r} = \begin{bmatrix} -\omega_E \cdot r_y \\ \omega_E \cdot r_x \\ 0 \end{bmatrix}}$$
$$\boxed{\mathbf{v}_{\text{rel}} = \mathbf{v} - \mathbf{v}_{\text{atm}}}$$

### 8.2 动压

$$\boxed{q = \frac{1}{2} \cdot \rho(h) \cdot V_{\text{rel}}^2}$$

### 8.3 气动阻力

$$\boxed{D = \frac{1}{2} \cdot \rho(h) \cdot V_{\text{rel}}^2 \cdot C_D \cdot S_{\text{ref}}}$$
$$\boxed{\mathbf{a}_{\text{drag}} = -\frac{D}{m} \cdot \frac{\mathbf{v}_{\text{rel}}}{V_{\text{rel}}}}$$

### 8.4 驻点热流（Sutton-Graves 半经验公式）

$$\boxed{\dot{q}_s = k \cdot \sqrt{\frac{\rho}{R_n}} \cdot V_{\text{rel}}^3}, \quad k = 1.83 \times 10^{-4},\ R_n = 1.0 \text{ m}$$

### 8.5 马赫数

$$Ma = \frac{V_{\text{rel}}}{a(h)}$$

### 8.6 轴向过载

$$n_x = \frac{T - D}{m \cdot g_0}$$

---

## Step 9 — 推力模型

### 9.1 推力与比冲的大气反压修正

发动机在海平面与真空之间存在推力差：

$$\boxed{T(h) = T_{\text{vac}} - (T_{\text{vac}} - T_{\text{sl}}) \cdot \frac{p_{\text{amb}}(h)}{p_0}}$$
$$\boxed{I_{\text{sp}}(h) = I_{\text{sp,vac}} - (I_{\text{sp,vac}} - I_{\text{sp,sl}}) \cdot \frac{p_{\text{amb}}(h)}{p_0}}$$

### 9.2 推力方向 — ENU 坐标基

当地天向 $\hat{\mathbf{u}} = \frac{\mathbf{r}}{\|\mathbf{r}\|}$

当地东向 $\hat{\mathbf{e}} = \frac{\boldsymbol{\omega}_E \times \mathbf{r}}{\|\boldsymbol{\omega}_E \times \mathbf{r}\|}$

当地北向 $\hat{\mathbf{n}} = \hat{\mathbf{u}} \times \hat{\mathbf{e}}$（右手定则）

水平发射方向 ($A$ 为发射方位角)：
$$\hat{\mathbf{h}}_A = \cos A \cdot \hat{\mathbf{n}} + \sin A \cdot \hat{\mathbf{e}}$$

推力方向（$\phi$ 为程序角，推力相对当地水平面的仰角）：
$$\boxed{\hat{\mathbf{u}}_T = \sin\phi \cdot \hat{\mathbf{u}} + \cos\phi \cdot \left(\cos A \cdot \hat{\mathbf{n}} + \sin A \cdot \hat{\mathbf{e}}\right)}$$

### 9.3 质量消耗与分级

$$\dot{m}_j = \frac{T_j(h)}{I_{\text{sp},j}(h) \cdot g_0}$$

$$t_{\text{burn},j} = \frac{m_{\text{prop},j}}{\dot{m}_j}$$

级间分离抛干质量：
$$m^+ = m^- - m_{\text{dry},j}$$

---

## Step 10 — 上升段完整动力学方程（ECI 系）

### 10.1 六维运动方程

$$\boxed{\frac{d\mathbf{r}}{dt} = \mathbf{v}}$$

$$\boxed{\frac{d\mathbf{v}}{dt} = \underbrace{\mathbf{g}(\mathbf{r})}_{\text{引力}} + \underbrace{\frac{T}{m}\hat{\mathbf{u}}_T}_{\text{推力}} - \underbrace{\frac{D}{m}\frac{\mathbf{v}_{\text{rel}}}{\|\mathbf{v}_{\text{rel}}\|}}_{\text{气动阻力}} - \underbrace{2\boldsymbol{\omega}_E \times \mathbf{v}}_{\text{Coriolis}}}$$

$$\boxed{\frac{dm}{dt} = -\frac{T}{I_{\text{sp}} \cdot g_0}}$$

物理含义：引力（球形+J2+J3+J4）+ 推力（ENU 方向）+ 气动阻力（与相对大气速度反向）+ Coriolis 惯性力。

---

## Step 11 — 俯仰程序角（轨迹控制变量）

### 11.1 分段光滑俯仰转弯

$$\boxed{\phi(t) = \begin{cases} 90^\circ & 0 \le t \le t_v \\[6pt] 90^\circ - \left(\dfrac{t - t_v}{t_{\text{end}} - t_v}\right)^{s} \cdot (90^\circ - \phi_f) & t_v < t < t_{\text{end}} \\[6pt] \phi_f & t \ge t_{\text{end}} \end{cases}}$$

| 参数 | 含义 | 范围 |
|------|------|------|
| $t_v$ | 垂直上升时间 | 5–20 s |
| $t_{\text{end}}$ | 俯仰转弯结束时间 | 200–400 s |
| $\phi_f$ | 终端程序角 | 2°–20° |
| $s$ | 形状指数 | 0.8–2.0 |

设计变量 $\mathbf{u} = [t_{\text{end}}, \phi_f, s, t_v]^T$。

### 11.2 备选：双线性切线制导（真空段最优控制）

$$\boxed{\phi(t) = \arctan\left(\frac{a \cdot t + b}{c \cdot t + d}\right)}$$

---

## Step 12 — 多目标代价函数（上升到入轨的优化目标）

### 12.1 总加权代价

$$\boxed{J(\mathbf{u}) = w_1 J_{\text{orbit}} + w_2 J_q + w_3 J_{\text{accel}} + w_4 J_{\text{heating}} + w_5 J_{\text{control}}}$$

权重：$w_1 = 10$, $w_2 = 5$, $w_3 = 3$, $w_4 = 2$, $w_5 = 0.1$。

### 12.2 入轨误差项 $J_{\text{orbit}}$（主导项）

$$\boxed{J_{\text{orbit}} = \left(\frac{h_f - h^*}{\sigma_h}\right)^2 + \left(\frac{v_f - v^*}{\sigma_v}\right)^2 + \left(\frac{\gamma_f}{\sigma_\gamma}\right)^2}$$

$h^* = 300$ km, $v^* = \sqrt{\mu_E/(R_E + h^*)} \approx 7729.9$ m/s, $\gamma^* = 0^\circ$

$\sigma_h = 5$ km, $\sigma_v = 50$ m/s, $\sigma_\gamma = 0.5^\circ$

### 12.3 动压约束 $J_q$

$$\boxed{J_q = \left[\frac{\max(0, q_{\max} - q_{\text{limit}})}{\sigma_q}\right]^2}, \quad q_{\text{limit}} = 60 \text{ kPa},\ \sigma_q = 20 \text{ kPa}$$

### 12.4 加速度约束 $J_{\text{accel}}$

$$\boxed{J_{\text{accel}} = \left[\frac{\max(0, n_{x,\max} - n_{\text{limit}})}{\sigma_n}\right]^2}, \quad n_{\text{limit}} = 6g,\ \sigma_n = 1g$$

### 12.5 热流约束 $J_{\text{heating}}$

$$\boxed{J_{\text{heating}} = \left[\frac{\max(0, \dot{q}_{s,\max} - \dot{q}_{\text{limit}})}{\sigma_{\dot{q}}}\right]^2}, \quad \dot{q}_{\text{limit}} = 500 \text{ kW/m}^2,\ \sigma_{\dot{q}} = 100 \text{ kW/m}^2$$

### 12.6 控制平滑项 $J_{\text{control}}$

$$\boxed{J_{\text{control}} = \frac{1}{1000}\int_{0}^{t_f} \left(\frac{d\phi}{dt}\right)^2 dt}$$

---

## Step 13 — LEO 入轨条件

### 13.1 目标圆轨道

$$h^* = 300 \text{ km}, \quad r_{\text{target}} = R_E + h^* = 6\,671\,000 \text{ m}$$

$$\boxed{v_{\text{circ}} = \sqrt{\frac{\mu_E}{r_{\text{target}}}}} \approx 7\,729.9 \text{ m/s}$$

### 13.2 飞行路径角

$$\boxed{\gamma = \arctan\left(\frac{v_r}{v_h}\right)}$$
$$v_r = \mathbf{v} \cdot \frac{\mathbf{r}}{\|\mathbf{r}\|}, \quad v_h = \sqrt{\|\mathbf{v}\|^2 - v_r^2}$$

### 13.3 理想入轨条件

$$\boxed{h_f \approx h^* = 300 \text{ km}, \quad \|\mathbf{v}_f\| \approx v_{\text{circ}}, \quad \gamma_f \approx 0^\circ}$$

### 13.4 注入点判定

轨迹上**第一个同时满足** $h \ge h^*$ 且 $v \ge 0.95 \cdot v_{\text{circ}}$ 的点。

### 13.5 轨迹状态诊断（从原始状态导出 15 个物理量）

1. 地心距 $r = \|\mathbf{r}\|$
2. 高度 $h = r - R_E$
3. 惯性速度 $V = \|\mathbf{v}\|$
4. 大气密度 $\rho(h)$
5. 大气压强 $p(h)$
6. 大气温度 $T(h)$
7. 声速 $a(h) = \sqrt{\gamma R_a T(h)}$
8. 大气速度 $\mathbf{v}_{\text{atm}} = [-\omega_E r_y,\ \omega_E r_x,\ 0]^T$
9. 相对速度 $\mathbf{v}_{\text{rel}} = \mathbf{v} - \mathbf{v}_{\text{atm}}$
10. 相对速度大小 $V_{\text{rel}}$
11. 动压 $q = \frac{1}{2}\rho V_{\text{rel}}^2$
12. 马赫数 $Ma = V_{\text{rel}} / a$
13. 阻力 $D = \frac{1}{2}\rho V_{\text{rel}}^2 C_D S_{\text{ref}}$
14. 飞行路径角 $\gamma = \arctan(v_r / v_h)$
15. 轴向过载 $n_x = (T - D)/(m g_0)$

---

## Step 14 — 数值积分方法（求解运动方程）

### 14.1 RK4（固定步长，0.5 s）

对 $\frac{d\mathbf{x}}{dt} = \mathbf{f}(t, \mathbf{x})$：

$$\begin{aligned}
\mathbf{k}_1 &= \mathbf{f}(t_n, \mathbf{x}_n) \\
\mathbf{k}_2 &= \mathbf{f}\left(t_n + \frac{\Delta t}{2}, \mathbf{x}_n + \frac{\Delta t}{2}\mathbf{k}_1\right) \\
\mathbf{k}_3 &= \mathbf{f}\left(t_n + \frac{\Delta t}{2}, \mathbf{x}_n + \frac{\Delta t}{2}\mathbf{k}_2\right) \\
\mathbf{k}_4 &= \mathbf{f}\left(t_n + \Delta t, \mathbf{x}_n + \Delta t \cdot \mathbf{k}_3\right) \\
\mathbf{x}_{n+1} &= \mathbf{x}_n + \frac{\Delta t}{6}\left(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4\right)
\end{aligned}$$

全局误差 $O(\Delta t^4)$。

### 14.2 RK45（DOPRI54，自适应步长 — 备选高精度）

七级五阶嵌入四阶，PI 步长控制：

$$\Delta t_{\text{new}} = \Delta t \cdot \min\left(2.0, \max\left(0.5, 0.9 \cdot \varepsilon^{-0.2}\right)\right)$$

$$\varepsilon = \sqrt{\frac{1}{n}\sum_{i=1}^{n}\left(\frac{x_i^{(5)} - x_i^{(4)}}{\text{atol} + \text{rtol} \cdot \max(|x_i^{(5)}|, |x_i|)}\right)^2}$$

---

## Step 15 — 优化算法（搜索最优俯仰程序）

### 15.1 PSO（粒子群，全局粗搜）

速度与位置更新：
$$\boxed{\mathbf{v}_i^{(k+1)} = w^{(k)} \cdot \mathbf{v}_i^{(k)} + c_1 r_1 (\mathbf{p}_{\text{best},i} - \mathbf{x}_i^{(k)}) + c_2 r_2 (\mathbf{g}_{\text{best}} - \mathbf{x}_i^{(k)})}$$
$$\boxed{\mathbf{x}_i^{(k+1)} = \mathbf{x}_i^{(k)} + \mathbf{v}_i^{(k+1)}}$$

惯性权重线性衰减：
$$\boxed{w^{(k)} = w_{\text{start}} - (w_{\text{start}} - w_{\text{end}}) \cdot \frac{k}{K_{\max}}}$$

参数：$w_{\text{start}} = 0.9$, $w_{\text{end}} = 0.4$, $c_1 = c_2 = 2.0$, 40 粒子 × 100 代，连续 20 代无改进早停。

### 15.2 GA（遗传算法）

- **锦标赛选择** ($k=3$)：随机选 3 个个体，取适应度最佳者为父代
- **BLX-α 交叉** ($p_c=0.85$, $\alpha=0.25$)：子代在父代范围 ±25% 内均匀采样
- **高斯变异** ($p_m=0.15$, $\sigma=8\%$·搜索范围)：随机一维加高斯扰动
- **精英保留**：$e=4$ 最优个体直接进下一代

### 15.3 SA（模拟退火，局部精调）

Metropolis 准则：
$$\boxed{P(\text{accept}) = \begin{cases} 1 & \Delta E \le 0 \\ \exp(-\Delta E/T) & \Delta E > 0 \end{cases}}$$

温度衰减：$T_{k+1} = 0.95 \cdot T_k$

自适应步长：$\sigma_j(T) = (x_{\text{high},j} - x_{\text{low},j}) \cdot 0.05 \cdot (T/T_0 + 0.01)$

### 15.4 混合策略

PSO（全局粗搜）→ SA（局部精细搜索）两阶段接力。

---

## Step 16 — LEO 交会对接（载荷已在轨，燃料追赶）

### 16.1 圆轨道角速度（Kepler 第三定律）

$$\boxed{n = \sqrt{\frac{\mu_E}{r^3}}}$$

### 16.2 相对漂移角速度

$$\boxed{\dot{\theta}_{\text{rel}} = n_{\text{phase}} - n_{\text{target}} > 0}, \quad r_{\text{phase}} < r_{\text{target}}$$

较低轨道角速度更大，燃料罐逐渐追上载荷。

### 16.3 等待时间

$$\boxed{t_{\text{wait}} = \frac{\Delta\theta}{|\dot{\theta}_{\text{rel}}|}}$$

### 16.4 Hohmann 上调转移（从调相轨到目标轨）

$$a_{\text{tr}} = \frac{r_{\text{phase}} + r_{\text{target}}}{2}$$

$$v_1^{\text{circ}} = \sqrt{\frac{\mu_E}{r_{\text{phase}}}}, \quad v_2^{\text{circ}} = \sqrt{\frac{\mu_E}{r_{\text{target}}}}$$

$$v_{t1} = \sqrt{\mu_E\left(\frac{2}{r_{\text{phase}}} - \frac{1}{a_{\text{tr}}}\right)}, \quad v_{t2} = \sqrt{\mu_E\left(\frac{2}{r_{\text{target}}} - \frac{1}{a_{\text{tr}}}\right)}$$

$$\boxed{\Delta v_{\text{Hohmann}} = |v_{t1} - v_1^{\text{circ}}| + |v_2^{\text{circ}} - v_{t2}|}$$

### 16.5 交会总 Δv

$$\boxed{\Delta v_{\text{rendezvous}} = \Delta v_{\text{Hohmann}}(r_{\text{phase}} \to r_{\text{target}}) + \Delta v_{\text{docking}}}$$

$\Delta v_{\text{docking}} \approx 15$ m/s（对接姿控余量）。

### 16.6 调相轨道选取权衡

| 调相高度 (km) | Δn (deg/h) | 最差等待 (Δθ=120°) | Hohmann Δv (m/s) | 总 Δv (m/s) |
|---|---|---|---|---|
| 250 | 2.71 | 44.2 h | 29.1 | 44.1 |
| 270 | 1.62 | 74.0 h | 17.4 | 32.4 |
| 280 | 1.08 | 111.2 h | 11.6 | 26.6 |
| 290 | 0.54 | 222.9 h | 5.8 | 20.8 |
| 295 | 0.27 | 446.2 h | 2.9 | 17.9 |

**发射窗口**：每日 2 次，每次 ~5–10 min（发射场穿越轨道面时）。

**工程策略**：通过精确发射时刻控制使 Δθ ≤ 30°，280 km 调相约 28 h 即可交会。

---

## Step 17 — TLI 注入（地月转移轨道）

### 17.1 活力公式（Vis-Viva）

$$\boxed{v^2 = \mu_E\left(\frac{2}{r} - \frac{1}{a}\right)}$$

### 17.2 转移椭圆参数

设 $r_1 = R_E + h_{\text{LEO}}$, $r_2 = 384\,400\,000$ m（地月平均距离）：

$$\boxed{a = \frac{r_1 + r_2}{2}}$$
$$\boxed{e = 1 - \frac{r_1}{a}}$$

### 17.3 各点速度

LEO 圆轨道速度：
$$\boxed{v_c = \sqrt{\frac{\mu_E}{r_1}}}$$

转移椭圆近地点速度（活力公式）：
$$\boxed{v_p = \sqrt{\mu_E\left(\frac{2}{r_1} - \frac{1}{a}\right)}}$$

转移椭圆远地点速度：
$$\boxed{v_a = \sqrt{\mu_E\left(\frac{2}{r_2} - \frac{1}{a}\right)}}$$

### 17.4 TLI Δv（单次冲量近似，近地点切向）

$$\boxed{\Delta v_{\text{TLI}} = v_p - v_c}$$

### 17.5 转移飞行时间（椭圆半周期）

$$\boxed{\text{TOF} = \pi \sqrt{\frac{a^3}{\mu_E}}}$$

### 17.6 C3 发射能量参数

$$E = \frac{v^2}{2} - \frac{\mu_E}{r} = -\frac{\mu_E}{2a}$$
$$\boxed{C_3 = v_\infty^2}, \quad v_\infty = \sqrt{2E} \text{ (当 } E > 0 \text{ 时)}$$

300 km LEO → 地月距离椭圆转移：$E < 0$, $C_3 \approx 0$（椭圆不逃逸）。

### 17.7 不同 LEO 高度下的 TLI 参数

| $h_{\text{LEO}}$ (km) | $v_c$ (km/s) | $v_p$ (km/s) | $\Delta v_{\text{TLI}}$ (km/s) | TOF (d) | $e$ |
|---|---|---|---|---|---|
| 200 | 7.784 | 10.917 | 3.133 | 4.98 | 0.9663 |
| **300** | **7.730** | **10.838** | **3.108** | **4.98** | **0.9659** |
| 400 | 7.677 | 10.761 | 3.084 | 4.98 | 0.9655 |
| 500 | 7.625 | 10.685 | 3.060 | 4.98 | 0.9651 |

---

## Step 18 — 质量预算（齐奥尔科夫斯基方程）

### 18.1 理想火箭方程

$$\boxed{\Delta v = I_{\text{sp}} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)}$$
$$\boxed{\text{MR} = \frac{m_0}{m_f} = \exp\left(\frac{\Delta v}{I_{\text{sp}} \cdot g_0}\right)}$$

### 18.2 结构系数

$$\boxed{\varepsilon = \frac{m_{\text{dry}}}{m_{\text{prop}}}}$$

### 18.3 推进剂质量反解（从 Δv 回推）

固定质量 $m_{\text{fixed}} = m_{\text{cargo}} + m_{\text{adapter}} = 40 + 4 = 44$ t。

$$m_0 = m_{\text{fixed}} + (1 + \varepsilon)m_{\text{prop}}, \quad m_f = m_{\text{fixed}} + \varepsilon \cdot m_{\text{prop}}$$

$$\text{MR} = \frac{m_{\text{fixed}} + (1 + \varepsilon)m_{\text{prop}}}{m_{\text{fixed}} + \varepsilon \cdot m_{\text{prop}}}$$

反解：
$$\boxed{m_{\text{prop}} = \frac{(\text{MR} - 1) \cdot m_{\text{fixed}}}{1 - (\text{MR} - 1) \cdot \varepsilon}}$$
$$\boxed{m_{\text{dry}} = \varepsilon \cdot m_{\text{prop}}}$$
$$\boxed{m_{\text{stack,LEO}} = m_{\text{fixed}} + m_{\text{prop}} + m_{\text{dry}}}$$

### 18.4 基线计算（$I_{\text{sp}} = 450$ s, $\varepsilon = 0.08$）

$$\text{MR} = \exp\left(\frac{3108.19}{450 \times 9.80665}\right) = 2.0225$$

$$m_{\text{prop}} = \frac{(2.0225 - 1) \times 44}{1 - (2.0225 - 1) \times 0.08} = 49.0 \text{ t}$$

$$m_{\text{dry}} = 0.08 \times 49.0 = 3.92 \text{ t}$$

$$m_{\text{stack,LEO}} = 44 + 49.0 + 3.92 = 96.9 \text{ t}$$

### 18.5 发射分配（载荷+燃料分开发射）

$$\boxed{m_{\text{LEO,A}} = m_{\text{fixed}} + m_{\text{dry}} = 44 + 3.92 = 47.9 \text{ t (Launch A: 载荷+TLI发动机)}}$$
$$\boxed{m_{\text{LEO,B}} = m_{\text{prop}} = 49.0 \text{ t (Launch B: TLI推进剂)}}$$

| 发射 | 入轨质量 | CZ-10 LEO 运力 | 余量 |
|------|---------|------------|------|
| Launch A | 47.9 t | ~70 t | +22.1 t |
| Launch B | 49.0 t | ~70 t | +21.0 t |

两发均在运力范围内。TLI 后质量 $m_f = 47.9$ t。MR = 96.9/47.9 = 2.0225。

---

## Step 19 — 可靠性分析

### 19.1 发动机簇可靠性

$N$ 台并联，允许 $f$ 台失效的 k-out-of-N 冗余模型：
$$\boxed{R_{\text{cluster}}(f) = \sum_{k=0}^{f} \binom{N}{k} (1-r)^k \cdot r^{N-k}}$$

CZ-10 S1 级 21 台 YF-100K，允许 1 台失效：
$$R_{\text{CZ-10 S1}} = r^{21} + 21 \cdot (1-r) \cdot r^{20}$$

对比 Starship Super Heavy 33 台 Raptor 不允许失效：$R_{\text{SH}} = r^{33}$ — 在相同单机可靠度下 CZ-10 明显更优。

### 19.2 多发任务可靠性

$$\boxed{P(N, K; R_L) = \sum_{s=K}^{N} \binom{N}{s} R_L^s (1-R_L)^{N-s}}$$

两发全成功：$P_2 = R_L^2$

### 19.3 总任务可靠性链

$$\boxed{R_{\text{total}} = R_L^2 \cdot R_{\text{rendezvous}} \cdot R_{\text{TLI}}}$$

基线 ($R_L = 0.95$, $R_{\text{rend}} = 0.98$, $R_{\text{TLI}} = 0.985$):
$$R_{\text{total}} = 0.95^2 \times 0.98 \times 0.985 = 0.8712$$

### 19.4 非对称发射可靠性（载荷+燃料分离特有）

载荷失败 = 任务失败；燃料失败 = 可重发。

$$\boxed{R_{\text{asym, relaunch}} = R_L \cdot [R_L + (1 - R_L) \cdot R_L'] \cdot R_{\text{rendezvous}} \cdot R_{\text{TLI}}}$$

基线对比：

| 方案 | 发射环节 | 总可靠度 |
|------|---------|---------|
| 对称两发 | $R_L^2 = 0.9025$ | 0.8712 |
| 非对称可重发 | $R_L \cdot [R_L + (1-R_L)R_L] = 0.9476$ | 0.9148 |

非对称可重发提升 ~0.044。核心优势：燃料失败时载荷在轨等待，不需重建 40 t 模块。

---

## Step 20 — 补充模块

### 20.1 Sutherland 粘性公式（备用）

$$\boxed{\mu(T) = \mu_{\text{ref}} \cdot \left(\frac{T}{T_{\text{ref}}}\right)^{3/2} \cdot \frac{T_{\text{ref}} + S}{T + S}}$$
$\mu_{\text{ref}} = 1.716 \times 10^{-5}$ Pa·s, $T_{\text{ref}} = 273.15$ K, $S = 110.4$ K。

（当前用于 $AtmoState$ 特征输出，未来边界层传热分析备用。）

### 20.2 Lambert 问题（高精度交会备用）

给定 $\mathbf{r}_1$, $\mathbf{r}_2$, $\Delta t$, 求 $\mathbf{v}_1$, $\mathbf{v}_2$。

**Stumpff 函数**（统一处理椭圆/抛物/双曲）:

$$\boxed{C(z) = \begin{cases} \dfrac{1 - \cos\sqrt{z}}{z} & z > 0 \\[8pt] \dfrac{\cosh\sqrt{-z} - 1}{-z} & z < 0 \\[8pt] \dfrac{1}{2} & z = 0 \end{cases}}$$
$$\boxed{S(z) = \begin{cases} \dfrac{\sqrt{z} - \sin\sqrt{z}}{z^{3/2}} & z > 0 \\[8pt] \dfrac{\sinh\sqrt{-z} - \sqrt{-z}}{(-z)^{3/2}} & z < 0 \\[8pt] \dfrac{1}{6} & z = 0 \end{cases}}$$

**通用变量时间方程**：
$$\boxed{\sqrt{\mu} \cdot \Delta t = \chi^3 \cdot S(z) + A \cdot \sqrt{y}}$$

Newton-Raphson 迭代求解 $\chi$，收敛后通过 $f$ 和 $g$ 函数反算 $\mathbf{v}_1$, $\mathbf{v}_2$。

> 当前方案使用 Hohmann+相位角模型处理 LEO 交会（Step 16），Lambert 作为高精度备选。

---

## 解题推导总图

```
┌──────────────────────────────────────────────────────┐
│ Step 1–3: 常数设定 + 选箭(CZ-10) + 选场(文昌)        │
│              ↓                                       │
│ Step 4:     任务架构决策 → 载荷+燃料分开发射           │
│              ↓                                       │
│ Step 5:     坐标系(ECI) + 初始条件                    │
│              ↓                                       │
│ Step 6:     引力模型: spherical→J2→J3→J4→总引力       │
│ Step 7:     大气模型: 位势高度→9层分层→非等温/等温→ρ,p,T │
│ Step 8:     气动力: v_rel→q→D→q̇_s(热流)              │
│ Step 9:     推力模型: T/Isp反压修正 + ENU方向分解       │
│              ↓                                       │
│ Step 10:    完整ECI运动方程(引力+推力+阻力+Coriolis)    │
│              ↓                                       │
│ Step 11:    俯仰程序角 φ(t) [设计变量 u]               │
│ Step 12:    多目标代价函数 J(u)                        │
│              ↓                                       │
│ Step 13:    LEO入轨条件: h*, v_circ, γ_f, 注入点判定   │
│ Step 14:    数值积分 RK4/RK45 求解轨迹                  │
│ Step 15:    优化算法 PSO/GA/SA 搜索 min J(u)           │
│              ↓                                       │
│ 最优俯仰程序 u* → Launch A/B 各自的上升段最优轨迹       │
│              ↓                                       │
│ Step 16:    LEO交会: 调相→Hohmann上调→对接             │
│ Step 17:    TLI注入: Vis-Viva→Δv_TLI→TOF→C3          │
│ Step 18:    质量预算: 齐奥尔科夫斯基→推进剂反解→发射分配 │
│ Step 19:    可靠性: 发动机簇→多发→串联链→非对称对比     │
│              ↓                                       │
│ Step 20:    补充模块(Sutherland / Lambert)              │
│              ↓                                       │
│         最终方案: Δv_TLI=3.108 km/s, 96.9 t LEO       │
│         Launch A: 47.9 t(载荷+TLI发动机)               │
│         Launch B: 49.0 t(推进剂)                       │
│         可靠性: 0.915(可重发) vs Starship 33发动机单发  │
└──────────────────────────────────────────────────────┘
```

---

## 关键数值汇总

| 指标 | 数值 |
|------|------|
| 推荐架构 | 载荷(先发) + 燃料(后发) → LEO 快速交会 → 组合体 TLI |
| Launch A 入轨质量 | 47.9 t |
| Launch B 入轨质量 | 49.0 t |
| 目标轨道 (LEO) | 300 km 圆轨道 |
| 目标轨道速度 | 7.730 km/s |
| 文昌自转增益 (正东) | ~438 m/s |
| 入轨最小倾角 | ~19.6° |
| TLI Δv | 3.108 km/s |
| TLI TOF | 4.98 d |
| TLI 偏心率 | 0.9659 |
| 组合体质量 | 96.9 t |
| TLI 推进剂 | 49.0 t |
| TLI 干重 | 3.92 t |
| CZ-10 S1 推进剂 | 1 420 t |
| CZ-10 S2 推进剂 | 285 t |
| S1 真空推力 | 29.34 MN (21×YF-100K) |
| 起飞质量 | ~2 189 t |
| 可靠性 (对称) | 0.871 |
| 可靠性 (非对称可重发) | 0.915 |
| J2 对入轨速度影响 | ~+41 m/s |
| 快速交会 (280 km) | 1.08 deg/h, Δv ~27 m/s |
