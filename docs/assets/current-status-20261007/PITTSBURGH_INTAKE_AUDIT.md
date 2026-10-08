# Pittsburgh Final v4 主线接收审计

审计时间：2026-10-07T10:18:28.840818+00:00。本次只读 ZIP、现成回执、已保存方法输出和绘图源码；没有运行优化、没有重跑 verify-saved、没有修改生产者文件。

## 1. 可接收的版本与结论

本机 Final v4 四包真实存在，四份 ZIP 的字节数、SHA256 与外置四包回执一致，所有包内 MANIFEST 成员逐个哈希通过。Final v4 Full 的两次已完成回放报告与外置 v4 回执的 report SHA256 精确一致。**旧 READY/FINAL_VALIDATION_RECEIPT 仍写 v3 是包内历史证据关联问题，不是科学实验失败；不能把它们改称 v4 回执。**

科学截点固定为 Full `E:\mobility_computation_lab_v2\deliveries\pittsburgh_algorithm_transfer_r1\MCL_C04_Pittsburgh_Algorithm_Transfer_R2_Final_v4_Private_Full.zip`，SHA256 `9dda906be5135173a39062d0639c3f28e88724cfa35081ddbed6e01acf918447`；manifest 建包时间 2026-10-06T19:15:25.629286+00:00，外部最终双回放时间 2026-10-06T19:24:32.221607+00:00。之后其他任务即使继续运行也不自动进入本批；本审计未接管任何生产者或重计算。

| 包 | 字节 | 受保护 payload | ZIP 文件总条目（含 MANIFEST） | SHA256 |
|---|---:|---:|---:|---|
| Private_Full | 59687654 | 465 | 466 | `9dda906be5135173a39062d0639c3f28e88724cfa35081ddbed6e01acf918447` |
| Review_Lite | 594602 | 115 | 116 | `c29b460645c348430f802ddb3f8c06a62ba136b3bb80d29244e77fdba8beeab5` |
| Volume_Handoff | 546448 | 75 | 76 | `71c0199274d1e999e98dcf7a1e91d5eae014eba1799c174cd8afba1add312b20` |
| ChatGPT_Upload | 426857 | 69 | 70 | `2d30b25d63f1cc68a08312455647e122166a0a91c116aaee99004afa8ebfea72` |

所有 ZIP 的 payload 成员哈希与清单一致。回执中的 member_count 是受保护 payload 数，不能直接称 ZIP 总文件数。

## 2. v3 → v4 精确差异

v3 为 464 个受保护 payload（ZIP 465 文件），v4 为 465 个受保护 payload（ZIP 466 文件）。共同文件中 458 个逐字节不变。

- 新增：record_double_replay.py。
- 删除：无。
- 修改：CHECKPOINT.md, EXECUTION_STATUS.json, FINAL_VALIDATION_RECEIPT.json, README_PACKAGE.md, READY.json, RUN_WINDOW.json。
- `runs/`、`input_snapshot/`、`shared_core_snapshot/`、`figures/` 科学 payload 共 398 份，全数不变。

v4 内部 READY 的 double_saved_replay_revision=v3，内部 FINAL_VALIDATION_RECEIPT 指向 v3 Full 与 464 个 payload；外置 `FINAL_DOUBLE_REPLAY_RECEIPT_v4.json` 绑定真正 v4 SHA256、中文加空格解包位置、两次各 465 成员前后不变、optimizer_calls=0、15/15 负测及重签清单后的语义拒绝。两份报告的哈希都在本机逐一验证。S0 应引用外置 v4 回执并另写增量放行关联，不覆盖历史 v3 原件。

## 3. 方法级状态与数值

| 方法 | 当前冻结 v4 状态 | 关键证据 |
|---|---|---|
| S72 FW | ACCEPTED | 初始化即通过，0 次更新；目标 763.227941458126 PCE·min，完整图 relative gap 6.405076187649018e−15，OD 残差0 |
| S72 finite | ACCEPTED | 360 路径，目标 763.227941458126 PCE·min，完整图 relative gap 1.4895526017788486e−15，OD 残差0 |
| Native rank26 | GATE_NOT_MET | 8 outer；raw OD 残差0.0013572688986740193 PCE > 1e−6；负 gap 不代表可行改进 |
| Native rank52 | GATE_NOT_MET | 8 outer；raw OD 残差0.0013572683147812983 PCE > 1e−6；不以投影恢复替代原始失败终点 |
| HiGHS T LP 尝试 | RESOURCE_LIMIT | 矩阵建成但没有解；private bytes 5,621,870,592 超出4,294,967,296上限；不是 infeasible |
| T exact-DAG LP | ACCEPTED | 同原问题可达域2,015,562变量；原始目标0.24793241990274612，对偶0.2479324199027458 PCE·min |
| T CG | ACCEPTED | 4自有生成列；Phase I人工流0；完整DAG最小reduced cost0；独立复算目标0.2479324199027461 PCE·min |
| T LR | ACCEPTED | 4自有路径；upper0.2479324199027461、lower0.24793241990274573；合同gap3.608224830031759e−16 |
| T ADMM | ACCEPTED | 本城冷启动1 outer并独立同配置冷启动确认；saved目标0.2479324199052491 PCE·min；两份状态SHA相同 |
| ADMM Tier2 | NOT_RUN | 主档与冷启动确认均通过，第二档未触发 |

CG history、LR history、主档和确认 history 均已从冻结 ZIP 读入机读审计，不能从稀少状态制造长曲线。原完整四阶段静态 FW 与 S72 FW 是不同实例，不能把旧四阶段运行或其他历史并入S72初始检查。

T4 总脉冲0.045027548453549955 PCE，最小已建实体时间弧容量2.5 PCE，容量不绑定；早期presolve台账的1.6666666667是早期输入下界，展示本次已建模型以2.5为准。exact-DAG证书通过不等于HiGHS尝试通过，不是拥堵瓶颈性能或需求压力实验。

ADMM 单端点 evaluator 的 `NUMERIC_PASS_CONFIRMATION_PENDING` 是局部检查状态，最终 ACCEPTED 还依据独立冷启动确认及总回放。不能只读单份pending字段否定完整最终接受链。保存 ADMM 目标0.2479324199052491，独立重算0.24793241990524933，差2.22e−16；这是浮点求和差，保留二者来源，不能把两者拼为新迭代。

目标均小于1时，`max(1,|ref|)`合同归一差不是真相对差。LR合同gap=3.608224830031759e-16，按保存U真正除以|U|所得相对差约1.45532594384e-15。ADMM保存绝对/合同归一差2.5029978090174154e−12 PCE·min/数值归一单位，true relative=1.0095484124259508e−11（比例）。独立重算对应绝对差2.5032198536223405e−12、true relative=1.0096379709455717e−11，勿不加来源混用。

## 4. 地理、人员、时间与模型范围

- 真正研究区为 Pittsburgh East End 的研究矩形，包含 Oakland、Shadyside、Squirrel Hill；CMU 是地理参照，不是全部出行人员身份。冻结 WGS84 bbox=[−79.985,40.425,−79.925,40.460]。它不是CMU校园、市政或Census行政边界，更不是全匹兹堡。
- 路由支持halo=[−79.990,40.420,−79.920,40.465]，只为连接道路/合法转向。需求活动范围与路由halo分别记载；不能把halo面积称校园。
- 原输入41个入口区、1,406正车辆OD、2,615.767323562197 PCE/h；S72只取72 OD、约149.92142389506478 PCE/h。17,534物理路+38,850非物理转向=56,384 solver弧。
- 原R2按OUT:origin装载，起点物理段P:origin不在保存路径；全部1,406路径回放通过。改成上游IN会变成另一个问题。额外182.3435812275791 PCE·min只是假设补首段的算术诊断，不是新求解。
- T4只取4 OD、首个五分钟脉冲，08:02:30出发、dt30s、H117；其余OD及其他11个五分钟bin在排除台账中。fractional PCE不是实测跟踪车辆数量。
- T图1,811,888弧：350,106行驶、779,805转向、681,742显式等待、4源连接、231零成本终端记账连接。sink记账不是排队到H。
- 人口/住户2020、就业2023、道路2026；合成工作日08:00—09:00 HBW drive/walk场景。未核验公交路径未入方式模型；不是同时实测交通、当地校准、干净城市holdout或DNL/DUE。

## 5. 现成图件与V边界

Full和Volume_Handoff内已有13组生产者图，分别附PNG/SVG/plot_data/source/caption；PIT_AT00是输入图，另外12组是保存结果，不需要主线另画一套。

| 图ID | 现成用途/边界 |
|---|---|
| PIT_AT00 | Frozen solver-arc roles and four input-only shortest durations; no new method result |
| PIT_S01 | FW and finite solve the same selected static instance. Their objective agreement is a bounded reconstruction result; the initial FW loading already passed. |
| PIT_S02 | Both Native ranks reached the eighth registered outer step; raw OD conservation remains above 1e-6 PCE, so neither rank is accepted. |
| PIT_S03 | These are the largest physical solver-road flows for the 72-OD static cohort. Turn arcs and the excluded 1,334 OD pairs are not represented as additional roads or trips. |
| PIT_S04 | Rank 26/52 changes path coordinates from 98 to 124, while each Native problem still has 56,384 explicit solver-link coordinates before 49,109 provably fixed zero links are removed from its working constraints. |
| PIT_T01 | Actual constructed T graph: physical traversal, turn, wait and connector arcs have distinct meanings. Sink ledger arcs are not queued waiting. |
| PIT_T02 | The four selected directed OD contribute 0.045028 PCE to this pulse. Eleven other 5-minute bins and unselected OD remain outside T; bars do not represent observed 30-second counts. |
| PIT_T03 | Saved two-phase CG reduced costs are checked against all legal DAG arcs for each commodity; a matching objective alone does not establish closure. |
| PIT_T04 | The LR curve uses saved nonnegative arc prices for its dual lower bound and a separately recovered feasible path solution for its upper bound. |
| PIT_T05 | Dots show actual residuals and ticks show registered main-stage stopping thresholds. The zero primal residual uses a stated display floor on the log axis; independent endpoint checks determine scientific status. |
| PIT_T06 | Actual CG-generated source-to-sink paths are decomposed into physical traversals, turn transitions, and explicit waits. Connector arcs are omitted from the bars; path cost and flow remain in plot data. |
| PIT_T07 | Physical road flow sums ADMM x across time copies sharing each GMNS link ID. This is a modeled four-OD pulse result, not an observed 30-second count or a spatial map. |
| PIT_T08 | Exact-DAG LP, CG, LR feasible recovery, and ADMM x use the same frozen T cost and demand. Their agreement tests numerical transfer on this low-demand pulse; it does not measure congestion improvement. |

已核查的 V 旧交付 `deliveries/six_city_preflight_r1/visual_closeout_r3_1/V_READY.json` 日期为2026-10-05，支持既有四阶段展示，不能当作随后C04 Final v4新算法图的V接受记录。它的匹兹堡manifest行已保存于本审计JSON。检查过的声明目录中未找到更新的C04专属V_READY；如果V另有已完成增量，应以确切路径/hash补充接收，不能重复制作。

**须定向交给V的一项具体错误：PIT_T05 dual residual单位。** 当前PIT_T05 SVG把primal/dual共用“· PCE”轴，RESULT_MATRIX的dual_residual_pce键及城市追加文案亦沿用PCE。冻结核明确rho=cost(min)/volume(PCE)，dual=rho×norm(z−z_previous)，因此primal为PCE，dual为min。建议分单位显示两行/两面板，保留真实单次状态与阈值；数值不变。原生产者图与JSON不改写，另存V修正版来源与主线当前说明。这是展示单位错误，不推翻数值接受。

## 6. 本次放行仍需什么

本次身份审计通过不等于公开许可。冻结PUBLIC_CANDIDATE_MANIFEST仍为PENDING_S0_INCREMENTAL_SCIENCE_AND_RIGHTS_REVIEW。请S0只做一次绑定Final v4 Full SHA256和外置v4回执的增量allowlist/quarantine，具体列出可接入的13组图/文案/下载及来源依赖；无新license证据的原始材料仍私有。既有已放行四阶段内容无需反复隐藏。

主线可在对应一城大卷增量接入已核准方法，保留原文件/锚点，把“尚无T结果”更新为方法级接受/资源限制/未达标；02、03比较表与图件源链接同步。Native失败、HiGHS资源界和低需求不绑定容量的范围必须与已接受结果一起说明。

本审计不等于新执行S0验收或浏览器验收；已保存双回放是生产者交付证据，本次只核对其哈希与版本身份。

## 7. 证据入口

- `E:\mobility_computation_lab_v2\deliveries\pittsburgh_algorithm_transfer_r1\DELIVERY_INDEX.md`
- `E:\mobility_computation_lab_v2\deliveries\pittsburgh_algorithm_transfer_r1\FOUR_PACKAGE_RECEIPT_final_v4.json`
- `E:\mobility_computation_lab_v2\deliveries\pittsburgh_algorithm_transfer_r1\FINAL_DOUBLE_REPLAY_RECEIPT_v4.json`
- `E:\mobility_computation_lab_v2\work\pittsburgh_algorithm_transfer_r1\validation\中文 空格 最终四包 v4\check_1\VERIFY_SAVED_REPORT.json`
- `E:\mobility_computation_lab_v2\work\pittsburgh_algorithm_transfer_r1\validation\中文 空格 最终四包 v4\check_2\VERIFY_SAVED_REPORT.json`
- 本附录机读版`PITTSBURGH_INTAKE_AUDIT.json`包括四包校验、差异列表、完整方法矩阵、真实历史、源scope和全部65个图附件hash。
