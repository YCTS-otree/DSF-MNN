# 实验保留与论文复现

本目录长期保留实验，不覆盖旧结果，不自动清理失败实验。所有语料均须为合成或已合法授权数据，绝不收集私钥或凭证。正式 DSF/DSH 数据不在本轮实验范围。

每次 `scripts/record_experiment.py` 创建独立的上海时间 + UUID 目录：

- `manifest.json`：命令、开始/结束时间、退出码、Python/SQLite/Node/OS、Git revision 与脏状态、源码哈希、测试/数据生成配置。
- `source.zip` / `source-files.json`：白名单源码快照与逐文件 SHA256。即使后续代码变化，也能恢复对应实验版本。
- `stdout.log` / `stderr.log`、JUnit XML、逐查询检索排名和原始指标。
- `work/`：本次合成 SQLite、WAL 故障样本、一致性备份及测试产物。保留失败样本，不只保留最佳结果。

`retained-initial/` 保留本轮早期、在记录器建立前运行的两组 benchmark 和合成数据库。其 provenance.json 明确标注缺失的历史源码快照/完整控制台日志。不得将后补记录描述成同时采集的原始数据。

普通文本、代码与逐查询 JSON 纳入 Git；大型数据库/二进制样本保留在本地 `work/` 或 `artifacts/`，由逐文件 SHA256 清单追踪，避免 Git 无 LFS 的大文件限制。这不代表允许清理它们。未来需另设持久备份位置，再进行存储迁移。发布包不混入这些研发数据。

复现实验应解压该次 source.zip，使用 manifest 中的运行环境和命令，对照原始语料、配置、逐查询结果；不要只比较平均值。初版仅有合成 8 query/规模，不能作为神经语义质量或优于其他论文系统的证据。早期时间计量的分辨率问题同样须记录。
