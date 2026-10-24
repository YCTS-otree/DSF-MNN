# 实验索引

所有编号独立保留。源码快照、数据库与失败样本不可被后续运行覆盖。大型文件在对应 work/artifacts 下保留，Git 中跟踪摘要与文本结果。

| 记录 | 内容 | 结论 |
|---|---|---|
| retained-initial | 两组早期规模对照、167 个合成 SQLite 样本（248,737,792 bytes），含开发中失败样本 | 历史源码快照/完整控制台日志缺失，明确标注；不得冒称论文完整复现 |
| 20261024T131935+0800-ad043dfdbc | 首次完整记录器、测试日志/源码/JUnit | Python 40 通过；记录器 GBK 输出异常，标记失败 |
| 20261024T132006+0800-62f4c67863 | UTF-8 修复后完整测试 | Python 40、Node 5 通过，DSH smoke 未 skip |
| 20261024T132038+0800-d61aba89f9 | 完整 100/1k/10k 消融；每 query 原始结果/延迟/路径/证据，数据库与备份 | 小图 PPR 有收益，10k 相比 hybrid 无召回增益 |
| 20261024T132204+0800-9245f92d0d | 压缩重试索引可用性回归 | Python 41、Node 5 通过，DSH smoke 未 skip |
| release-20261024T132259-49ba45f15e | v1.0.0 压缩包独立解压后 status/ingest/search/backup | 原始证据召回和备份通过，分发包 SHA256 见 manifest |

`release-*` 是独立分发包 smoke 验证记录，包括从压缩包解压后的全新环境目录、CLI 原始输出和证据召回检查。后续实验通过 record_experiment.py 生成新编号，并在此索引追加，不重命名旧记录。

## 研究基线冻结

- 固定标签 `research-baseline-29d7de6` 指向完整提交 `29d7de6b3fcb2e909ea8f49436640de77db09f6d`。
- `baselines/research-29d7de6/` 独立冻结源码、原始实验数据、配置、运行环境与依赖，含 SHA256 清单。不得清理、覆盖或把历史运行重新标成同一源码版本。
- `frozen-reproduction-20261024T133642-07614d86e4`：完全使用归档解压的源码、Python、Node 与 DSH 依赖，41 Python + 5 Node 测试通过，0 skip；与历史实验分开保存。
