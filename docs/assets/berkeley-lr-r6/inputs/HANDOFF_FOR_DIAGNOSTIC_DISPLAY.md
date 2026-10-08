# Berkeley T4 LR：阶段性诊断图交接

**状态：独立数值审计通过；原正式入口恢复与评估仍待共享重计算锁。** 本文件只授权将保存的 300 次运行作为“原 1% 证书后的诊断”展示。原已接收 LR 在第 10 次达到 1% 门槛并停止，其身份和结果保持不变。

诊断运行复用同一 T4 图、需求、容量、费用、步长规则与路径恢复语义。前 10 次科学数值字段与原运行完全一致。第 256 次最佳下界为 **43.66742440800643 PCE·min**，可行上界为 **43.667424408006426 PCE·min**；差别只有一个浮点 ULP，因此零 gap 是浮点截断报告。第 300 次记录的当前下界为 **43.66228345703368 PCE·min**，不能以最佳下界替代它。第 256 次计算 fallback 步长，产生第 257 次状态；当前下界回落而最佳界保留。

独立审计已复算 **39** 个保存快照的下界（最大绝对误差 **1.1527134802236105e-10 PCE·min**）、重新求解 **31** 次保存的恢复 LP，并检查最终 5 条正流路径、需求与容量、目标值及 2,150 条物理链路投影，均通过。快照只保存大于 `1e-12` 的乘子，因此 **2** 处投影范数核对标为跳过；完整最佳乘子和保存流另有独立检查。

图用 `LR_EXTENDED_PLOT_DATA.csv` 与 `RECOVERY_HISTORY.csv`；最佳价格用 `runs/T_LR_extended_300/best_multipliers.csv`，第 300 次记录价格用 `current_multipliers_t300_preupdate.csv`。原 `terminal_current_multipliers.csv` 是第 300 次试更新后的下一状态，不对应第 300 次 history 价格。证据见 `DIAGNOSTIC_AUDIT.json`、`SNAPSHOT_DUAL_RECHECK.csv`、`RECOVERY_RECHECK.csv`、`physical_link_flow_full.csv`、`MULTIPLIER_TIMING.json`。数值与哈希见同名 JSON。

原正式入口评估继续按共享锁排队；通过后将另写 `HANDOFF_TO_MAINLINE.json` / `.md` 和精简、Private Full 两档 ZIP。本阶段不得把 300 次诊断称为已由原正式入口接收。
