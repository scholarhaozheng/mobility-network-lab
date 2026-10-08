# R8 增量公开通知

本通知随 `PUBLIC_INCREMENT_RELEASE.json` 中获准的材料一起使用。网页展示由 A 负责；图旁和城市卷中应显式保留适用的来源与模型边界。

道路几何、路段和转向派生的图件及 plot data：© OpenStreetMap contributors。OpenStreetMap 数据采用 ODbL 1.0：<https://www.openstreetmap.org/copyright>；本批公开的 OSM 派生数据库部分按 ODbL 1.0 提供：<https://opendatacommons.org/licenses/odbl/1-0/>。原创建模叙述和图件不因此自动替第三方照片、GPS、商业数据或城市数据授权。Pittsburgh 的 Census/LODES 代理另保留美国 Census Bureau 来源；就业不是行程观测。

- Berkeley：T4 是冻结的 30 秒/H165 有限图；ADMM C2a 170 外层为事后诊断延续的正式通过端点。LR300 是原 LR10 已达 1% 门后另行执行的冷启动诊断，不能替换原 LR10。
- Urbana–Champaign：范围是中心城区 21 区子域，S72 与 T4 是不同子集；不是 UIUC 校园或全市。旧 UC_S02 记录 outer8 失败，新 UC_S02_C1 记录 outer9 当前通过。
- Pittsburgh：East End 合成 HBW 场景；S72 与 T4 是选中子集。T4 的微小脉冲使容量不绑定，方法通过不等于实测拥堵改善。Native 未过，HiGHS 尝试受资源限制。
- Chicago：Jane Byrne / West Loop R2 的 S20 与 T4 是独立工程问题。CG 有自身全图原始／对偶证书；HiGHS 仍受资源限制，Native、LR 和 ADMM 未过。失败图只作方法诊断，不作成功卡；独立构造可行 witness 不是 LR 自身恢复。

所有四城结果均非现场 GPS 速度验证、当地需求标定、动态网络装载或 DNL/DUE 结论。原始网络/需求、完整路径与乘子、精确 GPS/S2 和照片没有纳入本批公开 payload。此 S0 决定仅供本地集成，不授权 commit、push 或 deploy。
