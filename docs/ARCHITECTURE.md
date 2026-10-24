# DSF-MNN 架构 v1.0.0

单机模块化核心：事件引用 → Episode Formation → 带来源节点/关系 → 混合召回与局部激活 → Carryover / Dreaming / Compaction 计划。所有模块使用同一个 SQLite 可信存储，不为每日/长期/Self 再造互不关联的数据库。

## 数据边界

Raw Event 保留稳定来源 URI、内容哈希、序号、时间、来源类型和必要文本快照，既可引用 DSH 原日志，也可使用合成输入；不扫描整个 DSH home。一个 episode 可引用多个事件。事实由显式结构化输入形成，不把自由文本的推断自动转成事实。

节点包含 type、content、summary、四类时间、source_refs、confidence、status、owner_scope、version、embedding_ref、metadata。边有方向、类型、权重、evidence_refs、confidence、时间和状态；derived inference 显式标注。SQLite 外键、事务与应用校验共同约束；事件原文不可原位更新。

Scope = agent_id/user_id/session_id/workspace_id/visibility，初版严格完整相等。跨 session 共享须由可信 DSH binding 显式使用同一授权 memory scope，客户端不能把工具参数当授权。所有候选、边端点、证据与版本在精确 scope 内读取。初版没有自动 public visibility 扩权。

## 存储与恢复

Schema version 显式记录。未知新 schema 拒绝打开。写入 BEGIN IMMEDIATE，失败回滚；幂等键碰撞但载荷不同必须报错。nodes/history/edges/embeddings/FTS 在同一事务更新。备份用 SQLite backup API，经 integrity_check 与外键检查后发布到全新目标，不覆盖旧备份。恢复只到新的数据库路径。删除传播到派生节点、边、历史、任务和索引；旧离线备份/DSH 原日志由操作者独立管理。

## 检索

向量与 FTS 候选在授权 scope 过滤，RRF 合并。仅在候选诱导的有限子图扩散；限制 seed 数、邻接扇出、节点预算、hop 数和 PPR 迭代次数。支持 vector/hybrid/bfs/ppr 对照。历史事实可显式查询；默认抑制失效、未来、被取代节点。结果分别返回 relevance、evidence confidence、temporal validity、证据引用和路径，激活不代表真值。

## 演化与生命周期

新记忆只对有来源的稳定 ID 提出演化，更新需 expected version，保留每版快照与原因。显式事实取代需新事实的可信证据和生效时间；疑似冲突保留两端，不默默合并。访问次数不强化关系。

Daily/Dreaming 用固定事件上界、事务水位和任务收据；单个 scope 同类任务不并发。执行器只接受外部传入的 idle 状态，不自行打断 Agent。Carryover 随 Goal 的未完成状态延续，不按日期清空。Dreaming 可保守 no-op；Self Model 是引用真实记忆证据的版本投影，更新字段白名单且不能修改 Core/权限。调度先提供显式 tick API，不注册系统级定时任务。

## DSH 与认知压缩

先独立快照适配与 shadow checkpoint；MNN 提交完成、索引可用、关键 evidence/参数/任务均校验后，才返回准备收据。DSH 接收后仍负责本身日志事务。prepared、DSH committed 的收据可能暂时不一致，重试同快照幂等，恢复时对账；不先删除原始历史。

适配器工厂仅扩展 summarize，并要求可信 snapshotResolver。正式装配、精确选区绑定、原生压力/overflow/取消故障注入、生产 .DSF 门禁尚需集成验收。未启用前原 Basic 为唯一后端。
