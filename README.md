# DSF-MNN — Memory Neural Network

DSF 的独立记忆研究子项目，当前版本 **1.1.0（认知恢复研究版）**。在现有 `DSF_MNN` Git 仓库内开发，不搬动 DSF，不修改正式 DSH 会话。

已实现统一证据存储、Episode/事实演化、混合检索、多跳与局部 PPR，以及三种共享图谱的回忆。新增独立远程 LLM 分段 Dreaming、Carryover、ACR 和直接继承原生 CompactionEngine 的后端；真实超限会话已在隔离副本完成同 Session 原生对话续接，原始 3,901 个事件和 Self 保持完整。

**默认 Embedding 仍为 CPU 词项哈希基线。生产未启用；公开数据集、完整 A–F 和 Linux 实机尚未验收。** 真实提取与恢复的收益及负结果见 [首次恢复对照](docs/RECOVERY_EXPERIMENT_20261024.md)，不能将单会话实验解释为完整生产验收。

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
| WP02 | 增加真实分段 LLM notes、引用/精确数值校验、幂等去重与有证据推断关系；完整语义蕴含/通用事实合并待研究 |
| WP03 | 中英文 FTS 词项、可替换 Embedding、精确余弦、RRF、BFS/PPR、解释路径；真实语义模型及 ANN 未验收 |
| WP04 | 授权 stdio、官方只读导出、隔离原生自动/主动回忆及原文回查；正式回调未装配 |
| WP05 | 独立 CompactionEngine、ACR、原生选区/工具边界/服务端预算验证、隔离同 Session 恢复已实测；线上故障矩阵待完成 |
| WP06 | 真实远程分段提取与跨段巩固、可恢复收据/锁、水位、Carryover/No-op、上下文重建；生产后台调度未启用 |
| WP07 | Goal State、带真实证据的版本化 Self 投影；不改已有 Core / Self v0.1.0，不自动索引私人空间 |
| WP08 | 核心机制测试、原 100/1k/10k 消融、8 问题真实配对检索与 Token/失败记录；公开数据和完整 A–F 待运行 |
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
- [Cognitive Dreaming / ACR 操作说明](docs/COGNITIVE_DREAMING.md)、[独立 Backend 决策 ADR-003](docs/ADR-003.md)、[真实恢复对照](docs/RECOVERY_EXPERIMENT_20261024.md)
- [第三方声明](THIRD_PARTY_NOTICES.md)、[更新记录](CHANGELOG.md)

固定研究基线：提交 `29d7de6`，附注标签 `research-baseline-29d7de6`。源码、实验数据、环境和配置已独立冻结，见 [基线说明](docs/RESEARCH_BASELINE.md) 与 [冻结清单](baselines/research-29d7de6/manifest.json)。后续开发与实验不改写该基线。
