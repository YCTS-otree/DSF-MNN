# 运行、接入与迁移

## 独立运行

核心使用 Python 标准库，数据库必须使用 .sqlite/.sqlite3/.db 后缀；CLI 只从显式 stdin 接收 JSON，不扫描目录或自动打开消息中的文件路径。`configs/offline.example.json` 是设计参考，当前 CLI 不自动加载该文件；生命周期参数通过 Python DreamingConfig / RecallBudget 等 API 传入。

Windows Python 自带 SQLite 需支持 FTS5。测试机为 Python 3.10.11 / SQLite 3.40.1 / Node 24.19.0。使用系统既有环境；可选神经模型依赖尚未安装。`LocalSentenceTransformer` 仅接受已有本地模型目录、显式模型 ID/revision，禁用下载和 trust_remote_code。模型与词表的许可、摘要以及中英质量应单独记录。

Linux 采用相同源代码与数据格式。时区由 IANA ZoneInfo 处理；宿主若无系统时区库/tzdata，需要维护者选择安装方式。二进制向量固定 little-endian float32；路径作为引用/配置而非唯一身份。

## DSH 阶段接入

以下编号流程描述 v1.0.0 保留的影子接口。v1.1.0 首次恢复使用独立原生 CompactionEngine 与 ACR，不继承 Basic 摘要策略；见 [当前操作说明](COGNITIVE_DREAMING.md) 和 [ADR-003](ADR-003.md)。真实隔离验证已完成，正式 DSF 插件装配仍未启用。

1. 用户授权的只读快照导出器产出 `dsf-mnn-snapshot/1`，包含 session_id、有序唯一事件 ID/seq、来源 URI、aware observed_at、来源类型、正文哈希所覆盖的规范数据。
2. `snapshot.validate_snapshot` 校验 Python canonical JSON SHA256、绑定和顺序。不能以模型输入中的 user_id/workspace_id 作为授权。
3. `adapters/dsh/client.mjs` 从可信 resolveScope(agent) 取得完整 scope，通过 stdin 发送本地 Python worker；每次调用有 AbortSignal、超时和响应上限。无监听端口，无模型 API。
4. `createCognitiveBackend(BasicCompactionEngine, {resolveSnapshot, prepare})` 返回继承官方 Basic 的类；仅覆盖 summarize。prepare 可调用 stdio 的 prepare operation。返回模板型 SummaryResult，不伪造 llmStreamCall/模型计费用量。
5. 生产 resolveSnapshot 尚未实现。该 hook 的公开 input 不含 sourceEventSeqs，必须在本机实际 token-meter replay 和原始事件间建立严格映射。不能按文本模糊匹配，也不能拿整个 Session 作为压缩选区。
6. DSH 仍独占 surface replacement、start/summary/end、并发排斥、maintenance、flush、取消和 shrink 验证。prepared 只说明 MNN 已保存；DSH commit 后由可信观察者以 session/compaction_id/snapshot_digest 记 ack。中间崩溃可留下 prepared 未 ack，需对账，不声称跨库原子。

目前没有自动插件装配或修改正式 DSF config 的脚本，本轮也不尝试恢复 Basic。未来正式启用前必须通过 DSF 的 ArchiveManager 集中门禁：只停止本项目 Bridge/独立 DSH，生成完整且校验通过的 .DSF，再由明确开关安装新后端；备份失败不得开放。工作 DSH 3080 和全局设置不在范围。

## 三种回忆

Automatic Recall 使用 `Recall.context` 或 stdio recall，默认 hybrid，字节预算内输出来源和时间标签；可选 EvidenceRecall 增加同库存证回查。Voluntary Recall 使用绑定了 scope 的 MemoryTools，避免把大量内部对象倒入上下文。Spontaneous Association 接受 input/tool_result/reading/goal/dreaming cue，同图低成本 gate + 有预算深挖，候选经应用证据校验才可 related_to 入图。隔离内核已注册 3 个只读 MNN 工具；正式回调与工具集待绑定验收。

Core/Self 的现有 section/版本由 DSF 继续管理。SelfProjection 只是证据化 overlay，不自行提高 prompt role；order 不是真实安全层级。私人空间文件只能将来显式选择索引，不自动重排/覆盖/扫描，信件保持 external 标签。

## 备份、迁移和删除

`mnn backup <new.sqlite>` 使用 SQLite backup API、一致性/外键/schema 检查与原子链接发布，拒绝覆盖旧目标。`mnn --db <new.sqlite> restore <backup.sqlite>` 只恢复到新文件。运行中的主 db/WAL 不能随意当作备份复制。关库之后可迁移已验证快照。

`export` 输出带 schema、scope、hash、完整节点/边/历史的 JSON；`import` 仅允许目标 scope 为空，验证摘要、证据、完整版本链并重建当前 Provider 索引，不合并覆盖旧记忆。备份保留运行收据；JSON 交换侧重记忆与历史，不导入待确认的跨系统事务收据或成本计数。引入新 schema 前应先备份并实现显式迁移；当前未知版本拒绝打开，未提供猜测式自动迁移。

更换 Embedding：显式 `rebuild_index(scope, provider)`，批量生成且事务切换本 scope 的索引，失败回滚原索引；不重新执行 LLM 提取。原始记录与图始终可读。

维护 API 提供 forget_event / forget_scope，传播到关联历史、证据依赖节点、memory_refs 投影、边、FTS、向量及本 scope 派生收据；Dreaming 不调用删除。它不能抹掉 DSH 原日志、外部备份或操作者导出。重新导入已删除来源当前没有永久 tombstone 防护，正式接入前必须实现，以免授权的旧快照重新生成已删除内容。默认没有向模型开放任何删除工具。
