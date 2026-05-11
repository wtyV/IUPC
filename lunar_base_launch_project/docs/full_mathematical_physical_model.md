

# 完整数学物理建模公式汇总 v0.8

本文档把当前项目从任务定义到上升段、LEO 交会、TLI、质量预算、可靠性和优化算法的数学物理模型统一写出。它对应当前代码目录 `src/` 中已经实现的模型，并补充论文正文中应写清楚的公式。

> 说明：课程大纲中提到"大气层内选择杨炳蔚的模型"。当前代码采用的是"标准大气表 + 分层对数插值"的可计算简化版，并设置 90 km 以上不考虑气动力。论文中可以表述为"以杨炳蔚教材标准大气表为主模型，代码中用分层密度表和对数插值实现"。

## 1. 变量、常数与单位

除特别说明外，动力学计算统一使用 SI 单位。

| 符号 | 含义 | 当前取值 |
|------|------|----------|
| `g0` | 标准重力加速度 | 9.80665 m/s^2 |
| `mu_E` | 地球引力参数 | 3.986004418e14 m^3/s^2 |
| `R_E` | 地球平均半径 | 6371000 m |
| `omega_E` | 地球自转角速度 | 7.2921159e-5 rad/s |
| `J2` | 地球二阶带谐项 | 1.08262668e-3 |
| `r_EM` | 地月平均距离 | 384400000 m |
| `m_req` | 题目要求总载荷 | 40 t |
| `C_TLI` | 长征十号公开 TLI 运力 | >= 27 t |

文昌发射场建模参数：

    latitude  = 19.614 deg
    longitude = 110.951 deg
    altitude  = 50 m

## 2. 任务可行性与总体架构

题目目标是把总计 40 t 月球基地建设物资送入 Earth-Moon transfer orbit。首先用公开 TLI 运力做单发可行性判据：

$$m_{req} \leq C_{TLI}$$

当前公开数据给出：

$$40\ t > 27\ t$$

因此单发长征十号直接完成 40 t TLI 不可行。

主方案采用两发长征十号：

$$N_{launch} = 2,\quad\quad m_{payload,each} = 20\ t$$

每发相对公开 TLI 运力的等效余量为：

$$m_{margin,each} = C_{TLI} - m_{payload,each} = 27 - 20 = 7\ t$$

总交付质量：

$$m_{delivered} = N_{success}m_{payload,each}$$

两发全成功时：

$$m_{delivered} = 2 \times 20 = 40\ t$$

任务链为：

    CZ-10 Launch A -> Module A to LEO
    CZ-10 Launch B -> Module B to nearby LEO phasing orbit
    LEO rendezvous and docking
    Combined stack translunar injection

三发 2-out-of-3 方案不作为当前主方案，只作为可靠性扩展：

$$N_{launch} = 3,\quad\quad N_{required} = 2$$

## 3. 坐标系定义

### 3.1 ECEF 球形地固坐标

当前模型用球形地球近似。设地理纬度为 `varphi`，经度为 `lambda`，高度为 `h`，则 ECEF 位置为：

$$\mathbf r_{\mathrm{ECEF}} = \begin{bmatrix} (R_E+h)\cos\varphi\cos\lambda\\(R_E+h)\cos\varphi\sin\lambda\\(R_E+h)\sin\varphi \end{bmatrix}$$

由 ECEF 反算球形经纬度：

$$r = \parallel \mathbf{r} \parallel$$

$$\varphi = \arcsin\left( \frac{z}{r} \right)$$

$$\lambda = atan2(y,x)$$

$$h = r - R_{E}$$

### 3.2 ECI 惯性坐标

当前 `ascent_eci.py` 中，取初始时刻 ECI 与 ECEF 重合。地球自转角速度向量为：

$$\mathbf{\omega}_{E} = \begin{bmatrix}
0 \\
0 \\
\omega_{E}
\end{bmatrix}$$

发射点初始惯性速度来自地球自转：

$$\mathbf{v}_{0} = \mathbf{\omega}_{E} \times \mathbf{r}_{0}$$

大气随地球固连转动，因此当地大气速度近似为：

$$\mathbf{v}_{atm} = \mathbf{\omega}_{E} \times \mathbf{r}$$

火箭相对大气速度：

$$\mathbf{v}_{rel} = \mathbf{v} - \mathbf{v}_{atm}$$

### 3.3 局部 ENU 坐标基

局部天向单位向量：

$$\widehat{\mathbf{u}} = \frac{\mathbf{r}}{\parallel \mathbf{r} \parallel}$$

局部东向单位向量：

$$\widehat{\mathbf{e}} = \frac{\mathbf{\omega}_{E} \times \mathbf{r}}{\parallel \mathbf{\omega}_{E} \times \mathbf{r} \parallel}$$

局部北向单位向量：

$$\widehat{\mathbf{n}} = \frac{\widehat{\mathbf{u}} \times \widehat{\mathbf{e}}}{\parallel \widehat{\mathbf{u}} \times \widehat{\mathbf{e}} \parallel}$$

发射方位角 `A` 从正北顺时针计量，水平发射方向为：

$$\hat{\mathbf h}_A = \cos A\,\hat{\mathbf n} + \sin A\,\hat{\mathbf e}$$

程序角 `phi` 定义为推力方向相对当地水平面的夹角，`phi=90 deg` 为竖直向上，`phi=0 deg` 为水平。推力方向单位向量：

$$\hat{\mathbf T} = \sin\phi\,\hat{\mathbf u} + \cos\phi\,\hat{\mathbf h}_A$$

## 4. 发射几何与地球自转收益

发射点地球自转线速度：

$$v_{rot} = \omega_{E}R_{E}\cos\varphi$$

考虑发射方位角后的沿发射方向自转速度收益：

$$\Delta v_{rot}(A) = v_{rot}\sin A$$

文昌向东发射 `A=90 deg` 时：

$$\Delta v_{rot} \approx 438\ m/s$$

球形地球一阶近似下，发射方位角与入轨倾角关系为：

$$\cos i \approx \cos\varphi\sin A$$

正东发射时：

$$i_{\min} \approx \varphi$$

因此文昌低纬度有利于近赤道低倾角停泊轨道与 TLI 前的能量效率。

## 5. 上升段三维点质点动力学

### 5.1 状态量

ECI 上升段状态量为：

$$\mathbf{x} = \left[ \mathbf{r},\ \mathbf{v},\ m \right]^{T}$$

其中：

$$\mathbf{r} = [ x,y,z]^{T},\quad\quad\mathbf{v} = [ v_{x},v_{y},v_{z}]^{T}$$

### 5.2 连续动力学方程

$$\frac{d\mathbf{r}}{dt} = \mathbf{v}$$

$${\frac{d\mathbf v}{dt}} = \mathbf a_{\mathrm{grav}} + \mathbf a_{J2} + \mathbf a_{\mathrm{thrust}} + \mathbf a_{\mathrm{drag}}$$

$$\frac{dm}{dt} = - \frac{T}{I_{sp}g_{0}}$$

代码中采用一阶显式积分近似：

$$\mathbf{v}_{k + 1} = \mathbf{v}_{k} + \mathbf{a}_{k}\Delta t$$

$$\mathbf{r}_{k + 1} = \mathbf{r}_{k} + \mathbf{v}_{k + 1}\Delta t$$

$$m_{k + 1} = m_{k} - {\dot{m}}_{k}\Delta t$$

### 5.3 分级与质量模型

每一级用常推力、常比冲、推进剂消耗和干质量抛弃近似。第 `j` 级：

$${\dot{m}}_{j} = \frac{T_{j}}{I_{sp,j}g_{0}}$$

燃烧时间近似：

$$t_{burn,j} = \frac{m_{prop,j}}{{\dot{m}}_{j}}$$

当第 `j` 级推进剂耗尽时：

$$m^{+} = m^{-} - m_{drydrop,j}$$

当前占位分级参数：

| 级段 | 推进剂质量 | 抛弃干质量 | 推力 | 比冲 |
|------|------------|------------|------|------|
| booster_core_cluster | ~2800 t | ~80 t | ~10 MN | ~300 s |

这些数值用于生成趋势图和入轨量级，不应写成真实长征十号完整设计数据。

## 6. 程序角模型

程序角 `phi(t)` 采用分段光滑下降形式：

$$\phi(t) = 90^{\circ},\quad\quad 0 \leq t \leq t_{v}$$

$$\phi(t) = 90^\circ - \left( \frac{t-t_v}{t_{\mathrm{end}}-t_v} \right)^s \left(90^\circ-\phi_f\right), \qquad t_v < t < t_{\mathrm{end}}$$

$$\phi(t) = \phi_{f},\quad\quad t \geq t_{end}$$

其中：

| 符号 | 含义 |
|------|------|
| `t_v` | 垂直上升时间 |
| `t_end` | 总上升时间 |
| `phi_f` | 末端程序角 |
| `s` | 下降形状指数 |

当前 ECI 最优粗网格候选为：

    t_end = 305 s
    phi_f = 10 deg
    s     = 1.4

该候选末端结果约为：

    h_f     = 306.9 km
    v_f     = 7.723 km/s
    gamma_f = -0.02 deg

## 7. 地球引力与 J2 项

### 7.1 球形二体引力

设：

$$r = \parallel \mathbf{r} \parallel = \sqrt{x^{2} + y^{2} + z^{2}}$$

球形引力加速度：

$$\mathbf a_{\mathrm{grav}} = -{\frac{\mu_E}{r^3}}\mathbf r$$

### 7.2 J2 引力势函数

J2 势函数常写为：

$$U(r,\phi_g) = \frac{\mu_E}{r} \left[ 1 - J_2 \left(\frac{R_E}{r}\right)^2 P_2(\sin\phi_g) \right]$$

其中：

$$P_{2}(x) = \frac{1}{2}(3x^{2} - 1)$$

`phi_g` 为地心纬度。

### 7.3 代码采用的 J2 加速度形式

当前 `ascent_eci.py` 使用的总引力加速度写为：

$$\mathbf a = -\frac{\mu_E}{r^3} \begin{bmatrix} x \\ y \\ z \end{bmatrix} + \frac{3}{2}J_2\frac{\mu_E R_E^2}{r^5} \begin{bmatrix} x(5z^2/r^2-1) \\ y(5z^2/r^2-1) \\ z(5z^2/r^2-3) \end{bmatrix}$$

即：

$$a_x = -\frac{\mu_E x}{r^3} + \frac{3J_2\mu_E R_E^2 x}{2r^5} \left(5\frac{z^2}{r^2}-1\right)$$

$$a_y = -\frac{\mu_E y}{r^3} + \frac{3J_2\mu_E R_E^2 y}{2r^5} \left(5\frac{z^2}{r^2}-1\right)$$

$$a_z = -\frac{\mu_E z}{r^3} + \frac{3J_2\mu_E R_E^2 z}{2r^5} \left(5\frac{z^2}{r^2}-3\right)$$

v0.6 对照结果中，J2 相对球形引力使末端高度变化约：

$$\Delta h_{f} \approx - 2.27\ km$$

末端惯性速度变化约：

$$\Delta v_{f} \approx + 1.37\ m/s$$

## 8. 杨炳蔚/标准大气模型与当前实现

### 8.1 标准大气的通用分层公式

若采用教材标准大气表，可按分层温度梯度给出温度、压强和密度。设第 `i` 层下边界位势高度为 `H_i`，温度为 `T_i`，压强为 `p_i`，温度梯度为 `L_i=dT/dH`。

位势高度与几何高度关系可写为：

$$H = \frac{R_{E}h}{R_{E} + h}$$

若该层温度梯度不为零：

$$T(H) = T_{i} + L_{i}(H - H_{i})$$

$$p(H) = p_i \left[ \frac{T_i}{T(H)} \right]^{g_0/(R_a L_i)}$$

$$\rho(H) = \frac{p(H)}{R_{a}T(H)}$$

若该层为等温层，即 `L_i=0`：

$$T(H) = T_{i}$$

$$p(H) = p_i \exp\left[ -\frac{g_0(H-H_i)}{R_aT_i} \right]$$

$$\rho(H) = \frac{p(H)}{R_{a}T_{i}}$$

其中 `R_a` 为空气气体常数，约为：

$$R_{a} = 287.05287\ J/(kg \cdot K)$$

在论文中，可以把上式作为"杨炳蔚教材标准大气表的连续分层表达"，再说明代码中为简化计算只取密度表。

### 8.2 当前代码采用的密度表

当前 `atmosphere.py` 使用如下密度表，气动力只考虑到 90 km：| 高度 h / km | 密度 rho / kg m^-3 |
|-------------|-------------------|
| 0 | 1.225 |
| 10 | 4.135e-1 |
| 20 | 8.891e-2 |
| 30 | 1.841e-2 |
| 40 | 3.996e-3 |
| 50 | 1.027e-3 |
| 60 | 3.097e-4 |
| 70 | 8.283e-5 |
| 80 | 1.846e-5 |
| 90 | 0 |

边界处理：

$$\rho(h) = \rho_{0},\quad\quad h \leq 0$$

$$\rho(h) = 0,\quad\quad h \geq 90\ km$$

对于 `h_i <= h < h_{i+1}` 且 `rho_{i+1}>0` 的区间，采用对数线性插值：

$$f = \frac{h - h_{i}}{h_{i + 1} - h_{i}}$$

$$\ln\rho(h) = (1 - f)\ln\rho_{i} + f\ln\rho_{i + 1}$$

等价于：

$$\rho(h) = \rho_{i}^{1 - f}\rho_{i + 1}^{f}$$

对于最高层接近真空的区间，若上边界密度为零，则采用线性衰减：

$$\rho(h) = \rho_i \frac{h_{i+1}-h}{h_{i+1}-h_i}$$

### 8.3 指数大气对照模型

代码还保留一参数指数大气作为对照：

$$\rho(h) = \rho_{0}\exp\left( - \frac{h}{H_{s}} \right)$$

其中：

$$\rho_{0} = 1.225\ kg/m^{3},\quad\quad H_{s} = 8500\ m$$

`h>=90 km` 时仍令：

$$\rho(h) = 0$$

## 9. 气动力、动压与阻力

相对大气速度：

$$V_{rel} = \parallel \mathbf{v}_{rel} \parallel$$

动压：

$$q = \frac{1}{2}\rho(h)V_{rel}^{2}$$

阻力大小：

$$D = \frac{1}{2}\rho(h)V_{rel}^{2}C_{D}S_{ref}$$

当前代码参数：

$$C_{D} = 0.28,\quad\quad S_{ref} = 78.5\ m^{2}$$

阻力加速度方向与相对大气速度相反：

$$\mathbf a_{\mathrm{drag}} = -{\frac{D}{mV_{\mathrm{rel}}}}\mathbf v_{\mathrm{rel}}$$

若 `V_rel` 接近零，则令阻力加速度为零以避免数值奇异。

最大动压约束可写为：

$$q_{\max} \leq q_{limit}$$

当前优化评分中采用软惩罚形式，阈值取：

$$q_{limit} = 60\ kPa$$

## 10. LEO 入轨目标

目标停泊轨道半径：

$$r_{LEO} = R_{E} + h_{LEO}$$

圆轨道速度：

$$v_{circ} = \sqrt{\frac{\mu_{E}}{r_{LEO}}}$$

飞行路径角：

$$\gamma = \arctan \left( \frac{v_r}{v_h} \right)$$

其中：

$$v_{r} = \mathbf{v} \cdot \widehat{\mathbf{u}}$$

$$v_{h} = \sqrt{\parallel \mathbf{v} \parallel^{2} - v_{r}^{2}}$$

理想近圆入轨要求：

$$h_{f} \approx h_{LEO}$$

$$\parallel \mathbf{v}_{f} \parallel \approx v_{circ}$$

$$\gamma_{f} \approx 0$$

当前目标高度取：

$$h_{LEO} = 300\ km$$

## 11. LEO 交会对接模型

### 11.1 圆轨道平均角速度

半径为：

$$r = R_{E} + h$$

圆轨道平均角速度：

$$n = \sqrt{\frac{\mu_{E}}{r^{3}}}$$

轨道周期：

$$T_{orb} = \frac{2\pi}{n}$$

### 11.2 相位追赶

设目标模块在 `h_target`，追赶模块在 `h_phase`。相对漂移角速度：

$$\dot\theta_{\mathrm{rel}} = n_{\mathrm{phase}}-n_{\mathrm{target}}$$

若需要闭合相位角 `theta`，等待时间为：

$$t_{\mathrm{wait}} = {\frac{\theta}{|\dot\theta_{\mathrm{rel}}|}}$$

若 `h_phase<h_target`，则：

$$n_{phase} > n_{target}$$

追赶模块在低轨道上逐渐追上目标。

当前基线示例：

    h_target = 300 km
    h_phase  = 260 km
    theta    = 40 deg
    t_wait   = 18.5 h

### 11.3 两圆轨道 Hohmann 转移

从半径 `r1` 的圆轨道转移到半径 `r2` 的圆轨道：

$$a = \frac{r_{1} + r_{2}}{2}$$

初始圆轨道速度：

$$v_{1} = \sqrt{\frac{\mu_{E}}{r_{1}}}$$

目标圆轨道速度：

$$v_{2} = \sqrt{\frac{\mu_{E}}{r_{2}}}$$

转移椭圆在起点速度：

$$v_{t1} = \sqrt{\mu_E\left({\frac{2}{r_1}}-{\frac{1}{a}}\right)}$$

转移椭圆在终点速度：

$$v_{t2} = \sqrt{\mu_E\left({\frac{2}{r_2}}-{\frac{1}{a}}\right)}$$

两脉冲转移速度增量：

$$\Delta v_{\mathrm{H}} = | v_{t1}-v_1|+| v_2-v_{t2}|$$

考虑对接和姿控余量：

$$\Delta v_{\mathrm{rendezvous,total}} = \Delta v_{\mathrm{H}} + \Delta v_{\mathrm{docking margin}}$$

当前取：

$$\Delta v_{dockingmargin} = 20\ m/s$$

基线结果约为：

$$\Delta v_{rendezvous,total} \approx 43\ m/s$$

## 12. LEO 到地月转移轨道 TLI 模型

第一版采用拼接圆锥/Hohmann 型近似。LEO 半径：

$$r_{1} = R_{E} + h_{LEO}$$

远地点取地月平均距离：

$$r_{2} = r_{EM}$$

转移椭圆半长轴：

$$a = \frac{r_{1} + r_{2}}{2}$$

LEO 圆轨道速度：

$$v_{\mathrm{LEO}} = \sqrt{\frac{\mu_E}{r_1}}$$

转移椭圆近地点速度：

$$v_p = \sqrt{ \mu_E \left( \frac{2}{r_1} - \frac{1}{a} \right) }$$

TLI 速度增量：

$$\Delta v_{\mathrm{TLI}} = v_p-v_{\mathrm{LEO}}$$

转移飞行时间取半个椭圆周期：

$$t_{\mathrm{TOF}} = \pi\sqrt{\frac{a^3}{\mu_E}}$$

300 km LEO 基线：

$$\Delta v_{TLI} \approx 3.108\ km/s$$

$$t_{TOF} \approx 4.98\ d$$

## 13. 组合体 TLI 质量预算

采用理想火箭方程：

$$MR = \frac{m_0}{m_f} = \exp\left( {\frac{\Delta v_{\mathrm{TLI}}}{I_{\mathrm{sp}}g_0}} \right)$$

设 TLI 后仍需保留的非推进剂质量为：

$$m_{\mathrm{fixed}} = m_{\mathrm{cargo}} + m_{\mathrm{adapter}}$$

当前：

$$m_{cargo} = 40\ t,\quad\quad m_{adapter} = 4\ t$$

设 TLI 级干质量与推进剂质量比为：

$$\epsilon = \frac{m_{dry}}{m_{prop}}$$

则：

$$m_{dry} = \epsilon m_{prop}$$

TLI 点火前组合体质量：

$$m_{0} = m_{fixed} + m_{prop} + m_{dry}$$

TLI 结束后质量：

$$m_{f} = m_{fixed} + m_{dry}$$

代入火箭方程：

$$MR = {\frac{m_{\mathrm{fixed}}+(1+\epsilon)m_{\mathrm{prop}}}{m_{\mathrm{fixed}}+\epsilon m_{\mathrm{prop}}}}$$

解得推进剂质量：

$$m_{\mathrm{prop}} = {\frac{(MR-1)m_{\mathrm{fixed}}}{1-(MR-1)\epsilon}}$$

TLI 级干质量：

$$m_{dry} = \epsilon m_{prop}$$

LEO 初始组合体质量：

$$m_{\mathrm{stack,LEO}} = m_{\mathrm{fixed}} + m_{\mathrm{prop}} + m_{\mathrm{dry}}$$

折算每发需送入 LEO 的湿质量：

$$m_{\mathrm{LEO,per launch}} = {\frac{m_{\mathrm{stack,LEO}}}{2}}$$

当前名义参数：

$$I_{sp} = 450\ s,\quad\quad\epsilon = 0.08$$

计算结果约为：

$$MR = 2.022$$

$$m_{prop} = 49.0\ t$$

$$m_{dry} = 3.9\ t$$

$$m_{stack,LEO} = 96.9\ t$$

$$m_{LEO,perlaunch} = 48.5\ t$$

当前上升段占位模型每发末端质量约 69 t，因此模型余量为：

$$m_{\mathrm{margin,LEO}} = 69.0-48.5 \approx 20.5\ \mathrm{t}$$

## 14. 可靠性模型

### 14.1 发动机簇可靠性

设单台发动机关键阶段可靠性为 `r`，发动机数为 `N`。若不允许任何发动机失效：

$$R_{cluster} = r^{N}$$

若允许最多 `f` 台发动机失效仍可完成任务：

$$R_{\mathrm{cluster}} \sum_{k=0}^{f} \binom{N}{k} (1-r)^k r^{N-k}$$

该模型只用于敏感性分析，不能等同于真实整箭可靠性。

### 14.2 多发任务可靠性

设单发任务成功概率为 `R`，总发射次数为 `N`，至少需要 `K` 次成功。则任务成功概率为：

$$P(N,K;R) = \sum_{s=K}^{N} \binom{N}{s} R^s (1-R)^{N-s}$$

两发全成功：

$$P_{2} = R^{2}$$

三发至少两发成功：

$$P_{3,2} = \binom{3}{2}R^2(1-R)+R^3$$

$$P_{3,2} = 3R^{2} - 2R^{3}$$

当 `R=0.95`：

$$P_{2} = 0.9025$$

$$P_{3,2} = 0.99275$$

### 14.3 两发 LEO 组合任务总可靠性链

主方案不仅需要两次发射成功，还需要 LEO 交会对接和 TLI 点火成功：

$$R_{\mathrm{total}} = R_{\mathrm{launch}}^2 R_{\mathrm{rendezvous}} R_{\mathrm{TLI}}$$

当前基线敏感性取值：

$$R_{launch} = 0.95$$

$$R_{rendezvous} = 0.98$$

$$R_{TLI} = 0.985$$

于是：

$$R_{\mathrm{total}} = 0.95^2\times 0.98\times 0.985 \approx 0.871$$

二维敏感性分析扫描：

$$R_{rendezvous} \in [ 0.94,0.995]$$

$$R_{TLI} \in [ 0.94,0.995]$$

在 `R_launch=0.95` 下，总可靠性范围约为：

$$0.797 \leq R_{total} \leq 0.893$$

## 15. 优化模型

当前项目采用无依赖粗网格搜索。核心思想是枚举候选变量，计算目标函数评分，按评分从小到大排序。

### 15.1 上升段程序角优化变量

二维代理模型变量：

$$\mathbf u_{\mathrm{pitch}} = \left[ t_{\mathrm{end}},\ \phi_f \right]$$

ECI 模型变量：

$$\mathbf u_{\mathrm{ECI}} = \left[ t_{\mathrm{end}},\ \phi_f,\ s \right]$$

目标高度：

$$h^{*} = 300\ km$$

ECI 圆轨道目标速度：

$$v^{*} = \sqrt{\frac{\mu_{E}}{R_{E} + h^{*}}}$$

终端误差：

$$e_{h} = \frac{h_{f} - h^{*}}{100}$$

$$e_{v} = \frac{v_{f} - v^{*}}{500}$$

$$e_{\gamma} = \frac{\gamma_{f}}{5}$$

最大动压惩罚：

$$e_{q} = \frac{\max(0,q_{\max} - 60)}{20}$$

其中高度单位为 km，速度单位为 m/s，角度单位为 deg，动压单位为 kPa。

程序角评分函数：

$$J_{\mathrm{ascent}} = e_h^2+e_v^2+e_\gamma^2+e_q^2$$

当前 ECI 网格：

    t_end in {300,305,310,315,320,325,330,335,340} s
    phi_f in {6,7,8,9,10,11,12} deg
    s     in {1.2,1.3,1.35,1.4,1.5}

最优候选：

    t_end = 305 s
    phi_f = 10 deg
    s     = 1.4

### 15.2 LEO 交会轨道优化

交会优化变量：

$$\mathbf u_{\mathrm{rv}} = \left[ h_{\mathrm{target}},\h_{\mathrm{phase}} \right]$$

等待时间惩罚：

$$J_{t} = \frac{t_{wait}}{24}$$

速度增量惩罚：

$$J_{\Delta v} = \frac{\Delta v_{rendezvous,total}}{100}$$

交会评分：

$$J_{\mathrm{rv}} = J_{\Delta v} + 0.3J_t$$

当前候选网格：

    h_target in {280,300,320} km
    h_phase  in {h_target-40, h_target-20, h_target-10,
                 h_target+10, h_target+20, h_target+40} km

当前结果中，300 km 目标轨道、260 km 相位轨道是论文叙述采用的基线示例：

    t_wait = 18.5 h
    Delta_v_total = 43.3 m/s

### 15.3 总体方案多目标评价

论文中可以把总体优化写为多目标问题：

$$\max R_{total}$$

$$\min N_{launch}$$

$$\min\Delta v_{total}$$

$$\max m_{margin}$$

$$\min J_{ascent}$$

若写成加权单目标形式，可定义：

$$J_{\mathrm{total}} = w_1(1-R_{\mathrm{total}}) + w_2\left[\max(0,40-m_{\mathrm{delivered}})\right]^2 + w_3N_{\mathrm{launch}} + w_4\Delta v_{\mathrm{TLI}} + w_5J_{\mathrm{ascent}} + w_6J_{\mathrm{rv}}$$

约束条件包括：

$$m_{payload,each} \leq C_{TLI}$$

$$q_{\max} \leq q_{limit}$$

$$h_{f} \approx h_{LEO}$$

$$\gamma_{f} \approx 0$$

$$m_{stack,LEO}/2 \leq m_{LEO,perlaunch,max}$$

当前项目没有使用复杂优化库，而是用网格搜索得到可解释、可复现的第一版候选解。

## 16. 数值输出与论文应引用的关键结果

当前 `baseline_summary.json` 中的关键数值：

|---|---|
| 指标 | 结果 |

| 推荐架构                   | 两发长征十号 LEO 对接后 TLI |

## 17. 公式与代码对应关系

|---|---|
| 模型部分 | 主要代码文件 |

| 常数           | `src/constants.py`       |

## 18. 需要在最终论文中说明的局限

1.  长征十号完整分级质量、发动机性能和真实制导律未完全公开，当前上升段是校准量级的代理模型。

2.  大气模型采用标准大气表密度插值，没有加入风场、温度扰动和季节纬度变化。

3.  当前积分方法为一阶显式近似，后续高精度版本可替换为 RK4 或自适应积分。

4.  TLI 采用 Hohmann 型拼接圆锥估算，未引入真实月球星历、月球引力影响球、太阳摄动和中途修正。

5.  LEO 交会模型只估算相位漂移和两圆轨道转移，未模拟完整 GNC、姿态控制、相对导航和对接动力学。

6.  可靠性模型是参数化敏感性分析，不是工程统计可靠性评估。

因此论文写法应强调：本模型用于竞赛问题的一阶可行性、方案比较和物理量级论证，而不是完整工程发射任务设计。
