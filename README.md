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
| `share-skills` | "共享 skills" | 自动发现本机所有 AI 编码工具，一键同步 skills 到全部工具 |

## 安装

Skills 源文件存放在 `~/.ai-skills/` 目录下。

### share-skills：一键同步到所有 AI 工具

`share-skills` 不维护静态工具列表——它会**实时扫描本机**，自动发现所有已安装的 AI 编码工具（通过检测目录结构和内容特征，而非硬编码工具名），然后一键将 skills 分发到全部工具。

```
/share-skills          # 全量同步到所有已发现的工具
/share-skills --list   # 仅列出可共享的 skills
/share-skills --add <skill>  # 只同步单个 skill
```

**工作原理：**

1. **自动发现**：扫描 `~/.*` 目录和 `/Applications/`、`~/Library/Application Support/` 等位置，通过目录内容特征（`.md` 规则文件、`SKILL.md`、`package.json` 等）识别 AI 工具，不依赖目录名称匹配
2. **自动注册**：新发现的工具自动写入注册表（`share-skills/registry.json`），无需手动配置
3. **智能分发**：根据每个工具的格式要求自动选择分发方式——符号链接（Claude Code、Cursor、Kiro 等）、文件复制（VS Code、Windsurf 等）、合并写入（Cline）或自动跳过（TRAE 通过插件读取）

已支持 20+ 种工具，包括但不限于：Claude Code、Cursor、CodeBuddy、Windsurf、TRAE、Antigravity、Kiro、Qoder、Cline、VS Code Copilot、Amazon Q、Codex、Hermes 等。新工具安装后只需重新运行 `--sync` 即可自动识别并接入。

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
