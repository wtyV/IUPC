# Problem B：Lunar Base Construction 火箭与地月转移任务大纲

> 当前目录确认：`G:\国际大物`。  
> 本文件根据 `docs/notes.md` 中的国际大物题目重写。`docs/2026空天飞行力学-弹道学大作业要求.md` 只作为“物理量、弹道建模、程序角、发射方位角、积分方法、结果图表”的参考，不解决其中的 DF-X 导弹问题。

## 1. 题目重新理解

### 1.1 原题核心

英文题目：

```text
Problem B: Lunar Base Construction: A Heavy-Lift Rocket Design Challenge
With the advancement of lunar exploration programs (China's Chang'e, NASA's Artemis), building a permanent lunar base requires transporting large amounts of raw materials to the Moon. SpaceX's Starship uses 33 clustered engines, but this multi-engine configuration significantly increases launch failure risk. Based on China's current rocket launch capabilities and technological level (such as liftoff mass, mass ratios, thrust, specific impulse and so on), design a rocket launch scheme capable of delivering 40 tons of payload to the Earth-Moon transfer orbit, matching Starship's capacity but with higher reliability.
```

我们要解决的是：

> 基于中国当前和近期公开的重型运载能力，设计一种能够把总计 40 t 载荷送入地月转移轨道的发射方案，并证明它在可靠性上优于 Starship 依赖 33 台 Super Heavy 发动机的单次重型发射思路。

### 1.2 关键判断

公开资料显示，长征十号标准登月构型的地月转移轨道运载能力为“不小于 27 t”。因此：

- 单发长征十号无法直接把 40 t 单体载荷送入地月转移轨道。
- 如果 40 t 是月球基地原材料，则完全可以模块化拆分运输，不必是一个单体。
- 如果题目严格要求“一个 40 t 整体载荷”，则需要先进入 LEO，再通过第二发火箭补充推进级、推进剂或拖船，在轨组合后执行 TLI。
- 如果题目强调“更高可靠性”，最有竞争力的思路不是盲目追求单发最大运力，而是做冗余多发任务架构。

### 1.3 推荐主结论方向

建议论文最终主方案采用：

> 三发长征十号模块化货运方案：每发向地月转移轨道投送约 20 t 标准化月基原材料模块，任意两发成功即可满足 40 t 总交付要求；第三发作为任务级冗余，从而用“2-out-of-3”架构提高任务可靠性。

同时保留两个对照方案：

- 两发长征十号方案：每发约 20 t，刚好满足 40 t，成本更低但无冗余。
- LEO 在轨组合方案：先将 40 t 单体载荷和推进级/推进剂分别送入近地轨道，再组合执行 TLI，适合“必须保持 40 t 单体”的严格解释。

这会让论文非常清楚：不是因为中国单发火箭一定超过 Starship，而是通过合理的任务架构、模块化载荷和冗余发射，在可靠性指标上达到或超过题目要求。

## 2. 火箭选择：长征十号

### 2.1 为什么选择长征十号

本题要求基于中国当前火箭能力和技术水平，并且面向地月转移任务。长征十号是最合适的主火箭：

- 它是中国面向载人月球探测任务研制的新一代载人运载火箭。
- 公开资料明确给出其地月转移轨道运载能力不小于 27 t。
- 它的设计任务就是发射新一代载人飞船和月面着陆器进入地月转移轨道。
- 它比长征五号更贴合“40 t 级月球基地建设物资运输”的题目背景。
- 它相比 Starship 的 33 发动机 Super Heavy 构型，可以在论文中建立“更少发动机簇、更模块化、更冗余”的可靠性对比模型。

### 2.2 长征十号公开参数

| 参数 | 公开值或建模值 | 用途 |
|---|---:|---|
| 火箭名称 | 长征十号 | 主方案火箭 |
| 构型 | 三级半登月构型 | 地月转移任务 |
| 全箭高度 | 约 92.5 m | 尺度和气动参考 |
| 起飞质量 | 约 2189 t | 火箭方程和质量比估算 |
| 起飞推力 | 约 2678 t 量级 | 起飞推重比估算 |
| 地月转移轨道运力 | 不小于 27 t | 判断单发是否可满足 40 t |
| 衍生无助推构型高度 | 约 67 m | 对照构型 |
| 衍生无助推构型起飞质量 | 约 740 t | 对照构型 |
| 衍生无助推构型 LEO 运力 | 不小于 14 t | 不适合作为主方案 |

### 2.3 长征十号状态说明

截至当前资料，长征十号仍处于研制与试验阶段，不应在论文中写成“已经成熟服役”。可以写成：

> We use the publicly released design capability of Long March 10 as the baseline for a near-future Chinese lunar cargo launch architecture.

这比直接说“长征十号已经可以完成该任务”更稳健。

## 3. 发射点选择：文昌航天发射场

### 3.1 推荐选择文昌

文昌航天发射场适合作为本题发射点：

- 纬度低，接近 19°N，可以获得更大的地球自转速度收益。
- 沿海发射，落区安全性和海上运输条件更好。
- 已承担中国重型火箭和探月任务发射。
- 长征十号相关试验也在文昌开展，和题目背景一致。

### 3.2 建模经纬度

第一版可取：

```text
latitude = 19.6 deg N
longitude = 110.95 deg E
altitude = 0 to 100 m
```

如果需要和公开报道一致，也可用北纬 19°19′ 作为文昌纬度近似。精确经纬度对第一版结论影响很小，但对发射方位角和地球自转速度收益分析有用。

### 3.3 地球自转收益

发射点随地球自转的线速度为：

```text
v_rot = omega_E * R_E * cos(latitude)
```

文昌纬度约 19.6°，因此向东发射时可获得约 440 m/s 量级的自转速度分量。这个速度收益会降低入轨所需火箭速度增量，是选择文昌的重要物理理由。

## 4. 总体任务方案

### 4.1 方案 A：单发长征十号直接 TLI

方案描述：

- 一发长征十号从文昌发射。
- 上升段进入近地停泊轨道或直接注入地月转移轨道。
- 载荷目标为 40 t。

判断：

- 公开 TLI 运力不小于 27 t。
- 40 t 超过单发公开能力。
- 因此该方案作为不可行基准，用于证明必须采用多发或在轨组合。

用途：

- 在论文中作为 baseline。
- 说明题目难点不是简单“查火箭参数”，而是要设计任务架构。

### 4.2 方案 B：两发长征十号模块化直接 TLI

方案描述：

- 将 40 t 月基原材料拆分为两个 20 t 级模块。
- 每发长征十号直接把一个模块送入地月转移轨道。
- 两发全部成功后，满足 40 t 总投送要求。

优点：

- 每发载荷 20 t 小于 27 t TLI 运力，留出约 7 t 余量给适配器、轨道修正推进剂和不确定性。
- 不需要复杂的 LEO 对接和在轨加注。
- 载荷是月球基地原材料，本身适合模块化拆分。

缺点：

- 两发都必须成功才能达到 40 t。
- 任务成功概率为 `R_CZ10^2`，如果单发可靠性不够高，则任务级可靠性会下降。

用途：

- 作为最低发射次数的可行方案。
- 和三发冗余方案做成本-可靠性对比。

### 4.3 方案 C：三发长征十号冗余模块化 TLI

方案描述：

- 设计三个标准化货运模块，每个约 20 t。
- 每发长征十号发射一个模块进入地月转移轨道。
- 只要任意两发成功，总交付质量就达到 40 t。
- 第三发成功时，多出的 20 t 成为月球基地建设冗余物资。

优点：

- 任务成功条件从“两发全成”变成“三发中任意两发成功”。
- 对单次发射失败具有容错性。
- 非常适合“原材料”这种可拆分载荷。
- 可以用可靠性公式明确证明任务级可靠性提升。

可靠性公式：

```text
P_success_2_of_3 = C(3,2) * R^2 * (1 - R) + R^3
                 = 3R^2 - 2R^3
```

如果单发长征十号任务可靠性为 `R = 0.95`：

```text
P_success_2_of_3 = 0.99275
```

这比单次重型火箭发射的成功概率更容易形成“高可靠性”论证。当然，真实论文中不要假设 `R = 0.95` 就当真值，而应做 `R = 0.90 到 0.99` 的敏感性分析。

缺点：

- 发射成本更高。
- 总发射次数更多。
- 需要更复杂的任务调度和地月转移窗口设计。

推荐：

- 将方案 C 作为最终推荐方案。
- 将方案 B 作为成本优先方案。
- 将方案 D 作为单体载荷限制下的备选方案。

### 4.4 方案 D：LEO 在轨组合后 TLI

方案描述：

- 一发或多发长征十号先把 40 t 载荷、地月转移推进级、推进剂或拖船送入 LEO。
- 在近地停泊轨道完成对接、组合或推进剂转移。
- 组合体再执行 TLI。

适用场景：

- 如果题目要求“40 t 单体载荷”而不是“总计 40 t 原材料”。
- 如果论文希望比较 Starship 的在轨加注思想和中国多发组装方案。

优点：

- 可以把 40 t 作为一个整体送入地月转移轨道。
- 可以展示更高级的轨道力学和任务架构设计。

缺点：

- 对接、在轨加注、推进级长期停泊都会引入额外风险。
- 可靠性模型更复杂。
- 对竞赛时间和建模工作量要求更高。

建议：

- 作为扩展方案写，不作为第一版主方案。

## 5. 需要优化的问题

### 5.1 火箭方案优化

核心问题：

- 选择两发、三发还是 LEO 在轨组合？
- 每发载荷质量应该取 20 t、22 t、24 t 还是接近 27 t？
- 是否需要保留 TLI 余量？
- 如果以可靠性为主，是否值得多发一枚冗余火箭？
- 如果以成本为主，两发方案是否足够？

优化变量：

| 变量 | 解释 |
|---|---|
| `N_launch` | 发射次数 |
| `m_payload_each` | 每发载荷质量 |
| `m_margin` | 每发 TLI 能力余量 |
| `m_adapter` | 载荷适配器和轨道修正系统质量 |
| `m_total_delivered` | 成功进入地月转移轨道的总质量 |
| `R_launch` | 单发任务可靠性 |
| `R_mission` | 总任务可靠性 |

目标函数：

```text
maximize R_mission
minimize N_launch
minimize total_cost_proxy
maximize delivered_mass_margin
```

推荐结论方向：

- 成本优先：`N_launch = 2`, 每发约 20 t。
- 可靠性优先：`N_launch = 3`, 每发约 20 t，任意两发成功即可满足 40 t。
- 单体载荷优先：LEO 组装或推进级补给。

### 5.2 火箭质量比优化

要优化的问题：

- 40 t 目标下，长征十号每发留多少运力余量最合理？
- 每发载荷越接近 27 t，效率越高，但余量越小，可靠性可能下降。
- 每发载荷降低到 20 t，则可留出轨道修正推进剂、适配器、结构加强和误差余量。

核心指标：

```text
payload_fraction = m_payload / m0
propellant_payload_ratio = m_propellant / m_payload
mass_margin = m_TLI_capacity - m_payload_each
```

可做的图：

- 每发载荷质量 vs 任务成功概率。
- 每发载荷质量 vs 运力余量。
- 发射次数 vs 总投送质量。
- 发射次数 vs 成本代理量。

### 5.3 可靠性优化

题目明确提到 Starship 的 33 发动机簇增加失败风险，所以可靠性必须作为论文重点，而不是只算轨道。

发动机簇可靠性模型：

```text
R_cluster_no_engine_out = r_engine^N
```

其中：

- `r_engine` 为单台发动机点火和工作可靠性。
- `N` 为关键阶段并联发动机数量。

如果允许发动机失效容错：

```text
R_cluster_engine_out =
sum_{k=0}^{f} C(N,k) * (1-r_engine)^k * r_engine^(N-k)
```

其中 `f` 为可容忍失效发动机数。

任务级可靠性模型：

```text
R_two_launch_all_success = R_launch^2
R_three_launch_at_least_two = 3R_launch^2(1-R_launch) + R_launch^3
```

论文应比较：

- Starship 单次重型发射的发动机簇风险。
- 两发长征十号方案的全成功概率。
- 三发长征十号 2-out-of-3 冗余方案的成功概率。
- 在不同 `r_engine` 和 `R_launch` 假设下，结论是否稳定。

注意：

- 不要简单说“发动机越少一定越可靠”。真实可靠性还取决于发动机成熟度、冗余设计、质量控制、地面流程、发射次数和任务架构。
- 应写成“我们建立了一个可调参数的可靠性模型，并在合理假设范围内比较不同方案”。

### 5.4 上升段程序角优化

从大作业中可以借用“程序角”思想，但这里用于运载火箭入轨，不用于导弹射程。

优化目的：

- 减小重力损失。
- 减小气动损失。
- 控制最大动压 `max-Q`。
- 使火箭进入指定 LEO 停泊轨道或满足直接 TLI 注入条件。

程序角模型可设为：

```text
phi(t) = 90 deg,                                  0 <= t < t_vertical
phi(t) = smooth_transition(t),                    t_vertical <= t < t_pitch_end
phi(t) = phi_final or gravity-turn-following,     t_pitch_end <= t < cutoff
```

可优化变量：

| 变量 | 作用 |
|---|---|
| `t_vertical` | 垂直上升时间 |
| `t_pitch_start` | 俯仰转弯开始时间 |
| `t_pitch_end` | 俯仰转弯结束时间 |
| `phi_final` | 主动段后期目标俯仰角 |
| `k1, k2, k3` | 程序角曲线形状参数 |

约束：

```text
q = 0.5 * rho(h) * v_rel^2 <= q_max
altitude_cutoff near target LEO altitude
velocity_cutoff near orbital velocity
flight_path_angle near 0 deg at orbit insertion
```

推荐输出：

- 程序角-时间曲线。
- 高度-时间曲线。
- 速度-时间曲线。
- 动压-时间曲线。
- 质量-时间曲线。
- 入轨误差对程序角参数的敏感性。

### 5.5 发射方位角优化

优化目的：

- 利用地球自转速度收益。
- 获得合适停泊轨道倾角。
- 减少后续 TLI 平面调整代价。
- 保证下落区位于安全海域。

近似关系：

```text
cos(i) ~= cos(latitude) * sin(A0)
```

其中：

- `i` 为入轨倾角。
- `latitude` 为发射场纬度。
- `A0` 为发射方位角，按从北顺时针计。

文昌向东发射时，最低可达轨道倾角约接近发射场纬度，即约 19.6°。如果为了地月转移选择不同轨道面，则需要权衡：

- 向东发射，自转收益最大。
- 偏北或偏南发射，轨道平面更灵活，但速度收益降低。
- 发射窗口会受到月球轨道面和月球相位约束。

推荐输出：

- 发射方位角 vs 入轨倾角。
- 发射方位角 vs 地球自转速度收益。
- 发射方位角 vs TLI 平面变轨代价。
- 不同方位角下的地面轨迹和落区合理性。

### 5.6 地球引力场优化

第一版模型：

```text
g = -mu_E * r / |r|^3
```

高级模型加入 J2：

```text
U = mu_E/r * [1 - J2*(R_E/r)^2*P2(sin(phi))]
```

需要比较：

- 球形地球引力模型。
- WGS84 椭球地球 + J2。
- 可选 J4。

对本题的影响：

- 上升段入轨精度会受 J2 和地球形状影响。
- 地月转移长时间传播中，J2 的影响可能积累。
- 第一版用二体模型足够给出主结论，高级版用 J2 做误差分析更像竞赛高分论文。

### 5.7 大气模型优化

notes 中提到“大气层内选择杨炳蔚的模型”。建议：

- 主模型采用杨炳蔚/教材标准大气模型。
- 对照模型采用国际标准大气或指数大气模型。
- 90 km 以上第一版忽略气动力。

阻力模型：

```text
D = 0.5 * rho(h) * v_rel^2 * C_D * S_ref
a_drag = -D/m * v_rel/|v_rel|
```

其中：

- `v_rel = v_ECI - omega_E x r`，即相对于大气的速度。
- `rho(h)` 来自大气模型。
- `C_D` 第一版可取常数，高级版按马赫数分段。

要分析：

- 大气密度扰动对上升段损失的影响。
- `C_D` 不确定性对最大动压和入轨质量的影响。
- 程序角提前/滞后对气动损失的影响。

### 5.8 地月转移轨道优化

本题目标是把载荷送入 Earth-Moon transfer orbit，通常可理解为 TLI 后进入地月转移轨道，不一定要求近月制动或登月。

可比较三类转移轨道：

| 轨道方案 | 优点 | 缺点 | 是否推荐 |
|---|---|---|---|
| LEO 停泊后 Hohmann 型 TLI | 清晰、易算、工程常见 | 不是最低能量的全部可能 | 主方案 |
| 直接入地月转移轨道 | 少一次停泊轨道建模 | 发射窗口和制导复杂 | 可作为对照 |
| 低能转移/弱稳定边界 | 省燃料潜力 | 飞行时间长、模型复杂 | 高级扩展 |

第一版推荐：

- 先进入 200 km 到 400 km LEO 停泊轨道。
- 等待合适地月相位。
- 在近地点附近执行 TLI。

Hohmann 型估算：

```text
r1 = R_E + h_LEO
r2 = average Earth-Moon distance
a_transfer = (r1 + r2) / 2
v_LEO = sqrt(mu_E / r1)
v_perigee_transfer = sqrt(mu_E * (2/r1 - 1/a_transfer))
Delta_v_TLI = v_perigee_transfer - v_LEO
```

第一版通常会得到 `Delta_v_TLI` 约 3.1 到 3.2 km/s 量级。更高精度模型需要加入月球运动、地月旋转系和中途修正。

需要优化：

- 停泊轨道高度 `h_LEO`。
- TLI 点火时刻。
- TLI 方向。
- 转移飞行时间。
- 月球到达位置误差。
- 是否保留中途修正燃料。

### 5.9 直接 TLI 与先入轨再 TLI 的选择

建议结论：

- 论文主方案采用“先进入 LEO 停泊轨道，再执行 TLI”。
- 理由是它更易建模、更接近工程任务流程，也便于处理多发任务发射窗口。
- 直接 TLI 可作为对照，说明理论上减少停泊时间，但对发射窗口、上升段精度和实时制导要求更高。

比较指标：

| 指标 | 先 LEO 后 TLI | 直接 TLI |
|---|---|---|
| 建模难度 | 中等 | 高 |
| 发射窗口灵活性 | 较好 | 较差 |
| 多发任务协调 | 较好 | 较难 |
| 轨道注入精度 | 易分段控制 | 对上升段要求高 |
| 论文可解释性 | 强 | 中等 |

## 6. 建模框架

### 6.1 总体分层模型

建议按四层建模：

| 层级 | 名称 | 目的 |
|---|---|---|
| Model 0 | 数量级和可行性估算 | 证明单发 CZ-10 不足 40 t，必须多发 |
| Model 1 | 火箭质量和可靠性模型 | 比较 Starship、两发 CZ-10、三发 CZ-10 |
| Model 2 | 上升段三自由度模型 | 计算从文昌到 LEO/TLI 的轨迹和损失 |
| Model 3 | 地月转移模型 | 计算 TLI、转移轨道和任务窗口 |
| Model 4 | 联合优化模型 | 优化载荷、发射次数、程序角、方位角、轨道参数 |

### 6.2 火箭方程模型

对每一级：

```text
Delta_v_i = Isp_i * g0 * ln(m0_i / mf_i)
```

总速度增量：

```text
Delta_v_total = sum(Delta_v_i) - losses
losses = gravity_loss + drag_loss + steering_loss
```

由于长征十号详细分级质量和发动机曲线未完全公开，第一版可以采用：

- 总起飞质量和 TLI 运力作为校准约束。
- 结构系数和比冲作为可调参数。
- 通过“模型结果必须能复现 27 t TLI 运力量级”来反推合理参数范围。

### 6.3 上升段三自由度动力学

状态量：

```text
state = [r_x, r_y, r_z, v_x, v_y, v_z, m]
```

动力学：

```text
dr/dt = v
dv/dt = a_gravity + a_J2 + a_thrust + a_drag
dm/dt = -T / (Isp * g0)
```

初始条件：

```text
r0 = geodetic_to_ECI(latitude, longitude, altitude, time0)
v0 = omega_E x r0
m0 = launch_mass
```

推力方向：

```text
u_thrust = function(pitch_program, launch_azimuth, local_vertical, local_east, local_north)
a_thrust = T(t) / m * u_thrust
```

气动相对速度：

```text
v_rel = v - omega_E x r
```

分级事件：

- 助推器分离。
- 一级关机和分离。
- 二级关机和分离。
- 三级或上面级点火。
- 入轨或 TLI 注入。

第一版可以把分级简化为分段常推力、分段比冲和瞬时干质量抛弃。

### 6.4 地月转移模型

第一版：拼接圆锥模型。

阶段：

- 地球停泊轨道。
- TLI 脉冲机动。
- 地心转移椭圆。
- 月球影响球附近交会。

高级版：

- 地月二体运动，月球绕地运动。
- 地月旋转坐标系。
- 太阳摄动。
- 中途修正 TCM。

输出：

- TLI 所需速度增量。
- 转移时间。
- 月球交会距离误差。
- 到达时相对月球速度。
- 如果扩展到月球轨道插入，再计算 LOI。

### 6.5 任务可靠性模型

任务可靠性由多个部分组成：

```text
R_launch = R_engine_cluster * R_stage * R_guidance * R_separation * R_ground
```

不同任务架构：

```text
R_Starship_single = R_starship
R_CZ10_two = R_CZ10^2
R_CZ10_three_2of3 = 3R_CZ10^2 - 2R_CZ10^3
```

如果要考虑 Starship 33 发动机：

```text
R_SH_cluster = r_Raptor^33
```

如果考虑长征十号发动机簇：

```text
R_CZ_cluster = r_YF^N_CZ
```

注意 `N_CZ` 应作为公开资料和假设共同给出的变量。可以写：

- 官方资料确认长征十号进行了七台发动机并联的一级试验。
- 标准登月构型的完整并联发动机数量可作为公开资料估计值或敏感性参数。
- 可靠性结论主要依赖任务冗余架构，而不是某个未经完全公开的发动机数量。

## 7. 优化算法设计

### 7.1 优化变量汇总

| 类别 | 变量 |
|---|---|
| 任务架构 | 发射次数、每发载荷、冗余策略 |
| 火箭质量 | 结构系数、推进剂质量、载荷适配器质量、TLI 余量 |
| 上升段控制 | 垂直上升时间、俯仰转弯时间、终端俯仰角、程序角曲线参数 |
| 发射几何 | 发射点、发射方位角、发射时间 |
| 近地轨道 | 停泊轨道高度、倾角、等待时间 |
| 地月转移 | TLI 时刻、TLI 方向、飞行时间、中途修正余量 |
| 可靠性 | 单发动机可靠性、单发火箭可靠性、允许失败次数 |

### 7.2 目标函数

可做多目标优化：

```text
maximize R_mission
maximize m_delivered_success
minimize N_launch
minimize total_Delta_v
minimize propellant_payload_ratio
minimize trajectory_error
```

也可做加权目标：

```text
J = w1 * (1 - R_mission)
  + w2 * max(0, 40t - m_delivered_required)^2
  + w3 * N_launch
  + w4 * Delta_v_total
  + w5 * orbit_injection_error
  + w6 * constraint_penalty
```

约束：

```text
m_payload_each <= 27 t - margin
q_max <= q_limit
T/W > 1 at liftoff
LEO insertion error <= tolerance
TLI injection error <= tolerance
launch azimuth within safe range
```

### 7.3 推荐算法

至少使用两种算法，以符合竞赛论文“方法比较”的风格：

| 算法 | 用途 |
|---|---|
| 网格搜索 | 找可行域，直观稳定 |
| Differential Evolution | 全局优化，适合非线性多峰问题 |
| Particle Swarm Optimization | 适合展示群智能优化和 Pareto 结果 |
| Nelder-Mead/Powell | 在全局搜索结果附近局部精修 |
| Monte Carlo | 做可靠性和参数不确定性分析 |

推荐流程：

1. 用网格搜索扫描发射次数、每发载荷和可靠性。
2. 用差分进化优化程序角、发射方位角和停泊轨道高度。
3. 用局部优化精修 TLI 参数。
4. 用蒙特卡洛扰动检查结论稳定性。

## 8. 结果图表清单

必须有的图：

- 长征十号和 Starship 参数对比表。
- 单发 CZ-10、两发 CZ-10、三发 CZ-10 任务架构示意图。
- 单发 TLI 运力与 40 t 需求对比图。
- 两发和三发方案的任务可靠性曲线。
- 单发动机可靠性对发动机簇可靠性的影响图。
- 发射方位角 vs 入轨倾角图。
- 程序角曲线对比图。
- 上升段高度、速度、质量、动压曲线。
- LEO 停泊轨道和 TLI 转移轨道示意图。
- 停泊轨道高度 vs TLI Delta-v 曲线。
- 载荷质量 vs 运力余量曲线。
- 成本代理量 vs 任务可靠性 Pareto 前沿。

建议有的表：

- 公开参数和假设参数表。
- Delta-v budget 表。
- 任务架构对比表。
- 最优方案参数表。
- 敏感性分析表。

## 9. 论文结构建议

UPC/国际大物论文需要英文正式论文风格，题目开放、不唯一，必须有清晰假设、合理引用和强弱点分析。

建议结构：

```text
1. Summary
2. Restatement of the Problem
3. Assumptions and Notation
4. Launch Vehicle Selection: Long March 10
5. Mission Architecture
6. Rocket Performance and Mass Model
7. Ascent Trajectory Model
8. Earth-Moon Transfer Orbit Model
9. Reliability Model
10. Optimization Method
11. Results
12. Sensitivity Analysis
13. Strengths and Weaknesses
14. Conclusion
15. References
16. Appendix
```

摘要必须包含：

- 最终选择长征十号。
- 单发公开 TLI 能力 27 t，不足以单发完成 40 t。
- 提出两发和三发模块化方案。
- 推荐三发 2-out-of-3 冗余方案。
- 给出核心可靠性表达式和主要优化结果。

## 10. 从往年获奖论文借鉴的写法

从公开 UPC 获奖论文和规则可借鉴：

- 摘要直接给关键数字，不写空话。
- 先写 Assumptions and Notations。
- 把复杂任务拆成多个阶段模型。
- 简单模型先给数量级，再用数值模型修正。
- 结果必须有图和表。
- Strengths and Weaknesses 单独成节。
- 附录放代码，正文必须解释算法和物理意义。
- 所有变量单位统一，图轴必须标注单位。

本题应模仿这种叙述：

```text
We first show that a single Long March 10 cannot deliver a 40 t payload to TLI under public capability data. We then propose a modular multi-launch architecture. The main innovation is converting a single-launch heavy-lift requirement into a fault-tolerant logistics problem.
```

## 11. 下一步执行计划

### 第 1 阶段：题目和资料锁定

目标：

- 把英文题目转成可计算目标。
- 把长征十号、Starship、文昌、地月转移的公开数据整理成表。

任务：

- 建立 `docs/problem_definition.md`。
- 建立 `docs/references.md`。
- 建立长征十号参数表。
- 建立 Starship 参数表。
- 明确“40 t 是总物资还是单体载荷”的两种解释。

完成标准：

- 能写出一句清楚的研究问题。
- 能说明为什么单发 CZ-10 不够。
- 能说明为什么模块化多发合理。

### 第 2 阶段：火箭和可靠性一阶模型

目标：

- 不写复杂轨道仿真前，先证明三种方案的优劣。

任务：

- 实现火箭方程估算。
- 实现单发、两发、三发可靠性公式。
- 画可靠性曲线。
- 做载荷拆分扫描。

完成标准：

- 得到方案 A/B/C/D 的对比表。
- 得到推荐主方案。

### 第 3 阶段：上升段动力学

目标：

- 从文昌发射到 LEO 的三自由度仿真。

任务：

- 实现 ECI/ECEF 坐标转换。
- 加入地球自转初速度。
- 加入球形引力和 J2 对照。
- 加入杨炳蔚/标准大气模型。
- 加入阻力、推力、质量消耗、分级。
- 加入程序角控制。

完成标准：

- 输出高度、速度、动压、质量曲线。
- 找到一组可行的入轨程序角参数。
- 给出程序角对入轨误差和损失的影响。

### 第 4 阶段：地月转移轨道

目标：

- 计算 LEO 到地月转移轨道所需 TLI。

任务：

- 先实现 Hohmann 型估算。
- 再实现拼接圆锥传播。
- 加入月球相位和发射窗口。
- 对比停泊轨道高度。

完成标准：

- 有 TLI Delta-v 表。
- 有地月转移轨道图。
- 能说明为什么采用 LEO 停泊后 TLI。

### 第 5 阶段：联合优化

目标：

- 同时优化任务架构、程序角、方位角、停泊轨道和可靠性。

任务：

- 建立目标函数。
- 网格搜索可行域。
- 差分进化或 PSO 全局搜索。
- 局部优化精修。
- 蒙特卡洛敏感性分析。

完成标准：

- 给出最终推荐方案参数。
- 有 Pareto 前沿。
- 有可靠性和运力余量敏感性图。

### 第 6 阶段：英文论文成稿

目标：

- 写成 UPC 风格英文论文。

任务：

- 写 300 word summary。
- 写 assumptions and notation。
- 写模型和公式。
- 整理图表。
- 写 strengths and weaknesses。
- 写 AI use report，如果比赛规则要求。

完成标准：

- 论文中每个结论都有公式、数据或图表支持。
- 所有引用有来源。
- 没有把假设当事实。

## 12. 多智能体分工计划

后续可以把任务拆给多个 agent，注意每个 agent 负责独立文件，避免互相覆盖。

### Agent A：题目解析与资料组

职责：

- 精读 `docs/notes.md`。
- 整理题目目标、约束、关键词和评分点。
- 整理长征十号、Starship、文昌、NASA 轨道资料、UPC 规则和获奖论文。

交付：

- `docs/problem_definition.md`
- `docs/references.md`
- `docs/source_notes.md`

### Agent B：火箭参数与质量模型组

职责：

- 建立长征十号参数模型。
- 用火箭方程做 Delta-v 和质量比估算。
- 建立每发载荷和运力余量模型。

交付：

- `src/rocket_long_march_10.py`
- `results/tables/rocket_parameters.csv`
- `results/figures/payload_margin.png`

### Agent C：可靠性模型组

职责：

- 建立发动机簇可靠性模型。
- 比较 Starship、两发 CZ-10、三发 CZ-10。
- 做单发动机可靠性和单发火箭可靠性的敏感性分析。

交付：

- `src/reliability.py`
- `results/tables/reliability_summary.csv`
- `results/figures/reliability_comparison.png`

### Agent D：上升段动力学组

职责：

- 实现文昌到 LEO 的三自由度上升段仿真。
- 实现程序角、发射方位角、大气阻力、地球自转和 J2。

交付：

- `src/ascent_3dof.py`
- `src/atmosphere.py`
- `src/frames.py`
- `results/trajectories/ascent_baseline.csv`

### Agent E：地月转移轨道组

职责：

- 实现 LEO 到 TLI 的 Hohmann 型估算。
- 实现拼接圆锥模型。
- 输出转移轨道图和 Delta-v 表。

交付：

- `src/lunar_transfer.py`
- `results/tables/delta_v_budget.csv`
- `results/figures/earth_moon_transfer.png`

### Agent F：优化算法组

职责：

- 建立联合目标函数。
- 实现网格搜索、差分进化、PSO 或局部优化。
- 输出最优方案和 Pareto 前沿。

交付：

- `src/objectives.py`
- `src/optimize.py`
- `results/tables/optimization_summary.csv`
- `results/figures/pareto_front.png`

### Agent G：论文写作组

职责：

- 把模型、图表和结论整合成英文论文。
- 写摘要、假设、强弱点和结论。
- 统一图表编号、符号和引用。

交付：

- `report/paper.md`
- `report/paper.tex`
- `report/figures/*`

### Agent H：审查与复现实验组

职责：

- 检查公式单位。
- 检查每张图是否能复现。
- 检查引用是否可靠。
- 检查结论是否超过假设。

交付：

- `docs/review_checklist.md`
- `results/tables/sensitivity_summary.csv`

## 13. 推荐第一版代码目录

```text
G:\国际大物
├── docs
│   ├── notes.md
│   ├── menu.md
│   ├── problem_definition.md
│   └── references.md
├── src
│   ├── constants.py
│   ├── rocket_long_march_10.py
│   ├── reliability.py
│   ├── atmosphere.py
│   ├── frames.py
│   ├── ascent_3dof.py
│   ├── lunar_transfer.py
│   ├── objectives.py
│   ├── optimize.py
│   └── plot_results.py
├── results
│   ├── figures
│   ├── tables
│   └── trajectories
└── report
    ├── paper.md
    └── paper.tex
```

## 14. 第一版最终推荐结论模板

后续论文可以向这个结论靠拢：

```text
Based on public Long March 10 capability, a single launch cannot deliver a 40 t payload to an Earth-Moon transfer orbit because the released TLI capability is no less than 27 t. Since lunar base raw materials are naturally modular, we propose a three-launch Long March 10 architecture, with each launch carrying an approximately 20 t cargo module to TLI. Any two successful launches satisfy the 40 t requirement, while a third successful launch provides additional construction margin. Compared with a single heavy-lift Starship-style launch relying on a 33-engine booster, the proposed architecture shifts the problem from single-launch maximum capacity to fault-tolerant logistics. A reliability model shows that the 2-out-of-3 architecture can achieve higher mission success probability over a broad range of reasonable launch reliability assumptions.
```

## 15. 主要风险

- 长征十号详细分级质量和发动机参数未完全公开。
- 长征十号尚处于研制试验阶段，公开能力是设计能力，不是长期飞行统计。
- Starship 也处于发展过程中，可靠性不能只由发动机数量判断。
- 40 t 如果被解释为单体载荷，则模块化方案需要额外论证。
- 真实地月转移窗口和星历比 Hohmann 近似复杂。
- 在轨组合或推进剂转移会引入额外故障模式。

## 16. 资料来源

长征十号和中国载人月球任务：

- 中国载人航天工程网，2026-02-11，长征十号运载火箭系统低空演示验证与梦舟载人飞船系统最大动压逃逸飞行试验成功实施  
  https://www.cmse.gov.cn/xwzx/202602/t20260211_57264.html
- 中国载人航天工程网，2025-09-12，长征十号第二次系留点火试验取得圆满成功  
  https://www.cmse.gov.cn/xwzx/202509/t20250912_56855.html
- 中国政府网英文版/Xinhua，2024-06-15，Long March-10 约 92.5 m、约 2189 t、约 2678 t 推力、TLI 运力不小于 27 t  
  https://english.www.gov.cn/news/202406/15/content_WS666ccf85c6d0868f4e8e823e.html

Starship 参考：

- SpaceX Starship 官方页面，Super Heavy 33 台 Raptor 发动机、100 到 150 t LEO 载荷目标  
  https://www.spacex.com/vehicles/starship/

发射、转移轨道和任务窗口：

- NASA Basics of Space Flight, Chapter 4: Trajectories  
  https://science.nasa.gov/learn/basics-of-space-flight/chapter4-1/
- NASA Basics of Space Flight, Chapter 14: Launch  
  https://science.nasa.gov/learn/basics-of-space-flight/chapter14-1/

UPC/国际大物论文规则和风格：

- University Physics Competition Contest Rules  
  https://www.uphysicsc.com/contestrules.html
- UPC 2020 Gold Medal Paper: Ion Thrusters to Saturn  
  https://www.uphysicsc.com/2020-GM-A-340.pdf
- UPC 2017 Gold Medal Paper: Solar Sailing to Mars  
  https://www.uphysicsc.com/2017-GM-A-699.pdf
