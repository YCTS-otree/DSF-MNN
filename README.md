# DSF-MNN — Memory Neural Network

DSF 的独立记忆研究子项目，当前版本 **1.0.0（离线研究核心）**。在现有 `DSF_MNN` Git 仓库内开发，不搬动 DSF，不替换正式 DSH 会话或 Basic Compaction。

已实现统一的证据存储、Episode 归并、事实版本演化、混合检索、有方向的多跳与局部 Personalized PageRank，以及三种共享图谱的召回机制：Automatic Recall、Voluntary Recall、Spontaneous Association。Dreaming / Carryover / Self / Cognitive Compaction 提供可测试的核心与影子接口。

**当前默认 Embedding 是词项哈希基线，不是神经语义模型。生产 DSH 接入、真实模型记忆质量、LongMemEval/LoCoMo 与完整 A–F 对照尚未完成。** 本版可独立运行，不能当作完整生产系统验收结果。

## 直接运行（不安装依赖）

现有 Python >=3.10、SQLite FTS5 即可。Windows PowerShell 在项目根目录：

```powershell
./scripts/mnn.ps1 status
Get-Content -Raw configs/synthetic.events.json | ./scripts/mnn.ps1 ingest
./scripts/mnn.ps1 search 微信幂等
./scripts/mnn.ps1 search 微信幂等 --strategy ppr
./scripts/mnn.ps1 recall 微信幂等
./scripts/mnn.ps1 dream --at 2026-10-24T04:00:00+08:00 --idle
./scripts/mnn.ps1 backup data/backup-20261024.sqlite
./scripts/mnn.ps1 rebuild-index
```

默认数据库 `data/mnn.sqlite`；默认身份是合成测试身份。可用 `--agent / --user / --session / --workspace` 显式选择作用域，参数放在子命令前。CLI 是本地操作者接口，DSH 工具不能允许模型自行传入授权 scope。

Linux：`sh scripts/mnn.sh status`，或 `PYTHONPATH=src python3 -m dsf_mnn status`。Windows 已实测；Linux 迁移路径已设计，尚未在 Linux 主机实测。

也可由维护者按现有环境选择安装：`python -m pip install --no-build-isolation -e . --no-deps`，之后使用 `mnn`。本轮未执行安装，没有新建虚拟环境。

## 能力和边界

| 工作包 | 当前交付与状态 |
|---|---|
| WP00 | 完成固定源码调查、许可证/依赖比较、本机 DSH 核对与 ADR |
| WP01 | SQLite WAL、事件证据、节点/边、幂等、版本、备份/新路径恢复、JSON 导入导出与索引重建已测试 |
| WP02 | 确定性 Episode 归并、显式结构化事实、冲突/取代关系与可逆演化；自动 LLM 提取与语义分割待实现 |
| WP03 | 中英文 FTS 词项、可替换 Embedding、精确余弦、RRF、BFS/PPR、解释路径；真实语义模型及 ANN 未验收 |
| WP04 | 授权绑定的 stdio 客户端、规范快照、自动/主动回忆 API；生产 Session/Event/工具回调尚未装配 |
| WP05 | Cognitive Backend 子类工厂、影子检查点、持久 prepared/ack 收据；准确选区绑定和原生端到端压缩待验证 |
| WP06 | 显式 tick、时区/补执行、事务排斥、水位、跨日 Carryover、离线关联候选、Self No-op；后台实时调度/上下文重建待接入 |
| WP07 | Goal State、带真实证据的版本化 Self 投影；不改已有 Core / Self v0.1.0，不自动索引私人空间 |
| WP08 | T01–T14 对应核心机制测试、100/1k/10k 合成消融、成本记录；公开数据/真实模型/完整 A–F 待运行 |
| WP09 | 中文部署文档、源代码分发脚本；正式接入发布和 Linux 实机验证待完成 |

`MemoryTools` 提供 `memory_recall/search/explore/get_episode/get_evidence/get_related/trace_relation/get_timeline`。自发联想先 lexical gate，再在预算内 PPR；只生成有证据的 `related_to` 推断候选，经可信校验后可入图。无价值线索允许 No-op，不自动通知、不执行外部动作。

## 测试和实验记录

```powershell
python scripts/record_experiment.py test --dsh-node-modules ../DS_Friend/.runtime/node_modules --label foundation
python scripts/record_experiment.py benchmark --label scale-ablation
```

前者在独立目录保存 stdout/stderr/JUnit/合成测试库和源码快照；后者保存 100/1000/10000 规模数据库、备份、逐查询排名、配置、延迟、MRR、nDCG 和成本。失败也保留，不覆盖旧结果。记录制度见 [experiments/README.md](experiments/README.md)。不提供自动清理实验命令。

普通快速检查：`./scripts/test.ps1`。没有 `DSH_NODE_MODULES` 时，实际 DSH 包的 smoke test 会显式 skip，其余 Node 测试仍运行；不能将 skip 计为安装包验收通过。完整记录器更适合论文材料。

## 文档入口

- [架构](docs/ARCHITECTURE.md)、[源码研究](docs/REFERENCE_RESEARCH.md)、[ADR-001](docs/ADR-001.md)、[ADR-002](docs/ADR-002.md)
- [验证与性能报告](docs/TEST_REPORT.md)、[接入和迁移](docs/INTEGRATION.md)、[后续工作与限制](docs/ROADMAP.md)
- [第三方声明](THIRD_PARTY_NOTICES.md)、[更新记录](CHANGELOG.md)

固定研究基线：提交 `29d7de6`，附注标签 `research-baseline-29d7de6`。源码、实验数据、环境和配置已独立冻结，见 [基线说明](docs/RESEARCH_BASELINE.md) 与 [冻结清单](baselines/research-29d7de6/manifest.json)。后续开发与实验不改写该基线。
