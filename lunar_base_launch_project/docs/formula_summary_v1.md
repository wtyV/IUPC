# 月球基地运载方案 — 完整数学物理建模公式

**任务目标**：两枚长征十号运载火箭将总计 40 t 月球基地建设物资送入地月转移轨道（TLI：Translunar Injection）。

**推荐任务架构 —— 载荷+燃料分开发射**（Payload-Fuel Split）：

- **Launch A（载荷先发）**：将 40 t 月球基地物资 + 4 t 对接适配器 + TLI 级干质量（发动机/结构）送入 300 km LEO 停泊轨道。
- **Launch B（燃料后发）**：将 TLI 级推进剂送入 LEO，利用低轨快速调相与 A 交会对接。
- **组合体 TLI 点火**：A + B 对接后形成完整 TLI 级，近地点点火进入地月转移椭圆。

该方案的优势：(1) 载荷先到先等，不需拆分；(2) 燃料为纯推进剂，发射失败可重新发射；(3) 低轨快速交会缩短等待时间。

---

## 第一章 数值积分方法

### 1.1 经典四阶 Runge-Kutta 方法 (RK4)

对于一阶常微分方程组初值问题：

$$\frac{d\mathbf{x}}{dt} = \mathbf{f}(t, \mathbf{x}), \quad \mathbf{x}(t_0) = \mathbf{x}_0$$

RK4 单步积分公式为：

$$\begin{aligned}
\mathbf{k}_1 &= \mathbf{f}(t_n, \mathbf{x}_n) \\
\mathbf{k}_2 &= \mathbf{f}\left(t_n + \frac{\Delta t}{2}, \mathbf{x}_n + \frac{\Delta t}{2}\mathbf{k}_1\right) \\
\mathbf{k}_3 &= \mathbf{f}\left(t_n + \frac{\Delta t}{2}, \mathbf{x}_n + \frac{\Delta t}{2}\mathbf{k}_2\right) \\
\mathbf{k}_4 &= \mathbf{f}\left(t_n + \Delta t, \mathbf{x}_n + \Delta t \cdot \mathbf{k}_3\right) \\
\mathbf{x}_{n+1} &= \mathbf{x}_n + \frac{\Delta t}{6}\left(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4\right)
\end{aligned}$$

局部截断误差为 $O(\Delta t^5)$，全局累积误差为 $O(\Delta t^4)$。

### 1.2 Dormand-Prince 5(4) 自适应步长方法 (RK45)

采用七级五阶嵌入四阶的 DOPRI54 格式。第 $s$ 级计算：

$$\mathbf{k}_s = \mathbf{f}\left(t_n + c_s \Delta t, \mathbf{x}_n + \Delta t \sum_{j=1}^{s-1} a_{sj} \mathbf{k}_j\right)$$

五阶解 $\mathbf{x}_{n+1}^{(5)}$ 与四阶解 $\mathbf{x}_{n+1}^{(4)}$ 的差值用于误差估计，步长采用 PI 控制器调整：

$$\Delta t_{\text{new}} = \Delta t \cdot \min\left(2.0, \max\left(0.5, 0.9 \cdot \varepsilon^{-0.2}\right)\right)$$

其中 $\varepsilon$ 为经过容差标度化后的相对误差：

$$\varepsilon = \sqrt{\frac{1}{n}\sum_{i=1}^{n}\left(\frac{x_i^{(5)} - x_i^{(4)}}{\text{atol} + \text{rtol} \cdot \max(|x_i^{(5)}|, |x_i|)}\right)^2}$$

Butcher 表采用经典 DOPRI54 系数（7 级 7 列），不再赘列。

---

## 第二章 标准大气模型 — 杨炳蔚教材

### 2.1 基本常数

| 符号 | 数值 | 单位 | 含义 |
|------|------|------|------|
| $g_0$ | 9.80665 | m/s² | 标准重力加速度 |
| $R_a$ | 287.05287 | J/(kg·K) | 干空气气体常数 |
| $\gamma$ | 1.4 | — | 空气比热比 |
| $R_E$ | 6371000 | m | 地球平均半径 |
| $p_0$ | 101325 | Pa | 海平面标准气压 |
| $T_0$ | 288.15 | K | 海平面标准温度 |
| $\rho_0$ | 1.225 | kg/m³ | 海平面标准密度 |

### 2.2 位势高度与几何高度的转换

位势高度的定义考虑了重力随高度的变化：

$$H = \frac{R_E \cdot h}{R_E + h}$$

其反变换为：

$$h = \frac{R_E \cdot H}{R_E - H}$$

其中 $h$ 为几何高度 (m)，$H$ 为位势高度 (m)。

### 2.3 大气分层参数（9 层，0～120 km）

| 层 $i$ | 名称 | $H_{\text{base}}$ (km) | $H_{\text{top}}$ (km) | $T_{\text{base}}$ (K) | $L_i$ (K/km) | 类型 |
|--------|------|------------------------|----------------------|----------------------|-------------|------|
| 0 | 对流层 | 0 | 11 | 288.15 | −6.5 | 非等温 |
| 1 | 对流层顶 | 11 | 20 | 216.65 | 0 | 等温 |
| 2 | 平流层下部 | 20 | 32 | 216.65 | +1.0 | 非等温 |
| 3 | 平流层上部 | 32 | 47 | 228.65 | +2.8 | 非等温 |
| 4 | 平流层顶 | 47 | 51 | 270.65 | 0 | 等温 |
| 5 | 中间层 | 51 | 71 | 270.65 | −2.8 | 非等温 |
| 6 | 中间层上部 | 71 | 84.852 | 214.65 | −2.0 | 非等温 |
| 7 | 中间层顶 | 84.852 | 92 | 186.87 | 0 | 等温 |
| 8 | 热层底部 | 92 | 120 | 186.87 | +4.0 | 非等温 |

### 2.4 非等温层（$L_i \neq 0$）的温度、压强和密度

设第 $i$ 层的温度梯度为 $L_i = dT/dH$（常数）。由流体静力学平衡方程：

$$\frac{dp}{dH} = -\rho g_0$$

与理想气体状态方程：

$$p = \rho R_a T$$

联立求解。

**温度分布**（线性）：

$$T(H) = T_{\text{base},i} + L_i \cdot (H - H_{\text{base},i})$$

**压强分布**（对流体静力学方程积分）：

由 $\frac{dp}{dH} = -\frac{p g_0}{R_a T}$，代入 $T(H) = T_{\text{base},i} + L_i(H - H_{\text{base},i})$，令 $dT = L_i dH$：

$$\frac{dp}{p} = -\frac{g_0}{R_a L_i} \cdot \frac{dT}{T}$$

积分得：

$$\ln\frac{p(H)}{p_{\text{base},i}} = -\frac{g_0}{R_a L_i} \ln\frac{T(H)}{T_{\text{base},i}}$$

即完整的非等温层压强分布公式：

$$p(H) = p_{\text{base},i} \cdot \left[\frac{T_{\text{base},i}}{T(H)}\right]^{\frac{g_0}{R_a L_i}}$$

**密度**由理想气体状态方程给出：

$$\rho(H) = \frac{p(H)}{R_a \cdot T(H)}$$

### 2.5 等温层（$L_i = 0$）的温度、压强和密度

**温度**：

$$T(H) = T_{\text{base},i} = \text{const}$$

由 $\frac{dp}{dH} = -\frac{p g_0}{R_a T_{\text{base},i}}$，直接积分：

$$\frac{dp}{p} = -\frac{g_0}{R_a T_{\text{base},i}} dH$$

$$\ln\frac{p(H)}{p_{\text{base},i}} = -\frac{g_0}{R_a T_{\text{base},i}}(H - H_{\text{base},i})$$

即完整等温层压强分布公式：

$$p(H) = p_{\text{base},i} \cdot \exp\left[-\frac{g_0(H - H_{\text{base},i})}{R_a T_{\text{base},i}}\right]$$

**密度**同样由状态方程给出：

$$\rho(H) = \frac{p(H)}{R_a \cdot T_{\text{base},i}}$$

### 2.6 声速

由理想气体绝热声速公式：

$$a(H) = \sqrt{\gamma \cdot R_a \cdot T(H)}$$

### 2.7 Sutherland 动力粘性公式

空气动力粘性系数随温度的变化由 Sutherland 公式描述：

$$\mu(T) = \mu_{\text{ref}} \cdot \left(\frac{T}{T_{\text{ref}}}\right)^{3/2} \cdot \frac{T_{\text{ref}} + S}{T + S}$$

其中：

$$\mu_{\text{ref}} = 1.716 \times 10^{-5} \text{ Pa·s}, \quad T_{\text{ref}} = 273.15 \text{ K}, \quad S = 110.4 \text{ K}$$

### 2.8 热层延伸模型（$H \ge 120$ km）

对于超过 120 km 位势高度的大气，密度采用指数衰减外推：

$$\rho(H) = \rho_{120} \cdot \exp\left(-\frac{H - H_{120}}{H_{\text{scale}}}\right)$$

其中 $\rho_{120} = 2.44 \times 10^{-8}$ kg/m³, $H_{\text{scale}} = 15000$ m, $T \approx 380$ K。

### 2.9 边界条件

对于 $h \le 0$，取海平面标准值 $\rho = \rho_0$, $p = p_0$, $T = T_0$。

---

## 第三章 地球引力场模型

### 3.1 基本常数

| 符号 | 数值 | 含义 |
|------|------|------|
| $\mu_E$ | $3.986004418 \times 10^{14}$ m³/s² | 地球引力参数 |
| $R_E$ | $6\,371\,000$ m | 地球平均半径（用于引力计算） |
| $R_E^{\text{eq}}$ | $6\,378\,137$ m | 地球赤道半径 (WGS84) |
| $f$ | $1/298.257223563$ | 地球扁率 (WGS84) |

### 3.2 带谐项系数 (EGM2008)

| 系数 | 数值 | 含义 |
|------|------|------|
| $J_2$ | $+1.0826266835531513 \times 10^{-3}$ | 动力学扁率 |
| $J_3$ | $-2.5326564853322357 \times 10^{-6}$ | 梨形不对称 |
| $J_4$ | $-1.6196215913672832 \times 10^{-6}$ | 下一阶扁率修正 |

### 3.3 引力势函数的一般形式

地球引力势函数在球谐展开下的标准形式为：

$$U(r, \phi_g, \lambda) = \frac{\mu_E}{r}\left[1 - \sum_{n=2}^{N} J_n \left(\frac{R_E}{r}\right)^n P_n(\sin\phi_g) + \sum_{n=2}^{N} \sum_{m=1}^{n} \left(\frac{R_E}{r}\right)^n P_n^m(\sin\phi_g)\left(C_{nm}\cos m\lambda + S_{nm}\sin m\lambda\right)\right]$$

其中 $\phi_g$ 为地心纬度，$\lambda$ 为地心经度，$P_n$ 为 $n$ 阶 Legendre 多项式，$P_n^m$ 为 $n$ 阶 $m$ 次缔合 Legendre 函数。

加速度为势函数的负梯度：

$$\mathbf{a}_{\text{grav}} = -\nabla U(\mathbf{r})$$

本模型仅取带谐项（$m=0$，即 $J_n$ 项），忽略田谐项（$C_{nm}, S_{nm}$ 在 $m \ge 1$ 情况）。

### 3.4 球形二体引力加速度

取 $N=1$（仅保留中心引力项）：

$$r = \|\mathbf{r}\| = \sqrt{x^2 + y^2 + z^2}$$

$$\mathbf{a}_{\text{spherical}} = -\frac{\mu_E}{r^3} \begin{bmatrix} x \\ y \\ z \end{bmatrix}$$

写成分量形式：

$$a_x^{\text{sph}} = -\frac{\mu_E \cdot x}{r^3}, \quad a_y^{\text{sph}} = -\frac{\mu_E \cdot y}{r^3}, \quad a_z^{\text{sph}} = -\frac{\mu_E \cdot z}{r^3}$$

### 3.5 J2 项引力势与加速度

J2 项对应的势函数为：

$$U_{J2}(r, \phi_g) = -\frac{\mu_E}{r} \cdot J_2 \cdot \left(\frac{R_E}{r}\right)^2 \cdot P_2(\sin\phi_g)$$

其中二阶 Legendre 多项式：

$$P_2(x) = \frac{1}{2}(3x^2 - 1)$$

取 $x = \sin\phi_g = z/r$，则：

$$P_2(z/r) = \frac{1}{2}\left(\frac{3z^2}{r^2} - 1\right)$$

$$U_{J2} = -\frac{\mu_E J_2 R_E^2}{2r^3}\left(\frac{3z^2}{r^2} - 1\right)$$

对 $U_{J2}$ 求负梯度 $\mathbf{a}_{J2} = -\nabla U_{J2}$，得 ECEF 笛卡尔坐标系中的 J2 加速度分量：

$$\boxed{a_x^{J2} = -\frac{3}{2} \cdot \frac{\mu_E J_2 R_E^2}{r^5} \cdot x \cdot \left(1 - \frac{5z^2}{r^2}\right)}$$

$$\boxed{a_y^{J2} = -\frac{3}{2} \cdot \frac{\mu_E J_2 R_E^2}{r^5} \cdot y \cdot \left(1 - \frac{5z^2}{r^2}\right)}$$

$$\boxed{a_z^{J2} = -\frac{3}{2} \cdot \frac{\mu_E J_2 R_E^2}{r^5} \cdot z \cdot \left(3 - \frac{5z^2}{r^2}\right)}$$

### 3.6 J3 项引力势与加速度

J3 项对应的势函数为：

$$U_{J3}(r, \phi_g) = \frac{\mu_E}{r} \cdot J_3 \cdot \left(\frac{R_E}{r}\right)^3 \cdot P_3(\sin\phi_g)$$

注意：标准地球物理学约定中 J3 项取正号（J3 本身为负值，因此该项在北极区域贡献正值）。

三阶 Legendre 多项式：

$$P_3(x) = \frac{1}{2}(5x^3 - 3x)$$

其一阶导数为：

$$P_3'(x) = \frac{1}{2}(15x^2 - 3)$$

令 $s = z/r$，则 $P_3(s) = \frac{1}{2}(5s^3 - 3s)$, $P_3'(s) = \frac{1}{2}(15s^2 - 3)$。

通过链式法则求梯度 $\mathbf{a}_{J3} = -\nabla U_{J3}$，其完整形式为：

$$a_x^{J3} = \frac{x}{r} \cdot \frac{\partial U_{J3}}{\partial r} + \frac{\partial U_{J3}}{\partial s} \cdot \frac{\partial s}{\partial x}$$

$$a_y^{J3} = \frac{y}{r} \cdot \frac{\partial U_{J3}}{\partial r} + \frac{\partial U_{J3}}{\partial s} \cdot \frac{\partial s}{\partial y}$$

$$a_z^{J3} = \frac{z}{r} \cdot \frac{\partial U_{J3}}{\partial r} + \frac{\partial U_{J3}}{\partial s} \cdot \frac{\partial s}{\partial z}$$

其中各偏导数为：

$$\frac{\partial s}{\partial x} = -\frac{xz}{r^3}, \quad \frac{\partial s}{\partial y} = -\frac{yz}{r^3}, \quad \frac{\partial s}{\partial z} = \frac{1}{r} - \frac{z^2}{r^3}$$

$$\frac{\partial U_{J3}}{\partial r} = -4\mu_E J_3 \frac{R_E^3}{r^5} P_3(s), \quad \frac{\partial U_{J3}}{\partial s} = \mu_E J_3 \frac{R_E^3}{r^4} P_3'(s)$$

### 3.7 J4 项引力势与加速度

J4 项对应的势函数为：

$$U_{J4}(r, \phi_g) = -\frac{\mu_E}{r} \cdot J_4 \cdot \left(\frac{R_E}{r}\right)^4 \cdot P_4(\sin\phi_g)$$

四阶 Legendre 多项式：

$$P_4(x) = \frac{1}{8}(35x^4 - 30x^2 + 3)$$

其一阶导数为：

$$P_4'(x) = \frac{1}{2}(35x^3 - 15x)$$

以与 J3 类同的方式求梯度，得到 J4 加速度的三个笛卡尔分量：

$$a_x^{J4} = -\frac{x}{r} \cdot \frac{\partial U_{J4}}{\partial r} + \frac{\partial U_{J4}}{\partial s} \cdot \frac{\partial s}{\partial x}$$

$$a_y^{J4} = -\frac{y}{r} \cdot \frac{\partial U_{J4}}{\partial r} + \frac{\partial U_{J4}}{\partial s} \cdot \frac{\partial s}{\partial y}$$

$$a_z^{J4} = -\frac{z}{r} \cdot \frac{\partial U_{J4}}{\partial r} + \frac{\partial U_{J4}}{\partial s} \cdot \frac{\partial s}{\partial z}$$

其中：

$$\frac{\partial U_{J4}}{\partial r} = 5\mu_E J_4 \frac{R_E^4}{r^6} P_4(s), \quad \frac{\partial U_{J4}}{\partial s} = -\mu_E J_4 \frac{R_E^4}{r^5} P_4'(s)$$

### 3.8 总引力加速度

在 ECI/ECEF 坐标系中，总引力加速度为各阶贡献之和：

$$\boxed{\mathbf{a}_{\text{grav}}(\mathbf{r}) = \mathbf{a}_{\text{spherical}}(\mathbf{r}) + \mathbf{a}_{J2}(\mathbf{r}) + \mathbf{a}_{J3}(\mathbf{r}) + \mathbf{a}_{J4}(\mathbf{r})}$$

ECI 与 ECEF 坐标系的引力加速度表达式相同（因为 z 轴均为地球自转轴，带谐项仅依赖于 $z/r$ 比值）。

### 3.9 引力势的径向大小

在给定地心距 $r$ 和地心纬度 $\phi_g$ 处，引力势大小的标量形式为：

$$U(r, \phi_g) = \frac{\mu_E}{r}\left[1 - J_2\left(\frac{R_E}{r}\right)^2 P_2(\sin\phi_g) + J_3\left(\frac{R_E}{r}\right)^3 P_3(\sin\phi_g) - J_4\left(\frac{R_E}{r}\right)^4 P_4(\sin\phi_g)\right]$$

---

## 第四章 上升段质点动力学

### 4.1 坐标系

采用地心惯性坐标系 (ECI: Earth-Centered Inertial)。取仿真初始时刻 ($t=0$) ECI 与 ECEF 重合。地球自转角速度矢量：

$$\boldsymbol{\omega}_E = \begin{bmatrix} 0 \\ 0 \\ \omega_E \end{bmatrix}, \quad \omega_E = 7.2921159 \times 10^{-5} \text{ rad/s}$$

### 4.2 状态向量

上升段的 ECI 状态向量为 6 维（质量单独采用代数更新）：

$$\mathbf{x}(t) = \begin{bmatrix} r_x \\ r_y \\ r_z \\ v_x \\ v_y \\ v_z \end{bmatrix}_{\text{ECI}}, \quad m(t) \text{（单独更新）}$$

### 4.3 运动方程

完整的三维质点上升段动力学方程（ECI 框架下）：

$$\boxed{\frac{d\mathbf{r}}{dt} = \mathbf{v}}$$

$$\boxed{\frac{d\mathbf{v}}{dt} = \mathbf{g}(\mathbf{r}) + \frac{T}{m}\hat{\mathbf{u}}_T - \frac{D}{m}\frac{\mathbf{v}_{\text{rel}}}{\|\mathbf{v}_{\text{rel}}\|} - 2\boldsymbol{\omega}_E \times \mathbf{v}}$$

$$\boxed{\frac{dm}{dt} = -\frac{T}{I_{\text{sp}} \cdot g_0}}$$

其中每一项的物理含义：

| 项 | 符号 | 物理含义 |
|----|------|---------|
| $\mathbf{g}(\mathbf{r})$ | 引力加速度 | 球形 + J2 + J3 + J4（第三章） |
| $\frac{T}{m}\hat{\mathbf{u}}_T$ | 推力加速度 | 发动机推力沿箭体方向 |
| $-\frac{D}{m}\frac{\mathbf{v}_{\text{rel}}}{\|\mathbf{v}_{\text{rel}}\|}$ | 气动阻力加速度 | 与相对大气速度反向 |
| $-2\boldsymbol{\omega}_E \times \mathbf{v}$ | Coriolis 加速度 | 地球自转引起的惯性力 |

其中 $T$ 为发动机瞬时推力 (N)，$I_{\text{sp}}$ 为瞬时比冲 (s)，$g_0 = 9.80665$ m/s²。

### 4.4 初始条件

**初始位置** (ECEF = ECI 在 $t=0$ 时刻)：

发射点地理纬度为 $\varphi$（文昌 $\varphi = 19.614^\circ$），经度为 $\lambda$（文昌 $\lambda = 110.951^\circ$），高程为 $h_0$（文昌 $h_0 = 50$ m）：

$$r_0 = R_E + h_0$$

$$\begin{bmatrix} r_{x0} \\ r_{y0} \\ r_{z0} \end{bmatrix}_{\text{ECI}} = \begin{bmatrix} r_0 \cos\varphi \cos\lambda \\ r_0 \cos\varphi \sin\lambda \\ r_0 \sin\varphi \end{bmatrix}$$

**初始速度**（地球自转引起的切向速度）：

$$\begin{bmatrix} v_{x0} \\ v_{y0} \\ v_{z0} \end{bmatrix}_{\text{ECI}} = \boldsymbol{\omega}_E \times \mathbf{r}_0 = \begin{bmatrix} -\omega_E \cdot y_0 \\ \omega_E \cdot x_0 \\ 0 \end{bmatrix}$$

**初始质量**：

$$m_0 = \sum_{j} m_{\text{dry},j} + \sum_{j} m_{\text{prop},j} + m_{\text{payload}} + m_{\text{fairing}}$$

### 4.5 推力方向 — ENU 坐标基

在 ECI 系中，推力方向由当地 ENU（East-North-Up）坐标基和程序角确定。

**当地天向单位矢量** $\hat{\mathbf{u}}$：

$$\hat{\mathbf{u}} = \frac{\mathbf{r}}{\|\mathbf{r}\|}$$

**当地东向单位矢量** $\hat{\mathbf{e}}$（利用 $\boldsymbol{\omega}_E = [0, 0, \omega_E]^T$）：

$$\hat{\mathbf{e}} = \frac{\boldsymbol{\omega}_E \times \mathbf{r}}{\|\boldsymbol{\omega}_E \times \mathbf{r}\|} = \frac{1}{\sqrt{x^2 + y^2}}\begin{bmatrix} -y \\ x \\ 0 \end{bmatrix}$$

**当地北向单位矢量** $\hat{\mathbf{n}}$（右手定则）：

$$\hat{\mathbf{n}} = \hat{\mathbf{u}} \times \hat{\mathbf{e}}$$

**水平发射方向**（发射方位角 $A$ 从正北顺时针计量，文昌向东发射 $A = 90^\circ$）：

$$\hat{\mathbf{h}}_A = \cos A \cdot \hat{\mathbf{n}} + \sin A \cdot \hat{\mathbf{e}}$$

**推力方向单位矢量**（程序角 $\phi$ 定义为推力方向相对于当地水平面的仰角，$\phi = 90^\circ$ 为垂直向上，$\phi = 0^\circ$ 为水平）：

$$\boxed{\hat{\mathbf{u}}_T = \sin\phi \cdot \hat{\mathbf{u}} + \cos\phi \cdot \hat{\mathbf{h}}_A}$$

展开为完整形式：

$$\hat{\mathbf{u}}_T = \sin\phi \cdot \hat{\mathbf{u}} + \cos\phi \cdot \left(\cos A \cdot \hat{\mathbf{n}} + \sin A \cdot \hat{\mathbf{e}}\right)$$

### 4.6 程序角模型 — 分段光滑俯仰转弯

程序角 $\phi(t)$ 为时间的函数，采用分段光滑下降形式。设计变量为四个参数：$\{t_v, t_{\text{end}}, \phi_f, s\}$。

$$\boxed{\phi(t) = \begin{cases} 90^\circ & 0 \le t \le t_v \\[6pt] 90^\circ - \left(\dfrac{t - t_v}{t_{\text{end}} - t_v}\right)^{s} \cdot (90^\circ - \phi_f) & t_v < t < t_{\text{end}} \\[6pt] \phi_f & t \ge t_{\text{end}} \end{cases}}$$

| 参数 | 含义 | 典型范围 |
|------|------|---------|
| $t_v$ | 垂直上升段时间 | 5～20 s |
| $t_{\text{end}}$ | 俯仰转弯结束时间 | 200～400 s |
| $\phi_f$ | 终端程序角 | 2°～20° |
| $s$ | 形状指数（控制转弯的剧烈程度） | 0.8～2.0 |

备选方案：双线性切线制导律（适用于真空段最优控制）

$$\tan\theta(t) = \frac{a \cdot t + b}{c \cdot t + d}$$

$$\phi(t) = \arctan\left(\frac{a \cdot t + b}{c \cdot t + d}\right)$$

其中 $\theta$ 为推力方向与某个参考方向之间的夹角，$\{a, b, c, d\}$ 为待优化参数。

### 4.7 推力与比冲的大气反压修正

火箭发动机在海平面与真空之间存在推力差异，随环境大气压强 $p_{\text{amb}}(h)$ 的变化为：

$$\boxed{T(h) = T_{\text{vac}} - (T_{\text{vac}} - T_{\text{sl}}) \cdot \frac{p_{\text{amb}}(h)}{p_0}}$$

$$\boxed{I_{\text{sp}}(h) = I_{\text{sp,vac}} - (I_{\text{sp,vac}} - I_{\text{sp,sl}}) \cdot \frac{p_{\text{amb}}(h)}{p_0}}$$

其中 $p_0 = 101325$ Pa 为标准海平面大气压强。

### 4.8 质量消耗与分级模型

第 $j$ 级的瞬时推进剂质量流率：

$$\dot{m}_j = \frac{T_j(h)}{I_{\text{sp},j}(h) \cdot g_0}$$

第 $j$ 级的理论燃烧时间：

$$t_{\text{burn},j} = \frac{m_{\text{prop},j}}{\dot{m}_j}$$

级间分离时的质量跃变（抛弃该级干质量）：

$$m^+ = m^- - m_{\text{dry},j}$$

### 4.9 长征十号两级入轨模型参数

| 参数 | S1 助推+芯级 | S2 上面级 |
|------|------------|----------|
| 推进剂质量 $m_{\text{prop}}$ | 1 420 t | 285 t |
| 干质量 $m_{\text{dry}}$ | 260 t | 45 t |
| 真空推力 $T_{\text{vac}}$ | 29.34 MN (21×YF-100K) | 5.59 MN (4×YF-100K) |
| 海平面推力 $T_{\text{sl}}$ | 26.25 MN | 5.59 MN |
| 真空比冲 $I_{\text{sp,vac}}$ | 338.2 s | 340.0 s |
| 海平面比冲 $I_{\text{sp,sl}}$ | 301.8 s | 340.0 s |
| 发动机数量 | 21 | 4 |
| 载荷 $m_{\text{payload}}$ | — | 20 t |
| 整流罩 $m_{\text{fairing}}$ | 4 t（200 s 时抛离） | — |
| 参考面积 $S_{\text{ref}}$ | 78.5 m² | — |
| 阻力系数 $C_D$ | 0.30 | — |

---

## 第五章 气动力模型

### 5.1 大气相对速度

大气随地球固连转动，在 ECI 系中大气速度等于地球自转速度：

$$\mathbf{v}_{\text{atm}} = \boldsymbol{\omega}_E \times \mathbf{r} = \begin{bmatrix} -\omega_E \cdot r_y \\ \omega_E \cdot r_x \\ 0 \end{bmatrix}$$

火箭相对大气的速度为：

$$\boxed{\mathbf{v}_{\text{rel}} = \mathbf{v} - \mathbf{v}_{\text{atm}}}$$

相对速度的标量大小：

$$V_{\text{rel}} = \|\mathbf{v}_{\text{rel}}\| = \sqrt{(v_x + \omega_E r_y)^2 + (v_y - \omega_E r_x)^2 + v_z^2}$$

### 5.2 动压

$$\boxed{q = \frac{1}{2} \cdot \rho(h) \cdot V_{\text{rel}}^2}$$

### 5.3 气动阻力

阻力的大小为：

$$\boxed{D = \frac{1}{2} \cdot \rho(h) \cdot V_{\text{rel}}^2 \cdot C_D \cdot S_{\text{ref}}}$$

阻力的方向与相对大气速度方向相反，因此阻力加速度为：

$$\boxed{\mathbf{a}_{\text{drag}} = -\frac{D}{m} \cdot \frac{\mathbf{v}_{\text{rel}}}{V_{\text{rel}}} = -\frac{\rho(h) \cdot V_{\text{rel}} \cdot C_D \cdot S_{\text{ref}}}{2m} \cdot \mathbf{v}_{\text{rel}}}$$

当 $V_{\text{rel}} \approx 0$ 或 $\rho \approx 0$ 时，令 $\mathbf{a}_{\text{drag}} = \mathbf{0}$ 以避免数值奇异。

### 5.4 驻点热流密度 — Sutton-Graves 关联式

驻点对流热流密度采用经典的 Sutton-Graves 半经验公式：

$$\boxed{\dot{q}_s = k \cdot \sqrt{\frac{\rho}{R_n}} \cdot V_{\text{rel}}^3}$$

其中：

$$k = 1.83 \times 10^{-4} \text{ (SI 单位)}, \quad R_n = 1.0 \text{ m (等效头部曲率半径)}$$

### 5.5 马赫数

$$Ma = \frac{V_{\text{rel}}}{a(h)}$$

其中 $a(h)$ 为当地的声速。

### 5.6 轴向过载

轴向过载（以 $g$ 为单位）为：

$$n_x = \frac{T - D}{m \cdot g_0}$$

---

## 第六章 LEO 入轨条件

### 6.1 目标停泊轨道

目标为高度 $h^*$ 的圆轨道：

$$h^* = 300 \text{ km}$$

$$r_{\text{target}} = R_E + h^* = 6\,371\,000 + 300\,000 = 6\,671\,000 \text{ m}$$

圆轨道速度（由引力与离心力平衡得出）：

$$\boxed{v_{\text{circ}} = \sqrt{\frac{\mu_E}{r_{\text{target}}}}}$$

数值上：
$$v_{\text{circ}}(300\text{ km}) = \sqrt{\frac{3.986004418 \times 10^{14}}{6.671 \times 10^6}} \approx 7\,729.9 \text{ m/s}$$

### 6.2 飞行路径角

飞行路径角 $\gamma$ 定义为速度矢量相对于当地水平面的夹角：

$$\gamma = \arctan\left(\frac{v_r}{v_h}\right)$$

其中径向速度分量 $v_r$ 和水平速度分量 $v_h$ 分别为：

$$v_r = \mathbf{v} \cdot \hat{\mathbf{u}} = \mathbf{v} \cdot \frac{\mathbf{r}}{\|\mathbf{r}\|}$$

$$v_h = \sqrt{\|\mathbf{v}\|^2 - v_r^2}$$

### 6.3 理想入轨条件

$$\boxed{h_f \approx h^* = 300 \text{ km}, \quad \|\mathbf{v}_f\| \approx v_{\text{circ}}, \quad \gamma_f \approx 0^\circ}$$

### 6.4 注入点判定策略

在优化目标函数中，取轨迹上**第一个同时满足以下两个条件的点**作为入轨注入点：

1. 高度 $h \ge h^*$（已达到目标轨道高度）
2. 惯性速度 $v \ge 0.95 \cdot v_{\text{circ}}$（已接近轨道速度）

如果无点同时满足，依次降级为"首个 $h \ge h^*$ 的点"或"末态"。

---

## 第七章 轨道力学

### 7.1 活力公式 (Vis-Viva Equation)

活力公式是二体问题中最基本的轨道能量积分，适用于所有圆锥曲线轨道：

$$\boxed{v^2 = \mu\left(\frac{2}{r} - \frac{1}{a}\right)}$$

其中 $a$ 为轨道半长轴。对于椭圆轨道 $a > 0$，对于抛物线 $a \to \infty$，对于双曲线 $a < 0$。

### 7.2 TLI 注入 — 拼接圆锥法

设 LEO 停泊轨道半径为 $r_1$，目标远地点（地月平均距离）为 $r_2$：

$$r_1 = R_E + h_{\text{LEO}}, \quad r_2 = 384\,400\,000 \text{ m}$$

**转移椭圆半长轴**：

$$\boxed{a = \frac{r_1 + r_2}{2}}$$

**转移椭圆偏心率**：

$$\boxed{e = 1 - \frac{r_1}{a}}$$

**LEO 圆轨道速度**（活力公式 $a = r_1$ 时）：

$$\boxed{v_c = \sqrt{\frac{\mu_E}{r_1}}}$$

**转移椭圆近地点速度**（活力公式在 $r = r_1$ 处）：

$$\boxed{v_p = \sqrt{\mu_E\left(\frac{2}{r_1} - \frac{1}{a}\right)}}$$

**转移椭圆远地点速度**（活力公式在 $r = r_2$ 处）：

$$\boxed{v_a = \sqrt{\mu_E\left(\frac{2}{r_2} - \frac{1}{a}\right)}}$$

**TLI 速度增量**（单次冲量近似，在近地点沿切向实施）：

$$\boxed{\Delta v_{\text{TLI}} = v_p - v_c}$$

**转移飞行时间**（椭圆轨道半周期）：

$$\boxed{\text{TOF} = \pi \sqrt{\frac{a^3}{\mu_E}}}$$

**不同 LEO 高度下的 TLI 参数**：

| $h_{\text{LEO}}$ (km) | $v_c$ (km/s) | $v_p$ (km/s) | $\Delta v_{\text{TLI}}$ (km/s) | TOF (d) | $e$ |
|----------------------|-------------|-------------|-------------------------------|---------|-----|
| 200 | 7.784 | 10.917 | 3.133 | 4.98 | 0.9663 |
| 300 | 7.730 | 10.838 | 3.108 | 4.98 | 0.9659 |
| 400 | 7.677 | 10.761 | 3.084 | 4.98 | 0.9655 |
| 500 | 7.625 | 10.685 | 3.060 | 4.98 | 0.9651 |

### 7.3 C3 发射能量参数

轨道比能量：

$$E = \frac{v^2}{2} - \frac{\mu_E}{r} = -\frac{\mu_E}{2a}$$

双曲线超速 $v_\infty$（当 $E > 0$ 时，当 $E \le 0$ 时 $v_\infty = 0$）：

$$\boxed{v_\infty = \sqrt{2E} = \sqrt{v_p^2 - \frac{2\mu_E}{r_1}}}$$

C3 发射能量参数：

$$\boxed{C_3 = v_\infty^2 \quad (\text{单位：km}^2/\text{s}^2)}$$

对于 300 km LEO → 地月距离的 Hohmann 椭圆转移，$E < 0$，$v_\infty = 0$，$C_3 \approx 0$（这是椭圆转移的特征：刚好到达目标距离而不逃逸）。

### 7.4 Hohmann 圆轨道间转移

从圆轨道 $r_1$ 转移到圆轨道 $r_2$ 所需的速度增量，由两脉冲 Hohmann 转移给出：

$$a_{\text{tr}} = \frac{r_1 + r_2}{2}$$

$$v_1^{\text{circ}} = \sqrt{\frac{\mu}{r_1}}, \quad v_2^{\text{circ}} = \sqrt{\frac{\mu}{r_2}}$$

$$v_{t1} = \sqrt{\mu\left(\frac{2}{r_1} - \frac{1}{a_{\text{tr}}}\right)}, \quad v_{t2} = \sqrt{\mu\left(\frac{2}{r_2} - \frac{1}{a_{\text{tr}}}\right)}$$

$$\boxed{\Delta v_{\text{Hohmann}} = |v_{t1} - v_1^{\text{circ}}| + |v_2^{\text{circ}} - v_{t2}|}$$

### 7.5 LEO 相位交会

设目标模块在半径为 $r_{\text{target}}$ 的圆轨道上，追赶模块在半径为 $r_{\text{phase}}$ 的圆轨道上。

**圆轨道平均角速度**（由 Kepler 第三定律）：

$$\boxed{n = \sqrt{\frac{\mu}{r^3}}}$$

**轨道周期**：

$$T_{\text{orb}} = \frac{2\pi}{n}$$

**相对漂移角速度**：

$$\boxed{\dot{\theta}_{\text{rel}} = n_{\text{phase}} - n_{\text{target}}}$$

若 $r_{\text{phase}} < r_{\text{target}}$，则 $n_{\text{phase}} > n_{\text{target}}$，追赶模块在低轨道以更快的角速度逐渐追及目标模块。

**等待时间**（闭合给定的初始相位角 $\Delta\theta$）：

$$\boxed{t_{\text{wait}} = \frac{\Delta\theta}{|\dot{\theta}_{\text{rel}}|}}$$

**交会总速度增量**：

$$\boxed{\Delta v_{\text{rendezvous}} = \Delta v_{\text{Hohmann}}(r_{\text{phase}} \to r_{\text{target}}) + \Delta v_{\text{docking}}}$$

其中 $\Delta v_{\text{docking}} \approx 20$ m/s 为对接和姿控余量。

### 7.6 载荷-燃料快速交会（Payload-Fuel Fast Rendezvous）

适用于非对称发射架构：载荷（Launch A）已在 300 km 目标轨道等待，燃料罐（Launch B）以更低调相轨道追赶。

**追赶原理**：较低轨道的角速度更大（Kepler 第三定律 n = √(μ/r³)），因此燃料罐以相对角速度 Δn 逐渐追上载荷：

$$\boxed{\dot{\theta}_{\text{rel}} = n_{\text{phase}} - n_{\text{target}} > 0}, \quad r_{\text{phase}} < r_{\text{target}}$$

**等待时间**（闭合初始相位角 Δθ）：

$$\boxed{t_{\text{wait}} = \frac{\Delta\theta}{|\dot{\theta}_{\text{rel}}|}}$$

**Hohmann 上调转移** — 燃料罐从调相轨道提升至目标轨道与载荷对接：

$$\boxed{\Delta v_{\text{transfer}} = |v_{t1} - v_{\text{phase}}| + |v_{\text{target}} - v_{t2}|}$$

其中 v_t1, v_t2 为转移椭圆首末速度。

**调相轨道选取的权衡**：

| 调相高度 (km) | Δn (deg/h) | 最差等待 (h, Δθ=120°) | Hohmann Δv (m/s) |
|---|---|---|---|
| 250 | 2.71 | 44.2 | 44.1 |
| 270 | 1.62 | 74.0 | 32.4 |
| 280 | 1.08 | 111.2 | 26.6 |
| 290 | 0.54 | 222.9 | 20.8 |
| 295 | 0.27 | 446.2 | 17.9 |

**发射窗口**：B 必须在文昌发射场穿越 A 轨道面时发射。对于 ~19.6° 倾角、300 km 轨道，每日 2 次窗口，每次约 5–10 分钟。

**快速交会的工程策略**：
- 若 B 发射时 Δθ ≤ 30°（通过精确发射时刻控制），280 km 调相约 28 h 可完成交会
- 若采用更激进的 250 km 调相轨，30° 初始相位仅需 ~11 h，但 Δv 增至约 44 m/s
- 总 Δv 预算：Hohmann 上调 + 对接余量 ≈ 20–60 m/s（取决于调相轨选择）

---

## 第八章 齐奥尔科夫斯基火箭方程与质量预算

### 8.1 理想火箭方程

在无外力（真空、无引力）条件下，单级火箭的速度增量由齐奥尔科夫斯基方程给出：

$$\boxed{\Delta v = I_{\text{sp}} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)}$$

质量比：

$$\boxed{\text{MR} = \frac{m_0}{m_f} = \exp\left(\frac{\Delta v}{I_{\text{sp}} \cdot g_0}\right)}$$

### 8.2 TLI 级质量预算

TLI 级在 LEO 组合后单独工作。已知参数：

$$m_{\text{cargo}} = 40 \text{ t (总载荷)}$$

$$m_{\text{adapter}} = 4 \text{ t (对接机构、适配器)}$$

$$m_{\text{fixed}} = m_{\text{cargo}} + m_{\text{adapter}} = 44 \text{ t (TLI 后不可抛弃质量)}$$

定义 TLI 级结构系数（干质量与推进剂质量之比）：

$$\boxed{\varepsilon = \frac{m_{\text{dry}}}{m_{\text{prop}}}}$$

TLI 点火前组合体总质量：

$$m_0 = m_{\text{fixed}} + m_{\text{prop}} + m_{\text{dry}} = m_{\text{fixed}} + (1 + \varepsilon)m_{\text{prop}}$$

TLI 结束后质量：

$$m_f = m_{\text{fixed}} + m_{\text{dry}} = m_{\text{fixed}} + \varepsilon \cdot m_{\text{prop}}$$

质量比：

$$\text{MR} = \frac{m_0}{m_f} = \frac{m_{\text{fixed}} + (1 + \varepsilon)m_{\text{prop}}}{m_{\text{fixed}} + \varepsilon \cdot m_{\text{prop}}}$$

从火箭方程 $\text{MR} = \exp(\Delta v / (I_{\text{sp}} g_0))$ 反解推进剂质量 $m_{\text{prop}}$：

$$\boxed{m_{\text{prop}} = \frac{(\text{MR} - 1) \cdot m_{\text{fixed}}}{1 - (\text{MR} - 1) \cdot \varepsilon}}$$

进而：

$$\boxed{m_{\text{dry}} = \varepsilon \cdot m_{\text{prop}}}$$

$$\boxed{m_{\text{stack,LEO}} = m_{\text{fixed}} + m_{\text{prop}} + m_{\text{dry}}}$$

两发均摊，每发需送入 LEO 的湿质量：

$$\boxed{m_{\text{LEO, per launch}} = \frac{m_{\text{stack,LEO}}}{2}}$$

### 8.3 基线计算结果

取 $I_{\text{sp}} = 450$ s, $\Delta v_{\text{TLI}} = 3108.19$ m/s, $\varepsilon = 0.08$:

$$\text{MR} = \exp\left(\frac{3108.19}{450 \times 9.80665}\right) = 2.0225$$

$$m_{\text{prop}} = \frac{(2.0225 - 1) \times 44}{1 - (2.0225 - 1) \times 0.08} = 49.0 \text{ t}$$

$$m_{\text{dry}} = 0.08 \times 49.0 = 3.92 \text{ t}$$

$$m_{\text{stack,LEO}} = 44 + 49.0 + 3.92 = 96.9 \text{ t}$$

$$m_{\text{LEO, per launch}} = \frac{96.9}{2} = 48.5 \text{ t}$$

### 8.4 非对称发射质量预算（载荷+燃料分开发射）

**架构**：Launch A 载荷→LEO（先发）+ Launch B 燃料→LEO（后发）→ 快速交会对接 → 组合 TLI。

**已知**：
- $m_{\text{cargo}} = 40$ t（不可分割的月球基地物资）
- $m_{\text{adapter}} = 4$ t（对接机构与适配器）
- $m_{\text{fixed}} = m_{\text{cargo}} + m_{\text{adapter}} = 44$ t（必须到达月球的质量）
- $I_{\text{sp}} = 450$ s, $\varepsilon = 0.08$

**TLI 级推进剂质量反解**（同 §8.2）：

$$\boxed{m_{\text{prop}} = \frac{(\text{MR} - 1) \cdot m_{\text{fixed}}}{1 - (\text{MR} - 1) \cdot \varepsilon}} = 49.0 \text{ t}$$

$$\boxed{m_{\text{dry}} = \varepsilon \cdot m_{\text{prop}} = 3.92 \text{ t}}$$

**发射分配**：

$$\boxed{m_{\text{LEO,A}} = m_{\text{fixed}} + m_{\text{dry}} = 44 + 3.92 = 47.9 \text{ t (Launch A)}}$$

$$\boxed{m_{\text{LEO,B}} = m_{\text{prop}} = 49.0 \text{ t (Launch B)}}$$

$$\boxed{m_{\text{stack,LEO}} = m_{\text{LEO,A}} + m_{\text{LEO,B}} = 96.9 \text{ t}}$$

**LEO 运力验证**（CZ-10 估计 LEO 运力 ~70 t）：

| 发射 | 需入轨质量 | LEO 运力 | 余量 |
|------|-----------|---------|------|
| Launch A（载荷+TLI 发动机） | 47.9 t | ~70 t | ~22.1 t |
| Launch B（TLI 推进剂） | 49.0 t | ~70 t | ~21.0 t |

两发均在 CZ-10 运力范围内，余量充足。

**TLI 后的状态**：

$$\boxed{m_f = m_{\text{fixed}} + m_{\text{dry}} = 47.9 \text{ t}}$$

质量比 $\text{MR} = 96.9 / 47.9 = 2.0225$，与对称方案完全相同——TLI 性能不变。

---

## 第九章 发射几何与地球自转

### 9.1 ECEF 坐标

发射点在地固坐标系 (ECEF) 中的位置（球形地球近似）：

$$\boxed{\mathbf{r}_{\text{ECEF}} = \begin{bmatrix} (R_E + h)\cos\varphi \cos\lambda \\ (R_E + h)\cos\varphi \sin\lambda \\ (R_E + h)\sin\varphi \end{bmatrix}}$$

### 9.2 地球自转线速度

在地理纬度 $\varphi$ 处、海拔 $h$ 处，因地球自转而具有的东向线速度：

$$\boxed{v_{\text{rot}}(\varphi, h) = \omega_E \cdot (R_E + h) \cdot \cos\varphi}$$

文昌发射场 ($\varphi = 19.614^\circ$, $h = 50$ m)：

$$v_{\text{rot}} = 7.2921159 \times 10^{-5} \times (6\,371\,000 + 50) \times \cos(19.614^\circ) \approx 438 \text{ m/s}$$

### 9.3 沿发射方向的自转速度增益

发射方位角 $A$（从正北顺时针计量）下，沿发射方向的自转速度分量为：

$$\boxed{\Delta v_{\text{rot}}(A) = v_{\text{rot}} \cdot \sin A}$$

正东发射 ($A = 90^\circ$) 时取得最大值 $\Delta v_{\text{rot}} = v_{\text{rot}} \approx 438$ m/s。

### 9.4 ECI 初始惯性速度

发射时刻火箭在 ECI 系中的初始速度：

$$\boxed{\mathbf{v}_0 = \boldsymbol{\omega}_E \times \mathbf{r}_0 = \begin{bmatrix} -\omega_E \cdot y_0 \\ \omega_E \cdot x_0 \\ 0 \end{bmatrix}}$$

### 9.5 轨道倾角与发射方位角的关系

球形地球一阶近似下，入轨倾角 $i$ 与发射场纬度 $\varphi$、发射方位角 $A$ 的关系为：

$$\boxed{\cos i \approx \cos\varphi \cdot \sin A}$$

正东发射 ($A = 90^\circ$) 时：

$$i_{\min} \approx \varphi$$

文昌 ($\varphi = 19.6^\circ$) 正东发射可达到的最小倾角约 $19.6^\circ$，有利于近赤道低倾角停泊轨道，降低后续 TLI 的能量代价。

---

## 第十章 可靠性模型

### 10.1 发动机簇可靠性

设单台发动机在关键飞行段的可靠度为 $r$（各台独立同分布），助推/芯级共有 $N$ 台发动机并联工作。

**不允许任何发动机失效**（全串联模型）：

$$\boxed{R_{\text{cluster}} = r^N}$$

**允许最多 $f$ 台发动机失效仍能完成任务**（$k$-out-of-$N$ 冗余模型）：

$$\boxed{R_{\text{cluster}}(f) = \sum_{k=0}^{f} \binom{N}{k} (1-r)^k \cdot r^{N-k}}$$

长征十号 S1 级 21 台 YF-100K，允许 1 台失效：

$$R_{\text{CZ-10 S1}} = r^{21} + 21 \cdot (1-r) \cdot r^{20}$$

### 10.2 多发任务可靠性

设单发长征十号任务成功概率为 $R_L$（含发射、上升、入轨全过程），共发射 $N$ 发，至少需要 $K$ 发成功：

$$\boxed{P(N, K; R_L) = \sum_{s=K}^{N} \binom{N}{s} R_L^s (1-R_L)^{N-s}}$$

**两发全成功** ($N=2$, $K=2$)：

$$P_2 = R_L^2$$

**三发中至少两发成功** ($N=3$, $K=2$)：

$$P_{3,2} = \binom{3}{2} R_L^2 (1-R_L) + R_L^3 = 3R_L^2 - 2R_L^3$$

### 10.3 总任务可靠性链（两发 LEO 组合方案）

任务成功的充要条件：两发均成功 + LEO 交会对接成功 + TLI 点火成功。这是一个串联可靠性模型：

$$\boxed{R_{\text{total}} = R_L^2 \cdot R_{\text{rendezvous}} \cdot R_{\text{TLI}}}$$

**基线敏感性取值**：

$$R_L = 0.95, \quad R_{\text{rendezvous}} = 0.98, \quad R_{\text{TLI}} = 0.985$$

$$R_{\text{total}} = 0.95^2 \times 0.98 \times 0.985 = 0.8712$$

**二维敏感性扫描**：

- $R_{\text{rendezvous}} \in [0.94, 0.995]$
- $R_{\text{TLI}} \in [0.94, 0.995]$
- 在 $R_L = 0.95$ 固定下，$R_{\text{total}} \in [0.797, 0.893]$

### 10.4 非对称发射可靠性（载荷+燃料分开发射）

载荷（Launch A）与燃料（Launch B）角色不同，可靠性结构有区别：

**Launch A 失败 = 任务失败**（载荷不可替代）。
**Launch B 失败 = 可补救**（燃料可重新发射，载荷在轨等待）。

**不可重发方案**（两发必须一次成功）：

$$\boxed{R_{\text{asym, no-relaunch}} = R_L^2 \cdot R_{\text{rendezvous}} \cdot R_{\text{TLI}}}$$

与对称方案数值相同。

**可重发方案**（B 失败后允许重发一次燃料）：

$$\boxed{R_{\text{asym, relaunch}} = R_L \cdot [R_L + (1 - R_L) \cdot R_L'] \cdot R_{\text{rendezvous}} \cdot R_{\text{TLI}}}$$

其中 $R_L'$ 为燃料重发可靠性（可取与首发相同值）。

**基线数值对比** ($R_L = 0.95$, $R_{\text{rend}} = 0.98$, $R_{\text{TLI}} = 0.985$):

| 方案 | 发射环节可靠度 | 总可靠度 |
|------|-------------|---------|
| 对称两发（旧） | $R_L^2 = 0.9025$ | 0.8712 |
| 非对称无重发 | $R_L^2 = 0.9025$ | 0.8712 |
| 非对称可重发 | $R_L \cdot [R_L + (1-R_L)R_L] = 0.95 \times 0.9975 = 0.9476$ | 0.9148 |

重发燃料使发射环节可靠度提升约 5 个百分点，总可靠度从 0.871 提升至 0.915。

**关键结论**：载荷+燃料分离架构在可靠性上的核心优势不是串联公式本身，而是燃料发射失败时不需要重建整个载荷模块，只需重新发射推进剂。

---

## 第十一章 优化算法

### 11.1 粒子群优化 (Particle Swarm Optimization, PSO)

PSO 模拟鸟群觅食行为，每个粒子在搜索空间中根据自身历史最优和全局最优调整位置。

**第 $i$ 个粒子的速度与位置更新**：

$$\boxed{\mathbf{v}_i^{(k+1)} = w^{(k)} \cdot \mathbf{v}_i^{(k)} + c_1 \cdot r_1 \cdot (\mathbf{p}_{\text{best},i} - \mathbf{x}_i^{(k)}) + c_2 \cdot r_2 \cdot (\mathbf{g}_{\text{best}} - \mathbf{x}_i^{(k)})}$$

$$\boxed{\mathbf{x}_i^{(k+1)} = \mathbf{x}_i^{(k)} + \mathbf{v}_i^{(k+1)}}$$

其中 $c_1$ 为认知系数（个体最优权重），$c_2$ 为社会系数（全局最优权重），$r_1, r_2 \sim U(0, 1)$ 为均匀随机数。

**惯性权重线性衰减**（前期探索、后期开发）：

$$\boxed{w^{(k)} = w_{\text{start}} - (w_{\text{start}} - w_{\text{end}}) \cdot \frac{k}{K_{\max}}}$$

典型参数：$w_{\text{start}} = 0.9$, $w_{\text{end}} = 0.4$, $c_1 = c_2 = 2.0$, 种群大小 $N_p = 40\sim50$, 最大迭代 $K_{\max} = 80\sim100$。

**早停判据**：若全局最优值连续 15 代无改进（$\Delta J < 10^{-9}$），提前终止。

**边界处理**：速度不设限，位置超出边界时裁剪到边界值。

$$\mathbf{x}_i = \text{clip}(\mathbf{x}_i, \mathbf{x}_{\text{low}}, \mathbf{x}_{\text{high}})$$

### 11.2 遗传算法 (Genetic Algorithm, GA)

**编码**：实数编码（每个设计变量直接为实数）。  
**种群大小**：$N_p = 60$，最大代数 $G_{\max} = 80$。

**选择算子 — 锦标赛选择**：

从种群中随机选取 $k_{\text{tour}}$ 个个体，将其中适应度最佳（目标函数最小）者作为父代：

$$i^* = \arg\min_{i \in \mathcal{T}} J(\mathbf{x}_i), \quad |\mathcal{T}| = k_{\text{tour}} = 3$$

**交叉算子 — 混合交叉 (BLX-$\alpha$)**（以概率 $p_c = 0.85$ 执行）：

$$\Delta_j = |x_{\text{parent1},j} - x_{\text{parent2},j}|$$

$$x_{\text{child},j} \sim U\left(\min(x_{1j}, x_{2j}) - \alpha \Delta_j, \max(x_{1j}, x_{2j}) + \alpha \Delta_j\right)$$

$$\alpha = 0.25$$

**变异算子 — 高斯变异**（以概率 $p_m = 0.15$ 执行）：

随机选择一个维度 $j$，然后：

$$x_{\text{child},j} \leftarrow x_{\text{child},j} + \mathcal{N}(0, \sigma_j^2)$$

$$\sigma_j = \eta \cdot (x_{\text{high},j} - x_{\text{low},j}), \quad \eta = 0.08$$

**精英保留**：每代保留最优的 $e = 4$ 个个体直接进入下一代。

**早停判据**：连续 15 代最优值无改进。

### 11.3 模拟退火 (Simulated Annealing, SA)

SA 模拟金属退火的物理过程，在高温时接受较差解以跳出局部最优。

**Metropolis 接受准则**：

对于当前解 $\mathbf{x}$ 和新解 $\mathbf{x}'$，能量差 $\Delta E = J(\mathbf{x}') - J(\mathbf{x})$：

$$\boxed{P(\text{accept}) = \begin{cases} 1 & \text{if } \Delta E \le 0 \\ \exp\left(-\dfrac{\Delta E}{T}\right) & \text{if } \Delta E > 0 \end{cases}}$$

**温度衰减**（指数退火计划）：

$$\boxed{T_{k+1} = \alpha \cdot T_k}$$

其中 $\alpha = 0.92 \sim 0.95$（冷却速率），初始温度 $T_0 = 30 \sim 100$。

**自适应邻域生成**（高斯扰动，步长随温度缩放）：

$$x_{\text{new},j} = x_{\text{current},j} + \mathcal{N}\left(0, \sigma_j^2(T)\right)$$

$$\sigma_j(T) = (x_{\text{high},j} - x_{\text{low},j}) \cdot 0.05 \cdot \left(\frac{T}{T_0} + 0.01\right)$$

**重启机制**：当温度降至 $0.01 \cdot T_0$ 以下时，将当前解重置为历史最优解，温度恢复为 $0.5 \cdot T_0$。最多执行 $N_{\text{restart}} = 2 \sim 3$ 次。

### 11.4 混合优化策略

采用两阶段策略：PSO 全局粗搜索 → SA 局部精细搜索。

$$\mathbf{x}^* = \arg\min_{\mathbf{x}} J(\mathbf{x}) \quad \text{（Stage 1: PSO）}$$

$$\mathbf{x}^{**} = \arg\min_{\mathbf{x} \in \mathcal{N}(\mathbf{x}^*)} J(\mathbf{x}) \quad \text{（Stage 2: SA 精细搜索）}$$

---

## 第十二章 多目标代价函数

### 12.1 设计变量

$$\mathbf{u} = [t_{\text{end}}, \phi_f, s, t_v]^T$$

搜索空间：

$$t_{\text{end}} \in [200, 400] \text{ s}, \quad \phi_f \in [2^\circ, 20^\circ], \quad s \in [0.8, 2.0], \quad t_v \in [5, 20] \text{ s}$$

### 12.2 总加权代价函数

$$\boxed{J(\mathbf{u}) = w_1 J_{\text{orbit}} + w_2 J_q + w_3 J_{\text{accel}} + w_4 J_{\text{heating}} + w_5 J_{\text{control}}}$$

权重取值：$w_1 = 10$, $w_2 = 5$, $w_3 = 3$, $w_4 = 2$, $w_5 = 0.1$。

### 12.3 入轨误差项 $J_{\text{orbit}}$

$$\boxed{J_{\text{orbit}} = \left(\frac{h_f - h^*}{\sigma_h}\right)^2 + \left(\frac{v_f - v^*}{\sigma_v}\right)^2 + \left(\frac{\gamma_f}{\sigma_\gamma}\right)^2}$$

其中：

$$h^* = 300 \text{ km}, \quad v^* = \sqrt{\frac{\mu_E}{R_E + h^*}} \approx 7729.9 \text{ m/s}, \quad \gamma^* = 0^\circ$$

$$\sigma_h = 5 \text{ km}, \quad \sigma_v = 50 \text{ m/s}, \quad \sigma_\gamma = 0.5^\circ$$

### 12.4 动压约束惩罚项 $J_q$

$$\boxed{J_q = \left[\frac{\max(0, q_{\max} - q_{\text{limit}})}{\sigma_q}\right]^2}$$

$$q_{\text{limit}} = 60 \text{ kPa}, \quad \sigma_q = 20 \text{ kPa}$$

### 12.5 加速度约束惩罚项 $J_{\text{accel}}$

$$\boxed{J_{\text{accel}} = \left[\frac{\max(0, n_{x,\max} - n_{\text{limit}})}{\sigma_n}\right]^2}$$

$$n_{\text{limit}} = 6g, \quad \sigma_n = 1g$$

### 12.6 热流约束惩罚项 $J_{\text{heating}}$

$$\boxed{J_{\text{heating}} = \left[\frac{\max(0, \dot{q}_{s,\max} - \dot{q}_{\text{limit}})}{\sigma_{\dot{q}}}\right]^2}$$

$$\dot{q}_{\text{limit}} = 500 \text{ kW/m}^2, \quad \sigma_{\dot{q}} = 100 \text{ kW/m}^2$$

### 12.7 控制平滑项 $J_{\text{control}}$

$$\boxed{J_{\text{control}} = \frac{1}{1000}\int_{0}^{t_f} \left(\frac{d\phi}{dt}\right)^2 dt}$$

近似为离散求和：

$$J_{\text{control}} \approx \frac{1}{1000}\sum_{k=1}^{N} \left(\frac{\phi_k - \phi_{k-1}}{\Delta t_k}\right)^2 \Delta t_k$$

---

## 第十三章 坐标变换

### 13.1 ECEF 至球坐标

由 ECEF 位置反算球坐标（纬度 $\varphi$、经度 $\lambda$、高度 $h$）：

$$r = \sqrt{x^2 + y^2 + z^2}$$

$$\varphi = \arcsin\left(\frac{z}{r}\right)$$

$$\lambda = \operatorname{atan2}(y, x)$$

$$h = r - R_E$$

### 13.2 ECI 与 ECEF 的关系

ECI 与 ECEF 的 z 轴均沿地球自转轴。取 $t=0$ 时刻两坐标系重合，则任意时刻 ECI 系中的位置即为绝对惯性位置。地球自转效应通过初始速度（$\mathbf{v}_0 = \boldsymbol{\omega}_E \times \mathbf{r}_0$）、大气旋转速度（$\mathbf{v}_{\text{atm}} = \boldsymbol{\omega}_E \times \mathbf{r}$）和 Coriolis 项（$-2\boldsymbol{\omega}_E \times \mathbf{v}$）进入动力学方程。

---

## 第十四章 Lambert 问题（备用）

### 14.1 问题描述

Lambert 问题：给定两个位置矢量 $\mathbf{r}_1$, $\mathbf{r}_2$、飞行时间 $\Delta t$ 和引力参数 $\mu$，确定连接两点的开普勒轨道的初始速度 $\mathbf{v}_1$ 和终端速度 $\mathbf{v}_2$。

$$\mathbf{r}(t_0) = \mathbf{r}_1, \quad \mathbf{r}(t_0 + \Delta t) = \mathbf{r}_2 \quad \Longrightarrow \quad \mathbf{v}_1, \mathbf{v}_2$$

### 14.2 Stumpff 函数

通用变量法依赖 Stumpff 函数 $C(z)$ 和 $S(z)$（二者解析地处理椭圆、抛物、双曲三种情况的统一表达式）：

$$\boxed{C(z) = \begin{cases} \dfrac{1 - \cos\sqrt{z}}{z} & z > 0 \\[8pt] \dfrac{\cosh\sqrt{-z} - 1}{-z} & z < 0 \\[8pt] \dfrac{1}{2} & z = 0 \end{cases}}$$

$$\boxed{S(z) = \begin{cases} \dfrac{\sqrt{z} - \sin\sqrt{z}}{z^{3/2}} & z > 0 \\[8pt] \dfrac{\sinh\sqrt{-z} - \sqrt{-z}}{(-z)^{3/2}} & z < 0 \\[8pt] \dfrac{1}{6} & z = 0 \end{cases}}$$

该函数族满足关系：$C(z) = 1/2! - z/4! + z^2/6! - \cdots$, $S(z) = 1/3! - z/5! + z^2/7! - \cdots$

### 14.3 通用变量时间方程

设 $\chi$ 为通用变量，$z = \alpha \chi^2$（$\alpha = 1/a$），则有：

$$\boxed{\sqrt{\mu} \cdot \Delta t = \chi^3 \cdot S(z) + A \cdot \sqrt{y}}$$

其中：

$$A = \sqrt{r_1 r_2} \cdot \frac{\sin\Delta\theta}{\sqrt{1 - \cos\Delta\theta}}$$

$$y = r_1 + r_2 + A \cdot \frac{z \cdot S(z) - 1}{\sqrt{C(z)}}$$

采用 Newton-Raphson 迭代求解 $\chi$：

$$\chi^{(n+1)} = \chi^{(n)} - \frac{t_{\text{computed}}(\chi^{(n)}) - \Delta t}{dt/d\chi}$$

其中 $dt/d\chi = [\chi^2 C(z) + A \cdot \chi \cdot (1 - z \cdot S(z)) / \sqrt{y}] / \sqrt{\mu}$。

收敛后由 $\chi$ 计算 $\mathbf{v}_1$, $\mathbf{v}_2$（通过 $f$ 和 $g$ 函数展开）。

> 注：本项目当前主要使用 Hohmann+相位交会模型处理 LEO 交会，Lambert 求解器作为高精度扩展备用。

---

## 第十五章 上升段轨迹状态计算

### 15.1 飞行路径角

由速度矢量与当地天向的关系：

$$\boxed{\gamma = \arctan\left(\frac{v_r}{v_h}\right)}$$

其中：

$$v_r = \mathbf{v} \cdot \hat{\mathbf{u}} = \mathbf{v} \cdot \frac{\mathbf{r}}{\|\mathbf{r}\|}$$

$$v_h = \sqrt{\|\mathbf{v}\|^2 - v_r^2}$$

### 15.2 各物理量的计算

从原始状态 $[r_x, r_y, r_z, v_x, v_y, v_z, m]$ 经过以下步骤得到全部轨迹状态量：

1. **地心距**：$r = \|\mathbf{r}\| = \sqrt{r_x^2 + r_y^2 + r_z^2}$
2. **高度**：$h = r - R_E$
3. **惯性速度**：$V = \|\mathbf{v}\| = \sqrt{v_x^2 + v_y^2 + v_z^2}$
4. **大气密度** $\rho(h)$ — 完整标准大气模型（第二章）
5. **大气压强** $p(h)$ — 完整标准大气模型
6. **大气温度** $T(h)$ — 完整标准大气模型
7. **声速** $a(h) = \sqrt{\gamma R_a T(h)}$
8. **大气速度** $\mathbf{v}_{\text{atm}} = [-\omega_E r_y, \omega_E r_x, 0]^T$
9. **相对速度** $\mathbf{v}_{\text{rel}} = \mathbf{v} - \mathbf{v}_{\text{atm}}$
10. **相对速度大小** $V_{\text{rel}} = \|\mathbf{v}_{\text{rel}}\|$
11. **动压** $q = \frac{1}{2}\rho V_{\text{rel}}^2$
12. **马赫数** $Ma = V_{\text{rel}} / a$
13. **阻力** $D = \frac{1}{2}\rho V_{\text{rel}}^2 C_D S_{\text{ref}}$
14. **飞行路径角** $\gamma = \arctan(v_r / v_h)$
15. **轴向过载** $n_x = (T - D)/(m g_0)$

---

## 第十六章 公式与代码对照表

| 章节 | 公式内容 | 代码文件 |
|------|---------|---------|
| §1.1 | RK4 四阶 Runge-Kutta | `integrators.py` |
| §1.2 | RK45 Dormand-Prince 自适应积分 | `integrators.py` |
| §2.2 | 位势高度与几何高度转换 | `atmosphere_full.py` |
| §2.3 | 大气九层分层参数表 | `atmosphere_full.py` |
| §2.4 | 非等温层温度/压强/密度 | `atmosphere_full.py` |
| §2.5 | 等温层温度/压强/密度 | `atmosphere_full.py` |
| §2.6 | 声速 $a = \sqrt{\gamma R T}$ | `atmosphere_full.py` |
| §2.7 | Sutherland 粘性公式 | `atmosphere_full.py` |
| §3.4 | 球形二体引力 | `gravity_full.py` |
| §3.5 | J2 引力势与加速度 | `gravity_full.py` |
| §3.6 | J3 引力势与加速度 | `gravity_full.py` |
| §3.7 | J4 引力势与加速度 | `gravity_full.py` |
| §4.2–§4.3 | 6-DOF ECI 运动方程 | `ascent_full.py` |
| §4.5 | ENU 坐标基与推力方向 | `ascent_full.py` |
| §4.6 | 分段光滑俯仰转弯程序角 | `ascent_full.py` |
| §4.7 | 推力与比冲大气反压修正 | `ascent_full.py` |
| §4.8 | 质量消耗与分级 | `ascent_full.py` |
| §5.1 | 大气相对速度 | `ascent_full.py` |
| §5.2–§5.3 | 动压与气动阻力 | `ascent_full.py` |
| §5.4 | Sutton-Graves 驻点热流 | `objectives_full.py` |
| §6.1 | 目标圆轨道速度 | `objectives_full.py` |
| §6.2 | 飞行路径角 | `ascent_full.py` |
| §7.1 | Vis-Viva 活力公式 | `transfer_full.py` |
| §7.2 | TLI 注入 $\Delta v$ / 半长轴 / 偏心率 | `transfer_full.py` |
| §7.3 | C3 发射能量参数 | `transfer_full.py` |
| §7.4 | Hohmann 圆轨道间转移 | `rendezvous.py` |
| §7.5 | 圆轨道角速度 / 相位交会 | `rendezvous.py` |
| §7.6 | 载荷-燃料快速交会 | `rendezvous.py` → `estimate_fast_rendezvous()` |
| §8.1 | 齐奥尔科夫斯基火箭方程 | `mass_budget.py` |
| §8.2 | TLI 级质量预算（对称） | `mass_budget.py` → `solve_tli_mass_budget()` |
| §8.4 | 非对称发射质量预算 | `mass_budget.py` → `solve_split_mass_budget()` |
| §9.1–§9.5 | ECEF 坐标 / 自转速度 / 倾角-方位角 | `frames.py`, `launch_geometry.py` |
| §10.1 | 发动机簇可靠性 (k-out-of-N) | `reliability.py` |
| §10.2 | 多发任务可靠性 | `reliability.py` |
| §10.3 | 总任务串联可靠性链 | `reliability.py` |
| §10.4 | 非对称发射可靠性 | `reliability.py` → `payload_fuel_split_reliability()` |
| §11.1 | PSO 速度/位置更新 + 惯性权重衰减 | `optimizers.py` |
| §11.2 | GA 锦标赛选择 + BLX-α 交叉 + 高斯变异 | `optimizers.py` |
| §11.3 | SA Metropolis 准则 + 温度衰减 + 自适应邻域 | `optimizers.py` |
| §11.4 | PSO+SA 两阶段混合优化 | `optimizers.py` |
| §12.1–§12.7 | 多目标代价函数 | `objectives_full.py` |
| §13.1–§13.2 | ECEF 坐标变换 / ECI-ECEF 关系 | `frames.py` |
| §14.2–§14.3 | Stumpff 函数 / 通用变量时间方程 | `lambert.py` |
| §15.1–§15.2 | 轨迹状态计算（15 个物理量） | `ascent_full.py` |

---

## 第十七章 关键数值汇总

| 指标 | 符号 | 数值 |
|------|------|------|
| 推荐任务架构 | — | 载荷（先发）+ 燃料（后发）→ LEO 快速交会对接 → 组合体 TLI |
| Launch A 入轨质量（载荷+TLI 发动机） | $m_{\text{LEO,A}}$ | 47.9 t |
| Launch B 入轨质量（TLI 推进剂） | $m_{\text{LEO,B}}$ | 49.0 t |
| 目标停泊轨道高度 | $h^*$ | 300 km |
| 目标圆轨道速度 | $v_{\text{circ}}$ | 7.730 km/s |
| 文昌正东发射自转增益 | $\Delta v_{\text{rot}}$ | ~438 m/s |
| 入轨最小倾角 | $i_{\min}$ | ~19.6° |
| TLI 速度增量 (300 km LEO) | $\Delta v_{\text{TLI}}$ | 3.108 km/s |
| TLI 转移飞行时间 | TOF | 4.98 d |
| TLI 转移椭圆偏心率 | $e$ | 0.9659 |
| LEO 组合体初始质量 | $m_{\text{stack,LEO}}$ | 96.9 t |
| TLI 级推进剂质量 | $m_{\text{prop}}$ | 49.0 t |
| TLI 级干质量 | $m_{\text{dry}}$ | 3.92 t |
| S1 级推进剂 | $m_{\text{prop,S1}}$ | 1 420 t |
| S2 级推进剂 | $m_{\text{prop,S2}}$ | 285 t |
| S1 级真空推力 | $T_{\text{vac,S1}}$ | 29.34 MN |
| 总发射质量 | $m_0$ | ~2 034 t |
| 可靠性链 (对称, $R_L=0.95$) | $R_{\text{total}}$ | 0.871 |
| 可靠性链 (非对称可重发) | $R_{\text{total}}$ | 0.915 |
| J2 对入轨高度影响 | $\Delta h_{J2}$ | ~0 km |
| J2 对入轨速度影响 | $\Delta v_{J2}$ | ~+41 m/s |
| J3/J4 相对 J2 的贡献比 | — | $\sim 10^{-3}$ |
| 快速交会：280 km 调相，Δθ=120° 最差等待 | $t_{\text{wait}}$ | ~111 h |
| 快速交会：280 km 调相，Δθ=30° 等待 | $t_{\text{wait}}$ | ~28 h |
| 快速交会总 Δv（上调 + 对接，280 km） | $\Delta v_{\text{rendezvous}}$ | ~27 m/s |
