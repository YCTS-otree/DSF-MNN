# 固定研究基线

基线提交：`29d7de6b3fcb2e909ea8f49436640de77db09f6d`。

固定标签：`research-baseline-29d7de6`。后续开发可以继续提交，但不移动此标签，不修改基线提交及冻结材料。

`research-29d7de6/` 包含：

- `manifest.json` / `SHA256SUMS`：固定提交、冻结时间、工件大小和 SHA256。
- `artifacts/source-29d7de6.zip`：直接由该提交生成的完整 Git 源码快照。
- `artifacts/repository.bundle`：基线标签和祖先历史的离线 Git bundle。
- `artifacts/experiments.zip`：所有关联实验、源码快照、配置、合成数据库、失败样本、逐查询原始返回、日志与发布验证。
- `artifacts/environment-windows.zip`：冻结时现有 Python/Node 的运行文件、pytest/插件/时区依赖及实际 DSH 测试依赖闭包；仅作研究存档，不安装或替换系统环境。
- `environment-lock.json` / `requirements-frozen.txt`：固定环境版本、依赖、原记录与当前保存范围。
- `source-files.json` / `experiment-files.json` / `environment-files.json`：逐文件内容摘要。
- `provenance.json`：保留每个历史实验的原始 revision、dirty 状态及失败记录。

大工件保存在本地 artifacts，Git 跟踪文本清单；忽略规则不是清理许可。不得覆盖、迁移或自动删除这些原始文件。此目录不是正式运行数据库，也不是系统配置目录，不包含凭证、私钥或正式会话。

校验：

```powershell
python scripts/freeze_baseline.py --verify baselines/research-29d7de6
```

复现时在全新实验目录解压源码和环境，把新的测试工作目录、结果和日志放在该目录下，不能在冻结数据或旧实验 work 目录内重新运行。恢复仓库可使用 bundle 克隆到新目录，再检出 `research-baseline-29d7de6`；不要对当前工作区执行 reset。

保真边界：早期实验原本来自不同源码快照，部分记录当时是 dirty 状态；冻结这些记录不意味着它们都是 29d7de6 的精确运行结果。早期缺失的完整日志不补造。运行时版本与原记录核对，但历史完整环境变量和全部传递依赖的旧哈希未记录；当前运行文件快照不能倒推历史二进制完全相同。Windows OS 镜像未保存，Linux/新硬件性能不作等同保证。

新冻结结果和复现验证见 [docs/RESEARCH_BASELINE.md](../docs/RESEARCH_BASELINE.md)。
