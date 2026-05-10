# AI Skills

> 一次编写，处处同步。一套可复用的 AI 编码助手 Skills（Slash Commands），支持 **20+ 种工具**，包括 Claude Code、Cursor、VS Code Copilot、Cline、Windsurf、Kiro 等。
>
> Write once, sync everywhere. A collection of reusable skills for AI coding assistants — works across **20+ tools**.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/wukun2005-gif/ai-skills?style=social)](https://github.com/wukun2005-gif/ai-skills/stargazers)

---

每个 AI 编码工具都有自己的 "skills" 或 "rules" 系统，但互不兼容。你不得不为每个工具重复编写相同的指令。

**这个仓库解决了这个问题。** 把 skill 写在 `~/.ai-skills/`，然后运行 `/share-skills`，自动检测并同步到你机器上所有的 AI 工具——无需手动配置，无需操心格式差异。

Every AI coding tool has its own "skills" or "rules" system, but they're all incompatible. You end up rewriting the same instructions for each tool.

**This repo solves that.** Write your skill once in `~/.ai-skills/`, run `/share-skills`, and it auto-detects and syncs to every AI tool on your machine — no manual config, no format juggling.

## Quick Start

```bash
# 克隆到 ~/.ai-skills/
git clone https://github.com/wukun2005-gif/ai-skills.git ~/.ai-skills

# 创建符号链接到 Claude Code
ln -s ~/.ai-skills/* ~/.claude/skills/

# 同步到本机所有其他 AI 工具
/share-skills
```

## Skills 列表

| Skill | 触发词 | 说明 |
|-------|--------|------|
| [`dev-iterate`](dev-iterate/) | "开发" / "iterate" | 基于 PRD/Design Doc/Dev Plan 的迭代式开发，开发与测试交替进行，14 条自检，自动提交 |
| [`test`](test/) | "测试" / "test" | 智能测试——分析变更范围，针对性运行测试，避免全量执行 |
| [`commit`](commit/) | "提交" / "commit" | 分析变更、推断提交风格、commit & push |
| [`backlog-update`](backlog-update/) | "提建议" / "suggest" | 从 UX/安全/性能/稳定性等维度分析项目，建议优先级排序的新功能 |
| [`doc-consistency`](doc-consistency/) | "一致性检查" | 自动发现项目中所有 .md 文档，检查并修复文档间的一致性 |
| [`review-iterate`](review-iterate/) | "review" / "审查" | 迭代式审查与修复文档，直到与参考文档完全一致 |
| [`share-skills`](share-skills/) | "共享 skills" | 自动检测本机所有 AI 编码工具，一键同步 skills 到全部工具 |
| [`resume-tailor`](resume-tailor/) | "生成简历" / "resume" | 根据 JD 基于真实简历素材生成定制简历 |
| [`resume-html`](resume-html/) | "转html" / "resume html" | 将简历转为 ATS 友好的 HTML 格式，结合 JD 做克制的加粗高亮 |

## share-skills 工作原理

核心卖点：**零配置跨工具同步**。

1. **自动发现** — 扫描系统上的 AI 编码工具，通过检测目录内容特征识别（不硬编码路径）
2. **自动注册** — 新发现的工具自动写入注册表
3. **智能分发** — 每个工具获得正确的格式：符号链接（Claude Code、Cursor、Kiro）、文件复制（VS Code、Windsurf）、合并写入（Cline）、或跳过（TRAE 通过插件读取）

```
/share-skills              # 全量同步到所有已发现的工具
/share-skills --list       # 仅列出可共享的 skills（不同步）
/share-skills --add <skill>  # 只同步单个 skill
```

已支持工具：Claude Code、Cursor、CodeBuddy、Windsurf、TRAE、Antigravity、Kiro、Qoder、Cline、VS Code Copilot、Amazon Q、Codex、Hermes 等。新工具安装后自动识别，重新运行 `--sync` 即可。

## 目录结构

```
~/.ai-skills/
├── dev-iterate/         # 迭代式开发
│   └── SKILL.md
├── test/                # 智能测试
│   └── SKILL.md
├── commit/              # Git 提交
│   └── SKILL.md
├── share-skills/        # 跨工具同步引擎
│   ├── SKILL.md
│   └── registry.json    # 工具注册表（自动维护）
├── ...
└── LICENSE
```

## 添加自定义 Skill

1. 创建目录：`~/.ai-skills/my-skill/`
2. 添加 `SKILL.md`，包含 frontmatter：
   ```markdown
   ---
   name: my-skill
   description: 功能描述
   when_to_use: 触发词
   ---
   你的 skill 指令内容...
   ```
3. 运行 `/share-skills` 同步到所有工具

## Contributing

PRs welcome! 如果你有跨项目通用的 skill，欢迎提交。

## License

MIT
