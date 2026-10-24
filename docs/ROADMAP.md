# 后续验收清单

本版交付 WP00 和可运行的独立研究核心；WP02–WP09 不整体宣称完成。

1. 选择中文/英文/技术混合的已有本地模型或经授权外部 Provider，记录模型许可、revision、词表摘要和逐查询质量；当前机器缺 sentence-transformers 与模型，未自行安装。
2. 增加可替换的结构化 LLM extractor；先验证提取可信度、显式矛盾、去重、Episode 语义边界，禁止无证据因果与大批历史改写。当前仅确定性分组/显式事实。
3. 为本机 DSH 0.2.0-rc.2 实现精确选区 sourceEventSeqs 绑定和真实只读 snapshot 导出；审查 memory scope 跨 session 授权复用。不得依赖私有文件 monkey-patch。
4. 接入 pre-turn / 工具结果 / 阅读线索回调及原生主动工具。完成 prepared/ack 对账、删除 tombstone、防重导入、取消和崩溃故障矩阵，再启用 shadow。
5. 验证 DSH 的 pressure / context-overflow / /compact、Token Meter 收敛、持久事务、并发维护和工具配对。保留 Basic 配置回退。
6. Dreaming 从显式 tick 升级到 DSH 授权的真实后台调度；在 Agent idle 时重建上下文，不新增可见用户会话。扩展 replay、跨项目归纳、带证据的图组织和可选反思；允许 No-op。
7. Self overlay 对接主项目既有版本化投影与 prompt section，不重复人格库。私人空间只做授权选择索引，保留 external/creative/experience 的来源标签。
8. 研究 [LongMemEval](https://github.com/xiaowu0162/LongMemEval) 的 500 问题、answer_session_ids / turn has_answer 标注，接入信息更新、时间、多会话与 abstention。源码 MIT；数据分发页许可另行核对后再下载。
9. 研究 [LoCoMo](https://github.com/snap-research/locomo) 的 10 段长会话、QA evidence/dialog ID、多模态引用。仓库 LICENSE.txt 是 CC BY-NC 4.0，不能当成 MIT 数据无条件商用或分发；先确定适用范围。当前未下载或打包数据集。
10. 完整运行同模型/同预算的 A–F，对照普通 RAG，扩大 query 数、重复次数、随机 seed、置信区间和消融。保留全部原始结果与反例，优先诊断 10k 图检索收益消失。
11. 根据精确索引基线再评估 HNSW/SQLite 向量扩展，测试中文分词方案与冷启动延迟。每次优化单独实验，不覆盖基线。
12. Windows/Linux 双机验证、显式 schema migration、长期备份位置、DSF .DSF 门禁及正式版本发布。

已知限制：预算是合作式工作单位/字节代理；Python 内无法硬抢占 SQLite 或本地模型推理；全量 scope 扫描不适合更大规模；不具备完整语义事实判别、模型用后反馈学习、自动因果校验、数据集基准或生产端到端证明。程序不自行根据 Goal 执行任何外部行动。
