# Cognitive Dreaming 与 Adaptive Context Reconstruction v1.1.0

本模块已对一份真实超限 DSH 备份完成分段 LLM Dreaming、ACR、原生检查点提交与同 Session 对话续接。默认核心仍可离线运行。远程语义请求只在操作者显式运行恢复脚本时发生。

## 数据与流程

`recovery-inspect.mjs` 通过安装版 `JsonlSessionPersistence.open(id, 'read')` 读取授权副本，导出原始事件、header、surface 及事件投影。导出包含敏感对话，必须存放在私有实验目录，不能加入 Git。

`SemanticDreaming` 先将全部事件稳定编号、记录原始 URI/哈希/时间，剔除发送给提取模型的重复系统与 runtime 快照。剔除只针对模型载荷；原始事件仍全部保留。工具调用和结果形成完整 group，超大 group 分片带原始组号、事件范围和字符偏移，不假装结果已成功。模型每次只收到预算内的片段及少量同 scope 记忆候选。

每个 note 提供 kind/key/content/importance、原样证据 quote、carryover 候选和下一步。应用层校验来源范围、quote 子串、数值和日期来源、类型、置信标签与幂等 ID；单 note savepoint 防止半写入。没有证据的猜想不能成为当前事实。同 key 自动连接只能是 `related_to` 推断边；模型关系允许 supports/contradicts/depends_on，全部保留推断和证据，不从相似度制造因果。

已保存 notes 分批巩固为主题、决策和最终 Carryover。历史 Goal 观察与仍有效的 Carryover Goal 分开，任务不因跨日自动过期。矛盾两端保留；正式事实取代仍需既有版本演化 API，不让 LLM 自由重写旧事实。Self 更新固定 No-op。

OS 锁在网络请求期间排斥同一数据库的第二个语义 Dreaming；分块记录、Provider 原始响应和失败收据保留。run manifest 绑定源码、scope、输入和配置；不同版本必须新建 run。完成记录不覆盖。现有远程 worker 只通过主项目可信 `apiKeyEnvironment()` 取得凭证，不读取凭证文件、不记录环境、不输出密钥。

## ACR

`AdaptiveContextReconstruction.build(export, records, store, scope, dreaming, current_task=...)` 同时读取原上下文、版本化记忆、当前 Carryover Goal、原始 Self、任务和事件时间。当前任务可对旧证据优先排序，Goal 完成后重新计划不再续接该任务。

逐片段动作可以同时包含 KEEP_EXACT、CARRYOVER、CONSOLIDATE、ARCHIVE。ARCHIVE 表示移出活动上下文，不删除来源。旧的关键参数和决策可保留原文片段；长期细节以 memory_refs 按需召回；最近未回答的命令保留完整正文、source_ref 和 observed_at。精确来源时间与显示格式分开，不能让模型猜日期。桥接 accountId 与发送者 userId 分开，不把转发内容当认证身份。

完整有效 system 不经 LLM 重写。无预算空间、工具组未完成、媒体尾部缺乏原生计价、来源改变、记忆版本改变或 Provider 计数失败时拒绝提交。当前原文尾部选择适配已验证快照形态；其他复杂尾部必须显式扩展，不能猜测裁剪。

本地使用官方词表及沙箱 Jinja chat template 计算确定 Token 数，但这不是完整服务器封装价格。原生 DSH Provider 预检携带实际工具 schema 与回忆数据，再用服务端 usage 验证 `input + output_reserve <= context_budget`。缓存命中的输入也计入上下文。输出预算与计费分别保存。

## 召回与工具

三种回忆继续共用同一图谱。新 `EvidenceRecall` 在同 scope 原始事件上提供有界 CPU BM25 回查，避免选择性提取遗漏后原文无法找到；不按消息创建第二套记忆节点。Automatic Recall 只注入 4 KiB 以内的数据。Voluntary Recall 在隔离原生 Agent 上仅开放 memory_recall/search/get_evidence。Spontaneous Association 继续先廉价 gate，再有预算 PPR，产生需验证的候选；没有线索允许 No-op。

记忆和检索结果始终是数据，不提高身份/指令权限。本轮没有挂载外部操作或 Self 修改工具。

## 操作路径与回滚

本机现有 Python 3.10、Node 24、安装版 DSH 0.2.0-rc.2、tokenizers/Jinja 可直接使用；可选依赖定义在 `dreaming` extra，本轮没有安装工具链。Linux 使用同一算法与 SQLite，锁使用 flock 分支；Linux 实机尚未验证。

1. `recovery_prepare.py` 使用现有可信 DSF inspect 逐项校验备份，创建新的私有实验目录。不要对正式会话运行实验脚本。
2. 在副本运行 `recovery-inspect.mjs`，冻结标准化输入、问题集和数据哈希；先运行冻结 v1 的 `replay_v1_baseline.py`。
3. `run_cognitive_dreaming.py <private-run> [--variant 新名称]` 使用同一标准化输入；默认历史导出名仅为本次实验配置。通用引擎 API 可接收其他符合格式的导出。
4. `build_context_plan.py <run> --memory-directory <variant> --output <新计划名>`。人工检查 Carryover/来源，计划尚未提交。
5. `recovery-experiment.mjs <run> <DS_Friend目录> <计划名>` 再复制一份原生 sessions，服务端预算确认后提交并运行只读记忆问答。每次新建 native UUID 目录。
6. 退出后 `audit-recovery.mjs <native目录> <DSH node_modules>` 用官方持久化重新打开，核对前缀、身份、配对、完成原因。`compare_recovery.py` 创建新的逐查询对照目录。

恢复点包括原始 `.DSF`、只读导出、Dreaming 前后一致性 SQLite、Context Plan、before/after-compaction 和完整新日志。隔离实验回滚用新目录重新复制原快照；不覆盖正式 Session。生产启用前还要通过主项目 ArchiveManager 停止项目持有的服务并生成完整验证备份，保留原有网页回滚的三次独立确认。本轮没有部署生产开关。

## 已知限制

quote 与精确数值验证不等于语义蕴含证明；LLM 的 Carryover 完成状态仍需核实。当前语义 key 去重与显式矛盾边不能替代通用事实合并器。超大 note 集合采用有界批次，跨所有批次的递归全局整理还需扩展。CPU 原始证据回查上限 10,000 条候选事件，当前不是大规模倒排索引。没有神经 Embedding 质量验收、公开数据集成绩或生产多租户权限扩大。
