<a id="document-top"></a>

MOBILITY COMPUTATION LAB / STATIC CITY RECORD

# Ithaca

An 11-zone midday HBO\_LOCAL\_ACTIVITY scenario with 110 positive vehicle OD pairs; a 7.502 km² demand area uses 13.236 km² of road support.

The figures show saved method results, physical-flow maps and original-unit diagnostics. Drawing these figures invokes no optimizer.

<a id="gap-20261008"></a>

## Latest received evidence · 8 October 2026

Current accepted results preserve each frozen model, demand instance and numerical unit. The figures below read the received public evidence without additional optimization.

<dl class="accepted-method-notes"><dt>FW, finite, Native26 and Native52 original-space endpoints are received. FW has zero updates; Native26/52 each actually completed four outer rounds.</dt><dd>ITH_GC03 compares four method categories, not four iterations. Finite has an endpoint with solver nit=1 and no separate iteration-history file. No Algorithm B endpoint is claimed.</dd><dt>Exact-DAG LP, CG, LR and ADMM saved-state numerical endpoints are received by S0. CG has one record per phase, LR one iteration, ADMM one completed outer update.</dt><dd>0.6567553604 PCE pulse &lt; 2.5 PCE minimum physical time-arc capacity; the model is nonbinding. ITH_GC04 shows four methods, not four time steps or a congestion stress test.</dd><dt>Producer ADMM metadata retains NUMERIC_PASS_CONFIRMATION_PENDING; S0 now accepts the exact saved numerical endpoint using its Full-bound independent receipts.</dt><dd>The old producer string is retained as provenance, not the current reception status. This fixed-cost finite graph is not DNL/DUE.</dd><dt>Employment allocation and historical count coverage are added; the 27 unmatched source-link bridge cases and 2022 location limits remain diagnostic.</dt><dd>Counts, candidate roads and matched-route evidence are not interchangeable. No local calibration, concurrent holdout or complete 87-link model route is claimed.</dd></dl>

[Homepage city cards](<../index.html?atlas-view=full#ithaca>) · [Figure guide and saved-state interpretation](<../figure-update-status.html#top>) · [Earlier frozen chapters and history](<#gap-earlier-cutoff>)

### Received figure evidence

<a id="figure-gap-ith-gc01-employment"></a>

##### Employment allocation and spatial accounting limits

[![Employment allocation and spatial accounting limits](<../assets/figure-contract-r11/figures/ithaca/ith-employment-allocation.svg>)](<../assets/figure-contract-r11/figures/ithaca/ith-employment-allocation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Grey spans run from fully contained to all intersecting blocks; they are spatial accounting limits, not confidence intervals. Totals are 7,493 contained, 8,752.529 area-allocated and 10,858 intersecting-block jobs. This supplement did not replace the frozen HBO activity attraction. Frozen Ithaca S110 static and T4 finite fixed-cost endpoints, not DNL/DUE or local calibration. T4 capacity is nonbinding (0.65675536 PCE pulse versus 2.5 PCE minimum physical arc capacity). U.S. Census/LEHD, NYSDOT and © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/ith-employment-allocation.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/ith-employment-allocation.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/ith-employment-allocation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/ith-employment-allocation.source.json>)

<a id="figure-private-ithaca-native-history"></a>

##### Native L3: all 4 saved outer iterations

[![Native L3: all 4 saved outer iterations](<../assets/private-native-history-20261008/ithaca/native-complete-history.svg>)](<../assets/private-native-history-20261008/ithaca/native-complete-history.svg>)

All 4 saved outer checks are plotted for each Native rank on the same frozen S110 instance (110 positive OD, 421.261325634 PCE/h). Each marker is an actual saved check at outer 1–4; the connecting segments do not add intermediate observations. Rank 26 uses open circles and rank 52 filled squares; near-coincident lines are both retained. Panels separate checked BPR/Beckmann objective, signed full-graph relative gap, maximum original-OD residual, and physical-flow reconstruction residual. The horizontal FW value is an independent same-instance endpoint, not an additional Native iteration. Early checked objectives lie below that endpoint while OD conservation has not yet reached its frozen gate; these are not feasible upper bounds or better traffic solutions. Signed negative gaps remain negative and are not interpreted as superior optimality. The gap axis is symmetric-log with a linear interval of ±10⁻¹²; OD/reconstruction axes are logarithmic in their original PCE/h units. The original gap bounds ±10⁻⁵, OD absolute gate 10⁻⁶ PCE/h, and reconstruction gate 10⁻⁷ PCE/h are unchanged. Both runs reach their original acceptance checks at outer 4; other relative-OD/nonnegativity gates remain in the source records. These early states belong to the ultimately accepted run; no separate failed trial is added. Endpoint comparison and method-specific physical-flow maps remain separate evidence. Private local preview of complete saved numerical history: public release currently covers endpoints, not these per-iteration values. Engineering scenario, not observed traffic or measured policy effect.

[SVG](<../assets/private-native-history-20261008/ithaca/native-complete-history.svg>) · [PNG](<../assets/private-native-history-20261008/ithaca/native-complete-history.png>) · [PDF](<../assets/private-native-history-20261008/ithaca/native-complete-history.pdf>) · [Plot data](<../assets/private-native-history-20261008/ithaca/native-complete-history.plot.json>) · [Source and access](<../assets/private-native-history-20261008/ithaca/native-complete-history.source.json>) · [Caption](<../assets/private-native-history-20261008/ithaca/native-complete-history.caption.md>)

<a id="figure-gap-ith-gc03-s-endpoints"></a>

##### Accepted static endpoints and feasibility

<a id="table-r11-ith-static-endpoints"></a>

[![Accepted static endpoints and feasibility](<../assets/figure-contract-r12/figures/ithaca/ith-static-endpoints.svg>)](<../assets/figure-contract-r12/figures/ithaca/ith-static-endpoints.svg>)

Independent accepted endpoints on S110 · 110 OD · 421.261325634 PCE/h. Panels show signed objective difference from the same-instance FW endpoint (1638.7317576864 PCE·min/h), signed full-graph relative gap, and maximum original-OD and link-reconstruction residuals. Categories are method identities, not iteration numbers; no connecting trajectory is drawn. The signed symmetric-log axes retain exact zeros and negative roundoff, with a linear interval of ±1e−15 in each panel’s stated unit. The accompanying method-specific physical-flow figures remain the map evidence; scalar agreement does not imply identical flow.

[SVG](<../assets/figure-contract-r12/figures/ithaca/ith-static-endpoints.svg>) · [PNG](<../assets/figure-contract-r12/figures/ithaca/ith-static-endpoints.png>) · [PDF](<../assets/figure-contract-r12/figures/ithaca/ith-static-endpoints.pdf>) · [Source data](<../assets/figure-contract-r12/figures/ithaca/ith-static-endpoints.source.json>)

<a id="figure-gap-ith-gc04-t-endpoints"></a>

##### T4 finite-time endpoint comparison

<a id="table-r11-ith-time-endpoints"></a>

[ADMM convergence and feasibility](<#figure-parity-ithaca-admm-saved-state>)

###### Accepted methods on the same finite graph

[![Accepted methods on the same finite graph](<../assets/figure-contract-r12/figures/ithaca/time-method-objectives.svg>)](<../assets/figure-contract-r12/figures/ithaca/time-method-objectives.svg>)

The methods share this exact four-OD finite graph and fixed-cost objective. Categories are independent method endpoints, not an optimization timeline. Left: each saved objective with the independent reference. Right: signed differences retain full numerical precision, including negative roundoff. All shown methods currently satisfy their independent acceptance conditions. Objective proximity by itself is not a feasibility certificate and does not imply identical physical-link flow.

[SVG](<../assets/figure-contract-r12/figures/ithaca/time-method-objectives.svg>) · [PNG](<../assets/figure-contract-r12/figures/ithaca/time-method-objectives.png>) · [PDF](<../assets/figure-contract-r12/figures/ithaca/time-method-objectives.pdf>) · [Source data](<../assets/figure-contract-r12/figures/ithaca/time-method-objectives.source.json>)

<details id="gap-diagnostics" markdown="1">
<summary>Observation sources and coverage</summary>

These source figures describe observation coverage and geographic context. They do not establish calibrated traffic or validated routes.

<a id="figure-gap-ith-gc02b-observation-counts"></a>

##### Observation source links and network coverage

<a id="table-r11-ith-observation-bridge"></a>

[![Observation source links and network coverage](<../assets/figure-contract-r12/figures/ithaca/observation-source-coverage.svg>)](<../assets/figure-contract-r12/figures/ithaca/observation-source-coverage.svg>)

Saved source-link coverage contains 87 records: 60 remain geometric R2 candidates, 21 have endpoints outside the retained strongly connected component, and 6 are excluded by access filtering. The latter 27 are unbridged. These are input coverage categories. Candidate geometry does not establish an exact matched route, legal-turn validation, observed link flow or local calibration. All category counts come directly from the released aggregate CSV.

[SVG](<../assets/figure-contract-r12/figures/ithaca/observation-source-coverage.svg>) · [PNG](<../assets/figure-contract-r12/figures/ithaca/observation-source-coverage.png>) · [PDF](<../assets/figure-contract-r12/figures/ithaca/observation-source-coverage.pdf>) · [Source data](<../assets/figure-contract-r12/figures/ithaca/observation-source-coverage.source.json>)

<a id="figure-gap-ith-gc05-count-coverage"></a>

##### Historical count-record coverage

[![Historical count-record coverage](<../assets/figure-contract-r11/figures/ithaca/ith-count-record-coverage.svg>)](<../assets/figure-contract-r11/figures/ithaca/ith-count-record-coverage.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

The bounded acquisition contains 294 records and 76 unique RCSTA sites overall. Sites repeat across years; the annual site counts must not be added as distinct sites. Directional and combined count records are not summed vehicle volumes, and this is not a calibrated 2026 holdout. Frozen Ithaca S110 static and T4 finite fixed-cost endpoints, not DNL/DUE or local calibration. T4 capacity is nonbinding (0.65675536 PCE pulse versus 2.5 PCE minimum physical arc capacity). U.S. Census/LEHD, NYSDOT and © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/ith-count-record-coverage.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/ith-count-record-coverage.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/ith-count-record-coverage.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/ith-count-record-coverage.source.json>)

<a id="figure-gap-ith-gc06-counts-2022"></a>

##### 2022 observed counts and location evidence

<a id="table-r11-ith-counts-2022-summary"></a>

[![2022 observed counts and location evidence](<../assets/figure-contract-r12/figures/ithaca/observed-counts-2022.svg>)](<../assets/figure-contract-r12/figures/ithaca/observed-counts-2022.svg>)

GC06. Actual 2022 NYSDOT Region 03 source worksheet rows joined by 17 historical inside-model RCSTA codes: 51 records, three direction records per station. Panel a preserves source FEDERAL\_DIRECTION codes rather than resolving recorder heading; combined and directional records must not be summed. Each plotted value is the unmodified AVG\_WKDAY\_INTERVAL\_12 vehicle count, range 5–781, not PCE and not a model prediction. Panel b shows that only 3 source rows provide new coordinates, all inside the original extent; the remaining 48 are station-ID matches and do not establish updated recorder location. No local calibration, simultaneous observation, or fresh holdout is claimed. No precise GPS route coordinates are present. The scientific marks, source-direction symbols, axes and 51 plotted records are preserved exactly from the approved SVG. Only the outer typography and whitespace were adjusted. No underlying record CSV was reverse-engineered or published; these observed vehicle counts are not converted to PCE.

[SVG](<../assets/figure-contract-r12/figures/ithaca/observed-counts-2022.svg>) · [PNG](<../assets/figure-contract-r12/figures/ithaca/observed-counts-2022.png>) · [PDF](<../assets/figure-contract-r12/figures/ithaca/observed-counts-2022.pdf>) · [Source data](<../assets/figure-contract-r12/figures/ithaca/observed-counts-2022.source.json>)

</details>

<a id="gap-notice-ithaca-eca9326a0b"></a>

### Source and scope notice

Frozen Ithaca S110 static and T4 finite fixed-cost endpoints, not DNL/DUE or local calibration. T4 capacity is nonbinding (0.65675536 PCE pulse versus 2.5 PCE minimum physical arc capacity). U.S. Census/LEHD, NYSDOT and © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright.

### Complete approved source chapters

The following chapters are retained in full, including numerical tables and historical source-time statements. Their figures link to the same figure anchors above.

<details id="gap-source-volume-addendum-s0" markdown="1">
<summary>Approved source chapter — VOLUME_ADDENDUM_S0.md</summary>

Reading edition of the approved source, SHA-256 40dd2f19d26681ef2da8de8a894faea74a3fdb95d8827da74d622d477a9e55aa . Download original source text . The linked original preserves the complete source record; this reading edition displays accepted results.

### Ithaca / Cornell 增量章节：来源可追溯与同模型算法核验

本章供现有 Ithaca 城市卷追加。模型仍是 7.502 km² 需求范围、13.236 km² 道路支持范围内的 11 区、110 OD 午间 HBO\_LOCAL\_ACTIVITY 工程场景。Cornell 是本地定位与展示对象，数据不代表校园问卷，也不包含用 Cornell Tech 或纽约市替代本地证据的内容。原六城静态 R3 的 6/6 接收状态保持；本章的新结果分别标记提供方、接收方、公开与网页状态。

#### 1. 需求来源可以沿字段追到 421.261326 PCE/小时

冻结模型使用 2020 年普查街区面积分摊人口 27797.945573 人、住户 10361.965919 户，以及 1,127 个 OSM 活动对象。活动吸引权重为每区对象数加一。它表达机会代理，不能写成实际岗位或观察到的出行吸引量。人口与活动进入不同字段；GPS 只为观测支线提供位置证据，没有决定全部产生量或方式偏好。

HBO 场景率为 0.8 次/人/日，午间占比 0.08，内部捕获率 0.65，区内比例 0.12；重力阻抗系数为 0.04/分钟，往返分配权重为 0.6/0.4。这些是公开说明的工程假设。本轮没有把它们换成本地实测参数。原产生、分布、方式选择与分配输出保持原字节，新增查询将人口、产生量、OD 人次、方式概率、车辆数和 PCE 放在同一条可检查的记录中。

保存的区际 OD 合计 1017.627191536 人次。drive 人次除以 1.3 人/车后，形成 421.261325634 PCE/小时。独立字段检查的产生量分解误差与方式守恒误差处于浮点舍入量级，车辆/PCE 转换检查为零。`query.py --query lineage` 返回 330 条方式记录；查询本身采用 SQLite 只读连接，输出写到包外。查询结果不替代交通行为校准。

#### 2. 就业补充量明确保留了部分街区的空间不确定性

本轮从美国 Census LEHD 官方站点获取 LODES8 的纽约州 2020 年工作地文件，使用 S000、JT00、C000。JT00 统计全部岗位，不能当作不重复人数；工作地街区采用 2020 年普查地理编码，能够与原人口街区连接。原始压缩文件、HTTP 回执、字段含义和逐街区连接结果均已保留。[LODES 技术文档](<https://lehd.ces.census.gov/doc/help/onthemap/LODESTechDoc.pdf>)

原 11 个模型分区包含 367 个相交街区，其中 164 个在该稀疏工作地表中有记录。整块岗位合计 10,858；完全包含的街区岗位为 7,493；沿用原街区面积权重的场景量为 8752.529038。未出现的街区表示该发布表中无岗位记录，不能证明现实中没有任何就业。部分街区的岗位位置未知，面积权重并非岗位分布观测。

图 ITH\_GC01 将三种空间口径分别绘出。灰线是完整包含块到全部相交块的空间计账范围，不是统计置信区间。该补充没有改变 HBO 出行目的、原 OSM 活动吸引权重或任何四阶段输入。就业字段已具备可追溯性，是否用于新的需求模型仍需另立输入修订和受影响阶段。

#### 3. 原方式模型已经包含实际服务日的 TCAT 时刻表场景

原配置实现 drive、transit、walk，分别在 110、98、108 个 OD 上可用。公交使用 TCAT 静态 GTFS 20260922 版本中 2026-10-05 星期一服务：日历与例外表核查得到服务 ID 10、836 个有效班次和 627 个有效站点。原构建器在 11:00、11:15、11:30、11:45 四个出发时刻寻找直达服务，并要求至少两个时刻可用。

该成本包含近似 OSM 步行接入、时刻表等待与车内时间，尚不包含换乘、实时可靠性或本地观察到的选择偏好。广义成本的时间价值与零方式常数也是工程设定。新增就业与历史计数均未输入方式选择，因此本轮不重复已接收的产生、分布和选择步骤。日历重算与旧公交成本输出的复用会在核验报告中分别列出，不能把日历核对说成重新运行了所有公交路径。

#### 4. 27 条观测桥接缺口已经细化到具体来源规则

原观测链的 187 个 GPS 点、87 个有向源路段和完整次序继续保留；初始立即反向没有被删去。87 个源路段中，60 个有几何 R2 候选，另外 27 个仍未桥接。候选表同时保留方向相反的几何重叠，这些重叠不能自动变成合法的有向模型路径。

对 27 条缺口的源码与端点核查显示，6 条源路段所在 way 带有 access=no 与 motor\_vehicle=yes；原 R2 先按 access 排除，v004 源候选则采用独立的方式特定覆盖。其余 21 条至少一个端点不在 R2 保留的强连通分量中。这个结论定位了差异，尚未证明恢复六条边就会因果性地恢复其余 21 条。完整源图可达性复核、方向与源版本对照仍交 E/S0 核对。

三个地面设施候选的坐标均能追到原源对象。C1/C2 的历史过街图像分别来自 2017 与 2021 年，不是与 2023 GPS 同步的真值。C2 仍有附近设施的身份歧义。C3 源公交点与 GTFS 的 Dey @ Lincoln 站相距约 8 米，但附近照片不能确认目标物体；位置相近不能补成图像证据。图 ITH\_GC02 保留完整路线，仅进 Private Full；轻包提供 ITH\_GC02B 聚合诊断。源道路几何归属 © OpenStreetMap contributors。

#### 5. 294 条历史小时计数可查询，但校准兼容性仍未成立

本轮对 NYSDOT Short Counts 官方服务进行了模型边界框内的限定查询，获得 303 条记录，其中 294 条位于模型范围，涉及 76 个 RCSTA 站点。其数据年份为 2015–2019，均有平均工作日 11:00–12:00 字段。这里的记录数包括分方向与合计记录，不能相加当作站点交通总量。RCSTA 是可连接的六位站点编码；旧服务的 RC\_ID 在本次结果中均为 36，已原样保存而未当作唯一站号。

字段文档还区分车辆计数与轴数除二计数，本轮保留了这些单位，未自动转成 PCE。[NYSDOT 字段说明](<https://www.dot.ny.gov/divisions/engineering/technical-services/highway-data-services/hdsb/repository/Field_Definitions_SC%20Formats.pdf>) 图 ITH\_GC05 展示这一批历史记录的年份覆盖，不能据此断言纽约州交通档案在 2019 年后没有数据。`query.py --query counts` 返回范围内 294 行。

历史计数覆盖全目的、外部与穿行交通；本模型只表达内部 HBO 的一个车辆分量。站点到有向 R2 路段的对应、车辆构成、年份与需求口径尚未统一。数据也在基线结果已知后取得，因此不冒称 fresh holdout。材料缺口已从“未取得本地小时记录”推进为明确的兼容性与独立验证设计问题，原工程计算身份不因这些缺口而撤销。

在等待共享计算资源期间，另从 NYSDOT 官方区域下载列表补取 2022 年 Region 03 平均工作日流量档案。该 ZIP 实际包含 XLSX，工作表声明范围错误地写为 A1。本轮只读遍历了实际 2,403 条数据，按旧范围内 RCSTA 站号连接出 51 条记录、17 个站号，均保留车辆计数单位与 11–12 小时字段。独立核验直接解析原 XLSX XML，逐字段误差为零。51 条中只有 3 条自带新的位置坐标并落在原模型范围内；另外 48 条不能仅凭旧站号连接就认定 2022 年计数器位置完全一致。`query.py --query counts2022` 可返回这些记录。[NYSDOT 区域数据列表](<https://www.dot.ny.gov/divisions/engineering/technical-services/highway-data-services/hdsb>)

这一补充扩展了实际取得的年份，未改变冻结模型或独立保留样本身份。2015–2019 GIS 快照与 2022 工作表分别保留，未拼成一组同期观测，也未把合计记录与分方向记录重复相加。

#### 6. S110 比较在原 47,938 条求解弧中接受核验

S110 原样使用全部 110 个正 OD、15,148 条物理路段，以及原转向和分区连接弧，总计 47,938 条求解弧。规范化仅改字段表示，不改容量、自由流时间、BPR 参数、端点或需求。FW 与有限路径、Native26/52 均沿公共固定核心执行；路径池以输入自由流成本生成，未读取 FW 端点来制造初始解。

<dl class="accepted-method-notes"><dt>fw</dt><dd>ACCEPTED · 1638.73175769 · -1.38749590289e-16</dd><dt>finite</dt><dd>ACCEPTED · 1638.73175769 · -1.38749590289e-16</dd><dt>native26</dt><dd>ACCEPTED · 1638.73175768 · -1.02938321035e-12</dd><dt>native52</dt><dd>ACCEPTED · 1638.73175769 · 5.58189601731e-13</dd></dl>

静态表以小时流率乘分钟成本，单位为 PCE·min/h。既有机器字段 objective\_pce\_min 沿用原字段名，数值没有重新缩放。下节 T 使用一次释放的 PCE 总量，其目标单位为 PCE·min；两种目标不能跨模型直接相减。

FW 实际保存的更新次数为零：初始分配已经达到冻结门槛。报告保留微小负 gap，不补造收敛曲线。该现象只说明这个较低需求工程实例在其数值门内达标，不能证明拥堵压力条件下的普遍效率。路径生成时间、优化器时间、保存状态回放与绘图调用分别记录，不能仅比较优化器计时而隐去公共路径池成本。

求解前冻结的路径池包含550条路径，并经独立最短路和原始弧空间检查；所有OD首条自由流最短路成本误差小于7×10⁻¹⁴分钟。finite与Native共用相同冻结路径池。等成本路径的顺序属于该已登记实现的输入身份。

第二次诊断修正处理 Native 显式链流变量的内存估计超限：将 v=B₁ᵀx₁+Dθ 严格代回相同目标函数。由于路径弧关联非负，x₁≥0 与 Uθ≥0 已保证原链流非负，替换未添加裁剪，也没有删除非零小系数。小型异质 BPR 控制算例对目标、梯度和链流的误差均在 2×10⁻¹⁵ 内；这项控制不是城市求解结果。每次 Native 保存全部原始链流，并由另一个入口检查守恒、重构、原图 gap 和非负门。两项修正预算已用完，后续不得靠增加容差或改需求来制造接受状态。

本轮 Native26 与 Native52 各在第 4 轮达到原门，最大 OD 残差分别约为 7.59×10⁻¹¹ 与 1.25×10⁻¹⁰ PCE/h。实际进程树峰值采样分别为 371,503,104 与 426,643,456 bytes；含进程启动与检查的阶段用时约 43.45 与 58.88 秒。线程环境设为 1，但进程树采样会计入控制器、工作进程和运行库辅助线程，观察到最多 18 个线程，未将环境设定冒充实际线程数。完整逐轮状态与公共路径池成本均保留。

#### 7. T 使用独立时空状态，不能用其证书替代 D

T 输入规则在求解前冻结，时间步为 30 秒，容量从原 PCE/小时换为每 30 秒弧容量；物理弧成本仍是原自由流分钟。物理旅行时间向上取整为步数，原零时转向及分区接入保持有向语义，等待弧每步成本为 0.5 分钟。释放继承 11–12 午间口径，使用首个五分钟箱中点 11:02:30 的脉冲；脉冲总量与全小时 421.261326 PCE 分账。

实际 T 模型有 36360 条弧、4 个 commodity，脉冲量 0.656755360434 PCE，时域终点为 11 点后 1230 秒。 图构建采用输入最早到达与最晚离开界限，只剔除在声明时域内绝不可能进入任何选定 OD 路径的弧时状态。独立检查回到完整声明图域核查映射、全部可行弧时覆盖、单位与源汇，不把选定路径池冒充完整时间图。

每条物理短边至少占一个 30 秒时间步，逐段向上取整的延时会累积；保存的自由流分钟成本没有随取整步数一起增加。因此时域可达性与目标成本是两个明确声明的字段，离散到达时间不能写成实测行车时间。本轮只检验这张冻结有限图，不据此估计真实排队延误；更细时间步或合并物理短边应作为新的模型输入修订审查。

<dl class="accepted-method-notes"><dt>lp</dt><dd>ACCEPTED · 0.918428268939</dd><dt>cg</dt><dd>ACCEPTED · 0.918428268939</dd><dt>lr</dt><dd>ACCEPTED · 0.918428268939</dd><dt>admm</dt><dd>Accepted saved-state numeric result · 0.91842826894</dd></dl>

LP 参考证书必须与后续 CG/LR/ADMM 绑定同一弧表、需求表与模型签名。参考只用于端点核验，不把参考流或对偶变量输入后续方法。比较同时说明分母：合同归一差使用 max(1, abs(reference))，真相对差使用 abs(reference)。NaN、缺状态与数值未达门分别处理，不填零。该 T 是固定成本共享硬容量问题，没有据此声称 FIFO 排队、动态加载或 DUE。D 将在通过验收的公共引擎可用后另立城市最小案例。

原输入提案按 OD 字典序等距取四对，会产生 665,525 条弧时状态，完整弧 LP 预估峰值约 2.429 GB。此前未看任何 T 求解结果的资源规则允许顺次检查较短输入 OD；其四对候选产生 36,360 条状态，满足预先声明的 500 MB 参考预算。取样只作用于新增 T，原 S110、四阶段输入与每对保留需求的换算均不变，所有候选规模记入 INPUT\_SELECTION。

参考算法也按输入条件预先选择：若脉冲总量不超过任意物理弧时容量，有限 DAG 中每个 commodity 在单弧上最多携带自身总量，故共享容量必然冗余。此时用完整可达域的最短路原始解和节点势对偶证书严格求解同一 LP，并单独记录为一次证书构造、零次 HiGHS 调用；条件不成立则执行完整弧流 LP。该规则不是观察某次流量较小后补作的判断，独立 LP 核验仍逐项检查变量域、守恒、容量、全部约化成本与原始对偶差。

实际脉冲 0.656755360434 PCE 小于最小物理弧容量 2.5 PCE，因而本实例的共享容量不绑定，不能据此声称完成了拥堵压力测试。参考目标为 0.918428268939354 PCE·min；合同归一差的分母恰为 1，真相对差分母为 0.918428268939354。CG 两阶段各做一次受限主问题求解；LR 记录一次迭代；ADMM 完成一次外迭代，原守恒误差约 6.19×10⁻¹⁵ PCE，与参考目标差约 2.18×10⁻¹³ PCE·min。它们的快速结束符合这一冻结输入的性质，没有补造多轮曲线。

CG独立检查直接读取已保存的流、对偶和历史状态；结果元数据使用包内固定公共核心的来源哈希。需求、图、门槛和数值状态保持原字节，绘图和元数据整理没有再次运行CG。

#### 8. 数值、接收、公开和上线分别交付

本章数值表采用保存结果的独立核验状态；新增资产按本批 S0 逐文件清单作具体公开决定，网页由 A 统一接入。旧公开许可与原接收状态保持。E/S0 的请求文件已准备为本地附件，没有向其他会话自动发消息。

Private Full 保存新科学输入、状态、源码、配置和原空间检查；Volume Handoff 提供本章与图件及源数据；ChatGPT Upload 提供轻量判断材料，并准确说明不含完整求解状态、完整网络、原始精确路线等材料。最终 ZIP 的 CRC、成员 hash 与中文含空格目录的两次只读回放分别验证。成员 hash 证明字节一致，数学检查证明声明实例的数值性质，图件复现仅证明图可生成。

</details>

<a id="gap-earlier-cutoff"></a>

Original four-stage chapters retain their original demand, input identity and engineering assumptions.

**Private presentation preview.** Saved result verified; R3 fresh solve verified; All six negative controls rejected

Input snapshot: `mcl_s0_to_v_presentation_inputs_r3_v1@2026-10-05T03:57:54.309662+00:00`. Input version: `ithaca_city_aoi_intersection_2020_midday_r2; frozen configuration SHA-256 11c6f1ca1fbf09517251fb399cc7bbef9f258d2d483a111b34482cd3a01f4226`.

<a id="scope"></a>

## Scope and model instance

Ithaca uses a midday local-activity scenario, not the morning HBW purpose used by the other cases. Its declared period is Monday 5 October 2026, 11:00–12:00, and its purpose code is HBO\_LOCAL\_ACTIVITY. The demand area is the 7.501778 km² City portion inside the earlier research union. A 13.235585 km² road-support area supplies surrounding paths without adding its non-City residents to demand.

The earlier union combines an 8.193 km² campus-neighbor core and a 7.984 km² downtown-access corridor. These overlapping rectangles were chosen for source coverage and connectivity before assignment. Cornell's Ithaca campus and the October 2025 campus map establish geographic context, not a property boundary. Cornell Tech in New York City is unrelated to this case.

Eleven populated tract groups provide the demand zones; a zero-population intersecting tract is explicitly excluded. Source coordinates are WGS84; the earlier input preparation uses EPSG:32618. The aligned maps explicitly reproject the saved WGS84 road geometry into EPSG:26918 and label their local metric origin. The exercise combines earlier source checks with a new static four-stage calculation. It makes no institutional endorsement, causal, health, safety or emissions claim.

<a id="inputs"></a>

## Inputs and preparation

<a id="coverage-row-01"></a>

<a id="coverage-row-02"></a>

<a id="coverage-row-03"></a>

The demand denominator is an area-allocated estimate of 27,797.946 residents from 2020 City block data. The bounded service query returned 371 blocks, of which 369 intersect the research union. Block coverage reaches 99.76% of the City portion, which comprises 56.7% of the union. Whole contained blocks contribute their counts and boundary-cut blocks contribute overlap fractions; the analogous housing estimate is 10,361.966 occupied units.

These figures must not be confused with whole-tract counts. Thirteen tracts touch the broader union, and their complete populations and occupied units total 50,087 and 19,517 respectively. A previous coarse tract-area estimate of 22,354.75 residents for the union was superseded as the lead figure when finer block evidence exposed its inconsistency. The uncovered Cornell/Town portion does not acquire a block estimate by extrapolation.

Twenty-six ACS2024 block-group geometries were retrieved, but they supplied no 2024 population values. The original model did not compile employment. Attractions instead use 1,127 OSM amenity, shop, office, tourism, leisure or healthcare objects plus an explicit one-unit floor per zone. They represent activity opportunities rather than jobs; later employment evidence does not retroactively change this generation input.

Four OSM tiles contain 109,240 raw nodes and 5,761 highway ways before selection. The clipped source graph has 20,928 nodes and 24,420 segments, including 175 boundary-truncated segments; their selected lengths sum to 398,894.127 m. An undirected audit retains 26 components, with 20,682 nodes in the largest. Source length and component counts are geography checks, not traffic capacity or travel benefits.

The preflight distinguishes 12,938 footways, 453 cycleways and 243 steps segments, and preserves bridge, tunnel, layer, access, one-way and mode tags. Its draft exchange comprises 13 zones and 45,361 source-crosswalk rows as well as the node/link tables. Nine restriction relations seen in the source were not applied to that draft. The separate four-stage road graph encodes applicable passenger-car transitions; the two graph products must not be conflated.

TCAT feed version 20260922 provides a selected service day of 5 October 2026. Parsing its calendars and timetable gives one active service identifier, 836 trips, 24 routes and 168 stops in the union, of which 163 appear in active stop times. These are schedule facts rather than observed bus positions. The raw feed remains excluded under unresolved redistribution terms.

Other City layers describe 1,641 sidewalk polygons, 75 trails or footpaths and 86 one-way-street lines. Sidewalk polygons do not define legal pedestrian centerlines, and the one-way layer lacks the direction attribute needed to infer direction from vertex order. Five USGS elevation samples at candidate crossings cannot establish a path slope. These sources cover the municipal area and do not certify stop access across the whole union.

<a id="figure-r3-sources"></a>

##### Retained physical road graph

[![Retained physical road graph](<../assets/figure-contract-r11/figures/ithaca/sources.svg>)](<../assets/figure-contract-r11/figures/ithaca/sources.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

15,148 retained physical directed traversals in the saved 11:00–12:00 local activity model, shown in EPSG:26918. This is the retained model graph, not a claim to draw every road in the source archive. Virtual movements are excluded; colour has no traffic meaning. © OpenStreetMap contributors / ODbL. Reciprocal directed arcs can share geometry; no assigned flow is encoded. This drawing uses the frozen run\_20261005 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/sources.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/sources.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/sources.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/sources.source.json>)

<a id="figure-r3-population"></a>

##### Population and household inputs

[![Population and household inputs](<../assets/figure-contract-r11/figures/ithaca/population.svg>)](<../assets/figure-contract-r11/figures/ithaca/population.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved clipped-zone demographic allocation; not a campus census. All 11 zones are retained; population total 27,797.9. Occupied units total 10,362. Missing household fields are unknown, not zero. Census/ACS allocation is an input, not a simulated traffic quantity. This drawing uses the frozen run\_20261005 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/population.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/population.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/population.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/population.source.json>)

<a id="figure-r3-transit"></a>

##### Transit source geography

[![Transit source geography](<../assets/figure-contract-r11/figures/ithaca/transit.svg>)](<../assets/figure-contract-r11/figures/ithaca/transit.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

TCAT stops / 2026-10-05 service-day flags. Service-day flags do not certify pedestrian access or observed ridership. The gray retained road graph is geographic context, not a transit route model. Source stops and route shapes do not establish legal pedestrian access, operating service, or observed ridership. This drawing uses the frozen run\_20261005 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/transit.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/transit.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/transit.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/transit.source.json>)

<a id="generation"></a>

## 01 / Trip generation

<a id="coverage-row-06"></a>

The production rule multiplies allocated population by an assumed 0.8 local-activity person trips per person per day and an 0.08 share for the midday hour. It generates 1,779.068516672 person trips. The declared capture and intrazonal rules separate 622.673980835 external or uncaptured trips and 138.767344300 intrazonal trips, leaving 1,017.627191536 internal interzonal productions.

Activity-object weights allocate attractions before normalization to the production margin. The rates, temporal fraction, capture, utility terms and road parameters are engineering assumptions. The generation chart displays saved model quantities and the full zonal file keeps the underlying values; neither is a count of Cornell journeys.

<a id="figure-fs-g01"></a>

##### Trip generation and demand accounting

[![Trip generation and demand accounting](<../assets/figure-contract-r11/figures/ithaca/generation.svg>)](<../assets/figure-contract-r11/figures/ithaca/generation.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

All 11 zones; 11:00–12:00 local activity. The left panel shows saved interzonal productions/attractions. The right panel accounts for all generated persons, including excluded and intrazonal components. No top-12 truncation. Scenario assumptions, not measured trip counts. External and intrazonal components do not enter interzonal assignment; attractions are normalized to productions. This drawing uses the frozen run\_20261005 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/generation.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/generation.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/generation.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/generation.source.json>)

<a id="distribution"></a>

## 02 / Trip distribution

<a id="coverage-row-07"></a>

Directed drive times on the turn-expanded network provide the impedance used by the exponential gravity model. IPF processes the complete positive feasible zone-pair set. Seven iterations leave a maximum margin error of 9.870046824×10⁻⁸ persons.

A single PA-to-OD conversion allocates 60% forward and 40% reverse, producing 110 positive directed pairs and conserving 1,017.627191536 persons. No pair is selected merely to keep a small demonstration. Unreachable cells would remain structural zeros; a positive unreachable margin would fail the model instead of receiving an invented finite cost. The log(1 + trips) heatmap is indexed demand, not a geographic map.

<a id="figure-fs-d01"></a>

##### Trip distribution and directed OD margins

[![Trip distribution and directed OD margins](<../assets/figure-contract-r11/figures/ithaca/distribution.svg>)](<../assets/figure-contract-r11/figures/ithaca/distribution.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Full 11×11 model-zone matrix including zero cells; 110 positive OD pairs and 1,017.627191536 persons in 11:00–12:00 local activity. Colours are log(1+persons); margins are untransformed directed OD totals after PA direction. Every model zone is retained. Zero rows and columns remain visible; intrazonal cells are structural zeros. Labels use the final six digits of long zone IDs. This drawing uses the frozen run\_20261005 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/distribution.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/distribution.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/distribution.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/distribution.source.json>)

<a id="mode"></a>

## 03 / Mode choice

<a id="coverage-row-04"></a>

<a id="coverage-row-08"></a>

The OD model compares routed drive and walk costs with a direct TCAT service approximation from the frozen timetable. Four sample departure ticks and approximate walk-stop snaps produce transit availability for 98 pairs. A 45-minute walking threshold leaves walking available for 108 of the 110 pairs.

Saved aggregate demand is approximately 547.640 drive, 172.911 transit and 297.077 walk persons. Every modeled person has an available option. The USD 1.50 transit fare comes from the frozen fare table; USD 2 parking, USD 15/hour value of time, zero alternative constants and occupancy 1.3 are assumed. Transit has no transfers or reliability adjustment and is not validated against boardings.

Driving converts once to 421.261325634 PCE for the hour. Walking and transit remain person-trip outputs without their own capacity assignment. These conditional utilities explain modeled differences between alternatives; they are not estimates of observed modal shares.

<a id="figure-fs-m01"></a>

##### Mode choice: demand, cost and availability

[![Mode choice: demand, cost and availability](<../assets/figure-contract-r11/figures/ithaca/mode.svg>)](<../assets/figure-contract-r11/figures/ithaca/mode.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved OD-specific choice in 11:00–12:00 local activity; sums over every positive-demand OD. Persons, person-weighted generalized minutes, and available OD counts have separate axes. Transit is included only where saved as available. Generalized cost includes model time and money terms. Person totals precede the separate occupancy-to-PCE conversion. This drawing uses the frozen run\_20261005 evidence. Later supplementary datasets are separate and are not implied to have entered this scenario.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/mode.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/mode.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/mode.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/mode.source.json>)

<a id="assignment"></a>

## 04 / Physical-link assignment

<a id="coverage-row-09"></a>

The road representation contains 15,148 physical directed links, plus separate turn and zone-access arcs. Shared OSM topology, rather than intersecting lines in a drawing, defines connections. Each zone access point is an existing public-road node in the same tract. That choice supports a tract-level model but does not audit building entrances or every lawful movement.

All 110 positive vehicle OD pairs reach assignment. The first all-or-nothing loading meets the frozen 10⁻⁴ gap threshold, with a reported gap of zero, objective 1,638.731757686 PCE-min and no FW updates. Maximum node-balance residual is about 4.26×10⁻¹⁴ PCE. This numerical stop does not demonstrate that actual midday traffic is uncongested.

The original top-link and loading-detail charts retain physical roads only; their full table includes every physical link. The maximum modeled physical v/c is 0.1126. The R3 spatial companion joins the same saved flow to the frozen original two-point OSM segments, whose identity S0 checked. It supplies the missing geographical assignment view without recomputing traffic or drawing virtual movements as roads.

<a id="figure-fs-a01"></a>

<a id="figure-fs-a03"></a>

##### Frank–Wolfe: physical-road loading

[![Frank–Wolfe: physical-road loading](<../assets/figure-contract-r11/figures/ithaca/ithaca-fs_a03.svg>)](<../assets/figure-contract-r11/figures/ithaca/ithaca-fs_a03.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

v/c and BPR travel time for top 10 loaded physical road links; turn/access connectors excluded; v/c&gt;1 is allowed in static BPR. Single-pass engineering scenario; no local empirical calibration. City demand area 7.50 km2; 13.24 km2 road support

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/ithaca-fs_a03.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/ithaca-fs_a03.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/ithaca-fs_a03.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/ithaca-fs_a03.source.json>)

<a id="figure-r9-fw-physical-flow"></a>

##### Frank–Wolfe: physical flow and distribution

[![Frank–Wolfe: physical flow and distribution](<../assets/figure-contract-r11/figures/ithaca/fw-physical-flow.svg>)](<../assets/figure-contract-r11/figures/ithaca/fw-physical-flow.svg>)

<details markdown="1">
<summary>Description, units and scope</summary>

Saved Ithaca static Frank–Wolfe endpoint for 11:00–12:00 local activity. The map and 22-bin histogram use the same complete 15,148-link physical-flow vector, including 12,789 exact-zero links; 2,359 links exceed 1e-6 PCE. Flow is PCE accumulated during the declared one-hour period, not persons or flow per simulation time step. The map uses a square-root sequential color scale with original-unit ticks and gray road context; histogram counts are linear and no links are omitted. Turn, access and other nonphysical solver arcs are excluded. Only the saved iteration-0 initialization exists; FW performed zero subsequent updates. Reciprocal directed arcs may overlap geometrically; flows are not summed. This is a modeled engineering scenario, not observed traffic. © OpenStreetMap contributors / ODbL 1.0. R11 layout repair: map and all-link histogram share measured top and bottom panel bounds. The original saved physical-link IDs, exact flow vector, geographic vertices, display offsets, histogram edges and counts remain unchanged.

</details>

[PNG](<../assets/figure-contract-r11/figures/ithaca/fw-physical-flow.png>) · [SVG](<../assets/figure-contract-r11/figures/ithaca/fw-physical-flow.svg>) · [PDF](<../assets/figure-contract-r11/figures/ithaca/fw-physical-flow.pdf>) · [Source record](<../assets/figure-contract-r11/figures/ithaca/fw-physical-flow.source.json>)

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="figure-fs-a04"></a>

</details>

<a id="results"></a>

## Saved results and assignment checks

<a id="coverage-row-10"></a>

S0 R3 passed saved-result replay, a fresh four-stage run from the frozen inputs, saved-versus-fresh table comparison and six negative controls. These checks extend the earlier producer validation, which tested receipt continuity, boundary arithmetic, OD balance, mode availability and probabilities, PCE conversion and path/link reconstruction.

Earlier preflight work also reproduced source summaries in a fresh path containing spaces and Chinese characters. The subsequent City GIS replay matched five output tables and its summary. Separate S2 replay and negative tests addressed broken link references, missing hashes, unordered points used as paths, changed parent or weight records and missing current outputs. Such source and interface tests are distinct from the accepted four-stage solve.

<details markdown="1">
<summary>Saved initial checks and original endpoint views</summary>

<a id="figure-fs-a02"></a>

##### Frank–Wolfe: the saved initial check

<a id="table-r11-ithaca-initial-fw"></a>

[![Frank–Wolfe: the saved initial check](<../assets/figure-contract-r12/figures/ithaca/ithaca-initial-fw.svg>)](<../assets/figure-contract-r12/figures/ithaca/ithaca-initial-fw.svg>)

Only the actual saved iteration 0 is shown: objective 1638.7317576864 PCE·min/h and relative gap 0, against the unchanged 0.0001 stopping gate. There were zero updates. Each panel contains a single numerical point; no missing trajectory or second state is inferred. The companion physical-flow map reads this method’s own saved vector. This frozen original demand instance is not relabelled as a later selected-demand or transit-revision run.

[SVG](<../assets/figure-contract-r12/figures/ithaca/ithaca-initial-fw.svg>) · [PNG](<../assets/figure-contract-r12/figures/ithaca/ithaca-initial-fw.png>) · [PDF](<../assets/figure-contract-r12/figures/ithaca/ithaca-initial-fw.pdf>) · [Source data](<../assets/figure-contract-r12/figures/ithaca/ithaca-initial-fw.source.json>)

</details>

<a id="parity-ithaca-static-inputs"></a>

## Static assignment: demand margins and physical endpoints

<a id="figure-parity-ithaca-assignment-margins"></a>

##### Static assignment demand margins

[![Static assignment demand margins](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-margins.svg>)](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-margins.svg>)

S110: 110 positive source-zone OD pairs, 110 loaded solver-node OD pairs and 421.261325634 PCE/hour. Origin and destination margins sum the selected assignment PCE by source zone, after the saved mode/occupancy conversion. All source-zone polygons, including any zero selected demand, use a common square-root normalization with ticks in original PCE/hour. S110 contains 110 original zone-state ODs. The margin polygons are the original R2 City-block unions for the 11 populated zones, not the earlier preflight tract footprint. Virtual zone-state demand is joined through original connectors to saved physical OSM access nodes for display only; solver ODs are not aggregated. These are modeled assignment-input quantities, not population generation, observed traffic or assigned link flow. Both panels share one map extent; context roads outside this input footprint are clipped only for display.

[Complete evidence · same figure](<#figure-parity-ithaca-assignment-margins>) · [SVG](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-margins.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-margins.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-margins.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-margins.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-margins.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-margins.caption.md>)

<a id="figure-parity-ithaca-assignment-endpoints"></a>

##### Physical demand endpoints

[![Physical demand endpoints](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-endpoints.svg>)](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-endpoints.svg>)

S110: 110 positive source-zone OD pairs, 110 loaded solver-node OD pairs and 421.261325634 PCE/hour. Original access records locate 11 loaded physical origins and 11 loaded physical destinations. Open circles show the frozen access system and filled colors show selected endpoint PCE/hour. The largest loaded endpoint in each panel is labelled by its physical source ID (or the saved M-state road-midpoint identifier). Each side sums to the same total; this aggregation is for display only. S110 contains 110 original zone-state ODs. The margin polygons are the original R2 City-block unions for the 11 populated zones, not the earlier preflight tract footprint. Virtual zone-state demand is joined through original connectors to saved physical OSM access nodes for display only; solver ODs are not aggregated. These are modeled assignment-input quantities, not population generation, observed traffic or assigned link flow. Both panels share one map extent; context roads outside this input footprint are clipped only for display.

[Complete evidence · same figure](<#figure-parity-ithaca-assignment-endpoints>) · [SVG](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-endpoints.svg>) · [PNG](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-endpoints.png>) · [PDF](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-endpoints.pdf>) · [Plot data](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-endpoints.plot.json>) · [Source record](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-endpoints.source.json>) · [Caption](<../assets/template-parity-20261008/static-inputs/ithaca/assignment-endpoints.caption.md>)

<a id="figure-parity-ithaca-finite-physical-flow-input-context"></a>

##### Finite-path reference and physical support

[![Finite-path reference and physical support](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.svg>)](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.svg>)

Ithaca S110 finite-path own saved physical-link vector: 110 positive vehicle OD pairs, 421.2613256336401 PCE/hour, 550 frozen candidate paths and all 15,148 directed physical roads. The map uses original road vertices; the 22-bin histogram includes every physical road, including exact zeros. The absolute colour scale is the same square-root scale used in the companion Native card. The vector is read from finite/link\_flow.csv and checked by multiplication of its own saved 550-path vector and incidence matrix; it is not copied from FW. The finite run records one solver iteration, so this endpoint loading is not an iteration-history figure. FW stopped at its initial check; finite and FW agree to floating-point precision for this instance. All raw values remain in plot data; only |flow|≤1e-12 PCE/hour is hidden from coloured map overlays. Modelled engineering demand, not observed traffic.

[Complete evidence · same figure](<#figure-parity-ithaca-finite-physical-flow>) · [SVG](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.svg>) · [PNG](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.png>) · [PDF](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.pdf>) · [Plot data](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.plot.json>) · [Source record](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.source.json>) · [Caption](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.caption.md>)

<a id="figure-parity-ithaca-native-physical-flow-input-context"></a>

##### Native L3 physical flows against same-instance FW

[![Native L3 physical flows against same-instance FW](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.svg>)](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.svg>)

Ithaca S110 Native rank 26 own saved physical-link flow (a), signed rank 26−FW (b) and rank 52−FW (c), and all 15,148 rank-26 physical roads in a 22-bin histogram (d). Both Native vectors are read directly from their own outer-04 saved v arrays; exact source link IDs select the physical rows. Saved basis/pool products verify these arrays to below 1e-10 PCE/hour without running a solver or evaluator. The absolute map shares the finite card’s square-root scale; both difference maps share one symmetric zero-centred linear scale, in original PCE/hour, with the scientific-notation multiplier printed at each colourbar. Maximum absolute differences are 2.23848246605e-08 and 5.08217254946e-08 PCE/hour. These tiny numerical differences are not a traffic improvement. Rank 26/52 actually have four saved outer states; this card shows their final geographic endpoint and does not replace the saved-history card. FW belongs to this same S110 instance and stops at its initial check. All raw zeros and near-zero values remain in the histogram and plot data; only |value|≤1e-12 is hidden from coloured overlays. Modelled one-hour engineering scenario, not observations.

[Complete evidence · same figure](<#figure-parity-ithaca-native-physical-flow>) · [SVG](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.svg>) · [PNG](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.png>) · [PDF](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.pdf>) · [Plot data](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.plot.json>) · [Source record](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.source.json>) · [Caption](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.caption.md>)

<a id="parity-ithaca-static-methods"></a>

## Static assignment: method-specific physical flow

<a id="figure-parity-ithaca-finite-physical-flow"></a>

##### Finite-path reference and physical support

[![Finite-path reference and physical support](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.svg>)](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.svg>)

Ithaca S110 finite-path own saved physical-link vector: 110 positive vehicle OD pairs, 421.2613256336401 PCE/hour, 550 frozen candidate paths and all 15,148 directed physical roads. The map uses original road vertices; the 22-bin histogram includes every physical road, including exact zeros. The absolute colour scale is the same square-root scale used in the companion Native card. The vector is read from finite/link\_flow.csv and checked by multiplication of its own saved 550-path vector and incidence matrix; it is not copied from FW. The finite run records one solver iteration, so this endpoint loading is not an iteration-history figure. FW stopped at its initial check; finite and FW agree to floating-point precision for this instance. All raw values remain in plot data; only |flow|≤1e-12 PCE/hour is hidden from coloured map overlays. Modelled engineering demand, not observed traffic.

[Complete evidence · same figure](<#figure-parity-ithaca-finite-physical-flow>) · [SVG](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.svg>) · [PNG](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.png>) · [PDF](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.pdf>) · [Plot data](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.plot.json>) · [Source record](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.source.json>) · [Caption](<../assets/template-parity-20261008/static-methods/ithaca/finite-physical-flow.caption.md>)

<a id="figure-parity-ithaca-native-physical-flow"></a>

##### Native L3 physical flows against same-instance FW

[![Native L3 physical flows against same-instance FW](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.svg>)](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.svg>)

Ithaca S110 Native rank 26 own saved physical-link flow (a), signed rank 26−FW (b) and rank 52−FW (c), and all 15,148 rank-26 physical roads in a 22-bin histogram (d). Both Native vectors are read directly from their own outer-04 saved v arrays; exact source link IDs select the physical rows. Saved basis/pool products verify these arrays to below 1e-10 PCE/hour without running a solver or evaluator. The absolute map shares the finite card’s square-root scale; both difference maps share one symmetric zero-centred linear scale, in original PCE/hour, with the scientific-notation multiplier printed at each colourbar. Maximum absolute differences are 2.23848246605e-08 and 5.08217254946e-08 PCE/hour. These tiny numerical differences are not a traffic improvement. Rank 26/52 actually have four saved outer states; this card shows their final geographic endpoint and does not replace the saved-history card. FW belongs to this same S110 instance and stops at its initial check. All raw zeros and near-zero values remain in the histogram and plot data; only |value|≤1e-12 is hidden from coloured overlays. Modelled one-hour engineering scenario, not observations.

[Complete evidence · same figure](<#figure-parity-ithaca-native-physical-flow>) · [SVG](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.svg>) · [PNG](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.png>) · [PDF](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.pdf>) · [Plot data](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.plot.json>) · [Source record](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.source.json>) · [Caption](<../assets/template-parity-20261008/static-methods/ithaca/native-physical-flow.caption.md>)

<a id="parity-ithaca-construction"></a>

## Time-expanded network and path examples

<a id="figure-parity-ithaca-time-layers"></a>

##### Time-expanded network in layers

[![Time-expanded network in layers](<../assets/template-parity-20261008/construction/ithaca/time-layers.svg>)](<../assets/template-parity-20261008/construction/ithaca/time-layers.svg>)

Ithaca: the highlighted three saved arcs follow two physical road movements joined by a zero-time turn. This is an excerpt of an existing CG path, not a new optimization. Full graph and path records are from the accepted private package; the new presentation remains local/private. Physical node labels are schematic roles; exact routing state and link identifiers are retained in plot data. Early timing, road movement and zero-time turns come from saved arcs, not an interpolation. The slanted planes and horizontal positions are schematic display coordinates. A−/A+ and B−/B+ denote entry/exit routing states, not original intersections. Exact state IDs, physical-road IDs and time indices are retained in plot data.

[Complete evidence · same figure](<#figure-parity-ithaca-time-layers>) · [SVG](<../assets/template-parity-20261008/construction/ithaca/time-layers.svg>) · [PNG](<../assets/template-parity-20261008/construction/ithaca/time-layers.png>) · [PDF](<../assets/template-parity-20261008/construction/ithaca/time-layers.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/ithaca/time-layers.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/ithaca/time-layers.source.json>) · [Caption](<../assets/template-parity-20261008/construction/ithaca/time-layers.caption.md>)

<a id="figure-parity-ithaca-local-construction"></a>

##### Local construction details

[![Local construction details](<../assets/template-parity-20261008/construction/ithaca/local-construction.svg>)](<../assets/template-parity-20261008/construction/ithaca/local-construction.svg>)

Ithaca: panels map two source-directed physical roads to four routing entry/exit states and their time-indexed movements. This is an excerpt of an existing CG path, not a new optimization. Full graph and path records are from the accepted private package; the new presentation remains local/private. Physical node labels are schematic roles; exact routing state and link identifiers are retained in plot data. Early timing, road movement and zero-time turns come from saved arcs, not an interpolation. The turn has zero elapsed time; physical road durations are positive. No waiting arc is drawn and terminal bookkeeping states are outside this local excerpt. Plot data carry all exact source IDs, field values, and short-label aliases.

[Complete evidence · same figure](<#figure-parity-ithaca-local-construction>) · [SVG](<../assets/template-parity-20261008/construction/ithaca/local-construction.svg>) · [PNG](<../assets/template-parity-20261008/construction/ithaca/local-construction.png>) · [PDF](<../assets/template-parity-20261008/construction/ithaca/local-construction.pdf>) · [Plot data](<../assets/template-parity-20261008/construction/ithaca/local-construction.plot.json>) · [Source record](<../assets/template-parity-20261008/construction/ithaca/local-construction.source.json>) · [Caption](<../assets/template-parity-20261008/construction/ithaca/local-construction.caption.md>)

<a id="parity-ithaca-finite"></a>

## Optimization on the time-expanded network

<a id="figure-parity-ithaca-cg-phase1"></a>

##### Phase I: artificial-flow clearance

[![Phase I: artificial-flow clearance](<../assets/template-parity-20261008/optimization/ithaca/cg-phase1.svg>)](<../assets/template-parity-20261008/optimization/ithaca/cg-phase1.svg>)

This implementation uses one nonnegative artificial variable per restricted-master capacity row, not per commodity. The saved Phase I state contains four path-flow variables followed by 110 actual artificial capacity slacks, all exactly zero. The left panel sums those saved slacks; the heatmap retains all 110 rows at their actual saved round. Row-to-dynamic-arc indices are preserved in plot data. The color range uses the frozen 1e-8 PCE total-slack tolerance only as a display reference, not as a separate per-row gate. Zero capacity slack is not a plot of OD unmet demand. Four seed paths suffice; no extra solve or intermediate state is inferred.

[Complete evidence · same figure](<#figure-parity-ithaca-cg-phase1>) · [SVG](<../assets/template-parity-20261008/optimization/ithaca/cg-phase1.svg>) · [PNG](<../assets/template-parity-20261008/optimization/ithaca/cg-phase1.png>) · [PDF](<../assets/template-parity-20261008/optimization/ithaca/cg-phase1.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/ithaca/cg-phase1.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/ithaca/cg-phase1.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/ithaca/cg-phase1.caption.md>)

<a id="figure-parity-ithaca-cg-phase2"></a>

##### Phase II objective

[![Phase II objective](<../assets/template-parity-20261008/optimization/ithaca/cg-phase2.svg>)](<../assets/template-parity-20261008/optimization/ithaca/cg-phase2.svg>)

One actual Phase II round has real objective 0.91842826893935303 PCE·min. The same-graph independent reference is 0.9184282689393537. The four seed paths suffice and no new column is added. The Phase I artificial objective is not joined to the Phase II cost.

[Complete evidence · same figure](<#figure-parity-ithaca-cg-phase2>) · [SVG](<../assets/template-parity-20261008/optimization/ithaca/cg-phase2.svg>) · [PNG](<../assets/template-parity-20261008/optimization/ithaca/cg-phase2.png>) · [PDF](<../assets/template-parity-20261008/optimization/ithaca/cg-phase2.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/ithaca/cg-phase2.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/ithaca/cg-phase2.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/ithaca/cg-phase2.caption.md>)

<a id="figure-parity-ithaca-cg-pricing"></a>

##### Independent pricing closure

[![Independent pricing closure](<../assets/template-parity-20261008/optimization/ithaca/cg-pricing.svg>)](<../assets/template-parity-20261008/optimization/ithaca/cg-pricing.svg>)

One full-DAG minimum reduced-cost check is saved in each phase. Phase I units are dimensionless; Phase II units are minutes, with the unchanged absolute closure tolerance 1e-7. These are the global minima, not invented per-commodity reduced costs. Two phases are separate checks, not two iterations of one common objective.

[Complete evidence · same figure](<#figure-parity-ithaca-cg-pricing>) · [SVG](<../assets/template-parity-20261008/optimization/ithaca/cg-pricing.svg>) · [PNG](<../assets/template-parity-20261008/optimization/ithaca/cg-pricing.png>) · [PDF](<../assets/template-parity-20261008/optimization/ithaca/cg-pricing.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/ithaca/cg-pricing.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/ithaca/cg-pricing.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/ithaca/cg-pricing.caption.md>)

<a id="figure-parity-ithaca-lr-bounds"></a>

##### Lagrangian bounds and certified gap

[![Lagrangian bounds and certified gap](<../assets/template-parity-20261008/optimization/ithaca/lr-bounds.svg>)](<../assets/template-parity-20261008/optimization/ithaca/lr-bounds.svg>)

One actual evaluated LR state. Own lower and recovered feasible upper are both 0.918428268939353 PCE·min; they overlap at displayed precision. The original 1% certificate is retained. This is the frozen four-OD pulse; capacity redundancy does not establish a geographic-size cause.

[Complete evidence · same figure](<#figure-parity-ithaca-lr-bounds>) · [SVG](<../assets/template-parity-20261008/optimization/ithaca/lr-bounds.svg>) · [PNG](<../assets/template-parity-20261008/optimization/ithaca/lr-bounds.png>) · [PDF](<../assets/template-parity-20261008/optimization/ithaca/lr-bounds.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/ithaca/lr-bounds.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/ithaca/lr-bounds.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/ithaca/lr-bounds.caption.md>)

<a id="figure-parity-ithaca-lr-prices"></a>

##### Capacity prices at the best dual bound

[![Capacity prices at the best dual bound](<../assets/template-parity-20261008/optimization/ithaca/lr-prices.svg>)](<../assets/template-parity-20261008/optimization/ithaca/lr-prices.svg>)

The saved best-bound multiplier vector contains 36,360 original dynamic-arc entries, all exactly zero. Consequently there is no nonempty top-price ranking. The second panel sums every timed multiplier by its real 30-second departure index, including the zero sums; source/sink entries without a time suffix are excluded only from the time aggregation. Empty positive support is shown explicitly, not replaced with another city or method. These numerical details remain a private local preview.

[Complete evidence · same figure](<#figure-parity-ithaca-lr-prices>) · [SVG](<../assets/template-parity-20261008/optimization/ithaca/lr-prices.svg>) · [PNG](<../assets/template-parity-20261008/optimization/ithaca/lr-prices.png>) · [PDF](<../assets/template-parity-20261008/optimization/ithaca/lr-prices.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/ithaca/lr-prices.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/ithaca/lr-prices.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/ithaca/lr-prices.caption.md>)

<a id="figure-parity-ithaca-lr-recovery"></a>

##### Path-pool growth and primal recovery

[![Path-pool growth and primal recovery](<../assets/template-parity-20261008/optimization/ithaca/lr-recovery.svg>)](<../assets/template-parity-20261008/optimization/ithaca/lr-recovery.svg>)

One actual path-pool record and one actual feasible recovery call are shown in separate panels. The four paths belong to this method’s own pool; the objective is the saved recovered feasible upper bound. No intermediate call, pool growth or capacity-price effect is invented. A filled marker denotes a feasible call, as in Boston/Hong Kong.

[Complete evidence · same figure](<#figure-parity-ithaca-lr-recovery>) · [SVG](<../assets/template-parity-20261008/optimization/ithaca/lr-recovery.svg>) · [PNG](<../assets/template-parity-20261008/optimization/ithaca/lr-recovery.png>) · [PDF](<../assets/template-parity-20261008/optimization/ithaca/lr-recovery.pdf>) · [Plot data](<../assets/template-parity-20261008/optimization/ithaca/lr-recovery.plot.json>) · [Source record](<../assets/template-parity-20261008/optimization/ithaca/lr-recovery.source.json>) · [Caption](<../assets/template-parity-20261008/optimization/ithaca/lr-recovery.caption.md>)

<a id="figure-parity-ithaca-admm-saved-state"></a>

##### ADMM convergence and feasibility

[![ADMM convergence and feasibility](<../assets/figure-contract-r12/figures/ithaca/admm-saved-state.svg>)](<../assets/figure-contract-r12/figures/ithaca/admm-saved-state.svg>)

Four diagnostic panels follow the Hong Kong ADMM figure: original-unit feasibility, primal consensus, rho-scaled dual update, and log10 absolute objective error against the independent same-graph reference. This instance saved exactly one completed outer update, shown as a point rather than an invented convergence curve. Balance, capacity, and primal use PCE; rho-scaled dual and its own threshold use minutes. Only exact-zero residuals use a labeled 1e-16 display floor; positive residuals are unchanged. Objective-error display floor is 1e-15 PCE·min. Saved internal thresholds and the 1e-5 PCE feasibility gate are retained. All displayed states meet the frozen independent gates; objective agreement is not a claim of identical link flows.

[Complete evidence · same figure](<#figure-parity-ithaca-admm-saved-state>) · [SVG](<../assets/figure-contract-r12/figures/ithaca/admm-saved-state.svg>) · [PNG](<../assets/figure-contract-r12/figures/ithaca/admm-saved-state.png>) · [PDF](<../assets/figure-contract-r12/figures/ithaca/admm-saved-state.pdf>) · [Plot data](<../assets/figure-contract-r12/figures/ithaca/admm-saved-state.plot.json>) · [Source record](<../assets/figure-contract-r12/figures/ithaca/admm-saved-state.source.json>)

<a id="figure-parity-ithaca-admm-final-conservation"></a>

##### Commodity conservation at the final state

[![Commodity conservation at the final state](<../assets/template-parity-20261008/admm/ithaca/admm-final-conservation.svg>)](<../assets/template-parity-20261008/admm/ithaca/admm-final-conservation.svg>)

Final saved ADMM own-x state at completed outer 1. Reconstruct outflow minus inflow minus commodity supply in the original units and exact saved arc order, with the loader's lexical node order. The heatmap selects the 35 nodes with the largest maximum absolute residual across all four commodities; ties retain lexical node order. All 15,322 nodes were included in this selection. The complete per-commodity maximum residuals and worst-node IDs reproduce the saved independent check exactly; overall maximum is 6.19070599701655e-15 PCE against the unchanged 1e−5 PCE gate. Colors show log10(max(|residual|,1e−15 PCE)/(1 PCE)); sub-floor values and exact zeros share the floor color, with their raw signed and absolute values preserved in plot data. This is a final spatial conservation diagnostic, not an iteration-history heatmap. The run completed one actual update on the frozen capacity-nonbinding T4 pulse, not a multi-iteration stress test. Private local derivative of the accepted saved result; no new public asset release or optimizer run is claimed. Engineering scenario, not observed traffic.

[Complete evidence · same figure](<#figure-parity-ithaca-admm-final-conservation>) · [SVG](<../assets/template-parity-20261008/admm/ithaca/admm-final-conservation.svg>) · [PNG](<../assets/template-parity-20261008/admm/ithaca/admm-final-conservation.png>) · [PDF](<../assets/template-parity-20261008/admm/ithaca/admm-final-conservation.pdf>) · [Plot data](<../assets/template-parity-20261008/admm/ithaca/admm-final-conservation.plot.json>) · [Source record](<../assets/template-parity-20261008/admm/ithaca/admm-final-conservation.source.json>) · [Caption](<../assets/template-parity-20261008/admm/ithaca/admm-final-conservation.caption.md>)

<a id="figure-parity-ithaca-admm-physical-flow"></a>

##### ADMM and arc-flow LP: physical-link flow

[![ADMM and arc-flow LP: physical-link flow](<../assets/template-parity-20261008/admm/ithaca/admm-physical-flow.svg>)](<../assets/template-parity-20261008/admm/ithaca/admm-physical-flow.svg>)

Own saved ADMM x at its one completed update and the independent same-graph LP are projected onto the 684 physical links instantiated in the exact frozen Ithaca T4 graph. Sum across commodities and time, retain only physical\_road arcs, and join exact GMNS link IDs; each physical\_fraction is 1, so no serial-segment double counting occurs. The remaining 14,464 of 15,148 original physical roads appear as grey context, not solved zero-flow roads. Panels a–b share a square-root absolute PCE scale; panel c uses a distinct symmetric signed ADMM-minus-LP scale. Panel d includes every instantiated link, including zeros, with the identity line and equal linear axes. The actual maximum absolute difference is 2.26215512725091e-14 PCE and is not rounded to zero. All geometry uses original OSM endpoint coordinates with a common local metric projection; no schematic node positions are invented. The original IN-state loading and first physical-road traversal are preserved. Fixed-cost four-OD departure pulse, 0.656755360434 PCE; physical capacity is nonbinding for this frozen instance. This is a final spatial comparison, not evidence of a multi-round trajectory, area-size causality or measured traffic. Private local derivative; no new public asset release or optimizer run is claimed. © OpenStreetMap contributors, ODbL 1.0.

[Complete evidence · same figure](<#figure-parity-ithaca-admm-physical-flow>) · [SVG](<../assets/template-parity-20261008/admm/ithaca/admm-physical-flow.svg>) · [PNG](<../assets/template-parity-20261008/admm/ithaca/admm-physical-flow.png>) · [PDF](<../assets/template-parity-20261008/admm/ithaca/admm-physical-flow.pdf>) · [Plot data](<../assets/template-parity-20261008/admm/ithaca/admm-physical-flow.plot.json>) · [Source record](<../assets/template-parity-20261008/admm/ithaca/admm-physical-flow.source.json>) · [Caption](<../assets/template-parity-20261008/admm/ithaca/admm-physical-flow.caption.md>)

<a id="reproduction"></a>

## Reproduction and input identity

<a id="coverage-row-19"></a>

The public reproducibility archive is not yet available.

Producer stage receipts: Python 3.11.4; PYTHONDONTWRITEBYTECODE=1.

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

The model is one static forward pass using 2020 residents and 2026 OSM/GTFS, with uncalibrated rates, prices, speed and capacity assumptions. Assigned costs are not iterated back into generation, distribution or mode choice. No parcel-access audit, comprehensive pedestrian movement audit or observed traffic calibration is included.

The displayed source figures follow the approved public asset boundary. Raw City GIS, raw TCAT, personal traces and the historical photograph are not included in this preview.

A valid new visual does not authorize a different purpose or time period. HBO\_LOCAL\_ACTIVITY at 11:00–12:00, the separate demand and support areas, activity proxies and source vintages remain visible wherever the result is presented. Map-derived displays retain © OpenStreetMap contributors and ODbL attribution.

The bounded OSM trackpoint request yielded 5,000 points in four API segments. One five-point segment has increasing time and was classed ORDERED\_TRACE; the remaining 4,995 points have duplicate times and were classed ORDERED\_NO\_TIME. OSM privacy handling can affect order, so even the timed segment is not automatically a recovered trip. Exact traces and timestamps remain private, and travel mode is unknown.

No topology-aware matching output was produced for that sample. It cannot establish motor journeys, speeds from untimed segments, total trip volume or sampling penetration. A later matcher would need explicit radius and gap rules, directed connectivity and turn checks, and an account of unmatched portions.

Historical crossing imagery provides context only. No current marking, lane count, legal movement, georeferencing or safety condition follows from the dated imagery; the image itself is not included in the preview.

The earlier S2 exercise covers eight objects: five crossing points, two clipped lines and one clipped tract polygon. Levels 12, 14 and 16 yield 104 associations and 24 object-level groups. Point ownership, clipped-length/area weights and parent conservation passed independent checking and replay. Four-vertex cell geometry is an approximation; the sample is not citywide, does not redistribute population and does not aggregate nonadditive travel times or accessibility.

<a id="sources"></a>

## Sources and display provenance

- [official Cornell Ithaca map](<https://www.cornell.edu/about/maps/?loc=Arts+Quad&amp;zoom=16>)
- [October 2025 campus map](<https://fcs.cornell.edu/sites/default/files/2025-10/IthacaCampus_October2025.pdf>)
- [OpenStreetMap API](<https://wiki.openstreetmap.org/wiki/Api06>)
- [ODbL 1.0](<https://www.openstreetmap.org/copyright>)
- [City of Ithaca's 2020 tract service](<https://services5.arcgis.com/R1JbITZvSQHJsl5r/arcgis/rest/services/Tompkins_County_Census_Tracts_2020/FeatureServer/0>)
- [2020 census block service](<https://services5.arcgis.com/R1JbITZvSQHJsl5r/ArcGIS/rest/services/Census_Blocks_2020/FeatureServer/0>)
- [Census P1 and H1 tables](<https://www.census.gov/programs-surveys/decennial-census/about/rdo/summary-files.html>)
- [Census TIGERweb ACS2024 geography service](<https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/10>)
- [TCAT service](<https://www.tcatbus.com/>)
- [City GIS layer](<https://services5.arcgis.com/R1JbITZvSQHJsl5r/ArcGIS/rest/services/Existing_Sidewalks/FeatureServer/0>)
- [OSM trace visibility guidance](<https://wiki.openstreetmap.org/wiki/Visibility_of_GPS_traces>)
- [KartaView](<https://kartaview.org/doc/>)
- [CC BY-SA 4.0](<https://creativecommons.org/licenses/by-sa/4.0/>)
- [KartaView's terms](<https://kartaview.org/terms>)

[Return to the city atlas](<../index.html#ithaca>) · [Back to top](<#document-top>)
