# 数学物理建模 v0.6

## 1. 研究问题

设计一种中国当前及近期公开运载能力下的月球基地原材料运输方案，使总计 40 t 载荷进入地月转移轨道，并在可靠性上优于依赖单次 33 发动机重型发射的方案。

当前版本把问题拆成七个模型：

| 模型 | 目的 | 当前状态 |
|---|---|---|
| Model 0 可行性估算 | 判断单发是否可完成 40 t TLI | 已完成 |
| Model 1 任务架构模型 | 比较单发、两发 LEO 对接、三发冗余、40 t 单体方案 | 已完成 |
| Model 2 地月转移估算 | 计算 LEO 到 TLI 的速度增量 | 已完成 Hohmann 型一阶模型 |
| Model 3 可靠性模型 | 比较发动机簇和多发任务可靠性 | 已完成 |
| Model 4 上升段模型 | 建立文昌发射几何、基础上升段代理仿真和 ECI/J2 骨架 | 已完成 v0.6 调参基线 |
| Model 5 LEO 交会优化 | 估算两模块在 LEO 的相位追赶、对接速度增量和粗网格优化 | 已完成 v0.6 基线 |
| Model 6 总可靠性链 | 将发射、LEO 对接和 TLI 点火组合成任务可靠性 | 已完成 v0.6 敏感性分析 |
| Model 7 质量预算与引力对照 | 估算组合体 TLI 质量预算，对比球形引力和 J2 | 已完成 v0.6 基线 |

## 2. Model 0：单发可行性

公开资料给出长征十号登月构型地月转移轨道运力：

```text
C_TLI >= 27 t
```

题目要求：

```text
M_required = 40 t
```

因此单发直接 TLI 的质量约束为：

```text
M_required <= C_TLI
```

实际为：

```text
40 t > 27 t
```

所以单发长征十号不能作为主方案，只能作为不可行基准。

## 3. Model 1：任务架构

### 3.1 候选方案

| 方案 | 说明 | v0.6 判断 |
|---|---|---|
| A | 单发长征十号，40 t 直接 TLI | 不可行 |
| B | 两发长征十号，每发约 20 t，LEO 交会对接后 TLI | 推荐主方案 |
| C | 三发长征十号，每发 20 t，任意两发成功即可 | 可靠性扩展，不作为主方案 |
| D | 40 t 单体载荷先入 LEO，再与推进级/推进剂组合后 TLI | 备选，用于“不可拆分单体”约束 |

### 3.2 两发 LEO 对接组合方案

主方案流程：

```text
Launch 1: CZ-10 sends Cargo Module A + docking/TLI interface to LEO.
Launch 2: CZ-10 sends Cargo Module B + docking/TLI interface to LEO.
LEO phase: A and B perform rendezvous, docking, checkout, and phasing.
TLI phase: the combined logistics stack performs translunar injection.
```

每发模块化方案取：

```text
m_payload_each = 20 t
C_TLI_public = 27 t
m_equivalent_margin_each = C_TLI_public - m_payload_each = 7 t
m_equivalent_margin_total = 14 t
```

这里的余量是“按公开 TLI 运力折算的等效运力余量”，可用于：

- 载荷适配器。
- 对接机构。
- 轨道修正推进剂和接口结构。
- 飞行性能和公开参数不确定性。
- 组合体热控、通信和姿态控制接口。

这一路线借鉴中国载人登月“两枚火箭 + 分飞行器 + 在轨交会对接”的思想，但把对接地点从环月轨道前移到 LEO。原因是本题只要求进入地月转移轨道，LEO 组合后统一 TLI 更便于建模，也更容易保证两个模块进入同一转移轨道。

### 3.3 “40 t 单体载荷 + LEO 组合”是什么意思

这个备选方案用于另一种题意：如果 40 t 不是两包原材料，而是一个不能拆开的 40 t 大件，例如一整个大型居住舱、整套电站或一体化设备，那么“两个 20 t 模块”就不成立。

这种情况下，需要先把 40 t 单体送入 LEO，再用另一发或多发火箭送入 TLI 推进级、推进剂或空间拖船，在 LEO 对接后把这个完整 40 t 单体推入地月转移轨道。它比当前主方案更复杂，因为要解决大单体入轨、推进级连接、在轨加注或多推进级串联等问题。所以 v0.6 只把它作为备选，不作为主线。

## 4. Model 2：地月转移轨道

第一版采用 LEO 停泊后 Hohmann 型 TLI 估算。设：

```text
r1 = R_E + h_LEO
r2 = r_EM
a = (r1 + r2) / 2
```

LEO 圆轨道速度：

```text
v_LEO = sqrt(mu_E / r1)
```

转移椭圆近地点速度：

```text
v_p = sqrt(mu_E * (2/r1 - 1/a))
```

TLI 速度增量：

```text
Delta_v_TLI = v_p - v_LEO
```

转移时间一阶估算：

```text
TOF = pi * sqrt(a^3 / mu_E)
```

在 200-500 km LEO 高度范围内，v0.6 计算得到 TLI 速度增量约为 3.1 km/s，符合地月转移任务的数量级。

v0.6 增加组合体 TLI 质量预算。名义假设为：

```text
delivered cargo = 40 t
adapter and docking mass = 4 t
TLI stage Isp = 450 s
TLI stage structural fraction = 0.08
```

在 300 km LEO、TLI Delta-v 约 3.108 km/s 条件下，所需 TLI 推进剂约 `49.0 t`，TLI 级干质量约 `3.9 t`，LEO 初始组合体约 `96.9 t`，折算每发约 `48.5 t` LEO 湿质量。当前占位上升段模型每发末端质量约 `69 t`，因此保留约 `20.5 t` 建模余量。

## 5. Model 3：可靠性模型

### 5.1 发动机簇可靠性

若不允许发动机失效，且单台发动机关键阶段可靠性为 `r`，发动机数量为 `N`：

```text
R_cluster = r^N
```

若允许最多 `f` 台发动机失效仍能完成任务：

```text
R_cluster = sum_{k=0}^{f} C(N,k) (1-r)^k r^(N-k)
```

本式用于说明 33 台发动机簇对单发动机可靠性非常敏感。注意不能把它等同于完整 Starship 任务可靠性，因为真实系统可能存在发动机失效容错、飞控冗余和不同任务剖面。

### 5.2 多发任务可靠性

设单发长征十号任务成功概率为 `R`。

两发均成功：

```text
P_2 = R^2
```

三发中至少两发成功：

```text
P_3 = C(3,2)R^2(1-R) + R^3
    = 3R^2 - 2R^3
```

当 `R = 0.95`：

```text
P_2 = 0.9025
P_3 = 0.99275
```

三发冗余方案的可靠性更高，但需要多发一枚长征十号，成本和任务组织复杂度更高。按当前题意，v0.6 将两发 LEO 对接方案作为主方案；三发方案只作为可靠性敏感性分析，说明如果评分更强调可靠性而非发射次数，可以怎样扩展。

两发 LEO 对接方案的总可靠性链写为：

```text
R_total = R_launch^2 * R_rendezvous * R_TLI
```

当 `R_launch = 0.95`、`R_rendezvous = 0.98`、`R_TLI = 0.985` 时：

```text
R_total = 0.87118325
```

这里的 `R_rendezvous` 和 `R_TLI` 是敏感性参数，不应写成真实工程统计值。

v0.6 进一步扫描：

```text
R_rendezvous = 0.94 to 0.995
R_TLI = 0.94 to 0.995
```

在 `R_launch = 0.95` 固定时，任务可靠性范围约为 `0.7974` 到 `0.8935`。

## 6. Model 4：发射几何与文昌自转收益

文昌纬度取：

```text
lat = 19.614 deg
```

地球自转线速度：

```text
v_rot = omega_E * R_E * cos(lat)
```

v0.6 计算约为 438 m/s。向东发射时可最大化自转速度收益，这也是选择文昌的重要物理理由。

发射方位角 `A` 与轨道倾角 `i` 的近似关系：

```text
cos(i) ~= cos(lat) * sin(A)
```

其中 `A` 从正北顺时针计。正东发射 `A = 90 deg` 时，最低倾角约等于发射场纬度。

## 7. v0.6 上升段基础仿真

v0.2 新增 `ascent_3dof.py`。当前版本保留二维垂直面内的三自由度代理模型，用于生成第一版曲线和检查量级。v0.3 新增 `ascent_eci.py`，提供 ECI 三维点质点积分、地球自转、大气相对速度和 J2 选项。

状态量：

```text
x = [downrange, altitude, v_horizontal, v_vertical, mass]
```

动力学：

```text
d downrange/dt = v_horizontal
d altitude/dt = v_vertical
dv/dt = a_thrust + a_drag + a_gravity
dm/dt = -T / (Isp * g0)
```

动压：

```text
q = 0.5 * rho(h) * |v_rel|^2
```

程序角沿用空天飞行力学大作业形式：

```text
phi(t) = 90 deg                         0 <= t < t1
phi(t) = smooth decrease                t1 <= t < t2
phi(t) = phi_final                      t2 <= t <= cutoff
```

当前实现包括：

- 分段推力、比冲、推进剂消耗和干质量抛弃。
- 指数/分层大气密度模型。
- 阻力、动压和最大动压输出。
- 文昌向东发射的地球自转初速度。
- 程序角从垂直逐渐转为近水平。

v0.6 粗网格搜索得到的 ECI 程序角候选为：

```text
pitch_end_time = 305 s
final_pitch = 10 deg
shape = 1.4
```

该候选末端高度约 `306.9 km`，惯性速度约 `7.723 km/s`，飞行路径角约 `-0.02 deg`。v0.6 进一步对比球形引力与 J2，引入 J2 后末端高度变化约 `-2.27 km`，末端速度变化约 `+1.37 m/s`。注意：这仍不是最终制导轨迹，只是 v0.6 的数值框架和曲线生成器。

## 8. LEO 交会对接模型

设模块 A 在目标圆轨道 `h_target`，模块 B 进入相邻的相位轨道 `h_phase`。圆轨道平均角速度为：

```text
n = sqrt(mu_E / r^3)
```

相位追赶角速度：

```text
dot(theta_rel) = n_phase - n_target
```

若需要追赶相位角 `theta`：

```text
t_wait = theta / |dot(theta_rel)|
```

从相位圆轨道转入目标圆轨道的一阶速度增量采用两圆轨道 Hohmann 转移估算。v0.6 的 300 km 目标轨道示例中，260 km 相位轨道对应等待时间约 18.5 h，交会与对接速度增量约 43 m/s。

## 9. v0.6 推荐方案

推荐主方案：

```text
Architecture B:
2 Long March 10 launches
20 t cargo module per launch
LEO rendezvous and docking
combined translunar injection
40 t required delivered mass
14 t equivalent aggregate TLI margin
```

论文表达应强调：

- 单发不够，所以不是硬说长征十号“超过 Starship”。
- 原材料天然可模块化，拆分运输合理。
- 两发 LEO 交会对接借鉴了中国载人登月分发射、在轨交会对接的工程路线。
- 三发 2-out-of-3 是可靠性扩展，而不是当前主方案。
- 发动机簇可靠性只作为可调参数模型，不把未公开/未成熟数据写死。
