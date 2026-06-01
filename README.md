# Literature Research Pipeline

中文 | [English](README.en.md)

一个可移植、以 Zotero 为核心的 Agent Skill，支持 Google Scholar、IEEE Xplore 和 arXiv，可用于 Codex 和 Claude Code。

## 功能

- 多来源论文检索与筛选
- 导入 Zotero，并进行去重、标签整理和阅读笔记生成
- PDF 下载失败时保留元数据并提供回退流程


## 运行要求

- Python 3.10+
- Zotero Desktop
- Chrome DevTools MCP
- Zotero MCP

可选组件：

- Obsidian MCP

## 系统支持

- Windows：已测试
- Linux / Ubuntu：已完成可移植适配，尚未实际测试
- macOS：已完成可移植适配，尚未实际测试

## 安装

将本仓库放入所使用客户端的个人 skills 目录，并保持目录名为：

```text
literature-research-pipeline
```

常见安装位置：

```text
Codex:       ~/.codex/skills/literature-research-pipeline
Claude Code: ~/.claude/skills/literature-research-pipeline
```

Claude Code 也支持仅在当前项目中安装：

```text
<project>/.claude/skills/literature-research-pipeline
```

运行环境检查：

```text
<python> "<skill-dir>/scripts/preflight.py" --json
```

Windows 通常使用 `python` 或 `py -3`，Linux 和 macOS 通常使用 `python3`。

## MCP 依赖说明

本仓库不包含 MCP 服务端代码。使用前需要在所使用的客户端中单独配置：

- Chrome DevTools MCP：用于 Google Scholar 和 IEEE Xplore 浏览器自动化
- Zotero MCP：用于 Zotero 文献检索、去重、标签和笔记管理
- Obsidian MCP：可选，用于生成主题综述

Zotero Desktop 还需要开放本机 Connector API：

```text
http://127.0.0.1:23119/connector
```

## arXiv 访问说明

arXiv 分支优先使用官方 API，并遵守请求间隔限制。脚本包含跨进程节流、本地缓存和冷却机制。API 返回 `429` 或超时时，会自动回退到 arXiv 官方搜索页和摘要页。

Thank you to arXiv for use of its open access interoperability.

## 发布状态

当前已在 Windows 上测试。Linux / Ubuntu 和 macOS 尚未进行完整实机验证。

第三方项目来源和许可证说明见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
