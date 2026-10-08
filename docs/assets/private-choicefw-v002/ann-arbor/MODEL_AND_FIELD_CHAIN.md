# 模型身份与字段链

实验交付ID：ANN_TRANSIT_CHOICE_FW_V002。沿用规范模型ID：ANN_ARBOR_CHOICE_TIMETABLE_R1。MODEL_ID_MAP.json给出三组完整签名及网络/需求SHA256。

|实例|模型 ID|正车辆 OD|PCE/h（1小时）|初始 max(v/c)|初始全图 relative gap|门槛|真实 FW 更新|
|---|---|---:|---:|---:|---:|---:|---:|
|S600|ANN_ARBOR_R2_S600_20261008|600|1647.816622273|0.717965484|5.10282992012e-05|1e-5|1|
|ChoiceR1|ANN_ARBOR_CHOICE_TIMETABLE_R1|600|1569.500896674|0.683023907|3.61499914206e-05|1e-5|1|
|S72|ANN_ARBOR_R2_S72_20261008|72|243.071388651|0.139679497|1.03023091153e-11|1e-5|0|

三组均使用Central Ann Arbor约19.633 km²城市子区域、25个原分区及原bounded routing halo。S72使用独立72 OD子集，地理区域不变。旧S600和S72仅复核保存状态；新分支完成一次真实FW更新。S72 Native初始通过、0 NLP调用的既有结论保持。

## 字段与单位

person OD.person_trips → new choice.probability/person_trips → assignment_od_pce.volume_pce → selected_zone_od.volume_pce → demand.volume → path_flow.flow → link_flow.flow_pce_per_period → physical_assigned_flow.assigned_flow_pce_hour。

新choice中drive_person / 1.2 persons per vehicle × 1 PCE per vehicle，得到车辆/PCE需求。FW直接使用已转换的demand.volume。期间为一小时，因此PCE/period与PCE/h数值相同。transit和walk为人员方式结果，assignment_eligible=false；公交乘客没有被转换为道路公交车辆数。路段流量求和会重复计数行程，不能当成总需求。

FIELD_CHAIN.csv保留600条完整私有OD映射。历史manifest.physical_links=14203是原接口对求解弧总数的字段名；真正物理道路弧数为5138，另有9065条转向弧。未改历史合同字段。

## 文件级哈希

|环节|文件|SHA256|
|---|---|---|
|generation|frozen_r2/run_20261005_r2/generation/generation.csv|e9be015b490d788e425fb3a7e34b440f24483617408387b0b1fd0fbac2e34641|
|generation_ledger|frozen_r2/run_20261005_r2/generation/generation_ledger.json|6412a52fefaebf6beb0be009cd076d2f9aaf4ca9b0a3bf3cf84d61161b5cae90|
|distribution|frozen_r2/run_20261005_r2/distribution/pa_distribution.csv|87c16b5873faf17219c066f5ad1ff8a0f47563bae5ee0a2fdaaec8d9263a5a11|
|person_OD|frozen_r2/run_20261005_r2/distribution/od_person.csv|2c6f66e99971c765449ae3efe4958abfa74f38066ab9b6f56ebd6ba19a30f2d6|
|mode_parameters|frozen_r2/config.json|48506fd020b8d379e74ebce0a70bed1f21a505ada8125b56870f1fb3fd107c39|
|new_timetable_revision|transit/INPUT_REVISION.json|030156dbe217a3feb0edd9aa49638406836c2822bfec2f1c2d48da812dc421b3|
|new_mode_costs|transit/mode_costs.csv|d2cb647366e6ddc09188564cb550320e5366890a835d91834b872cf83dc4f736|
|new_person_choice|transit/mode_choice_by_od.csv|80baf4a11188d44d342f11cbca1ee7cfeb4511444ccce1faf1b7a228ff6596aa|
|new_vehicle_OD|transit/assignment_od_pce.csv|dcb6853a1a7ec4c6c263b571daa68a1e33ec2be4ef12701b2112e2203092ceea|
|access|frozen_r2/inputs/access.csv|7dc8f75fa5d8426941116007e11fe256d4215005f71f081aa296de44ec1d1432|
|OD_selection|S/ChoiceR1/instance/selected_zone_od.csv|6bf190f0183946126c0cbbceee6803992e9121c20ffede0adffb5020cbd7ce13|
|assignment_OD|S/ChoiceR1/instance/demand.csv|8e77e2c3e2d9f65f7771e2fcb3710c2581143e34630d8127d1c6a1ae651dc8d8|
|directed_solver_graph|S/ChoiceR1/instance/link.csv|437a5ebab64a3ca2d3d4a72d76db159f056baeff8db4a48371bb96e66747d380|
|physical_inventory|frozen_r2/inputs/physical_road_links.csv|9354521b28573a68057933873f9fc54b1546bc26eecb8984d7fab54901f571bf|
|accepted_FW_source|shared_core/source/mcl_assignment.py|b66c412281da24a66deacc3b6d90bc44e040d6f4fc7975d9b5e315fa76de5bbe|
|new_assigned_solver_flow|S/ChoiceR1/FW/link_flow.csv|2e239809188812e468e5cabfdb006db7bf40d5f49a22af82f6d9b01573abb0b2|
|new_assigned_paths|S/ChoiceR1/FW/path_flow.csv|e7fccbff5b64034bd71d61e6f8b9f49433898903df27e8e78a2f8a10419b7cda|
|new_assigned_physical_flow|verification/physical_assigned_flow.csv|055144a64bb8c801d77dff6575d053cb733df44005a07b4ee6b978e307121c30|
|new_actual_checkpoints|verification/CHECKPOINT_AUDIT.json|422b92303fc2e9807b6af962a25535a689c59e9ebcd711571a39070cc1082b9d|
