# v1.0.0 验证与性能记录

日期：2026-10-24。所有表格来自实际运行，合成语料，无正式 DSF 会话、无模型 API 费用。当前交付是研究核心，不是生产端到端验收。

## 正确性

首次核心通过 34 项 Python 测试，边界扩展后 38 项，随后加入工具接口和工具尾部边界回归。最终测试结果以 experiments 中 manifest / JUnit 为准。Node 5 项在指定本机安装路径后全部实际通过、0 skip；其中一项加载真实 `BasicCompactionEngine` 与 Cordis Context，运行继承的 summarize hook。它不等同于真实 DSH Session 压缩事务的完整验证。

| 场景 | 已验证机制 |
|---|---|
| T01/T02 | 原始事实与证据可重取、aware 时间、未来/失效过滤 |
| T03/T04/T13 | 有方向的二跳路径、关系类型过滤、激活/可信度/时间分离、可解释证据 |
| T05/T06 | 显式事实 key 与生效时间取代、旧事实历史保留、推测不能退休可信事实 |
| T07 | Checkpoint 精确参数/任务/原始引用、预算不足拒绝、未完成工具调用拒绝、近期尾部不切断工具配对 |
| T08/T10 | Goal Carryover 跨日保持、Dreaming 幂等与 No-op、Self 不强制更新 |
| T09 | Self 字段白名单、真实工具经历证据、稳定特征要求独立日期证据；尚未证明长期身份质量 |
| T11 | WAL 中断回滚、备份新路径恢复、JSON 版本历史迁移、索引损坏重建 |
| T12 | SQL scope 前置过滤、证据/边端点隔离、FTS 排名不共享其他 scope 的统计 |
| T14 | 循环/悬空 PPR、节点/扇出/hop/计算预算、零权重边不传播；非大规模相关性质量证明 |
| 自发联想 | 普通输入低成本 No-op、cue 幂等、预算总额、候选不自动入图、版本过期拒绝、证据验证入口 |

初次执行遇到 Windows 默认 pytest 临时目录访问失败，改用项目独立测试目录；开发中修复了 edge SQL 列数、Windows fsync 模式与 SQLite 连接未关闭问题。早期完整日志缺失已在 retrospective provenance 中明确标注；后续记录器保留所有运行，包括失败。

## 规模与算法消融

语料：每规模 8 query，4 个精确事实、4 个有方向二跳。Embedding=`lexical-hash-baseline/1/256`，不含神经语义；k=5，固定生成器，无随机抽样。这是 smoke benchmark，样本量不足以支持论文效果结论。

优化后首次记录（benchmarks/results-v1.0.0.json）：

| 规模 | Vector Recall@5 | Hybrid | BFS | PPR | PPR median/p95 ms |
|---|---:|---:|---:|---:|---:|
| 100 | .500 | .500 | .875 | 1.000 | 2.16 / 2.57 |
| 1,000 | .500 | .500 | .625 | .625 | 18.12 / 26.70 |
| 10,000 | .125 | .500 | .500 | .500 | 221.57 / 242.99 |

10k 的 PPR、BFS 相比 hybrid 没有质量收益；小图优势随语料扩张消失。当前哈希向量的碰撞、弱 seed 选择和固定 reset 预算会稀释跨事件激活。不能将这归因于神经 Embedding 本身，也不能宣称优于 HippoRAG/A-MEM。默认改为 hybrid，显式探索保留 PPR。逐查询 gold、retrieved ID、rank、MRR、nDCG 和 Evidence Precision 全部保留在原始 JSON；不删除不利结果。

## 性能优化对照

移除新增节点和重建时无需执行的 FTS DELETE，避免反复扫描增长中的 FTS 表。没有改变检索排名。

| 规模 | 原写入 条/s | 优化后 条/s | 原重建 ms | 优化后 ms |
|---|---:|---:|---:|---:|
| 100 | 1478.4 | 1714.0 | 27.9 | 22.9 |
| 1,000 | 1078.8 | 1335.4 | 437.2 | 273.2 |
| 10,000 | 456.3 | 1341.0 | 18460.1 | 3247.1 |

10k 完成增量写入、受限 Dreaming、备份后重新打开并召回；数据库约 50.38 MB。所有规模备份再开召回为 true，查询未触发预算截断。以上单次测量，不能当作显著性检验。

早期检索计时使用 Windows `time.monotonic()`，短查询有 0 ms（约 16 ms 分辨率），已保留原数值并标明测量缺陷。改用 `perf_counter`；写入/重建从一开始便使用 perf_counter，两组吞吐仍可对照。早期未同步保存历史 source tree，不能将回溯说明冒充完整论文复现记录。新增完整记录器运行会保留新的源码快照与环境指纹。

## 成本和待验证

本轮 LLM 提取/链接/Dreaming/Self Reflection 请求、API Embedding 请求与模型 Token 均为 0；检索/向量处理量有独立计数。上下文节省 Token 尚无真实 DSH Token Meter 实测，记录为 null，不将字节数冒充 Token 节省。

尚未运行神经语义模型、HNSW、LongMemEval/LoCoMo、DSH 原生 A–F、实际压力/overflow/取消/持久化故障注入、Linux 主机、真实跨日持续运行。上述项目不计入通过。
