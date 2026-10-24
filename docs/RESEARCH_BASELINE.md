# 研究基线冻结：29d7de6

日期：2026-10-24。运行版本保持 1.0.0；本次保存研究资产和复现工具，不改动记忆引擎或覆盖已有发布包。

## 固定标识

- 完整提交：`29d7de6b3fcb2e909ea8f49436640de77db09f6d`。
- 固定附注标签：`research-baseline-29d7de6`，不移动、不覆盖、不重写。
- 冻结目录：`baselines/research-29d7de6/`。
- 原始实验仍留在 experiments，冻结副本独立保存，未来实验使用新编号。

冻结材料不是仅有一份版本号清单。已保存该提交的 Git archive、含完整祖先历史和标签的 Git bundle、全部已声明的历史测试工件、原始与优化对照、失败样本、源码快照、100/1k/10k 合成库及备份、逐查询排名/预算/激活路径/证据、日志、配置和 v1.0.0 分发验证。

## 数据与环境

原始实验数据共 **384,055,516 bytes**，无损归档为 experiments.zip。环境保存现有 Python 3.10.11 / SQLite 3.40.1 / Node 24.19.0 的 Windows 运行文件，以及 pytest 8.4.2、插件/时区等 **16 个 Python distribution** 和实际 DSH/Cordis 测试闭包的 **35 个 npm 包**。未创建新的系统安装、修改全局环境或读取私钥/凭证/正式会话。OS 镜像未归档。

| 工件 | bytes | SHA256 |
|---|---:|---|
| source-29d7de6.zip | 155295 | `dc92e35430e3d1dc56934a095f00bd4e7459c1a7dc6760574c12e24d97b2bfed` |
| repository.bundle | 127620 | `e2c921c6f9919e989ac48bf913174f0909a74144b383768580ff9a745d26a2e8` |
| experiments.zip | 37369423 | `e97e125169f5b3a98c9a0044f5319f8a5affa155de9f964acd95c23083f44db2` |
| environment-windows.zip | 54157884 | `207edf3161be02f9dddfecb0d1039d8ff6abe88a731d38b2c84840bdb858e1ce` |

源码/测试/数据生成器/配置以 Git commit 的实际字节冻结；历史每 query 的预算和算法参数以其原始 JSON 冻结。`environment-lock.json` 固定传递依赖版本，`environment-files.json` 对实际运行文件逐个保存 SHA256。16 个 Python 固定版本另见 requirements-frozen.txt。后续安装器或依赖升级不得改写这些文件。

## 实际验证

- 冻结时校验所有已声明原始实验工件，再检查归档：**3,871 个归档成员和 10 个顶层受检文件通过**。完整 source archive 另有逐文件清单和整体摘要。
- `git bundle verify` 通过，bundle 包含固定标签与完整历史。
- 完全从冻结 archive 解压的 Python/Node/DSH 依赖运行该提交的测试，**41 Python passed + 5 Node passed，0 skipped**。测试未使用原安装目录的 node_modules。
- 新复现记录：`experiments/frozen-reproduction-20261024T133642-07614d86e4/`，保留 stdout/stderr、JUnit、环境输出、运行清单及逐文件摘要。原实验结果未覆盖。

复现使用干净控制环境：固定 PYTHONHASHSEED=0、启用归档中 pytest 插件、禁用用户 site-packages、不继承账户凭证。它是独立的复现验证，不把新耗时填入历史性能表，不宣称还原当时未记录的全部环境变量。

## 后续操作

```powershell
python scripts/freeze_baseline.py --verify baselines/research-29d7de6
python scripts/validate_frozen_baseline.py
```

第二条每次新建独立复现目录，测试产生的数据库只写入该目录；不在基线或原始历史 work 目录运行写入任务。冻结脚本拒绝覆盖已有基线；环境更新、算法变更、数据增加和优化应建立新实验，必要时另外冻结新基线。

历史溯源边界已保留在 provenance.json：早期实验来自不同源码快照且存在 dirty 工作区，不能统一改标成 29d7de6；早期缺失日志不补造。原记录没有历史全部传递依赖的文件哈希，本次环境文件哈希属于冻结时的保存状态；相同运行版本不证明历史二进制逐字节相同。未增加神经语义模型、生产 DSH 端到端或公开数据集的验收结论。
