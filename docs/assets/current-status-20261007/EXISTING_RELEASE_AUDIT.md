# 现有 S0 放行证据审计（只读）

记录时间：2026-10-07T10:18:18.886415+00:00。结论仅来自现有回执与逐文件 SHA；没有运行验证器/求解器，没有修改生产者或网页，没有联系其他任务，也没有代行 S0 新放行。

## 当前结论

已找到的 S0 不可变增量仅 v001/v002/v003：5 个 Ann Arbor 文件、2 个 Berkeley 转向图文件、2 个 Urbana 历史照片缩略图。没有在这些清单中找到 Berkeley 新算法/ADMM/LR 或 Pittsburgh Final v4 的新增逐文件公开放行。科学接受与公开许可必须分列。

## 应保留的旧放行

静态 R3 的 PUBLIC_ASSET_RELEASE_MATRIX.csv 记录 2,555 个继承批准文件和182个 INCLUDE_WITH_NOTICE 文件。PUBLIC_WHITELIST.csv 的650行包含139个 INCLUDE_WITH_NOTICE 与511个 PRIVATE_RESEARCH_ONLY，文件名叫白名单不代表所有行可公开。Pittsburgh r3_map/ 和 Urbana r3_map/ 有显式 PRIVATE_RESEARCH_ONLY override。

Berkeley/Pittsburgh 的历史公开矩阵共 58 行（30/28），逐项路径与哈希完整保存在 JSON baseline.target_city_rows。当前主线身份统计：`{"EXACT_PREVIOUSLY_APPROVED_BYTES": 54, "CURRENT_BYTES_DIFFER_FROM_APPROVED_VERSION": 4}`。当前字节不同仅表示不能冒充旧版本，不撤销旧文件的既有许可。

| 增量 | 已获准内容 | READY SHA-256 | 范围 |
|---|---|---|---|
| v001 | ann_arbor，5 文件 | `9bb1e35732382d8c3c9c7c9006c58fbe9e22c02724ff19e6496576fe8ddce051` | Five previously computed public assets approved for local A candidate with individual notices; no numerical solve or city evidence rerun. |
| v002 | berkeley，2 文件 | `28d472a36fea4161ddd1902b08af1ef2c6ec43c94108852d34fe87792729c393` | Additive two-file public candidate for Berkeley local frozen-OSM turn engineering chart; technical private receipt accepted; no solve rerun. |
| v003 | urbana_champaign，2 文件 | `8af38ac8f901d8dc79816692e2e3c0e319a7f88d333c5c8f2c96265c3fd73117` | Two dated, credited, no-EXIF Commons thumbnails for local A candidate; C02 partial technical private receipt accepted. |

## Berkeley 明确已获准的新增文件

| 文件 | 发布文件路径 | SHA-256 |
|---|---|---|
| turn_candidate.png | `deliveries/six_city_preflight_r1/evidence_continuation_r2/s0_coordination/release/v002/assets/berkeley/turn_candidate.png` | `0e10b6ba8c480a92b740e4750061d8f8ee1b9d626fa29e9b8098fedc1a456e20` |
| turn_candidate.svg | `deliveries/six_city_preflight_r1/evidence_continuation_r2/s0_coordination/release/v002/assets/berkeley/turn_candidate.svg` | `67998c9cac366e90b605f4e47fca7440e6d0082de5629ed07c19aaf251eeb26f` |

v002 仅许可带 OSM/范围说明的本地候选拷贝，不授权部署；不得称实测交通、政策效果或已认证合法转向。原始 GPS、S2/路线交叉表、精确相机定位、私人地图/inspector、两张原始照片及其 EXIF、完整私有文章、作为求解器输入的转向 sidecar 仍按原决定隔离。

## Berkeley 新算法、ADMM、LR

- 原 S72 与 T4 LP/CG/LR 科学接受可按现有事实表述；不要把较旧 ADMM 失败状态覆盖当前 C2a。
- C2a ADMM READY：170 次真实 outer，原300上限，18门通过、fresh确认PASS；科学身份是已见 T4 的诊断后接受。`public_release=PENDING_S0`。
- LR：300轮同模型冷启动诊断，原10轮1%结果保留；正式23/23检查PASS。`HANDOFF_TO_MAINLINE.json`是科学/显示交接，不是S0逐资产公开决定。
- 新图、绘图数据、history、乘子/路径/精确流量与Full包不得因科学PASS、代码license或目录名被自动视为公开获准。现有本地私有候选可保留准确当前状态；公开包增量需单独清单。

## Pittsburgh Final v4

v4 实际已到达。4个ZIP的本次只读哈希与外层 v4回执一致；Private Full 为465个受保护文件，加 MANIFEST.json 自身共466个ZIP条目；其余3包同样相差1，这是显式计数口径，不是缺文件。旧S0截止时“未收到”仅是2026-10-05历史，不代表当前未交付。

| 包 | SHA-256 | ZIP条目 / 受保护文件 |
|---|---|---|
| Private_Full | `9dda906be5135173a39062d0639c3f28e88724cfa35081ddbed6e01acf918447` | 466 / 465 |
| Review_Lite | `c29b460645c348430f802ddb3f8c06a62ba136b3bb80d29244e77fdba8beeab5` | 116 / 115 |
| Volume_Handoff | `71c0199274d1e999e98dcf7a1e91d5eae014eba1799c174cd8afba1add312b20` | 76 / 75 |
| ChatGPT_Upload | `2d30b25d63f1cc68a08312455647e122166a0a91c116aaee99004afa8ebfea72` | 70 / 69 |

当前 `CURRENT_STATE_AUDIT.json` 与 READY 仍明确 `PENDING_S0_INCREMENTAL_SCIENCE_AND_RIGHTS_REVIEW`，`web_integration=A_ONLY_AFTER_S0`。13图及文章是候选。S FW/finite、T exact-DAG LP/CG/LR/ADMM accepted；Native26/52 GATE_NOT_MET，HiGHS RESOURCE_LIMIT。T4只有0.04502754845 PCE且容量不绑定，不能按同拥堵难度与Berkeley比较。

版本关联仍需补记：外层 `FINAL_DOUBLE_REPLAY_RECEIPT_v4.json` 的v4/465回执真实存在；但v4 ChatGPT ZIP内的 `FINAL_VALIDATION_RECEIPT.json` 仍为v3/464，READY也引用v3。不能把内部旧回执改口说成v4已验；本审计只读记录二者，未执行重放，也不推定科学失败。

## 主线收口所需边界

保留历史已准许文件，不因算法新增待决而重新隐藏。对未有新许可依据的增量保持“本地私有候选／待S0逐文件审查”，不得直接放入公开包。若后续获准联系S0，交付一次增量审查：现有release/manifest与hash、Berkeley当前各方法包、LR正式PASS、Pittsburgh外层v4/465与内层旧v3/464绑定差异、明确图/数据/代码/原始素材分类。

所有详细路径、哈希、原回执全文、已释放9文件及当前候选比对、58条Berkeley/Pittsburgh旧矩阵行、明确隔离项见同目录 `EXISTING_RELEASE_AUDIT.json`。

搜索限制：首次广域rg遇到历史临时validator目录拒绝访问；未绕过。当前S0 release根、上述城市当前回执与包可读。未发现的结论限于已检查范围。
