# 第三方与算法来源

本项目初版独立实现机制，没有复制 HippoRAG、A-MEM 或 DSH 的实现源码。源码调查链接与固定 revision 见 docs/REFERENCE_RESEARCH.md。论文表达、图表与数据集未打包。

| 项目 | 许可 | 本项目用法 |
|---|---|---|
| HippoRAG 2.0.0a5 | MIT，Copyright (c) 2025 OSU Natural Language Processing | 阅读源码与论文；独立实现局部 PPR 与证据网络 |
| A-MEM agentic-memory 0.0.1 | MIT，Copyright (c) 2025 AGI Research | 机制参考；独立实现有界且可逆的 note 演化 |
| DeepSeek Harness 0.2.0-rc.2 | MIT，安装包声明及上游 LICENSE | 适配器可选 peer dependency；子类扩展公开接口，不重分发其包 |
| Python / SQLite | 各自官方许可 | 使用系统现有 runtime/标准库，不打包 runtime |
| sentence-transformers | Apache-2.0（可选依赖） | 未安装、未重分发；模型权重另有许可，启用前单独审查 |

以后若直接引入第三方代码或发布第三方依赖，必须保留对应完整许可证与版权声明。本仓库自身代码采用 GNU GPL v3.0，完整条款见根目录 LICENSE；第三方项目保留各自许可。
