# 源码调查（WP00）

调查日期：2026-10-24。公开 GitHub 使用连接器读取；论文阅读原文。源码固定 commit，不能把远端 master 等同于本机安装包。

## HippoRAG 1 与 2

- [第一代论文](https://arxiv.org/abs/2405.14831)：实体索引与图 PPR，段落通过实体关联。
- [第二代论文 v2，§3、附录 G](https://arxiv.org/html/2502.14802v2)：加入 passage 节点、query-to-triple contextualization、LLM recognition filter；phrase 与 dense passage 共同形成 reset 分布。不是简单向量 Top-K 加任意图扩散。
- 调查 commit `d5c8329422e0a0b834a15874545cb6a74b4f9b26`，包版本 `2.0.0a5`。
- [HippoRAG.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329422e0a0b834a15874545cb6a74b4f9b26/src/hipporag/HippoRAG.py)：`index`、`add_fact_edges`、`add_passage_edges`、`retrieve`、`graph_search_with_fact_entities`、`run_ppr`。检索先选 fact 并 recognition rerank；空 fact 回退 DPR；fact 的主客体提供 phrase 权重，按出现段落数抑制高频实体，叠加低权重 dense passage reset，再按 passage PPR 排名。该 revision 使用 igraph 的无向投影与 prpack；不能据此把带方向的因果证据变成双向因果。
- [setup.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329422e0a0b834a15874545cb6a74b4f9b26/setup.py)：torch、transformers、igraph、litellm、pandas/pyarrow 等不是本项目必需底层。vLLM 为可选且不适合当前 Windows 默认路径。

MNN 独立实现有预算的局部 PPR、dangling reset、类型过滤和证据返回；保留事件/事实/经历而非直接套文档 QA 的 extraction。当前不宣称复现完整 HippoRAG 2，未引入其 recognition LLM。

## A-MEM

- [论文 v11，§3](https://arxiv.org/html/2502.12110v11)。论文还指向 evaluation 和 production-ready 的其他仓库；本次主调查按用户指定 `agiresearch/A-mem`，不混称所有仓库为同一实现。
- commit `ceffb860f0712bbae97b184d440df62bc910ca8d`，包 `agentic-memory 0.0.1`。
- [memory_system.py](https://github.com/agiresearch/A-mem/blob/ceffb860f0712bbae97b184d440df62bc910ca8d/agentic_memory/memory_system.py)：MemoryNote 保存 content/context/keywords/tags/links/evolution_history；add_note、find_related_memories、process_memory、consolidate_memories 已阅读。新 note 查邻居，LLM 可 strengthen 或 update_neighbor。这里的邻居返回包含位置索引，而演化阶段又使用 memories 字典顺序，不能将这种定位方式照搬到持久化系统；MNN 全程使用稳定 ID 与预期版本。
- [retrievers.py](https://github.com/agiresearch/A-mem/blob/ceffb860f0712bbae97b184d440df62bc910ca8d/agentic_memory/retrievers.py)：Chroma/PersistentChroma 路径、metadata 转换与复制 collection。MNN 不采用周期重建 collection 作为可信存储。
- [pyproject.toml](https://github.com/agiresearch/A-mem/blob/ceffb860f0712bbae97b184d440df62bc910ca8d/pyproject.toml)：sentence-transformers、chromadb、rank_bm25、nltk、litellm、sklearn 等。只借鉴 note 与有界演化机制，不引入整个依赖树。

MNN 演化以新证据、稳定 ID、expected version、变更历史、可逆新版本执行；相似度只能给 related_to 候选，不能自动产生因果或退休事实。

## DeepSeek Harness：远端与安装包分别核对

远端调查 commit `22ddee3792402c3e70ec5f86a63c3e3e895a2f60`：[compaction-basic/src/index.ts](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/compaction/compaction-basic/src/index.ts)。本机实际包位于相邻 DSF `.runtime/node_modules/@deepseek-ai/`，`dsh`、`dsh-compaction`、`dsh-compaction-basic` 均为 `0.2.0-rc.2`，核对了 JS 与 d.ts。

- `ctx.compaction` 是单一 CompactionEngine service，每个 context 一个实现；不能同时把两个服务无条件叠加。回退方式是保持或恢复原 Basic 插件配置，而非 monkey-patch node_modules。
- `BasicCompactionEngine.summarize(input, agent, signal)` 是公开的子类扩展点，返回 summary ContentBlock[]、provider/model，可选 usage/rawOutput。模板/远端结果不能伪造 llmStreamCall=true。
- `compactSurfaceRegion` 先同步 append start 获得持久排斥标记；summarize 后再次检查 surface 稳定性，再写 summary 和带 sourceEventSeqs 的替代 user/message，最后 end。失败也尝试闭合 end；持久 flush 失败单独报告。
- `compactNow` 借助 agent.runMaintenance 仅在 idle 执行；自动压力压缩发生在 pre-step；overflow 根据规范错误码触发并限制重试。取消信号经过整个过程。
- Token Meter 负责 routed request、保留尾部和摘要收敛价格；工具配对 helper 检查选区前后边界。不在 MNN 重建这些事务语义。
- 本机 `dsh-system-prompt` 的 section 在 system 内排序；context 是持久 user-role snapshot。主项目现有 `dsh/cognitive.js` 已提供 Core、Self、room 与 memory 工具，MNN 不重复替换。

安装文件 SHA256（lib/index.js）：

| 包 | 摘要 |
|---|---|
| dsh-compaction | `6ec67e516116e64da69cda58d6b182b22b51c5dc21c7e7615becdf59479a27ae` |
| dsh-compaction-basic | `b7ac52f20a36430cf01a66b3a36f23a48ffdb22708d714dbe1fff541b5df4ec5` |
| dsh-system-prompt | `ff422afac6ba85f89afa985d921aed0b603feb354a05a549c48eae04cf0d2f57` |
| dsh-session | `87ea85e2fb5318bf1f826db9a1c88c1b26d3ea328027a7f32b211880c4d62b9d` |

DSF HEAD `57022a3d24afbde3f52c86bc3874ae0a991be5c4`，remote HEAD 可读；工作区有用户修改，未改动。SYS_Prompt.txt / Self_model.txt 与 bootstrap 已存在，保持原文件和版本。DSF_MNN 无 remote，无远端推送。

## 可选评测

LongMemEval / LoCoMo 需要独立数据许可、下载与模型答案评判协议。初版先运行可重复合成 T01–T14 场景与 100/1000/10000 规模，不把合成结果当作公开 benchmark 分数；真实 A–F 六组 DSH/模型评测列为未验证。
