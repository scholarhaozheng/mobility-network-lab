<a id="document-top"></a>

MOBILITY COMPUTATION LAB / STATIC CITY RECORD

# Chicago

A five-zone Jane Byrne/West Loop morning HBW case with 20 positive vehicle OD pairs and three recorded Frank–Wolfe updates.

The figures show saved method results, physical-flow maps and original-unit diagnostics. Drawing these figures invokes no optimizer.

<a id="chicago-late-status-20261008"></a>

<a id="gap-20261008"></a>

## Latest received evidence · 8 October 2026

Current accepted results preserve each frozen model, demand instance and numerical unit. The figures below read the received public evidence without additional optimization.

<dl class="accepted-method-notes"><dt>Own pool grows from 128 to 182 paths: 26 feasibility rounds plus 10 bound/price iterations. Lower 239.1173646810 and feasible upper 241.2268172335 PCE·min give a 0.8744685% gap, passing the original 1% gate.</dt><dd>This independently named post-diagnostic hybrid is newly accepted.</dd><dt>B has six saved iteration records and an accepted original-space endpoint. Native80 reaches the original gates after three outer solves.</dt><dd>Native80 retains 20 major plus 80 uncompressed minor coordinates, U=I80; it demonstrates no compression advantage. Original rank26/52 representations still fail their full-gap gates.</dd><dt>ACS/TIGER area allocation estimates 51,874.133727 households for the original five zones.</dt><dd>This is an engineering allocation, not a model-zone observed count; the old generation model did not consume this field and the original four stages were not rerun.</dd></dl>

[Homepage city cards](<../index.html?atlas-view=full#chicago>) · [Figure guide and saved-state interpretation](<../figure-update-status.html#top>) · [Earlier frozen chapters and history](<#gap-earlier-cutoff>)

### Received figure evidence

<a id="figure-gap-c06-households-gap"></a>

##### Household allocation to the five model zones

[![Household allocation to the five model zones](<../assets/figure-contract-r11/figures/chicago/chi-household-allocation.svg>)](<../assets/figure-contract-r11/figures/chicago/chi-household-allocation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The five estimates total 51,874.133727 households. ACS tract totals are allocated by area; these are not observed model-zone counts or confidence intervals. Original population, demand inputs and S/T results are unchanged. The approved original retains the zone-location map; this derivative uses only public aggregate values. Frozen Jane Byrne S20/T4 engineering scenarios. LR is a new self-priced recovery hybrid; Native80 is uncompressed. Household figure is ACS/TIGER area allocation not used by old generation. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright; U.S. Census ACS/TIGER.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/chi-household-allocation.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/chi-household-allocation.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chi-household-allocation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/chi-household-allocation.source.json>)

<a id="figure-gap-c06-lr-self-pool-gap"></a>

##### New LR hybrid: own-pool feasibility and certified bounds

[![Own-pool feasibility recovery](<../assets/figure-contract-r11/figures/chicago/chi-lr-feasibility.svg>)](<../assets/figure-contract-r11/figures/chicago/chi-lr-feasibility.svg>)

Own-pool feasibility recovery

<details markdown="1">
<summary>Description, units and scope</summary>

These are the hybrid’s 26 own-pool feasibility rounds. They precede the separate 10 original-cost iterations; they are not 36 equivalent subgradient steps. Frozen Jane Byrne S20/T4 engineering scenarios. LR is a new self-priced recovery hybrid; Native80 is uncompressed. Household figure is ACS/TIGER area allocation not used by old generation. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright; U.S. Census ACS/TIGER.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/chi-lr-feasibility.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/chi-lr-feasibility.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chi-lr-feasibility.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/chi-lr-feasibility.source.json>)

[![Lagrangian bounds and own recovery](<../assets/figure-contract-r11/figures/chicago/chi-lr-bounds.svg>)](<../assets/figure-contract-r11/figures/chicago/chi-lr-bounds.svg>)

Lagrangian bounds and own recovery

<details markdown="1">
<summary>Description, units and scope</summary>

All 10 original-cost iterations are retained. At the independently checked endpoint, lower=239.1173646810 and upper=241.2268172335 PCE·min. Recovery uses the hybrid’s own path pool; the bounds do not relabel the earlier pure LR result. Frozen Jane Byrne S20/T4 engineering scenarios. LR is a new self-priced recovery hybrid; Native80 is uncompressed. Household figure is ACS/TIGER area allocation not used by old generation. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright; U.S. Census ACS/TIGER.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/chi-lr-bounds.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/chi-lr-bounds.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chi-lr-bounds.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/chi-lr-bounds.source.json>)

[![Lagrangian certificate gap](<../assets/figure-contract-r11/figures/chicago/chi-lr-certificate.svg>)](<../assets/figure-contract-r11/figures/chicago/chi-lr-certificate.svg>)

Lagrangian certificate gap

<details markdown="1">
<summary>Description, units and scope</summary>

Gap is (own feasible upper−full-graph lower)/max(1,|own feasible upper|). The 10 saved original-cost points end at 0.8744685%. The named hybrid is accepted at its original gate. Frozen Jane Byrne S20/T4 engineering scenarios. LR is a new self-priced recovery hybrid; Native80 is uncompressed. Household figure is ACS/TIGER area allocation not used by old generation. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright; U.S. Census ACS/TIGER.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/chi-lr-certificate.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/chi-lr-certificate.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chi-lr-certificate.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/chi-lr-certificate.source.json>)

<a id="figure-private-chicago-native-history"></a>

##### Native80: all three saved outer iterations

[![Native80: all three saved outer iterations](<../assets/private-native-history-20261008/chicago/native-complete-history.svg>)](<../assets/private-native-history-20261008/chicago/native-complete-history.svg>)

One accepted Chicago S20 run, not three separate experiments: 20 OD, 100 input paths and 80 uncompressed minor coordinates (U = I80). All three existing outer states are plotted at their actual indices 1–3. The original Beckmann objective increases as the early OD deficit is removed; the negative early signed gap is not a better feasible solution. The saved per-OD gate is |r\_i| ≤ 10⁻⁶ + 10⁻⁸ max(1, q\_i), alongside the displayed relative OD-L1 gate. Maximum per-OD residuals are 0.716124, 1.32514×10⁻⁵ and 1.78858×10⁻¹⁰ PCE/hour. The third state passes the complete frozen checks. These are the saved controller checks; the separately released independent final replay reports objective 5601.461468294976 and gap 1.4899811815539771×10⁻¹², agreeing at numerical precision. The first two states are part of this accepted run’s full history, not discarded failed trials. PRIVATE PREVIEW: the numerical history comes from the existing private Full run; the public released increment contains its endpoint only. No solver was run.

[SVG](<../assets/private-native-history-20261008/chicago/native-complete-history.svg>) · [PNG](<../assets/private-native-history-20261008/chicago/native-complete-history.png>) · [PDF](<../assets/private-native-history-20261008/chicago/native-complete-history.pdf>) · [Plot data](<../assets/private-native-history-20261008/chicago/native-complete-history.plot.json>) · [Source and access](<../assets/private-native-history-20261008/chicago/native-complete-history.source.json>) · [Caption](<../assets/private-native-history-20261008/chicago/native-complete-history.caption.md>)

<a id="figure-gap-c06-native-b-increment"></a>

##### Algorithm B and Native80: separate accepted S20 methods

<a id="table-r11-chi-native-endpoints"></a>

###### Algorithm B: full-graph gap

[![Algorithm B: full-graph gap](<../assets/figure-contract-r11/figures/chicago/chi-algorithm-b-gap.svg>)](<../assets/figure-contract-r11/figures/chicago/chi-algorithm-b-gap.svg>)

The 6 recorded Algorithm B iterations end at an independently recomputed 1.5807459e−9 full-graph relative gap. The original 1e−5 gate is unchanged. Its approved source PNG retains a flow map; map coordinates are not included in the public plot data and are not reconstructed here. Frozen Jane Byrne S20/T4 engineering scenarios. LR is a new self-priced recovery hybrid; Native80 is uncompressed. Household figure is ACS/TIGER area allocation not used by old generation. © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright; U.S. Census ACS/TIGER.

[SVG](<../assets/figure-contract-r11/figures/chicago/chi-algorithm-b-gap.svg>) · [PNG](<../assets/figure-contract-r11/figures/chicago/chi-algorithm-b-gap.png>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chi-algorithm-b-gap.pdf>) · [Source data](<../assets/figure-contract-r11/figures/chicago/chi-algorithm-b-gap.source.json>)

###### Native80: accepted original-coordinate endpoint

[![Native80: accepted original-coordinate endpoint](<../assets/figure-contract-r12/figures/chicago/chicago-native80-endpoint.svg>)](<../assets/figure-contract-r12/figures/chicago/chicago-native80-endpoint.svg>)

The accepted Native80 endpoint uses the full uncompressed 80-dimensional minor representation (U=I80), with 20 major paths; no compression advantage is claimed. Its checked objective is 5601.461468294976 PCE·min/h. The three panels show the actual full-graph gap, original-OD residual and link-reconstruction residual with their own units. Each is a single method endpoint, not an iteration trajectory. Public accepted data do not include this method’s complete physical-flow vector, so no flow map is inferred from FW or another representation.

[SVG](<../assets/figure-contract-r12/figures/chicago/chicago-native80-endpoint.svg>) · [PNG](<../assets/figure-contract-r12/figures/chicago/chicago-native80-endpoint.png>) · [PDF](<../assets/figure-contract-r12/figures/chicago/chicago-native80-endpoint.pdf>) · [Source data](<../assets/figure-contract-r12/figures/chicago/chicago-native80-endpoint.source.json>)

<a id="gap-notice-chicago-238ee8f602"></a>

### Source and scope notice

Frozen Jane Byrne S20/T4 engineering scenarios. The LR method uses self-priced recovery; Native80 is uncompressed. Household allocation uses ACS/TIGER geography and was not used by the original generation model. © OpenStreetMap contributors; road-derived data ODbL 1.0: https://www.openstreetmap.org/copyright; U.S. Census ACS/TIGER.

### Complete approved source chapters

The following chapters are retained in full, including numerical tables and historical source-time statements. Their figures link to the same figure anchors above.

<details id="gap-source-volume-gap-appendix-s0" markdown="1">
<summary>Approved source chapter — VOLUME_GAP_APPENDIX_S0.md</summary>

Reading edition of the approved source, SHA-256 af017e15d54a1806f8fe5f604a53286990f552abe73dd963800a22932664a8da . Download original source text . The linked original preserves the complete source record; this reading edition displays accepted results.

### Chicago Jane Byrne / West Loop：可行性证书与输入缺口补充章

交付章节：数值事实以本章所列独立回执为准。

研究地点是 Jane Byrne / West Loop 的原五分区，科学实例保持 S20 和 T4。现有四阶段结果保留原输入身份。新的 LR 混合方法与 Native80 表示属于查看该实例诊断后登记的 post-diagnostic 实验，其方法身份分别说明。

#### 1. 本轮新增了哪些可核验结果

| 项目 | 实际结果 | 结论范围 |
| --- | --- | --- |
| 官方住户／已占住房 | 原五区约 51,874.13372714 户；官方表与几何独立重算通过 | 面积分摊的工程估计；原人口和四阶段依赖未改 |
| LR 自有路径池新混合候选 | 上界 241.2268172335、下界 239.1173646810 PCE·min；间隙 0.8744685% | 通过原 1% 证书门；不是原次梯度 LR 被追认成功 |
| Native 输入路径完整 80 维新表示 | full gap 1.489981182e-12；最大 OD 误差 1.788578174e-10 PCE/h | 新表示通过原门；不声称压缩优势 |
| 公共 Algorithm B，同一 S20 | full gap 1.580745907e-09；Beckmann 目标 5601.4614682869 | 公共冻结实现、无损 ID 适配，原空间独立通过 |
| 新 D 输入账目 | 20 OD、12 个五分钟 bin、240 行，总量 1754.94825124 PCE | 只完成输入账目，公共 D 引擎尚待接入 |

新增 LR 混合候选、Native80 与 S20 Algorithm B 已由 S0 按精确 Full 和保存态接收。此处图文由本批 S0 清单逐资产放行，网页由 A 接入；本轮没有修改 A、其他城市或旧交付。原有 61 项 INCLUDE\_WITH\_NOTICE 与 15 项 PRIVATE\_RESEARCH\_ONLY 决策保持，不因新一轮核验而重新撤销。

#### 2. 三种不能混用的模型身份

S20 是静态、单类 BPR／Beckmann 分配，原图为 27,129 条有向道路边和 15,133 个节点。全部 20 个正车辆 OD 的一小时总量为 1754.948251239727 PCE。核心输入签名为 `626bf2dc8bfc27d9b82d3f48b1a8bbbcea1f977d81aad662139672f313dac614`。新 Native 与 Algorithm B 均使用此图和此需求。Stage 3 已经完成车辆占用率及 PCE 换算，求解前没有再次换算。按静态流率口径，S20 的 Beckmann 积分单位为（PCE/h）·min；它与下述 T4 脉冲费用的 PCE·min 口径分开记账。

T4 是固定费用、共享硬容量的有限时间图：4 个事前选择 OD、总脉冲 66.53295454563035 PCE、dt=30 s、H=169，共 1,351,628 条弧和 490,223 个节点。它保留原 q\_hour/12 的首个五分钟脉冲和终端账本连接语义，签名为 6e4fa0f4202317139e9ea6a159dd7bfddd7b15925a0cdbd6858cfa35ed6df706 。LR 和 CG 的本章结果属于这个 T4，目标单位为 PCE·min。将其数值与 S20 的一小时 Beckmann 积分直接排序没有科学意义。

新的 D 账目覆盖全部 S20 一小时需求，把每个 OD 的小时量均分到 12 个时间段。每段放入 q\_hour/12，12 段累计仍为 q\_hour。候选服务率按原小时容量除以 3600，自由流延迟按分钟乘 60。均匀释放与这种供给换算是明确的工程假设；尚无动态加载、FIFO／队列检验或 DUE 结果。T4 的优化 PASS 不能替代 D 的计算。

#### 3. 官方住户字段：增加输入证据，不重复计算旧四阶段

新增住户修订使用 Census ACS 2019–2023 五年期的 B11001 总住户和 B25003 已占住房字段，以及 2023 TIGER/Line 普查区边界。使用官方全国表文件，再筛选 Cook County 的 1,332 个普查区；实际与模型范围相交的为 30 个普查区、54 条“普查区—模型区”权重。

官方 TIGER 的 `.prj` 声明 NAD83／EPSG:4269；模型区沿原 WGS84 经纬度口径保留。当前固定 pyproj 运行环境中，原脚本的经纬度投影入口与按官方 NAD83 声明建立的入口展开为同一条 PROJ pipeline，三点坐标控制也完全一致，证据保存在 `CRS_METADATA_CONTROL.json`。这不表示两种地理基准在所有地区或运行环境中恒等。对普查区 t 和模型区 z，权重为 EPSG:26916 下的交叠面积除以该完整普查区面积，估计户数为各普查区官方户数乘该权重后的和。没有把裁剪后的一小块重新归一化成整个普查区，也没有把缺失或 Census sentinel 改成零。源普查区 MOE 逐项保留；本轮未在缺乏误差协方差信息的情况下构造模型分区置信区间。

五区估计分别为：8 区 8,941.13228966 户，24 区 3,708.37570269 户，28 区 24,955.52722450 户，32 区 12,604.09095983 户，33 区 1,665.00755046 户。所选普查区的两项官方总量一致，输出同时保存 households 与 occupied\_housing\_units。独立检查重新解析全国原始表和官方边界 ZIP，核对几何、权重、覆盖、源 MOE 及最终分区汇总，没有只检查生产者已经筛好的 JSON。

这些户数依赖区内均匀分布假设，不能称为五个模型区实测户数。保留的小数用于复现面积分摊，不表示官方统计精度或估计误差因计算而改善。原人口分摊方法和统计支持域也与本次户数分摊不完全相同，因此不能直接把二者比值解释为当地实测家庭规模。原人口总量 73,375.24195493403 保持。读取原产生配置后，实际依赖是 population 和 active\_license\_weight，households 并未参与该模型，故 `affected_stages=[]`，未为增加这个字段重跑已接受的产生、分布、方式或分配。

[原五分区住户字段补充](<#figure-gap-c06-households-gap>)

来源：[ACS B11001 官方表](<https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-b11001.dat>)、[ACS B25003 官方表](<https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-b25003.dat>)、[TIGER/Line 2023 Illinois tract](<https://www2.census.gov/geo/tiger/TIGER2023/TRACT/tl_2023_17_tract.zip>)。实际源字节、下载记录、空间权重和独立回执均随 Private Full 保存。

#### 4. 人口、活动、人员 OD 与车辆 OD 的查询链

本轮提供可运行的 `lineage_cli.py`，从原配置、人口分摊、产生表、分布矩阵、方式成本和车辆换算一直追踪到 S20 与 T4。全 20 OD 查询和 28→32 单 OD 查询均已实际通过，非法起点则返回 INVALID\_INPUT。检查重新演算产生率、吸引权重、OD 边际、广义费用和方式概率，并保留原 IPF 的正确归一化分母；它不是仅把输入文件名串联起来的目录索引。

原配置产生量为 10272.533873690763 人次，进入区际分布的量为 2835.2193491386506 人次。原方式与 occupancy/PCE 换算得到 S20 的 1754.948251239727 PCE/h；T4 再依据原选择和 q\_hour/12 规则得到 66.53295454563035 PCE。查询明确列出子实例未代表的量，保持“产生量、区际人员 OD、分方式人员量、车辆 PCE 和时间子实例”之间的差别。

GPS 或照片没有参与这些产生率、重力分布或方式参数的标定。新住户字段也尚未成为实际消费字段。E 的服务日 GTFS 成本到位后，才另立 `CH_MODE_TRANSIT_EXTENSION`；已列出 20 OD 成本请求和合法乘车、接驳、换乘、票价、服务日期等所需字段。当前空白请求字段不是可用公交成本，更不是零成本公交。计划中的受影响阶段为方式选择和随后的分配，原 S20/T4 算法比较仍冻结。

#### 5. CG 已有证书的接收与参照边界

CG 的 425 列、268 轮保存状态已由 S0 的同 Full 独立接收回执接受。其自身可行原始目标为 241.2185242449435 PCE·min，对偶目标与之在数值精度内一致，并有逐 commodity 的完整图定价闭合。本轮复用这份更晚的接收事实；没有按旧矩阵的资料日期把 CG 重新降为未接收，也没有重复优化已成功的方法。

该数值只作为独立端点评价参照。LR 的初值、修复、路径池、价格和停止规则均未读取 CG 解或目标。 CG\_EXTERNAL\_REFERENCE.json 保存来源报告 SHA、允许用途以及旧公开决策的保留情况。

#### 6. LR：先查自有池阻塞，再建立可行上下界

新候选明确命名为“LR 自有可行性定价与受限恢复对偶锚点混合方法”。第一阶段用自身受限恢复的可行性价格生成路径；人工量清零后，再按原费用做完整图拉格朗日定价，并把当前价格向同一自有池恢复 LP 的容量对偶价格混合一半。它含有受限主问题对偶反馈，不能称为冻结投影次梯度 LR 原样通过。所有新增列均由该候选自己的定价产生，没有外部 CG 列或构造 witness 输入。

对非负容量价格 λ，下界按 L(λ)=Σ\_k q\_k·SP\_k(c+λ)−Σ\_a u\_aλ\_a 重算。可行上界必须来自满足原 OD 和共享容量的自有路径流，证书为 (U−L)/max(1,|U|)。人工可行性价格不作为原费用下界；current\_priced、best\_bound\_price、recovery\_dual\_anchor 和 postupdate\_unpriced 分开保存。有符号差值未被裁剪成零。

本候选实际完成 26 次可行性恢复与 10 次原费用迭代，总共 36 次受限 LP；由原 128 条扩充到 182 条，新增 54 条。独立检查从原 1,351,628 弧 CSV 图重新计算最优价格和当前价格的最短费用下界，展开所有正流路径并复核原图合法性、OD、非负和共享容量。得到 U=241.2268172335、L=239.1173646810 PCE·min，证书 0.8744685%，OD 与容量误差均为 0，满足原 1% 门。

历史生成核验覆盖每条新路径的合法性、实际价格快照和价格下的路径费用；独立完整图最短路证书针对端点 current/best 两套价格计算。本章不把这一范围扩大为独立重跑了所有历史定价调用。

[LR 自有路径池的实际恢复与上下界](<#figure-gap-c06-lr-self-pool-gap>)

#### 7. Native80：完整输入路径坐标表示

检查原程序发现，Native 用 OD 增广拉格朗日项逼近守恒，原实现没有硬 OD 等式。本轮固定表示数值控制将 v=B1ᵀx1+Dθ 精确代入目标，保留非负 link 约束、minor Uθ≥0、原 OD ALM、γ=0 和相同 λ/rho 更新；没有悄悄添加硬 OD 约束。通用小例在非零 OD 残差下比较了原目标与代入目标及解析梯度，均通过。

Native80 使用 NATIVE\_L3\_INPUT\_PATH\_IDENTITY80 ：保留原 K5 的 100 条输入成本路径和 20 major／80 minor 分割，令 U=I80，D=A\_minor，M=C\_minor，初值来自原输入成本 seed，λ0=0、rho0=10。该构造仅依赖输入路径，不读取 FW、finite、CG 的状态。80 维已是不压缩的完整 minor 坐标，本章不据此声称压缩优势。

候选 2 的三次实际外层求解依次消除 OD 残差。第一轮和第二轮的有符号 full gap 分别约 −0.0062460 和 −4.57e-8，但守恒尚未通过；这些负数保留原值，未据此提前认定成功。第三轮才同时满足全部原门。独立原图检查得到目标 5601.4614682950、全图间隙 1.489981182e-12、最大 OD 误差 1.788578174e-10 PCE/h，以及 link 重构误差 1.136868377e-13 PCE/h。

#### 8. 公共 Algorithm B 的同实例对照

复用公共已接受的 tap-b Algorithm B 执行器及精度输出兼容差异，二进制 SHA 为 `c421c48200c033a8c37bf570ee7d1198bbb4689e2961dee61ae41f8d58f7ee1f`。原字符串节点 ID 经双射映射到整数后交给公共接口；独立检查逐边逐字段比较容量、自由流分钟、BPR α/β 和全部 OD 的双精度值，确认无新增、删除或合并道路，无需求改变。first\_thru\_node=1 保持全部节点的物理通行语义。

这个适配是本任务的无损转换，不是已经证明官方 TAPLab Chicago 转换器逐字节对齐。公共 B 的求解参数保持冻结，并额外要求 Chicago 原 full-gap 1e-5 门。执行器实际返回 23 条正路径和 6 条迭代记录。原空间重算目标为 5601.4614682869，有符号相对间隙为 1.580745907e-09；最大 OD 误差 1.136868377e-13，路径展开与 link 流差异 4.547473509e-13。公共检查的路径／弧费用松弛、原点支持无环和守恒等附加门也全部通过。

Algorithm B 与 Native80 的已接受结果

#### 11. 尚待外部接口的边界与交付方式

已对已知 E 工作／交付目录检查服务日 GTFS 成本和 D 接口；本轮尚未取得可消费的 Chicago 服务日公交成本或公共动态加载核心。20 OD 请求、依赖范围和 D 输入账目已经实做并独立核对，保留等待接口的明确状态。历史 2011 轨迹和 2024 照片没有 same-ramp 记录，旧 GPS／照片／TemplateFit 工作保持暂停；受限新观测和映射仍由 E 提供。没有相机点反推物体坐标、异地照片替代或新日期 restriction 回写原 S/T。

本章、新图、plot\_data、source、单位、源码、策略、输入、实际状态和独立回执随交付整理。Private Full 保存完整科学复现依赖；轻量 ChatGPT Upload 明确列出未携带的大状态；Volume Handoff 只提供向既有城市长文追加的材料。最终 Full 的只读回放在中文且含空格的路径执行，输出写到输入树之外，前后成员 SHA 必须一致。实际回放收据与归档 bytes/SHA 是交付是否完成的依据。最终 ZIP 冻结后产生的两次回放收据写在包外，并随轻量上传包和大卷交接包提供，均绑定所测 Full ZIP 的 SHA；两次 Full 只读回放最终均 PASS，精确归档身份见本批 S0 接收清单。

</details>

<a id="gap-earlier-cutoff"></a>

Original four-stage chapters retain their original demand, input identity and engineering assumptions.

**Private presentation preview.** Saved result verified; R3 fresh solve verified; All six negative controls rejected

Input snapshot: `mcl_s0_to_v_presentation_inputs_r3_v1@2026-10-05T03:57:54.309662+00:00`. Input version: `chicago_jane_byrne_west_loop_2023resident_2026activity_hbw_am; frozen configuration SHA-256 e8fff06e035b36e2fb4ec257416154c4895d083f75a753baff8fb1a2e5a20fae`.

<a id="scope"></a>

## Scope and model instance

Chicago here means the Jane Byrne interchange and West Loop study rectangle, bounded by −87.670 to −87.625 longitude and 41.864 to 41.893 latitude. Its projected area is 12.023 km² in EPSG:26916. Five clipped community-area fragments provide zones for a resident-origin HBW scenario in the weekday 08:00–09:00 local hour.

This georeferenced street case is distinct from Chicago Sketch, Chicago Regional and the earlier Traffic Assignment Lab teaching display. It neither reruns TemplateFit nor certifies diamond layouts, UTDFX output or lane movements. The local Sketch files contain 933 nodes, 2,950 directed links and 387 centroid nodes; Regional has 12,982 nodes, 39,018 links and 1,790 centroids. Those demand-bearing benchmarks were checked against their TNTP metadata, but their audited conversion did not certify street geometry or CRS. Their IDs are therefore not forced onto this OSM map.

A Dan Ryan/Stevenson alternative was considered through a bounded source-count query returning 10,349 highway ways, including 167 with \_link tags. Jane Byrne/West Loop was chosen for the detailed case because the acquired roads, interchange objects, stop tags and official zones provided a workable bounded input. The alternative remains a source inventory, not a second processed or assigned network.

<a id="inputs"></a>

## Inputs and preparation

<a id="coverage-row-01"></a>

<a id="coverage-row-02"></a>

<a id="coverage-row-03"></a>

The source query records the OSM database at 4 October 2026, 18:24:21 UTC. Ways are split along their original node sequences and clipped to the rectangle; synthetic edge terminals are specific to each way. Shared node identity creates a junction, whereas crossing lines in a two-dimensional view do not. Source way/segment IDs, WGS84 geometry, access, direction, bridge/tunnel and layer fields remain traceable.

The full clipped compilation contains 95,225 directed GMNS links built from 52,014 physical node-pair segments and 40,990 nodes. It retains 146 undirected components, with 40,080 nodes in the largest. The auto graph has 924 strong components, the largest containing 15,154 nodes. These counts describe the source graph, not the final demand graph or universal drivability.

The earlier F01 drew 17,998 unique auto-eligible physical source segments in EPSG:32616. The updated source figure draws all 27,129 retained physical directed traversals in the current model, projected in EPSG:26916; reciprocal arcs can share geometry. Source compilation lengths also use EPSG:26916. Unknown capacity and free-speed values remain unknown in the preflight. The subsequent model explicitly supplies its engineering parameters; the figure itself contains no virtual connectors or assigned traffic.

The five intersecting City community areas are Near North Side, West Town, Near West Side, Loop and Near South Side. Each clipped polygon retains its official identity, area and interior representative point. Applying clipped-area fractions to 2023-end ACS whole-community populations produces an approximate 73,375 residents inside the rectangle. This uniform-area allocation is uncertain in dense, mixed-use neighborhoods and is neither a block census nor a campus count.

The four-stage road graph is a screened strongly connected component with 15,133 nodes and 27,129 directed links. Each of the five access anchors lies on that graph, on a walk-eligible street and within the relevant clipped polygon. This new zone abstraction does not retroactively fill the empty preflight connector table or certify driveways and crossings.

The model combines 2023 allocated population with 2026 active business-license records used as attraction weights and the 2026 OSM street source. Business licenses are not measured employment. Household counts are unknown, and income categories in the City source concern families. These heterogeneous inputs do not describe a single observed year or provide local calibration.

<a id="figure-chicago-f01-sources-gmns"></a>

##### Retained physical road graph

[![Retained physical road graph](<../assets/figure-contract-r11/figures/chicago/sources.svg>)](<../assets/figure-contract-r11/figures/chicago/sources.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

27,129 retained physical directed traversals in the saved 08:00–09:00 HBW model, shown in EPSG:26916. This is the retained model graph, not a claim to draw every road in the source archive. Virtual movements are excluded; colour has no traffic meaning. © OpenStreetMap contributors / ODbL. Reciprocal directed arcs can share geometry; no assigned flow is encoded. This drawing uses the frozen runs/chicago\_core\_hbw\_am\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/sources.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/sources.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/sources.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/sources.source.json>)

<a id="figure-r3-population"></a>

##### Resident population inputs

[![Resident population inputs](<../assets/figure-contract-r11/figures/chicago/population.svg>)](<../assets/figure-contract-r11/figures/chicago/population.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Clipped community-area allocation of ACS population; uniform-area assumption. All 5 zones are retained; population total 73,375.2. Households are unknown. Missing household fields are unknown, not zero. Census/ACS allocation is an input, not a simulated traffic quantity. This drawing uses the frozen runs/chicago\_core\_hbw\_am\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/population.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/population.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/population.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/population.source.json>)

<a id="figure-r3-transit"></a>

##### Transit source geography

[![Transit source geography](<../assets/figure-contract-r11/figures/chicago/transit.svg>)](<../assets/figure-contract-r11/figures/chicago/transit.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

OSM source-tagged stops; no service calendar. 953 saved stop records. Stop tags and road proximity do not prove legal walk access or operating service. The frozen scenario has no accepted service-day transit paths; no zero-demand transit bar is implied. The gray retained road graph is geographic context, not a transit route model. Source stops and route shapes do not establish legal pedestrian access, operating service, or observed ridership. This drawing uses the frozen runs/chicago\_core\_hbw\_am\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/transit.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/transit.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/transit.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/transit.source.json>)

<a id="generation"></a>

## 01 / Trip generation

<a id="coverage-row-06"></a>

The assumed production rule is 0.4 HBW trips per resident per day with a 35% AM-hour fraction. It gives 10,272.533873691 persons in the hour. The predeclared capture and intrazonal shares allocate 7,190.773711584 to external or uncaptured travel and 246.540812969 to intrazonal travel.

The remaining 2,835.219349139 persons enter interzonal distribution. Attraction mass is weighted by active licenses and normalized to productions. The five-zone bars are saved scenario outputs rather than observed commuting. External entering commuters have no measured input in this model and are not added to the internal matrix.

<a id="figure-fs-g01"></a>

##### Trip generation and demand accounting

[![Trip generation and demand accounting](<../assets/figure-contract-r11/figures/chicago/generation.svg>)](<../assets/figure-contract-r11/figures/chicago/generation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

All 5 zones; 08:00–09:00 HBW. The left panel shows saved interzonal productions/attractions. The right panel accounts for all generated persons, including excluded and intrazonal components. No top-12 truncation. Scenario assumptions, not measured trip counts. External and intrazonal components do not enter interzonal assignment; attractions are normalized to productions. This drawing uses the frozen runs/chicago\_core\_hbw\_am\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/generation.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/generation.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/generation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/generation.source.json>)

<a id="distribution"></a>

## 02 / Trip distribution

<a id="coverage-row-07"></a>

Gravity uses shortest travel time on the directed source-road model, followed by IPF. All twenty positive interzonal pairs are balanced; twenty is the complete pair set for the five modeled zones, not a selected smoke sample. Twenty-seven iterations leave a maximum margin discrepancy of 2.40705383×10⁻⁵ persons.

The declared AM PA direction is applied once to obtain 2,835.219349139 directed person trips. Intrazonal and excluded travel remains in the generation ledger. No Sketch or Regional OD data is substituted. The heatmap order follows official zone IDs 8, 24, 28, 32 and 33 on both axes. Color is log(1 + persons), but the downloadable numerical table retains the untransformed quantities.

<a id="figure-fs-d01"></a>

##### Trip distribution and directed OD margins

[![Trip distribution and directed OD margins](<../assets/figure-contract-r11/figures/chicago/distribution.svg>)](<../assets/figure-contract-r11/figures/chicago/distribution.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Full 5×5 model-zone matrix including zero cells; 20 positive OD pairs and 2,835.219349139 persons in 08:00–09:00 HBW. Colours are log(1+persons); margins are untransformed directed OD totals after PA direction. Every model zone is retained. Zero rows and columns remain visible; intrazonal cells are structural zeros. Labels use the final six digits of long zone IDs. This drawing uses the frozen runs/chicago\_core\_hbw\_am\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/distribution.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/distribution.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/distribution.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/distribution.source.json>)

<a id="mode"></a>

## 03 / Mode choice

<a id="coverage-row-04"></a>

<a id="coverage-row-08"></a>

Driving is available on all twenty pairs. Walking is available on ten under the frozen 35-minute path limit. Their OD-specific routed time, money and access terms feed a conditional logit; the resulting sums are approximately 2,105.938 drive and 729.281 walk persons. No internal interzonal person is left without an option.

Transit is Not modelled. CTA's Developer License Agreement was not accepted for this run, and a licensed service-day cost matrix was not obtained. The case therefore makes no transit ridership estimate, and an unmodeled transit label must not be shown as a prediction of zero passengers. Dividing drive persons once by the assumed 1.2 occupants per vehicle gives 1,754.948251240 vehicle/PCE trips. Walk persons are recorded without a capacity assignment.

<a id="figure-fs-m01"></a>

##### Mode choice: demand, cost and availability

[![Mode choice: demand, cost and availability](<../assets/figure-contract-r11/figures/chicago/mode.svg>)](<../assets/figure-contract-r11/figures/chicago/mode.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved OD-specific choice in 08:00–09:00 HBW; sums over every positive-demand OD. Persons, person-weighted generalized minutes, and available OD counts have separate axes. Transit is not modeled; no zero bar is shown. Generalized cost includes model time and money terms. Person totals precede the separate occupancy-to-PCE conversion. This drawing uses the frozen runs/chicago\_core\_hbw\_am\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/mode.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/mode.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/mode.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/mode.source.json>)

<a id="assignment"></a>

## 04 / Physical-link assignment

<a id="coverage-row-09"></a>

The exact twenty-pair Stage 3 PCE file feeds static BPR Frank–Wolfe. The saved run makes three genuine updates and ends at relative gap 2.0989113152700773×10⁻⁵, below tolerance 10⁻⁴. Its objective is 5,601.462458069 PCE-min. Of 27,129 retained links, 1,891 carry positive loading; maximum modeled v/c is 0.97274. BPR would also permit a ratio above one without imposing a hard capacity constraint.

Direction and shared-node topology are source based, but OSM restriction relations were not fetched. Their status is UNKNOWN\_NOT\_FETCHED, not a finding that restrictions do not exist. This correction accompanies the frozen evidence without rewriting its hashed network\_semantics field. Real turn legality and parcel access remain unverified.

A01 uses the most-loaded directed segment for each distinct OSM way. It never adds flows across serial segments to manufacture a way volume. A03 reports ten selected links from that same solution, while the R3 flow map uses the frozen source crosswalk to place physical-link PCE geographically. Existing display-only label repairs preserve the full original-link mapping and prevent truncated IDs from collapsing distinct bars.

A02 retains the actual saved iteration values. The road maps and bar charts are views of one solution, not new solves. Colors, v/c and BPR travel times describe the assumed scenario; no traffic counts were inferred from image pixels or map appearance.

<a id="figure-fs-a01"></a>

<a id="figure-fs-a03"></a>

##### Frank–Wolfe: physical-road loading

[![Frank–Wolfe: physical-road loading](<../assets/figure-contract-r11/figures/chicago/chicago-fs_a03.svg>)](<../assets/figure-contract-r11/figures/chicago/chicago-fs_a03.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

v/c and one-hour BPR link time on ten representative loaded directed segments from distinct source ways; capacities are engineering proxies. Single-pass engineering scenario; no local empirical calibration. Jane Byrne / West Loop 12.023 km2

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/chicago-fs_a03.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/chicago-fs_a03.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chicago-fs_a03.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/chicago-fs_a03.source.json>)

<a id="figure-r9-fw-physical-flow"></a>

##### Frank–Wolfe: physical flow and distribution

[![Frank–Wolfe: physical flow and distribution](<../assets/figure-contract-r11/figures/chicago/fw-physical-flow.svg>)](<../assets/figure-contract-r11/figures/chicago/fw-physical-flow.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved Chicago static Frank–Wolfe endpoint for 08:00–09:00 HBW. The map and 22-bin histogram use the same complete 27,129-link physical-flow vector, including 25,238 exact-zero links; 1,891 links exceed 1e-6 PCE. Flow is PCE accumulated during the declared one-hour period, not persons or flow per simulation time step. The map uses a square-root sequential color scale with original-unit ticks and gray road context; histogram counts are linear and no links are omitted. Turn, access and other nonphysical solver arcs are excluded. The endpoint follows 3 actual FW updates; all 4 saved checks remain separate diagnostic evidence. Reciprocal directed arcs may overlap geometrically; flows are not summed. This full saved static case is distinct from the separate S20 and T4 method-transfer instances. This is a modeled engineering scenario, not observed traffic. © OpenStreetMap contributors / ODbL 1.0. R11 layout repair: map and all-link histogram share measured top and bottom panel bounds. The original saved physical-link IDs, exact flow vector, geographic vertices, display offsets, histogram edges and counts remain unchanged.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/fw-physical-flow.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/fw-physical-flow.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/fw-physical-flow.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/fw-physical-flow.source.json>)

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="figure-fs-a04"></a>

</details>

<a id="results"></a>

## Saved results and assignment checks

<a id="coverage-row-10"></a>

R3 receiver evidence includes a saved-result PASS, a fresh four-stage calculation from frozen inputs, successful saved-table comparison and six rejected negative controls. The producer's independent checks had already followed hash continuity, OD margins, availability and probability arithmetic, person-to-PCE conversion, path/link flow, node conservation, objective and full-network gap.

The earlier preflight had its own solver-free reproduction. A fresh directory with spaces and Chinese characters reproduced eight selected CSV files byte for byte and passed structural checks. Other checks covered crosswalk hashes, link geometry direction, sampled metric lengths, zone areas and representative points, population allocation, stops and S2 conservation. Those interface tests must not be presented as the four-stage solve itself.

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="figure-fs-a02"></a>

##### Frank–Wolfe objective and relative gap

[![Frank–Wolfe objective and relative gap](<../assets/figure-contract-r11/figures/chicago/trace.svg>)](<../assets/figure-contract-r11/figures/chicago/trace.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

4 saved record(s), 3 updates; final objective 5601.46245807 PCE-min, gap 2.09891131527e-05 against 0.0001. Original iteration samples and objective retained. An accepted numerical gap concerns this scenario and demand set; it does not certify real traffic conditions. This drawing uses the frozen runs/chicago\_core\_hbw\_am\_v1 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/trace.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/trace.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/trace.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/trace.source.json>)

</details>

<a id="parity-chicago-static-inputs"></a>

## Static assignment: demand margins and physical endpoints

<a id="figure-parity-chicago-assignment-margins"></a>

##### Static assignment demand margins

[![Static assignment demand margins](<../assets/template-parity-20261008/static-inputs/chicago/assignment-margins.svg>)](<../assets/template-parity-20261008/static-inputs/chicago/assignment-margins.svg>)

Chicago S20: origin and destination margins from the exact frozen 20-OD vehicle-demand table, after its existing person-to-vehicle conversion. Each map sums to 1754.94825123973 PCE/h; all 5 model zones remain, including zero selected margins. Both panels use the same square-root colour normalization with original-unit ticks. The source-zone ledger is joined exactly to actual prepared node OD rows, rather than to person-trip generation or all-mode distribution. The 20 selected pairs retain the Jane Byrne / West Loop S20 identity and five clipped model zones. All saved road geometry is retained as pale context and clipped only at the common display viewport. These are model inputs, not observed travel or an optimization trajectory. Private local derivative; no new public release is claimed. © OpenStreetMap contributors, ODbL 1.0; source-zone geography as documented in the frozen case.

[Complete evidence · same figure](<#figure-parity-chicago-assignment-margins>) · [SVG](<../assets/template-parity-20261008/static-inputs/chicago/assignment-margins.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/chicago/assignment-margins.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/chicago/assignment-margins.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/chicago/assignment-margins.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/chicago/assignment-margins.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/chicago/assignment-margins.caption.md>)

<a id="figure-parity-chicago-assignment-endpoints"></a>

##### Physical demand endpoints

[![Physical demand endpoints](<../assets/template-parity-20261008/static-inputs/chicago/assignment-endpoints.svg>)](<../assets/template-parity-20261008/static-inputs/chicago/assignment-endpoints.svg>)

Chicago S20: the exact prepared 20-OD demand is aggregated only for display at its real origin and destination loading nodes, with 5 positive origin nodes and 5 positive destination nodes. Each side sums to 1754.94825123973 PCE/h. Light open circles retain all 5 saved model access nodes; filled markers share a square-root colour scale, while fixed marker area does not add another quantity. OSM node coordinates are derived from the matched physical-link geometry endpoints; all repeated occurrences agree. Both panels use identical geographic extent and road/zone context. The demand table, zone-access ledger and network instance hashes were checked together. These are engineering loading points, not observed trip ends or parcel entrances. Private local derivative; no new public release is claimed. © OpenStreetMap contributors, ODbL 1.0.

[Complete evidence · same figure](<#figure-parity-chicago-assignment-endpoints>) · [SVG](<../assets/template-parity-20261008/static-inputs/chicago/assignment-endpoints.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/chicago/assignment-endpoints.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/chicago/assignment-endpoints.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/chicago/assignment-endpoints.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/chicago/assignment-endpoints.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/chicago/assignment-endpoints.caption.md>)

<a id="parity-chicago-construction"></a>

## Time-expanded network and path examples

<a id="figure-parity-chicago-time-layers"></a>

##### Time-expanded network in layers

[![Time-expanded network in layers](<../assets/template-parity-20261008/construction/chicago/time-layers.svg>)](<../assets/template-parity-20261008/construction/chicago/time-layers.svg>)

Chicago: selected time layers 46–50 use 30 seconds per time step. Every arrow is an actual saved arc; only node-time states occurring as saved endpoints are drawn. The highlighted continuous chain is selected from saved construction records to explain incidence; it is not an optimized or observed trajectory. State aliases: A = osm:1324341003, B = osm:1324341002, C = osm:1324341004. Pale arrows show other saved arcs in this local slice. Time planes and horizontal placement are schematic; this is neither a full graph nor observed traffic. This T4 graph has no independent turn connectors; the later static turn sidecar is excluded. The highlighted structural chain carries no assigned-flow claim.

[Complete evidence · same figure](<#figure-parity-chicago-time-layers>) · [SVG](<../assets/template-parity-20261008/construction/chicago/time-layers.svg>) · [PNG](<../assets/template-parity-20261008/construction/chicago/time-layers.png>) · [PDF](<../assets/template-parity-20261008/construction/chicago/time-layers.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/chicago/time-layers.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/chicago/time-layers.source.json>) · [Caption](<../assets/template-parity-20261008/construction/chicago/time-layers.caption.md>)

<a id="figure-parity-chicago-local-details"></a>

##### Local construction details

[![Local construction details](<../assets/template-parity-20261008/construction/chicago/local-details.svg>)](<../assets/template-parity-20261008/construction/chicago/local-details.svg>)

Chicago: the physical road chain is mapped to physical-node states and then to exact time-indexed arcs in the saved construction slice. Panel c contains all 18 retained arcs, with exact endpoint times; strong teal/blue highlights the same continuous chain used in the companion layered figure. The highlighted continuous chain is selected from saved construction records to explain incidence; it is not an optimized or observed trajectory. All layout coordinates are schematic. Source/sink terminal bookkeeping is outside this excerpt and must not be read as road travel or waiting. This T4 graph has no independent turn connectors; the later static turn sidecar is excluded. The highlighted structural chain carries no assigned-flow claim.

[Complete evidence · same figure](<#figure-parity-chicago-local-details>) · [SVG](<../assets/template-parity-20261008/construction/chicago/local-details.svg>) · [PNG](<../assets/template-parity-20261008/construction/chicago/local-details.png>) · [PDF](<../assets/template-parity-20261008/construction/chicago/local-details.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/chicago/local-details.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/chicago/local-details.source.json>) · [Caption](<../assets/template-parity-20261008/construction/chicago/local-details.caption.md>)

<a id="released-c06-t-admm-main"></a>

<a id="parity-chicago-finite"></a>

## Optimization on the time-expanded network

<a id="released-c06-t-lr"></a>

<a id="figure-parity-chicago-lr-bounds"></a>

##### Lagrangian bounds and certified gap

[![Lagrangian bounds and certified gap](<../assets/template-parity-20261008/optimization/chicago/lr-bounds.svg>)](<../assets/template-parity-20261008/optimization/chicago/lr-bounds.svg>)

All ten original-cost states of the accepted self-priced feasibility/recovery dual-anchor hybrid are retained. They follow 26 distinct own-pool feasibility rounds. Bounds and certificate have separate panels; the final gap is 0.8744685%. This result does not relabel the earlier pure LR run or its unsuccessful endpoints.

[Complete evidence · same figure](<#figure-parity-chicago-lr-bounds>) · [SVG](<../assets/template-parity-20261008/optimization/chicago/lr-bounds.svg>) · [PNG](<../assets/template-parity-20261008/optimization/chicago/lr-bounds.png>) · [PDF](<../assets/template-parity-20261008/optimization/chicago/lr-bounds.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/chicago/lr-bounds.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/chicago/lr-bounds.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/chicago/lr-bounds.caption.md>)

<a id="figure-parity-chicago-lr-prices"></a>

##### Capacity prices at the best dual bound

[![Capacity prices at the best dual bound](<../assets/template-parity-20261008/optimization/chicago/lr-prices.svg>)](<../assets/template-parity-20261008/optimization/chicago/lr-prices.svg>)

The best-bound multiplier state is the saved price vector that supports the accepted hybrid lower bound, kept separate from current and unevaluated post-update prices. Panel a ranks its ten largest positive dynamic-arc prices by exact identity; panel b sums all timed prices by departure index. There are 504 positive prices among 1,351,628 entries. This is the named hybrid, not the original pure LR experiment. The detailed vector is currently private.

[Complete evidence · same figure](<#figure-parity-chicago-lr-prices>) · [SVG](<../assets/template-parity-20261008/optimization/chicago/lr-prices.svg>) · [PNG](<../assets/template-parity-20261008/optimization/chicago/lr-prices.png>) · [PDF](<../assets/template-parity-20261008/optimization/chicago/lr-prices.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/chicago/lr-prices.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/chicago/lr-prices.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/chicago/lr-prices.caption.md>)

<a id="figure-parity-chicago-lr-recovery"></a>

##### Path-pool growth and primal recovery

[![Path-pool growth and primal recovery](<../assets/template-parity-20261008/optimization/chicago/lr-recovery.svg>)](<../assets/template-parity-20261008/optimization/chicago/lr-recovery.svg>)

Panel a retains all 26 own-pool feasibility augmentation rounds and the ten separate original-cost rounds; the divider marks the phase boundary. Panel b shows the ten saved feasible original-cost recovery objectives. The 128 inherited own-LR paths grow to 182 through 54 new own-price events; no CG pool or reference witness was used. These are two stages of the named hybrid, not 36 identical subgradient steps.

[Complete evidence · same figure](<#figure-parity-chicago-lr-recovery>) · [SVG](<../assets/template-parity-20261008/optimization/chicago/lr-recovery.svg>) · [PNG](<../assets/template-parity-20261008/optimization/chicago/lr-recovery.png>) · [PDF](<../assets/template-parity-20261008/optimization/chicago/lr-recovery.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/chicago/lr-recovery.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/chicago/lr-recovery.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/chicago/lr-recovery.caption.md>)

<a id="chicago-admm116"></a>

### ADMM: saved continuation to outer116

The saved ADMM continuation reaches outer 116 but remains unconverged. Original x is infeasible: capacity excess 0.0421644796900 PCE, primal 0.121224522778 PCE, dual 0.0391348952092 min and endpoint stationarity 0.0250952425689 min. The CG objective difference is not evaluated. Outer 34–36 retains the original coordination; 37–116 uses the registered alpha=1.6 candidate.

<a id="figure-chicago-admm116-history"></a>

##### ADMM: actual history and original stopping gates

[![ADMM: actual history and original stopping gates](<../assets/mainline-publication-20261009/chicago/ADMM_HISTORY_33_116.svg>)](<../assets/mainline-publication-20261009/chicago/ADMM_HISTORY_33_116.svg>)

All 84 actual saved rows from outer 33–116 are plotted. Outer 33 is the inherited boundary; 34–36 retain the original coordination and 37–116 use alpha=1.6 (divider at 36.5). Panels show original-x objective in PCE·min, capacity excess in PCE, primal residual in PCE and rho-scaled dual residual in min, with saved original thresholds. Rho is fixed at 0.14357255844301195 min/PCE and has no separate panel. The stationarity diamond is the only verified endpoint shown, not an invented history. At outer116 the original x remains infeasible; its objective 241.864094592416 PCE·min is not a feasible upper bound. CG objective difference is not evaluated, not zero. Provider audits and two completed exact-archive read-only replays are reused; mainline checked the saved histories and signatures without running an optimizer.

[SVG](<../assets/mainline-publication-20261009/chicago/ADMM_HISTORY_33_116.svg>) · [PNG](<../assets/mainline-publication-20261009/chicago/ADMM_HISTORY_33_116.png>) · [PDF](<../assets/mainline-publication-20261009/chicago/ADMM_HISTORY_33_116.pdf>) · [Saved history · 84 rows](<../assets/mainline-publication-20261009/chicago/ADMM_HISTORY_33_116.csv>) · [Endpoint checks](<../assets/mainline-publication-20261009/chicago/ENDPOINT_AUDIT.json>) · [Verification identity](<../assets/mainline-publication-20261009/chicago/VERIFICATION_IDENTITY.json>) · [Source and reuse notice](<../assets/mainline-publication-20261009/NOTICE.md>)

<a id="figure-chicago-admm116-capacity"></a>

##### ADMM: original-x capacity excess at outer116

[![ADMM: original-x capacity excess at outer116](<../assets/mainline-publication-20261009/chicago/ADMM_CAPACITY_DETAIL.svg>)](<../assets/mainline-publication-20261009/chicago/ADMM_CAPACITY_DETAIL.svg>)

The ten largest positive original-x capacity excesses at outer116 are ranked. Commodity bars retain PCE flow, black marks are the frozen per-arc capacity, and the right panel shows positive excess against the original 1e−5 PCE gate. The maximum is 0.0421644796900 PCE. These are generated time-arc model values, not measured passenger records. Reused provider figure; no numerical or geometric change. This failing diagnostic does not relabel successful CG or LR hybrid results, the old pure-LR endpoints, or the failed rank26/52 reductions.

[SVG](<../assets/mainline-publication-20261009/chicago/ADMM_CAPACITY_DETAIL.svg>) · [PNG](<../assets/mainline-publication-20261009/chicago/ADMM_CAPACITY_DETAIL.png>) · [PDF](<../assets/mainline-publication-20261009/chicago/ADMM_CAPACITY_DETAIL.pdf>) · [Saved capacity rows](<../assets/mainline-publication-20261009/chicago/CAPACITY_TOP_ARCS.csv>) · [Endpoint checks](<../assets/mainline-publication-20261009/chicago/ENDPOINT_AUDIT.json>) · [Verification identity](<../assets/mainline-publication-20261009/chicago/VERIFICATION_IDENTITY.json>) · [Source and reuse notice](<../assets/mainline-publication-20261009/NOTICE.md>)

Low-rank26/52 remain below their gates. The I80/full-minor result is not a compression success. The accepted LR hybrid does not reclassify the older pure-LR endpoint. These saved diagnostics were checked by the provider and two existing read-only archive replays; mainline performed only summary/history/signature checks.

<a id="reproduction"></a>

## Reproduction and input identity

Current S0 reception and the released algorithm figures are integrated in [the current method record](<#algorithm-retry-r2>). [Public reception summary](<../assets/algorithm-transfer-r8/CURRENT_STATUS.json>) · [Source and scope notice](<../assets/algorithm-transfer-r8/NOTICE.md>). Private solver inputs, checkpoints and complete compute archives are outside this figure release.

<a id="coverage-row-19"></a>

The public reproducibility archive is not yet available.

Python 3.11, standard library numerical stages, shapely/pyproj input build, matplotlib/numpy figures; numeric library threads=1

Runtime versions above are recorded producer facts. The V presentation task does not replace or upgrade the frozen numerical environment.

<a id="limitations"></a>

## Model limits and observations

<a id="coverage-row-05"></a>

<a id="coverage-row-11"></a>

<a id="coverage-row-12"></a>

<a id="coverage-row-13"></a>

<a id="coverage-row-14"></a>

<a id="coverage-row-15"></a>

<a id="coverage-row-16"></a>

<a id="coverage-row-17"></a>

<a id="coverage-row-18"></a>

The scope is a five-zone urban-core engineering scenario rather than metropolitan Chicago, an observed traffic forecast, a benchmark-network reproduction or a TemplateFit result. Utility, rates, occupancy, capacities, speeds and access costs were not fitted to local observations. The one-hour single pass includes no congestion feedback to demand and no dynamic traffic loading.

The earlier network figure has a recorded scale/legend issue requiring presentation review. Contextual figures should remain distinct from current model output, and unrendered preflight panels should be explained in text rather than represented by empty cards. The provided permission covers the checked derived assets, not private benchmark inputs, raw GPS, third-party photographs or teaching packages.

Acquisition records and frozen-input commands serve different purposes. Remote City and OSM downloads may change; byte equality refers to the archived inputs. The retained commands are historical producer references with their original layouts and output paths, not an advertised portable download-and-run CLI. S0 owns the final executable delivery contract.

OSM-derived maps retain © OpenStreetMap contributors and ODbL attribution. The scholarly benchmark source and photo licenses remain provenance facts; mentioning them does not bring those unlisted source bytes into this preview.

A separate OSM object query found 953 stop/platform nodes in the rectangle. Spatial association to community areas and a nearest walking node were recorded, but proximity does not prove pedestrian access. OSM walking ways and tagged crossings likewise do not establish a timetable. Because the CTA feed was not obtained under its license, current feed stop, route, trip and service-day totals are not available.

A separate pinned MapConstruction archive supplies historical aggregate evidence: 889 trip files and 118,360 points from April 2011, with 83,405 points from 873 trips overlapping the rectangle. Its indivisible download exceeds the original 50,000-point sampling cap. The bounded matching exercise selected ten distinct-trip contiguous runs totaling 1,778 timed points. UIC shuttle is the archive-level description; individual trip mode was not independently checked. EPSG:32616 is an explicit inference from the UTM-like coordinates, not a published source CRS declaration. Precise traces remain private.

Two independent matching engines used the same sample and the same 5,963-node, 10,283-link auto adapter. Native trace2route returned ten paths, but only two passed the predeclared distance gate. MapMatcher4GMNS 0.2.1 HMM returned ten complete paths and all ten passed that gate, with valid original link references and directed adjacency. Segment-wise 95th-percentile offsets were 5.423–14.749 m and the largest point offset 25.880 m. These are internal smoke-test metrics, not surveyed accuracy or evidence of a 2026 shuttle route; turn restrictions were not validated for either matcher.

The source contains 174 ways with a motorway, trunk or other \_link ramp tag. A deterministic twenty-way candidate list retains endpoints, identities and relevant topology tags, alongside five SOURCE\_TAGGED traffic objects. It supports further human review but does not classify interchange type or certify movement legality.

Three photographs credited to AlphaBeta135 and dated 31 July 2024 were previously inspected under CC BY 4.0. They show grade-separated decks, a curved carriageway below overpasses and a Downtown Exits sign with 51A–51D. Missing numeric camera coordinates prevent binding pixels to a road link; no VLM, lane-count or automatic movement update followed. The image bytes and gallery are outside this preview's allowlist. Historical descriptions are kept separate from modeled road evidence.

The original S2 sample uses s2sphere 0.2.5 on 100 objects: twenty GMNS nodes, fifty links, five zones, twenty stops and five tagged objects. Levels 12/14/16 produce 1,380 associations with clipped-object length or area denominators; maximum parent-child weight discrepancy is about 5.53×10⁻⁷. Only fifty of 95,225 links are sampled. A private extension covers ten historical GPS points and fifty HMM route links, generating 194 associations and 180 verified object-level combinations. It does not cover every selected trace point or all 418 unique matched links. Approximate four-vertex cell polygons and nonadditive travel measures limit interpretation; precise GPS-derived cell identifiers stay private.

<a id="sources"></a>

## Sources and display provenance

- [Transportation Networks for Research repository](<https://github.com/bstabler/TransportationNetworks>)
- [OSM extract](<https://www.openstreetmap.org/copyright>)
- [City of Chicago community-area layer](<https://data.cityofchicago.org/d/igwz-8jzy>)
- [City's ACS five-year community-area table](<https://data.cityofchicago.org/d/t68z-cikk>)
- [Developer License Agreement](<https://www.transitchicago.com/downloads/sch_data/developers_license_agreement.htm>)
- [MapConstruction Chicago archive](<https://github.com/pfoser/mapconstruction/tree/master/data/tracks>)
- [MapMatcher4GMNS 0.2.1 HMM](<https://pypi.org/project/mapmatcher4gmns/0.2.1/>)
- [CC BY 4.0](<https://creativecommons.org/licenses/by/4.0/>)

[Return to the city atlas](<../index.html#chicago>) · [Back to top](<#document-top>)

<a id="r3-method-transfer"></a>

<a id="algorithm-retry-r2"></a>

## Chicago Jane Byrne / West Loop R2：追加计算后的算法证据

Accepted evidence includes S20 FW, finite-path, Algorithm B and the uncompressed Native80 representation, plus T4 CG and the own-pool LR recovery hybrid. CG has 425 columns and a full-graph pricing certificate. The LR hybrid retains 26 feasibility rounds and 10 original-cost bound/price rounds, with a 0.8744685% certified gap. S20 hourly demand and the T4 pulse remain separate engineering instances.

<dl class="accepted-method-notes"><dt>S20 FW / finite</dt><dd>REUSED_PRIOR_ACCEPTED · Prior accepted endpoints were replayed; they are not new optimizations.</dd><dt>T CG</dt><dd>S0 ACCEPTED · Independent complete-graph primal/dual and pricing acceptance; objective 241.2185242449435 PCE·min, 425 columns.</dd></dl>

<a id="algorithm-retry-r2-section-1"></a>

### 1. 本次问题与结论的范围

本章使用Jane Byrne / West Loop R2原输入，保留已接受四阶段与静态结果。S20与T4保持各自图、需求和单位；新的方法扩展属于查看该实例后登记的post-diagnostic工程实验，不是当地实测标定。

<dl class="accepted-method-notes"><dt>S_FW</dt><dd>ACCEPTED · REUSED_PRIOR_ACCEPTED · 原状态复用，正式只读重放</dd><dt>S_finite</dt><dd>ACCEPTED · REUSED_PRIOR_ACCEPTED · 原状态复用，正式只读重放</dd></dl>

<a id="algorithm-retry-r2-section-2"></a>

### 3. Accepted S20 static methods

静态 S20 包含全部 20 个正车辆 OD，总量 1754.948251239727 PCE/h，27129 条有向道路边，15133 个节点。Stage 3 已换算车辆 PCE，本次没有再次除以 occupancy 或乘 PCE。K5 输入路径池是 100 条真实简单合法路径；major 数量为 20，minor 维度为 80。两档输入-only basis rank 为 26 和 52，其路径坐标数分别为 46 和 72。Native 工作模型另含 2916 个活跃显式 link 变量，因此总优化变量分别为 2962 和 2988；不能把路径坐标数当成总变量，也不据此声称获得加速。

FW 和 finite 的原结果已经通过独立原图检查。本次保留完整路径与 link 状态，只在最终只读重放中重新核验，不重新优化。原 finite 的 Beckmann 目标约 5601.461468286856 PCE min，full gap 约 8.0051e-12。它是输入相同的数值参照，不能用于生成或重新挑选 Native basis。

<a id="figure-r9-s20-fw-map-distribution"></a>

[![S20 Frank–Wolfe physical loading and distribution](<../assets/plot-semantics-r9/chicago/s20-fw-map-distribution.svg>)](<../assets/plot-semantics-r9/chicago/s20-fw-map-distribution.svg>)

**S20 Frank–Wolfe physical loading and distribution.** Frank–Wolfe own saved physical-link flow on the frozen Chicago Jane Byrne / West Loop R2 S20 instance: 20 selected OD pairs and 1,754.9482512397267 PCE in one declared hour. The full map and 22-bin histogram each retain all 27,129 directed physical links. 1,891 links exceed 1e−6 PCE/h; exact zeros remain in the histogram. The vector is joined one-to-one by persistent link ID to every original road geometry vertex. Both method cards share a square-root colour scale and constant overlay width in PCE/hour. Tiny values with absolute magnitude at most 1e−12 PCE/h are hidden only from coloured overlays; all raw values and geographic context remain. The finite card reads its own saved vector, not the FW vector or a difference map. Both S20 endpoints retain their own REUSED\_PRIOR\_ACCEPTED status; this does not accept Native, LR or ADMM diagnostics. This is a static one-hour instance, distinct from the separate four-OD T4 pulse.

[SVG](<../assets/plot-semantics-r9/chicago/s20-fw-map-distribution.svg>) · [PNG](<../assets/plot-semantics-r9/chicago/s20-fw-map-distribution.png>) · [PDF](<../assets/plot-semantics-r9/chicago/s20-fw-map-distribution.pdf>) · [Plot data](<../assets/plot-semantics-r9/chicago/s20-fw-map-distribution.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/chicago/s20-fw-map-distribution.caption.md>) · [Source record](<../assets/plot-semantics-r9/chicago/s20-fw-map-distribution.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-chicago-s20-fw-map-distribution>)

<a id="figure-r9-s20-finite-map-distribution"></a>

[![S20 finite-path reference and physical support](<../assets/plot-semantics-r9/chicago/s20-finite-map-distribution.svg>)](<../assets/plot-semantics-r9/chicago/s20-finite-map-distribution.svg>)

**S20 finite-path reference and physical support.** Finite-path own saved physical-link flow on the frozen Chicago Jane Byrne / West Loop R2 S20 instance: 20 selected OD pairs and 1,754.9482512397267 PCE in one declared hour. The full map and 22-bin histogram each retain all 27,129 directed physical links. 1,868 links exceed 1e−6 PCE/h; exact zeros remain in the histogram. The vector is joined one-to-one by persistent link ID to every original road geometry vertex. Both method cards share a square-root colour scale and constant overlay width in PCE/hour. Tiny values with absolute magnitude at most 1e−12 PCE/h are hidden only from coloured overlays; all raw values and geographic context remain. The finite card reads its own saved vector, not the FW vector or a difference map. Both S20 endpoints retain their own REUSED\_PRIOR\_ACCEPTED status; this does not accept Native, LR or ADMM diagnostics. This is a static one-hour instance, distinct from the separate four-OD T4 pulse.

[SVG](<../assets/plot-semantics-r9/chicago/s20-finite-map-distribution.svg>) · [PNG](<../assets/plot-semantics-r9/chicago/s20-finite-map-distribution.png>) · [PDF](<../assets/plot-semantics-r9/chicago/s20-finite-map-distribution.pdf>) · [Plot data](<../assets/plot-semantics-r9/chicago/s20-finite-map-distribution.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/chicago/s20-finite-map-distribution.caption.md>) · [Source record](<../assets/plot-semantics-r9/chicago/s20-finite-map-distribution.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-chicago-s20-finite-map-distribution>)

<details markdown="1">
<summary>Original FW and finite-minus-FW physical-flow view</summary>

<a id="released-c06-s-flow"></a>

</details>

上一轮 Native 的主要障碍是最优性而非守恒。原 rank26/52 的 full gap 约为 0.00638167 和 0.00479636，分别约为 1e-5 门槛的 638 倍和 480 倍，而守恒误差已经接近浮点精度。独立表示空间诊断还表明，在硬 OD 等式下，即使暂时取消非负约束，固定压缩 link 子空间与 finite link 流的最小欧氏距离仍分别约 528.3448 和 303.1601 PCE/h。这说明当前压缩空间不能精确表示这个 finite 流，但并不证明 1e-5 gap 永远不可达到。追加外层的意义是检验现有冻结方法继续迭代是否改善端点；它不是新的 basis 设计实验。

<a id="released-c06-s-convergence"></a>

##### Frank–Wolfe: S20 objective and relative gap

[![Frank–Wolfe: S20 objective and relative gap](<../assets/figure-contract-r12/figures/chicago/chi-fw-history.svg>)](<../assets/figure-contract-r12/figures/chicago/chi-fw-history.svg>)

Accepted Chicago Jane Byrne / West Loop R2 S20 Frank–Wolfe run. All six actual saved states, iterations 0–5, are plotted without smoothing or invented samples. The Beckmann objective is PCE·min/h on the frozen one-hour 1,754.9482512397267 PCE/h demand. The full-graph relative gap ends at 3.446136191653708e-6, below the unchanged 1e-5 gate. The small rise between saved gaps at iterations 3 and 4 is retained. This S20 method history is distinct from the separate four-state full-city presentation record. Numerical results are engineering scenarios, not observed traffic.

[SVG](<../assets/figure-contract-r12/figures/chicago/chi-fw-history.svg>) · [PNG](<../assets/figure-contract-r12/figures/chicago/chi-fw-history.png>) · [PDF](<../assets/figure-contract-r12/figures/chicago/chi-fw-history.pdf>) · [Source data](<../assets/figure-contract-r12/figures/chicago/chi-fw-history.source.json>)

<a id="algorithm-retry-r2-section-4"></a>

### 4. 有限时空问题与 LP

T4 是独立于静态 Beckmann 问题的固定成本、共享容量网络流问题。4 个 OD 按事前哈希规则和资源档选择，总脉冲量为 66.53295454563035 PCE。采用首个 5 分钟 bin 的中点 08:02:30 出发，q\_T=q\_hour/12，dt=30 s，H=169。其他 OD 与其他 11 个时间 bin 属于本实例明确排除的量，不悄悄纳入或遗失。

该 T 图有 1351628 条弧、490223 个时空节点，LP 精确可达变量域有 1550188 个变量、565265 条等式行、603066 条非冗余容量行。只消去原问题中确定无法承流的变量，不使用有限路径池冒充完整 arc LP。每条真实道路的代价是原 t0，时间推进是 ceil(t0/dt)，容量按原小时容量换算成 30 秒容量。waiting、movement 和终端 ledger connector 语义分别保留，不能把零成本补到 H 的账本连接当成道路拥堵或实际排队。

<a id="released-c06-t-input-seed-paths"></a>

##### Time-expanded network: seed-path support

[![Time-expanded network: seed-path support](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_input_seed_paths.svg>)](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_input_seed_paths.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

T4 input-cost seed paths Each panel shows the saved input-cost seed path for one OD. Initial path support alone establishes no optimization or capacity-feasibility conclusion.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_input_seed_paths.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_input_seed_paths.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_input_seed_paths.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_input_seed_paths.source.json>)

<a id="algorithm-retry-r2-section-5"></a>

### 5. CG：从自己的合法列继续

CG 上一轮 121 个 Phase I master 之后，人工量从约 53.83337 降至 20.3733943 PCE，但仍未清零，终端最小 reduced cost 仍为 -1。这个证据说明旧轮数预算耗尽时还有改善方向，不能据此宣称原 T 问题不可行。本次仅加载本城自己的 151 条已保存合法列，继续最多 1200 个新 Phase I 轮次，并为 Phase II 注册 300 轮和总 5400 秒墙钟预算。

master 与完整 DAG 定价函数保持原数学实现。薄适配只增加自己的父列加载、实时进度，并保存最后实际求得的 Phase II master；后来追加但尚未重解的列只能补零流，不能冒充已被求解。定价检查独立从原 CSV 图重算，逐 commodity 检查所有允许弧上的最短费用。目标碰到 LP 数字仍不足以通过，必须同时满足 OD、容量、Phase I 清零、Phase II 实际执行、定价闭合和对偶 gap。

本次 CG 状态为 **ACCEPTED**；恢复端点的实际轮数 268；保存合法列数 425；终端 Phase I 人工量 0 PCE；可用原始目标 241.2185242 PCE min。原始路径支持地图显示真实保存的候选列，列数不等于 PCE 流量。只有存在完整 master 状态时，才输出相应原坐标流及目标证书。中断前已定价的 70 个 master 与恢复历史分开保留，不把它们重复当作当前列池的延续。

独立原图核验得到的对偶下界为 241.2185242 PCE min，最大 OD 误差为 7.105427358e-15 PCE，最大共享容量超量为 7.105427358e-15 PCE。逐 OD 全图 reduced cost 为 \[0.0, -8.881784197001252e-16, -3.552713678800501e-15, -2.6645352591003757e-15\]。CG 的 ACCEPTED 来自自身可行流、对偶界与完整图定价证书；LP 求解器仍按自己的资源停止状态报告，没有把 CG 的证书填入 LP 输出或声称 LP 数值对比已经完成。

<a id="figure-r9-cg-phase-one"></a>

[![Column generation: Phase I feasibility](<../assets/plot-semantics-r9/chicago/cg-phase-one.svg>)](<../assets/plot-semantics-r9/chicago/cg-phase-one.svg>)

**Column generation: Phase I feasibility.** All 208 saved Phase I master states, rounds 0–207, show total artificial OD demand flow in PCE. The frozen master has four artificial variables in OD conservation equalities; they are not capacity-row slacks. Total artificial flow decreases from 20.373394302610762 to 0 PCE, first clearing the 1e−8 PCE gate at round 207. Per-OD artificial trajectories are not available in the saved history, so no artificial-flow heatmap is invented. Step segments and markers use only actual saved states; the threshold may visually coincide with zero on this linear scale. Chicago Jane Byrne / West Loop R2 T4 engineering pulse; modelled scenario, not observed traffic. CG is accepted on its own independently checked full-graph primal/dual pricing certificate. © OpenStreetMap contributors, ODbL 1.0.

[SVG](<../assets/plot-semantics-r9/chicago/cg-phase-one.svg>) · [PNG](<../assets/plot-semantics-r9/chicago/cg-phase-one.png>) · [PDF](<../assets/plot-semantics-r9/chicago/cg-phase-one.pdf>) · [Plot data](<../assets/plot-semantics-r9/chicago/cg-phase-one.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/chicago/cg-phase-one.caption.md>) · [Source record](<../assets/plot-semantics-r9/chicago/cg-phase-one.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-chicago-cg-phase-one>)

<a id="figure-r9-cg-phase-two"></a>

[![Column generation: Phase II real cost](<../assets/plot-semantics-r9/chicago/cg-phase-two.svg>)](<../assets/plot-semantics-r9/chicago/cg-phase-two.svg>)

**Column generation: Phase II real cost.** All 60 saved Phase II master objectives, rounds 0–59, in PCE·minutes. They decrease from 374.533127798287 to 241.2185242449435. The dashed reference is the final same-run full-graph-valid CG dual bound, 241.2185242449434 PCE·minutes, independently checked at pricing closure; it is not a time series of per-round valid bounds and not a HiGHS LP result. The endpoint independent objective is 241.2185242449435 PCE·minutes. The frozen producer recomputes 241.21852424494347, differing only at floating-point precision. No objective transformation, interpolation, omitted rounds or smoothing is applied. Chicago Jane Byrne / West Loop R2 T4 engineering pulse; modelled scenario, not observed traffic. CG is accepted on its own independently checked full-graph primal/dual pricing certificate. © OpenStreetMap contributors, ODbL 1.0.

[SVG](<../assets/plot-semantics-r9/chicago/cg-phase-two.svg>) · [PNG](<../assets/plot-semantics-r9/chicago/cg-phase-two.png>) · [PDF](<../assets/plot-semantics-r9/chicago/cg-phase-two.pdf>) · [Plot data](<../assets/plot-semantics-r9/chicago/cg-phase-two.plot_data.json>) · [Caption](<../assets/plot-semantics-r9/chicago/cg-phase-two.caption.md>) · [Source record](<../assets/plot-semantics-r9/chicago/cg-phase-two.source.json>) · [Same figure on homepage](<../index.html?atlas-view=full#atlas-r9-chicago-cg-phase-two>)

<a id="figure-r9-cg-pricing-closure"></a>

##### Column generation: full-graph pricing closure

[![Column generation: full-graph pricing closure](<../assets/figure-contract-r11/figures/chicago/cg-pricing-closure.svg>)](<../assets/figure-contract-r11/figures/chicago/cg-pricing-closure.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Separate columns show Phase I dimensionless pricing and Phase II minute-valued pricing. Upper panels preserve every saved full-graph minimum with its phase-specific negative-reduced-cost gate (−1e−8 and −1e−7). Lower panels show the actual saved four-commodity reduced costs, T01–T04, across every round; their matrix minimum is checked against the plotted minimum for every state. Each heatmap has its own explicitly labelled scale and units. The final Phase I minimum is 0; final Phase II minimum is −3.552713678800501e−15 min, satisfying the frozen full-graph closure gate. Linear axes retain signed roundoff; no positive floor or smoothed pricing history is added. Chicago Jane Byrne / West Loop R2 T4 engineering pulse; modelled scenario, not observed traffic. CG is accepted on its own independently checked full-graph primal/dual pricing certificate. © OpenStreetMap contributors, ODbL 1.0. R11 layout repair: compact two-row spacing and shared serif bold panel headings; all 268 saved rounds and all four OD pricing values per round remain unchanged.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/cg-pricing-closure.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/cg-pricing-closure.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/cg-pricing-closure.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/cg-pricing-closure.source.json>)

<details markdown="1">
<summary>Original combined CG record</summary>

<a id="released-c06-t-cg"></a>

</details>

<a id="released-c06-t-cg-generated-paths"></a>

##### Column generation: generated-path support

[![Column generation: generated-path support](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_cg_generated_paths.svg>)](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_cg_generated_paths.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

CG-generated column support on original roads Color encodes the number of saved generated columns using each physical road.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_cg_generated_paths.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_cg_generated_paths.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_cg_generated_paths.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/chicago-c06_t_cg_generated_paths.source.json>)

<a id="algorithm-retry-r2-section-6"></a>

<details markdown="1">
<summary>Method below gate / witness / resource diagnostic</summary>

Retained diagnostic, not an accepted optimizer result. CG acceptance does not certify LR or ADMM.

<a id="released-c06-t-physical-flow"></a>

##### Column generation: physical flow and distribution

[![Column generation: physical flow and distribution](<../assets/figure-contract-r12/figures/chicago/chi-cg-physical.svg>)](<../assets/figure-contract-r12/figures/chicago/chi-cg-physical.svg>)

Accepted Chicago R2 T4 column-generation endpoint on the original 30-second/H169 finite graph. The map sums this method’s own saved movement-arc flow over commodities and time onto each original physical-link ID; the unit is PCE in the selected pulse, not an hourly rate. The complete 27,129-link vector includes 26,597 exact zeros and 532 positive values. All physical links remain gray context, and positive links use a square-root sequential scale with original-unit colorbar ticks. The 22-bin histogram counts every physical link, including zeros, on a linear count axis. Public saved geometry is joined by a unique exact ID set; no static FW flow is reused. Ledger connectors are excluded. © OpenStreetMap contributors; road-derived data ODbL 1.0: https://www.openstreetmap.org/copyright. Numerical results are engineering scenarios, not observed traffic.

[SVG](<../assets/figure-contract-r12/figures/chicago/chi-cg-physical.svg>) · [PNG](<../assets/figure-contract-r12/figures/chicago/chi-cg-physical.png>) · [PDF](<../assets/figure-contract-r12/figures/chicago/chi-cg-physical.pdf>) · [Source data](<../assets/figure-contract-r12/figures/chicago/chi-cg-physical.source.json>)

</details>

### 8. 解释边界与可以据此说什么

该城市输入是 generic weekday 08–09 HBW 工程场景，drive/walk 语义保持，公交尚未建模。activities 的 business-license 权重是活动代理，不是就业人数。没有当期同匝道 GPS 和现场标定，算法路径不能冒充观测轨迹。旧 2011 GPS、2024 照片、老师原版 TemplateFit 缺包和设施扩展任务仍暂停。

原 R2 转向资料边界为 UNKNOWN\_NOT\_FETCHED，并非确认没有禁转。之后取得的 3 条 restriction、1 条可解析对、2 条未决和 1.261013 min 局部敏感性来自新日期独立侧件，没有混入当前 R2。这保证新结果与已接受输入可以按字节比较，但也限定了可宣称的现实交通意义。

T 图的细道路分段逐段向上取整会把最短网格行程推到约 40–67 分钟，而 cost 累计仍约 2.69–4.30 分钟。这是所注册离散化的两种时间语义，不是实测拥堵。有限时空固定成本 LP/CG/LR/ADMM 不构成真正 DNL 或 DUE，其线性目标也不能与静态 Beckmann 目标横向排名。本次可以评价算法在该冻结工程问题上的证据完整性、计算边界和验收状态，不能据此给出城市现实政策效益。

<a id="algorithm-retry-r2-section-9"></a>

### 9. 核验、复现与接入

正式只读入口 verify\_saved.py 使用 CSV、NumPy 与 heapq 重建原坐标证据，安装运行时拦截以禁止已知优化器导入、子进程启动和网络调用。完整包在中文加空格路径解压后连续执行两次，输出目录位于输入树之外，并比较全部输入文件前后 SHA256。最终打包回执记录这两次实际结果；本段不替代回执。

图件读取已接受的保存状态，保留 C 布局、蓝绿/深蓝和 DejaVu Serif。正文区分 S20 静态需求和 T4 有限时间脉冲；所有图件接入均为绘图与排版，没有新增优化。

对仍未通过的方法，完整状态与界限比重复降低门槛更有用。后续若继续，需要先依据本次实际末态提出独立注册实验；改变 basis、离散化、局部核或 horizon 都应是新科学问题或新算法版本，不能伪装成当前冻结迁移已经通过。

Source and scope notice. © OpenStreetMap contributors; road-derived data ODbL 1.0: https://www.openstreetmap.org/copyright; numerical results are engineering scenarios, not observed traffic. Jane Byrne / West Loop R2 engineering S20 and separate T4. CG is accepted on its own full-graph certificate; the current Native80 and own-pool LR hybrid retain their separate identities. Complete notice .

<a id="chicago-r3-input-construction-ledger"></a>

<a id="chicago-r3-input-time-layer-excerpt"></a>

##### Time-expanded network: saved input layers

[![Time-expanded network: saved input layers](<../assets/figure-contract-r11/figures/chicago/chicago-input-time-layer-excerpt.svg>)](<../assets/figure-contract-r11/figures/chicago/chicago-input-time-layer-excerpt.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

INPUT ONLY / NOT OPTIMIZED. 18 actual dynamic\_arc rows connect 3 selected physical/IN/OUT states over steps 46–50 (23–25 minutes after 08:00). Time coordinates and edge directions come directly from the frozen input; vertical spacing is schematic. Chicago has physical movement and one-step waiting; its new turn sidecar is excluded. Connector examples are also exact saved records; their sink-time jumps are ledger bookkeeping, not observed waiting. No optimized flow/path is shown. Structural excerpt selected from records; arrows carry no assigned flow and no optimized path. Saved bookkeeping examples outside this local excerpt: Source: source\_T01\_t5 → nosm:9913425856\_t5; t=5→5; cost=0 min Sink: nosm:261207373\_t88 → sink\_T01\_t169; t=88→169; cost=0 min Ledger jumps align arrival bookkeeping to H; they are not physical travel or waiting. State spacing is schematic. Full graph support and nonselected neighbours are omitted from this excerpt; all shown edges are saved input rows.

</details>

[PNG](<../assets/figure-contract-r11/figures/chicago/chicago-input-time-layer-excerpt.png>) · [SVG](<../assets/figure-contract-r11/figures/chicago/chicago-input-time-layer-excerpt.svg>) · [PDF](<../assets/figure-contract-r11/figures/chicago/chicago-input-time-layer-excerpt.pdf>) · [Source record](<../assets/figure-contract-r11/figures/chicago/chicago-input-time-layer-excerpt.source.json>)
