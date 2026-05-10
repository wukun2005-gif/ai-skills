# AI Skills

> Every AI coding tool has its own skills format. You end up rewriting the same instructions for Claude Code, Cursor, Windsurf, Cline... every time you refine a workflow.
>
> This repo fixes that. Write once, sync everywhere. Works across **20+ tools**.

每个 AI 编码工具都有自己的 skills/rules 系统，互不兼容。你不得不为每个工具重复编写相同的指令。**这个仓库解决了这个问题。**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/wukun2005-gif/ai-skills?style=social)](https://github.com/wukun2005-gif/ai-skills/stargazers)

<!-- TODO: Replace with actual demo GIF -->
![demo](./demo.gif)

---

## How it works

Write your skill once in `~/.ai-skills/`, run `/share-skills`, and it auto-detects and syncs to every AI tool on your machine — no manual config, no format juggling.

```
/share-skills              # detect all tools, sync everything
/share-skills --add test   # sync just one skill
/share-skills --list       # see what's available without syncing
```

Detection works by scanning for directory content patterns, not hardcoded paths — so new tools get picked up automatically.

## Quick Start

```bash
git clone https://github.com/wukun2005-gif/ai-skills.git ~/.ai-skills
ln -s ~/.ai-skills/* ~/.claude/skills/
/share-skills
```

## Skills

| Skill | Description |
|-------|-------------|
| `dev-iterate` | Iterative dev workflow: PRD → dev → test → commit, with 14 self-checks |
| `test` | Smart test runner — analyzes changes, runs targeted tests, skips the rest |
| `commit` | Infers commit style from git history, commits and pushes |
| `backlog-update` | Analyzes your project and suggests prioritized features |
| `doc-consistency` | Finds all .md files and checks cross-document consistency |
| `review-iterate` | Iterative doc review against a reference document |
| `share-skills` | The sync engine — detect tools, sync skills |

## Supported tools

Claude Code, Cursor, CodeBuddy, Windsurf, TRAE, Antigravity, Kiro, Qoder, Cline, VS Code Copilot, Amazon Q, Codex, Hermes, and more. New tools are detected automatically.

## Add your own skill

```bash
mkdir ~/.ai-skills/my-skill/
```

Drop a `SKILL.md` in there:

```markdown
---
name: my-skill
description: What it does
when_to_use: trigger words
---

Your instructions here...
```

Run `/share-skills` and it goes everywhere.

## Contributing

PRs welcome! If you have cross-project workflows worth sharing, submit them.

## License

MIT
