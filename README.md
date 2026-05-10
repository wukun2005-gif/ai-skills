# AI Skills

一套可复用的 AI 编码助手 Skills（Slash Commands），适用于 Claude Code 及主流 AI 编码工具。

## Skills 列表

| Skill | 触发词 | 说明 |
|-------|--------|------|
| `dev-iterate` | "开发"、"迭代开发" | 基于 PRD/Design Doc/Dev Plan 的迭代式开发，开发与测试交替进行 |
| `test` | "测试"、"test" | 智能测试——分析变更范围，针对性运行测试 |
| `commit` | "提交"、"commit" | 分析变更、推断提交风格、commit & push |
| `backlog-update` | "建议功能"、"提建议" | 从 UX/安全/性能/稳定性等维度分析并建议新功能 |
| `doc-consistency` | "一致性检查" | 检查并修复项目中所有 .md 文档之间的一致性 |
| `review-iterate` | "review"、"审查" | 迭代式审查与修复文档，直到与参考文档一致 |
| `share-skills` | "共享 skills" | 将 skills 分发/同步到本机所有已安装的 AI 编码工具 |

## 安装

Skills 源文件存放在 `~/.ai-skills/` 目录下。Claude Code 通过 `~/.claude/skills/` 中的符号链接读取。克隆本仓库后，可通过 `share-skills` 命令一键同步到所有已支持的工具：

```
/share-skills --sync
```

支持的工具包括：Cursor、CodeBuddy、Windsurf、TRAE、Antigravity、Kiro、Qoder、Cline、VS Code Copilot、Amazon Q、Codex 等 20+ 种。

## 目录结构

```
~/.ai-skills/
├── dev-iterate/        # 迭代式开发
├── test/               # 智能测试
├── commit/             # Git 提交
├── backlog-update/     # 功能建议
├── doc-consistency/    # 文档一致性
├── review-iterate/     # 文档审查
├── share-skills/       # Skills 分发
└── LICENSE
```

## License

MIT
