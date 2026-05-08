# 完整数学物理建模公式汇总 v0.8

本文档把当前项目从任务定义到上升段、LEO 交会、TLI、质量预算、可靠性和优化算法的数学物理模型统一写出。它对应当前代码目录 `src/` 中已经实现的模型，并补充论文正文中应写清楚的公式。

> 说明：课程大纲中提到“大气层内选择杨炳蔚的模型”。当前代码采用的是“标准大气表 + 分层对数插值”的可计算简化版，并设置 90 km 以上不考虑气动力。论文中可以表述为“以杨炳蔚教材标准大气表为主模型，代码中用分层密度表和对数插值实现”。

## 1. 变量、常数与单位

除特别说明外，动力学计算统一使用 SI 单位。

| 符号 | 含义 | 当前取值 |
|---|---|---:|
| `g0` | 标准重力加速度 | 9.80665 m/s^2 |
| `mu_E` | 地球引力参数 | 3.986004418e14 m^3/s^2 |
| `R_E` | 地球平均半径 | 6371000 m |
| `omega_E` | 地球自转角速度 | 7.2921159e-5 rad/s |
| `J2` | 地球二阶带谐项 | 1.08262668e-3 |
| `r_EM` | 地月平均距离 | 384400000 m |
| `m_req` | 题目要求总载荷 | 40 t |
| `C_TLI` | 长征十号公开 TLI 运力 | >= 27 t |

文昌发射场建模参数：

```text
latitude  = 19.614 deg
longitude = 110.951 deg
altitude  = 50 m
```

## 2. 任务可行性与总体架构

题目目标是把总计 40 t 月球基地建设物资送入 Earth-Moon transfer orbit。首先用公开 TLI 运力做单发可行性判据：

```math
m_{\rm req} \le C_{\rm TLI}
```

当前公开数据给出：

```math
40\ {\rm t} > 27\ {\rm t}
```

因此单发长征十号直接完成 40 t TLI 不可行。

主方案采用两发长征十号：

```math
N_{\rm launch}=2,\qquad
m_{\rm payload,each}=20\ {\rm t}
```

每发相对公开 TLI 运力的等效余量为：

```math
m_{\rm margin,each}=C_{\rm TLI}-m_{\rm payload,each}
=27-20=7\ {\rm t}
```

总交付质量：

```math
m_{\rm delivered}=N_{\rm success}m_{\rm payload,each}
```

两发全成功时：

```math
m_{\rm delivered}=2\times 20=40\ {\rm t}
```

任务链为：

```text
CZ-10 Launch A -> Module A to LEO
CZ-10 Launch B -> Module B to nearby LEO phasing orbit
LEO rendezvous and docking
Combined stack translunar injection
```

三发 2-out-of-3 方案不作为当前主方案，只作为可靠性扩展：

```math
N_{\rm launch}=3,\qquad N_{\rm required}=2
```

## 3. 坐标系定义

### 3.1 ECEF 球形地固坐标

当前模型用球形地球近似。设地理纬度为 `varphi`，经度为 `lambda`，高度为 `h`，则 ECEF 位置为：

```math
\mathbf r_{\rm ECEF}
=
\begin{bmatrix}
(R_E+h)\cos\varphi\cos\lambda\\
(R_E+h)\cos\varphi\sin\lambda\\
(R_E+h)\sin\varphi
\end{bmatrix}
```

由 ECEF 反算球形经纬度：

```math
r=\|\mathbf r\|
```

```math
\varphi=\arcsin\left({z\over r}\right)
```

```math
\lambda=\operatorname{atan2}(y,x)
```

```math
h=r-R_E
```

### 3.2 ECI 惯性坐标

当前 `ascent_eci.py` 中，取初始时刻 ECI 与 ECEF 重合。地球自转角速度向量为：

```math
\boldsymbol\omega_E=
\begin{bmatrix}
0\\0\\\omega_E
\end{bmatrix}
```

发射点初始惯性速度来自地球自转：

```math
\mathbf v_0=\boldsymbol\omega_E\times \mathbf r_0
```

大气随地球固连转动，因此当地大气速度近似为：

```math
\mathbf v_{\rm atm}=\boldsymbol\omega_E\times \mathbf r
```

火箭相对大气速度：

```math
\mathbf v_{\rm rel}=\mathbf v-\mathbf v_{\rm atm}
```

### 3.3 局部 ENU 坐标基

局部天向单位向量：

```math
\hat{\mathbf u}={\mathbf r\over \|\mathbf r\|}
```

局部东向单位向量：

```math
\hat{\mathbf e}=
{\boldsymbol\omega_E\times \mathbf r
\over
\|\boldsymbol\omega_E\times \mathbf r\|}
```

局部北向单位向量：

```math
\hat{\mathbf n}=
{\hat{\mathbf u}\times \hat{\mathbf e}
\over
\|\hat{\mathbf u}\times \hat{\mathbf e}\|}
```

发射方位角 `A` 从正北顺时针计量，水平发射方向为：

```math
\hat{\mathbf h}_A
=
\cos A\,\hat{\mathbf n}
+
\sin A\,\hat{\mathbf e}
```

程序角 `phi` 定义为推力方向相对当地水平面的夹角，`phi=90 deg` 为竖直向上，`phi=0 deg` 为水平。推力方向单位向量：

```math
\hat{\mathbf T}
=
\sin\phi\,\hat{\mathbf u}
+
\cos\phi\,\hat{\mathbf h}_A
```

## 4. 发射几何与地球自转收益

发射点地球自转线速度：

```math
v_{\rm rot}=\omega_E R_E\cos\varphi
```

考虑发射方位角后的沿发射方向自转速度收益：

```math
\Delta v_{\rm rot}(A)=v_{\rm rot}\sin A
```

文昌向东发射 `A=90 deg` 时：

```math
\Delta v_{\rm rot}\approx 438\ {\rm m/s}
```

球形地球一阶近似下，发射方位角与入轨倾角关系为：

```math
\cos i\approx \cos\varphi\sin A
```

正东发射时：

```math
i_{\min}\approx \varphi
```

因此文昌低纬度有利于近赤道低倾角停泊轨道与 TLI 前的能量效率。

## 5. 上升段三维点质点动力学

### 5.1 状态量

ECI 上升段状态量为：

```math
\mathbf x=
\left[
\mathbf r,\ \mathbf v,\ m
\right]^T
```

其中：

```math
\mathbf r=[x,y,z]^T,\qquad
\mathbf v=[v_x,v_y,v_z]^T
```

### 5.2 连续动力学方程

```math
{d\mathbf r\over dt}=\mathbf v
```

```math
{d\mathbf v\over dt}
=
\mathbf a_{\rm grav}
+
\mathbf a_{J2}
+
\mathbf a_{\rm thrust}
+
\mathbf a_{\rm drag}
```

```math
{dm\over dt}=-{T\over I_{\rm sp}g_0}
```

代码中采用一阶显式积分近似：

```math
\mathbf v_{k+1}=\mathbf v_k+\mathbf a_k\Delta t
```

```math
\mathbf r_{k+1}=\mathbf r_k+\mathbf v_{k+1}\Delta t
```

```math
m_{k+1}=m_k-\dot m_k\Delta t
```

### 5.3 分级与质量模型

每一级用常推力、常比冲、推进剂消耗和干质量抛弃近似。第 `j` 级：

```math
\dot m_j={T_j\over I_{{\rm sp},j}g_0}
```

燃烧时间近似：

```math
t_{{\rm burn},j}={m_{{\rm prop},j}\over \dot m_j}
```

当第 `j` 级推进剂耗尽时：

```math
m^+=m^- - m_{{\rm dry\ drop},j}
```

当前占位分级参数：

| 级段 | 推进剂质量 | 抛弃干质量 | 推力 | 比冲 |
|---|---:|---:|---:|---:|
| booster_core_cluster | 1420 t | 260 t | 26.27 MN | 305 s |
| second_stage | 285 t | 45 t | 4.20 MN | 340 s |
| third_stage_proxy | 110 t | 0 t | 1.80 MN | 450 s |

这些数值用于生成趋势图和入轨量级，不应写成真实长征十号完整设计数据。

## 6. 程序角模型

程序角 `phi(t)` 采用分段光滑下降形式：

```math
\phi(t)=90^\circ,\qquad 0\le t\le t_v
```

```math
\phi(t)
=
90^\circ
-
\left(
{t-t_v\over t_{\rm end}-t_v}
\right)^s
\left(90^\circ-\phi_f\right),
\qquad
t_v<t<t_{\rm end}
```

```math
\phi(t)=\phi_f,\qquad t\ge t_{\rm end}
```

其中：

| 符号 | 含义 |
|---|---|
| `t_v` | 垂直上升时间 |
| `t_end` | 俯仰转弯结束时间 |
| `phi_f` | 后段最终程序角 |
| `s` | 程序角曲线形状指数 |

当前 ECI 最优粗网格候选为：

```text
t_end = 305 s
phi_f = 10 deg
s     = 1.4
```

该候选末端结果约为：

```text
h_f     = 306.9 km
v_f     = 7.723 km/s
gamma_f = -0.02 deg
```

## 7. 地球引力与 J2 项

### 7.1 球形二体引力

设：

```math
r=\|\mathbf r\|=\sqrt{x^2+y^2+z^2}
```

球形引力加速度：

```math
\mathbf a_{\rm grav}
=
-{\mu_E\over r^3}\mathbf r
```

### 7.2 J2 引力势函数

J2 势函数常写为：

```math
U(r,\phi_g)
=
{\mu_E\over r}
\left[
1
-
J_2
\left({R_E\over r}\right)^2
P_2(\sin\phi_g)
\right]
```

其中：

```math
P_2(x)={1\over 2}(3x^2-1)
```

`phi_g` 为地心纬度。

### 7.3 代码采用的 J2 加速度形式

当前 `ascent_eci.py` 使用的总引力加速度写为：

```math
\mathbf a=
-{\mu_E\over r^3}
\begin{bmatrix}
x\\y\\z
\end{bmatrix}

+
{3\over 2}J_2{\mu_E R_E^2\over r^5}
\begin{bmatrix}
x(5z^2/r^2-1)\\
y(5z^2/r^2-1)\\
z(5z^2/r^2-3)
\end{bmatrix}
```

即：

```math
a_x=-{\mu_E x\over r^3}
 + {3J_2\mu_E R_E^2 x\over 2r^5}
 \left(5{z^2\over r^2}-1\right)
```

```math
a_y=-{\mu_E y\over r^3}
 + {3J_2\mu_E R_E^2 y\over 2r^5}
 \left(5{z^2\over r^2}-1\right)
```

```math
a_z=-{\mu_E z\over r^3}
 + {3J_2\mu_E R_E^2 z\over 2r^5}
 \left(5{z^2\over r^2}-3\right)
```

v0.6 对照结果中，J2 相对球形引力使末端高度变化约：

```math
\Delta h_f \approx -2.27\ {\rm km}
```

末端惯性速度变化约：

```math
\Delta v_f \approx +1.37\ {\rm m/s}
```

## 8. 杨炳蔚/标准大气模型与当前实现

### 8.1 标准大气的通用分层公式

若采用教材标准大气表，可按分层温度梯度给出温度、压强和密度。设第 `i` 层下边界位势高度为 `H_i`，温度为 `T_i`，压强为 `p_i`，温度梯度为 `L_i=dT/dH`。

位势高度与几何高度关系可写为：

```math
H={R_E h\over R_E+h}
```

若该层温度梯度不为零：

```math
T(H)=T_i+L_i(H-H_i)
```

```math
p(H)
=
p_i
\left[
{T_i\over T(H)}
\right]^{g_0/(R_a L_i)}
```

```math
\rho(H)={p(H)\over R_a T(H)}
```

若该层为等温层，即 `L_i=0`：

```math
T(H)=T_i
```

```math
p(H)
=
p_i
\exp\left[
-{g_0(H-H_i)\over R_aT_i}
\right]
```

```math
\rho(H)={p(H)\over R_aT_i}
```

其中 `R_a` 为空气气体常数，约为：

```math
R_a=287.05287\ {\rm J/(kg\cdot K)}
```

在论文中，可以把上式作为“杨炳蔚教材标准大气表的连续分层表达”，再说明代码中为简化计算只取密度表。

### 8.2 当前代码采用的密度表

当前 `atmosphere.py` 使用如下密度表，气动力只考虑到 90 km：

| 高度 h / km | 密度 rho / kg m^-3 |
|---:|---:|
| 0 | 1.225 |
| 1 | 1.112 |
| 2 | 1.007 |
| 5 | 0.736 |
| 10 | 0.4135 |
| 20 | 0.0889 |
| 30 | 0.0184 |
| 40 | 0.0040 |
| 50 | 0.00103 |
| 60 | 0.00031 |
| 70 | 0.000083 |
| 80 | 0.0000185 |
| 90 | 0 |

边界处理：

```math
\rho(h)=\rho_0,\qquad h\le 0
```

```math
\rho(h)=0,\qquad h\ge 90\ {\rm km}
```

对于 `h_i <= h < h_{i+1}` 且 `rho_{i+1}>0` 的区间，采用对数线性插值：

```math
f={h-h_i\over h_{i+1}-h_i}
```

```math
\ln\rho(h)
=(1-f)\ln\rho_i+f\ln\rho_{i+1}
```

等价于：

```math
\rho(h)=\rho_i^{1-f}\rho_{i+1}^{f}
```

对于最高层接近真空的区间，若上边界密度为零，则采用线性衰减：

```math
\rho(h)
=
\rho_i
{h_{i+1}-h\over h_{i+1}-h_i}
```

### 8.3 指数大气对照模型

代码还保留一参数指数大气作为对照：

```math
\rho(h)=\rho_0\exp\left(-{h\over H_s}\right)
```

其中：

```math
\rho_0=1.225\ {\rm kg/m^3},\qquad H_s=8500\ {\rm m}
```

`h>=90 km` 时仍令：

```math
\rho(h)=0
```

## 9. 气动力、动压与阻力

相对大气速度：

```math
V_{\rm rel}=\|\mathbf v_{\rm rel}\|
```

动压：

```math
q={1\over 2}\rho(h)V_{\rm rel}^2
```

阻力大小：

```math
D={1\over 2}\rho(h)V_{\rm rel}^2 C_D S_{\rm ref}
```

当前代码参数：

```math
C_D=0.28,\qquad S_{\rm ref}=78.5\ {\rm m^2}
```

阻力加速度方向与相对大气速度相反：

```math
\mathbf a_{\rm drag}
=
-{D\over mV_{\rm rel}}\mathbf v_{\rm rel}
```

若 `V_rel` 接近零，则令阻力加速度为零以避免数值奇异。

最大动压约束可写为：

```math
q_{\max}\le q_{\rm limit}
```

当前优化评分中采用软惩罚形式，阈值取：

```math
q_{\rm limit}=60\ {\rm kPa}
```

## 10. LEO 入轨目标

目标停泊轨道半径：

```math
r_{\rm LEO}=R_E+h_{\rm LEO}
```

圆轨道速度：

```math
v_{\rm circ}=\sqrt{\mu_E\over r_{\rm LEO}}
```

飞行路径角：

```math
\gamma
=
\arctan
\left(
{v_r\over v_h}
\right)
```

其中：

```math
v_r=\mathbf v\cdot \hat{\mathbf u}
```

```math
v_h=
\sqrt{\|\mathbf v\|^2-v_r^2}
```

理想近圆入轨要求：

```math
h_f\approx h_{\rm LEO}
```

```math
\|\mathbf v_f\|\approx v_{\rm circ}
```

```math
\gamma_f\approx 0
```

当前目标高度取：

```math
h_{\rm LEO}=300\ {\rm km}
```

## 11. LEO 交会对接模型

### 11.1 圆轨道平均角速度

半径为：

```math
r=R_E+h
```

圆轨道平均角速度：

```math
n=\sqrt{\mu_E\over r^3}
```

轨道周期：

```math
T_{\rm orb}={2\pi\over n}
```

### 11.2 相位追赶

设目标模块在 `h_target`，追赶模块在 `h_phase`。相对漂移角速度：

```math
\dot\theta_{\rm rel}
=
n_{\rm phase}-n_{\rm target}
```

若需要闭合相位角 `theta`，等待时间为：

```math
t_{\rm wait}
=
{\theta\over |\dot\theta_{\rm rel}|}
```

若 `h_phase<h_target`，则：

```math
n_{\rm phase}>n_{\rm target}
```

追赶模块在低轨道上逐渐追上目标。

当前基线示例：

```text
h_target = 300 km
h_phase  = 260 km
theta    = 40 deg
t_wait   = 18.5 h
```

### 11.3 两圆轨道 Hohmann 转移

从半径 `r1` 的圆轨道转移到半径 `r2` 的圆轨道：

```math
a={r_1+r_2\over 2}
```

初始圆轨道速度：

```math
v_1=\sqrt{\mu_E\over r_1}
```

目标圆轨道速度：

```math
v_2=\sqrt{\mu_E\over r_2}
```

转移椭圆在起点速度：

```math
v_{t1}
=
\sqrt{\mu_E\left({2\over r_1}-{1\over a}\right)}
```

转移椭圆在终点速度：

```math
v_{t2}
=
\sqrt{\mu_E\left({2\over r_2}-{1\over a}\right)}
```

两脉冲转移速度增量：

```math
\Delta v_{\rm H}
=
|v_{t1}-v_1|+|v_2-v_{t2}|
```

考虑对接和姿控余量：

```math
\Delta v_{\rm rendezvous,total}
=
\Delta v_{\rm H}
+
\Delta v_{\rm docking\ margin}
```

当前取：

```math
\Delta v_{\rm docking\ margin}=20\ {\rm m/s}
```

基线结果约为：

```math
\Delta v_{\rm rendezvous,total}\approx 43\ {\rm m/s}
```

## 12. LEO 到地月转移轨道 TLI 模型

第一版采用拼接圆锥/Hohmann 型近似。LEO 半径：

```math
r_1=R_E+h_{\rm LEO}
```

远地点取地月平均距离：

```math
r_2=r_{\rm EM}
```

转移椭圆半长轴：

```math
a={r_1+r_2\over 2}
```

LEO 圆轨道速度：

```math
v_{\rm LEO}
=
\sqrt{\mu_E\over r_1}
```

转移椭圆近地点速度：

```math
v_p
=
\sqrt{
\mu_E
\left(
{2\over r_1}
-
{1\over a}
\right)}
```

TLI 速度增量：

```math
\Delta v_{\rm TLI}
=
v_p-v_{\rm LEO}
```

转移飞行时间取半个椭圆周期：

```math
t_{\rm TOF}
=
\pi\sqrt{a^3\over \mu_E}
```

300 km LEO 基线：

```math
\Delta v_{\rm TLI}\approx 3.108\ {\rm km/s}
```

```math
t_{\rm TOF}\approx 4.98\ {\rm d}
```

## 13. 组合体 TLI 质量预算

采用理想火箭方程：

```math
MR
=
{m_0\over m_f}
=
\exp\left(
{\Delta v_{\rm TLI}\over I_{\rm sp}g_0}
\right)
```

设 TLI 后仍需保留的非推进剂质量为：

```math
m_{\rm fixed}
=
m_{\rm cargo}
+
m_{\rm adapter}
```

当前：

```math
m_{\rm cargo}=40\ {\rm t},\qquad
m_{\rm adapter}=4\ {\rm t}
```

设 TLI 级干质量与推进剂质量比为：

```math
\epsilon={m_{\rm dry}\over m_{\rm prop}}
```

则：

```math
m_{\rm dry}=\epsilon m_{\rm prop}
```

TLI 点火前组合体质量：

```math
m_0=m_{\rm fixed}+m_{\rm prop}+m_{\rm dry}
```

TLI 结束后质量：

```math
m_f=m_{\rm fixed}+m_{\rm dry}
```

代入火箭方程：

```math
MR
=
{m_{\rm fixed}+(1+\epsilon)m_{\rm prop}
\over
m_{\rm fixed}+\epsilon m_{\rm prop}}
```

解得推进剂质量：

```math
m_{\rm prop}
=
{(MR-1)m_{\rm fixed}
\over
1-(MR-1)\epsilon}
```

TLI 级干质量：

```math
m_{\rm dry}=\epsilon m_{\rm prop}
```

LEO 初始组合体质量：

```math
m_{\rm stack,LEO}
=
m_{\rm fixed}
+
m_{\rm prop}
+
m_{\rm dry}
```

折算每发需送入 LEO 的湿质量：

```math
m_{\rm LEO,per\ launch}
=
{m_{\rm stack,LEO}\over 2}
```

当前名义参数：

```math
I_{\rm sp}=450\ {\rm s},\qquad
\epsilon=0.08
```

计算结果约为：

```math
MR=2.022
```

```math
m_{\rm prop}=49.0\ {\rm t}
```

```math
m_{\rm dry}=3.9\ {\rm t}
```

```math
m_{\rm stack,LEO}=96.9\ {\rm t}
```

```math
m_{\rm LEO,per\ launch}=48.5\ {\rm t}
```

当前上升段占位模型每发末端质量约 69 t，因此模型余量为：

```math
m_{\rm margin,LEO}
=
69.0-48.5
\approx 20.5\ {\rm t}
```

## 14. 可靠性模型

### 14.1 发动机簇可靠性

设单台发动机关键阶段可靠性为 `r`，发动机数为 `N`。若不允许任何发动机失效：

```math
R_{\rm cluster}=r^N
```

若允许最多 `f` 台发动机失效仍可完成任务：

```math
R_{\rm cluster}
=
\sum_{k=0}^{f}
\binom{N}{k}
(1-r)^k
r^{N-k}
```

该模型只用于敏感性分析，不能等同于真实整箭可靠性。

### 14.2 多发任务可靠性

设单发任务成功概率为 `R`，总发射次数为 `N`，至少需要 `K` 次成功。则任务成功概率为：

```math
P(N,K;R)
=
\sum_{s=K}^{N}
\binom{N}{s}
R^s
(1-R)^{N-s}
```

两发全成功：

```math
P_2=R^2
```

三发至少两发成功：

```math
P_{3,2}
=
\binom{3}{2}R^2(1-R)+R^3
```

```math
P_{3,2}=3R^2-2R^3
```

当 `R=0.95`：

```math
P_2=0.9025
```

```math
P_{3,2}=0.99275
```

### 14.3 两发 LEO 组合任务总可靠性链

主方案不仅需要两次发射成功，还需要 LEO 交会对接和 TLI 点火成功：

```math
R_{\rm total}
=
R_{\rm launch}^2
R_{\rm rendezvous}
R_{\rm TLI}
```

当前基线敏感性取值：

```math
R_{\rm launch}=0.95
```

```math
R_{\rm rendezvous}=0.98
```

```math
R_{\rm TLI}=0.985
```

于是：

```math
R_{\rm total}
=
0.95^2\times 0.98\times 0.985
\approx 0.871
```

二维敏感性分析扫描：

```math
R_{\rm rendezvous}\in[0.94,0.995]
```

```math
R_{\rm TLI}\in[0.94,0.995]
```

在 `R_launch=0.95` 下，总可靠性范围约为：

```math
0.797 \le R_{\rm total}\le 0.893
```

## 15. 优化模型

当前项目采用无依赖粗网格搜索。核心思想是枚举候选变量，计算目标函数评分，按评分从小到大排序。

### 15.1 上升段程序角优化变量

二维代理模型变量：

```math
\mathbf u_{\rm pitch}
=
\left[
t_{\rm end},\ \phi_f
\right]
```

ECI 模型变量：

```math
\mathbf u_{\rm ECI}
=
\left[
t_{\rm end},\ \phi_f,\ s
\right]
```

目标高度：

```math
h^*=300\ {\rm km}
```

ECI 圆轨道目标速度：

```math
v^*=\sqrt{\mu_E\over R_E+h^*}
```

终端误差：

```math
e_h={h_f-h^*\over 100}
```

```math
e_v={v_f-v^*\over 500}
```

```math
e_\gamma={\gamma_f\over 5}
```

最大动压惩罚：

```math
e_q=
{\max(0,q_{\max}-60)\over 20}
```

其中高度单位为 km，速度单位为 m/s，角度单位为 deg，动压单位为 kPa。

程序角评分函数：

```math
J_{\rm ascent}
=
e_h^2+e_v^2+e_\gamma^2+e_q^2
```

当前 ECI 网格：

```text
t_end in {300,305,310,315,320,325,330,335,340} s
phi_f in {6,7,8,9,10,11,12} deg
s     in {1.2,1.3,1.35,1.4,1.5}
```

最优候选：

```text
t_end = 305 s
phi_f = 10 deg
s     = 1.4
```

### 15.2 LEO 交会轨道优化

交会优化变量：

```math
\mathbf u_{\rm rv}
=
\left[
h_{\rm target},\ h_{\rm phase}
\right]
```

等待时间惩罚：

```math
J_t={t_{\rm wait}\over 24}
```

速度增量惩罚：

```math
J_{\Delta v}={\Delta v_{\rm rendezvous,total}\over 100}
```

交会评分：

```math
J_{\rm rv}
=
J_{\Delta v}
+
0.3J_t
```

当前候选网格：

```text
h_target in {280,300,320} km
h_phase  in {h_target-40, h_target-20, h_target-10,
             h_target+10, h_target+20, h_target+40} km
```

当前结果中，300 km 目标轨道、260 km 相位轨道是论文叙述采用的基线示例：

```text
t_wait = 18.5 h
Delta_v_total = 43.3 m/s
```

### 15.3 总体方案多目标评价

论文中可以把总体优化写为多目标问题：

```math
\max R_{\rm total}
```

```math
\min N_{\rm launch}
```

```math
\min \Delta v_{\rm total}
```

```math
\max m_{\rm margin}
```

```math
\min J_{\rm ascent}
```

若写成加权单目标形式，可定义：

```math
J_{\rm total}
=
w_1(1-R_{\rm total})
+
w_2\left[\max(0,40-m_{\rm delivered})\right]^2
+
w_3N_{\rm launch}
+
w_4\Delta v_{\rm TLI}
+
w_5J_{\rm ascent}
+
w_6J_{\rm rv}
```

约束条件包括：

```math
m_{\rm payload,each}\le C_{\rm TLI}
```

```math
q_{\max}\le q_{\rm limit}
```

```math
h_f\approx h_{\rm LEO}
```

```math
\gamma_f\approx 0
```

```math
m_{\rm stack,LEO}/2 \le m_{\rm LEO,per\ launch,max}
```

当前项目没有使用复杂优化库，而是用网格搜索得到可解释、可复现的第一版候选解。

## 16. 数值输出与论文应引用的关键结果

当前 `baseline_summary.json` 中的关键数值：

| 指标 | 结果 |
|---|---:|
| 推荐架构 | 两发长征十号 LEO 对接后 TLI |
| 每发载荷模块 | 20 t |
| 300 km LEO TLI Delta-v | 3.108 km/s |
| TLI 飞行时间估算 | 4.98 d |
| LEO 初始组合体质量 | 96.9 t |
| 每发 LEO 湿质量需求 | 48.5 t |
| TLI 推进剂质量 | 49.0 t |
| TLI 级干质量 | 3.9 t |
| LEO 交会等待时间示例 | 18.5 h |
| LEO 交会总 Delta-v 示例 | 43.3 m/s |
| ECI 上升段末端高度 | 306.9 km |
| ECI 上升段末端惯性速度 | 7.723 km/s |
| ECI 上升段末端飞行路径角 | -0.02 deg |
| `R_launch=0.95` 总可靠性链 | 0.871 |
| J2 相对球形引力末端高度差 | -2.27 km |

## 17. 公式与代码对应关系

| 模型部分 | 主要代码文件 |
|---|---|
| 常数 | `src/constants.py` |
| 任务架构 | `src/architecture.py` |
| 发射几何 | `src/launch_geometry.py` |
| 坐标与自转 | `src/frames.py` |
| 大气密度 | `src/atmosphere.py` |
| 二维上升段代理 | `src/ascent_3dof.py` |
| ECI/J2 上升段 | `src/ascent_eci.py` |
| LEO 交会 | `src/rendezvous.py` |
| TLI 速度增量 | `src/transfer.py` |
| TLI 质量预算 | `src/mass_budget.py` |
| 可靠性 | `src/reliability.py` |
| 目标函数 | `src/objectives.py` |
| 网格搜索 | `src/optimize.py` |
| 结果生成 | `src/run_baseline.py` |
| 增强图表 | `src/paper_figures.py` |

## 18. 需要在最终论文中说明的局限

1. 长征十号完整分级质量、发动机性能和真实制导律未完全公开，当前上升段是校准量级的代理模型。
2. 大气模型采用标准大气表密度插值，没有加入风场、温度扰动和季节纬度变化。
3. 当前积分方法为一阶显式近似，后续高精度版本可替换为 RK4 或自适应积分。
4. TLI 采用 Hohmann 型拼接圆锥估算，未引入真实月球星历、月球引力影响球、太阳摄动和中途修正。
5. LEO 交会模型只估算相位漂移和两圆轨道转移，未模拟完整 GNC、姿态控制、相对导航和对接动力学。
6. 可靠性模型是参数化敏感性分析，不是工程统计可靠性评估。

因此论文写法应强调：本模型用于竞赛问题的一阶可行性、方案比较和物理量级论证，而不是完整工程发射任务设计。
