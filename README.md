 # Literature Research Pipeline

  中文 | English (README.en.md)

  一个可移植、以 Zotero 为核心的 Codex 文献研究 skill，支持 Google Scholar、IEEE Xplore 和 arXiv。

  ## 功能

  - 多来源论文检索与筛选
  - 导入 Zotero，并进行去重、标签整理和阅读笔记生成
  - PDF 下载失败时保留元数据并提供回退流程
  - 可选：在 Obsidian 中生成主题综述
  - 已整合必要流程，不依赖本地其他检索类 skill

  ## 运行要求

  - Python 3.10+
  - Python 包：arxiv
  - Zotero Desktop
  - Chrome DevTools MCP
  - Zotero MCP

  可选组件：

  - Obsidian MCP

  ## 系统支持

   系统              状态
  ━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Windows           已测试
  ────────────────  ────────────────────────────────
   Linux / Ubuntu    已完成可移植适配，尚未实际测试
  ────────────────  ────────────────────────────────
   macOS             已完成可移植适配，尚未实际测试

  ## 安装

  将本仓库放入 Codex 的 skills 目录，并保持目录名为：

  literature-research-pipeline

  安装 Python 依赖：

  ```bash
  pip install arxiv

  运行环境检查：

  <python> "<skill-dir>/scripts/preflight.py" --json

  Windows 通常使用 python 或 py -3，Linux 和 macOS 通常使用 python3。

  ## MCP 依赖说明

  本仓库不包含 MCP 服务端代码。使用前需要单独配置：

  - Chrome DevTools MCP：用于 Google Scholar 和 IEEE Xplore 浏览器自动化
  - Zotero MCP：用于 Zotero 文献检索、去重、标签和笔记管理
  - Obsidian MCP：可选，用于生成主题综述

  Zotero Desktop 还需要开放本机 Connector API：

  http://127.0.0.1:23119/connector

  ## 发布状态

  当前版本：v0.1.0-beta

  当前已在 Windows 上测试。Linux / Ubuntu 和 macOS 尚未进行完整实机验证。

  第三方项目来源和许可证说明见 THIRD_PARTY_NOTICES.md (THIRD_PARTY_NOTICES.md)。
