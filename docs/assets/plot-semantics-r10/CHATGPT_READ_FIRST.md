# 给 ChatGPT 的阅读须知 · R10

日期：2026-10-08。请先阅读 `CURRENT_PLOT_REVIEW.md` 和 `SHORT_TRACE_REVIEW.json`。本版按 S0 release_v002 更新此前短图／端点表，旧 R9 指南是历史截止，不能把其中已被更新的“当前失败／未接收”继续当作当前状态。

## 这次应回答的核心问题

用户要知道：优化图为什么只见起点、终点或一个点？算法是否错误、区域是否太小？请依记录数、初值、实际停止门和模型结构回答，不能在两个未经证实的原因中强选一个。图的用途一致应先看科学问题、指标、单位和数据总体，再看字体及卡片格式。

## 最新事实必须分开

- Ann Arbor：原 R2 全城 FW（R3发布图）是 0 更新，gap 5.10282992009334e−5 在原 1e−4 内；新 S600 FW 在 1e−5 门下实际 1 更新，保存 iteration 0、1。新 S72 Native26/52 都是初始化通过、0更新。不要混成 Native600，也不要把两条记录说成两次更新。
- Urbana：新 418-OD CUMTD 场景已将 1667.0899464425695 PCE/h 送入 FW；仍 0 更新。初始 max(v/c)≈1.013，不能以零更新推断低负载。原 S72/T4 没有被这个新需求覆盖；新 B 仅是 S72 的独立方法。UC_C1/C2 是方式量和费用组件图，没有获准的新 FW 迭代图。
- Urbana/Pittsburgh 原 T4：脉冲分别约0.051623/0.045028 PCE，最小容量3.75/2.5 PCE；完整证书证明容量冗余。CG每阶段各1条、LR1、ADMM1的短过程有明确模型解释；不支持面积因果结论，也不是从LP答案热启动。
- Pittsburgh：全城FW真实gap为4.773992564434884e−7，不是0。最新S72 Native26/52已到outer14并通过原OD/full-gap/非负/重构门；每rank14点，原outer8失败仍保留。PIT_G05与已修正PIT_T05不同，T4并未续跑。PIT_T05线段比较残差与门限，不是两迭代。
- Ithaca：S110 FW0更新，Native26/52各4外轮。T4为4commodity、36360arctimes、0.6567553604341558PCE脉冲，低于最小2.5PCE容量；CG两阶段各1次、LR1、ADMM1。S0已接收保存态数值端点；producer ADMM pending字段作为历史原字节保留，不能覆盖S0最新结论。四方法端点图不表示四次迭代。
- Chicago：新LR是另行命名的own-pool feasibility＋restricted recovery dual-anchor hybrid，26可行性轮＋10原费用轮，证书0.8744685%；旧纯LR759轮未获自身可行上界仍失败。Native80是20major＋80未压缩minor坐标，3外轮通过，不代表旧rank26/52成功或压缩优势。B有6条真实记录。ADMM完整1–33，新增公开图9–33共25点；容量超量1.491228076PCE，primal/dual约618.27/174.74倍门，仍失败。CG保持原已接受证书，HiGHS资源失败不被覆盖。
- Berkeley及旧参考城市本批未重跑。香港CG PhaseII也只有两个保存检查点；不要宣称旧城全部算法都有长过程。Berkeley原LR10与独立cold-start300分开，不能连成310。

## 科学图型与原单位

静态主图用各方法自己的完整物理流量地图＋全物理路段含0分布。七张新优化相关图是新增证据，不替代24张R9规范主图；端点类别、rank类别与路段编号均不是迭代轴。Boston ADMM目标面板是原始目标，Hong Kong是log10绝对目标误差，不能统一写成相对误差。rho-scaled dual及其门使用min，primal／容量／守恒使用PCE。最终节点热图与跨迭代热图的用途不同。

本指南保留42幅Boston/Hong Kong完整参考表及实际函数/指标/轴。沿用R9函数和SVG核验，不冒称本轮重新逐张实看42幅。新增14张S0 PNG已实看，66公开文件已逐项核验实际bytes/SHA及target。

## 接收与公开身份

本批105决定，66公开＝60COPY_FILE＋6MERGE_TEXT；14PNG＝10accepted＋4diagnostic。旧133项保留，本跟踪链累计199接收项。24张R9是本地保存数据派生图，不因本次接收而冒充已获S0新字节批准。

Ann时刻表派生图仍有定向HOLD；新choice没有FWassignment。公开v002正文已移除受限新需求数值，不从PrivateFull补回。原始GTFS/GPS、精确路线、详细几何、完整状态、私有源码、源行计数CSV及PrivateFull不属于本网页资料。部分获准caption/plot/source保留producer pending字样；S0新结论在旁明确给出，二者分别记账。

## 应如何反馈

请按“城市／实例／图ID → 实际绘制对象 → 保存长度 → 原门与最新状态 → 原因证据 → 仍缺什么”逐项反馈。不要编造迭代、插值成新记录、改阈值、将NaN写成0或让一方法成功替整个城市标绿。短记录不足以证明地理范围是原因；需要区域、需求、容量的控制实验，但本轮没有新增实验。网页整理调用优化器0次、matcher0次，未commit/push/deploy。
