---
name: commit
description: Git 提交并推送到当前分支，然后更新项目任务跟踪文件。分析变更、推断提交风格、起草提交信息、commit、push。
when_to_use: 用户说"提交"、"commit"、"提交并推送"
allowed-tools:
  - Bash(git add *)
  - Bash(git commit *)
  - Bash(git push *)
  - Bash(git status *)
  - Bash(git diff *)
  - Bash(git log *)
---

## 提交、推送、更新任务跟踪 流程

按以下步骤执行：

### 1. 分析变更

运行以下命令了解当前状态：
- `git status` — 查看哪些文件有变更
- `git diff` — 查看具体改动内容
- `git log --oneline -10` — 查看最近提交风格（语言、格式、前缀约定）

### 2. 推断提交风格

从 `git log` 中推断项目的提交约定：
- 语言（中文/英文）
- 是否使用前缀（`feat:` / `fix:` / `chore:` 等）
- 简洁程度

起草的提交信息应遵循项目已有风格，不要引入新格式。

### 3. 起草提交信息

- 如果 `$ARGUMENTS` 不为空，用其作为提交信息的核心内容
- 否则根据变更内容和项目历史风格起草
- 提交信息末尾动态生成 `Co-Authored-By` trailer（见下方检测规则）

#### Trailer 对照表

**工具：**

| 工具标识 | 显示名 | 邮箱 |
|---------|--------|------|
| claude-code | Claude | noreply@anthropic.com |
| cursor | Cursor | cursoragent@cursor.com |
| cline | Cline | noreply@cline.ai |
| copilot | Copilot | 223556219+Copilot@users.noreply.github.com |
| windsurf | Windsurf Cascade | cascade@windsurf.ai |
| trae | Trae AI | trae@bytedance.com |
| codebuddy | CodeBuddy | noreply@codebuddy.ai |

**模型：**

| 模型名 | 显示名 | 邮箱 |
|--------|--------|------|
| mimo-v2.5-pro | mimo-v2.5-pro | support-mimo@xiaomi.com |
| claude-opus-4-7 | Claude Opus 4.7 | noreply@anthropic.com |
| claude-sonnet-4-6 | Claude Sonnet 4.6 | noreply@anthropic.com |
| claude-haiku-4-5 | Claude Haiku 4.5 | noreply@anthropic.com |

#### 检测规则

**工具检测** — 按优先级匹配：
1. 系统提示含 "Claude Code" → `claude-code`
2. 环境变量 `VSCODE_INJECTION=1` → `claude-code`（VS Code 内的 Claude Code）
3. 环境变量 `TERM_PROGRAM=cursor` → `cursor`
4. 系统提示含 "Cline" 或项目有 `.clinerules/` → `cline`
5. 系统提示含 "Copilot" 或 "GitHub Copilot" → `copilot`
6. 系统提示含 "Windsurf" 或 "Cascade" → `windsurf`
7. 系统提示含 "Trae" → `trae`
8. 系统提示含 "CodeBuddy" → `codebuddy`

**模型检测** — 从系统提示中提取模型名（如 "You are powered by the model xxx"），在模型表中查找。

**未命中处理** — 若工具或模型不在表中：
1. 用 WebSearch 搜索 `"{工具或模型名}" "Co-Authored-By" email` 获取正确的显示名和邮箱
2. 将新条目写入 skill 目录的 `trailer-map.json`（`~/.ai-skills/commit/`）对应分区（`tools` 或 `models`）
3. 同步更新所有已分发的 SKILL.md 副本（`~/.ai-skills/commit/SKILL.md` 及各工具副本）中的对照表

**生成规则：**
- 先输出工具 trailer：`Co-Authored-By: {显示名} <{邮箱}>`
- 再输出模型 trailer：`Co-Authored-By: {显示名} <{邮箱}>`
- 两条 trailer 紧挨着（中间不能有空行），位于提交信息最末尾

### 4. 确认待提交文件、提交信息，然后提交并推送

**4a. 展示待提交文件列表并允许排除**

从 `git status` 中整理出所有变更文件（含新增、修改、删除），以编号列表形式展示给用户：

```
待提交文件列表：
  1. src/foo.js        (modified)
  2. src/bar.ts        (new file)
  3. test/baz.test.mjs (modified)
  4. .env.local        (modified)
```

然后询问用户：「是否有不需要提交的文件？请告诉我编号或文件名，没有请回复"无"。」

如果用户指定了排除文件，从列表中移除对应文件，重新展示最终列表并再次确认。

**4b. 确认提交信息并执行**

展示最终的文件列表和计划的提交信息，获得用户确认后执行：

```bash
git add <具体文件>
git commit -m "$(cat <<'EOF'
提交信息

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: mimo-v2.5-pro <support-mimo@xiaomi.com>
EOF
)"
git push origin main
```

不要使用 `git add -A` 或 `git add .`，只添加与本次变更直接相关的文件。

**4c. 验证 push 成功**

执行 `git status`，确认输出包含 `Your branch is up to date with 'origin/main'` 或 `nothing to commit`，且不含 `ahead` 字样。若仍显示 `ahead N`，说明 push 未成功，必须排查原因（网络、认证、权限）并重试 `git push origin main`，直到验证通过。

### 5. 更新项目任务跟踪

检查项目中是否存在任务跟踪文件（如 `backlog.md`、`TODO.md`、`CHANGELOG.md` 等）：
- 如果存在且有变更，检查是否需要更新对应条目的状态
- 如果 `$ARGUMENTS` 中提到了某个任务编号，同步将该项标记为已完成
- 任务跟踪文件的更新作为独立 commit 提交并推送
