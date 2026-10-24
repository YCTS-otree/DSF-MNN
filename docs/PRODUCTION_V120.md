# MNN 1.2.0 验收记录（2026-10-24）

## 固定基线及隔离

DSF 基线 `1ffbc76`，分支 `integration/mnn-v1.2.0`；MNN 基线 `7fcccbc`，分支 `integration/v1.2.0`。MNN 原研究标签及 baselines/research-29d7de6 保持不变。

冻结源码 ZIP SHA256：`01b50b84522807b8d3cf3438c12b6e707eeaf6f079283d088bb142de136db254`。维护前正式 DSF `20261024-191704-08f0ebc6.DSF`，58 文件完整校验；正式数据未用于回滚演练。

## 实际执行结果

| 验证 | 结果 |
| --- | --- |
| DSF Node 自动测试 | 184 项：181 通过，3 跳过 |
| DSF Python unittest | 59 通过 |
| MNN Python pytest | 62 通过 |
| MNN 原生 Node 适配器 | 9 通过 |
| JS/MJS 与 Python 静态检查 | 通过 |
| 合成整份 DSF 恢复及恢复前备份 | 通过，正式数据写入 false |
| 独立 DSH 完整 profile 加载 | 通过，创建 weixin Agent；未提交模型聊天 |
| WebUI | 隔离数据预览、状态/禁用态、未验收启用被拒绝；不操作正式开关 |

安装门禁逐项重新执行测试，日志、哈希和报告保存在本机 `.research/mnn-v120/validation-*/`。Windows owned-worker tree 取消测试在沙箱内曾因 taskkill 权限不足失败，获得操作测试自建进程的执行权限后通过；没有杀其他服务。

## 三轮真实 Provider / 原生 DSH

最终原始记录：`.research/mnn-v120/native-b1f85a8a-dac1-4b7f-baa4-8d04212b29c5/`。使用合成聊天、独立存储、真实 DeepSeek 官方 API，测试路由窗口 65,536（用于较快触发阈值，不代表模型正式容量）。真实 native tokenMeter、官方词表及 Provider 用量参与预算。

| 轮 | 整理前预测压力 | 整理后 | 累计 checkpoint |
| --- | --- | --- | --- |
| 1 / Soft | 86.09% | 15.42% | 1 |
| 2 / Emergency | 98.64% | 37.91% | 2 |
| 3 / Soft | 87.14% | 18.35% | 3 |

三轮保持同一个 Session `9790bc66-47da-411b-970d-20f13b2087b0`。每轮原事件前缀完全相等，Carryover 存在，精确参数 `port=3099` 有证据召回。退出后官方持久化只读重开：3 个工具调用、3 个结果配对，pending input=0，末轮 completed，三个 checkpoint 保留。

另一次成功运行 native-916557f8… 的三轮也保留。全部失败样本保留：路由 catalog 窗口覆盖、Surface 顺序、旧成功收据错误复用、16K 配置无法达到 60% 水位、undefined 恢复 source 严格校验失败。对应修复已进入回归。没有删除失败目录或用后续结果覆盖它们。

## 跨日与故障

跨日期三天 Mock 验证旧/新记忆、Carryover、多次重建、精确参数、Self no-op、同 Session 与重复 Dreaming 无额外 LLM 调用。中断后保留事件、重新打开继续；变更源前缀拒绝接纳。

故障注入涵盖：持久化 JSON 原子 replace 失败保留旧文件；SQL 记忆已提交但 receipt 文件未写的中断不重复提取；重复事实计数非负；恢复过期 lease；有限失败退避；记忆未持久化禁止 checkpoint；工具边界与 Inbox 并发；新一次紧急保护不复用旧 success receipt；Windows 取消终止自建工作进程及其子进程。

## 检索质量，保留负面结果

真实 v1.1 冻结图与 8 题固定 gold，逐次克隆库、4KiB 注入预算；测量的是正确原始来源覆盖及排名，**不是模型答案准确率**。

| 变体 | 来源覆盖 | Source MRR |
| --- | --- | --- |
| v1.1 Evidence Hybrid | 7/8 = 0.875 | 0.504419 |
| 初次 v1.2 拼接方案（失败样本） | 6/8 = 0.750 | 0.490530 |
| 修复后的条件式关联 | 7/8 = 0.875 | 0.504419 |

失败样本 retrieval-9b427670… 保留。修复结果 retrieval-9334c4be…：完整保留原 Hybrid 上下文，只有显式关系问题且有剩余预算时补 PPR，不驱逐直接事实。G5 缺口仍存在，原始来源可查但预算内自动召回未覆盖。

v1.1 原图 Hybrid MRR 0.2708 低于早期冻结 0.3125 的负面结论未被抹去；该指标与上表 Source MRR 定义不同，不能混用为提升。样本少，PPR 未证明普遍优于 Hybrid。

## 正式部署记录

实际正式整理和激活结果另记在本机 `formal-*/report.json` 与 [部署状态](mnn-deployment-v120.md)。隔离通过不等于微信/QQ 端到端或多天生产验收。启用建议：先原 Session 一次整理，校验前缀、Self 与恢复水位，启用 MNN 后受控恢复；持续观察用量、延迟、召回来源与故障。禁止一次开放互联网或扩大渠道白名单。
