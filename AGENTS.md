# DSF-MNN 维护规则

- 不读取、复制或输出私钥。凭证不进入源码、日志、测试语料、导出或发布包。
- 本仓库是 DSF 的独立研究子项目；不修改相邻 DS_Friend 的未提交工作，不管理工作 DSH 的 3080 或全局配置。
- 默认离线、合成数据和影子接口。生产启用前必须经过主项目 ArchiveManager 的停服、完整 .DSF 备份及校验；备份失败不得开放。备份不等于授权。
- 不修改官方 node_modules，不迁移或覆盖正式 DSH 会话，不自动替换 Basic Compaction。
- 每个工作包记录实际验证和未完成项；词项哈希向量不代表神经语义 Embedding，合成评测不代表 LongMemEval/LoCoMo。
- 原始证据不可被演化覆盖；作用域须在检索和遍历前过滤。Self Model 无可靠证据允许 no-op。
- 使用现有 Python/Node；不自动安装工具链或模型。更新版本和 CHANGELOG，发布包放入新的 Release/vX.Y.Z 目录。
- 固定研究基线为 `29d7de6b3fcb2e909ea8f49436640de77db09f6d`，标签 `research-baseline-29d7de6`。不得移动/覆盖该标签、重写该提交、修改或清理 `baselines/research-29d7de6/` 及其关联原始实验。复现实验使用全新目录与编号，不覆盖基线结果。
