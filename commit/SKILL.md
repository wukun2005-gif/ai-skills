---
name: commit
description: Git 提交并推送到当前分支，然后更新项目任务跟踪文件。分析变更、推断提交风格、起草提交信息、commit、push。支持通过参数指定要提交的文件列表（`file1 file2 -- msg`）或排除列表（`--skip file -- msg`）。
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

### 0. 解析参数

如果 `$ARGUMENTS` 不为空，按以下规则解析出三个变量：

**语法规则：**
- `--skip <file>`：排除单个文件，可重复使用（如 `--skip a.js --skip b.js`）
- `--` 之后的内容：提交信息（无论是否包含 `--skip`）
- `--` 之前、非 `--skip` 及其参数的部分：显式文件列表
- 若存在显式文件列表，则隐式排除所有其他变更文件

**解析流程：**
1. 如果参数中包含 `--`，`--` 之前为选项部分，之后为 `$COMMIT_MSG`
2. 从选项部分提取所有 `--skip <file>` 对（每个 `--skip` 后跟恰好一个 token），存入 `$SKIP_FILES`
3. 剩余 token 存入 `$INCLUDE_FILES`
4. 如果参数中不含 `--`：
   a. 先运行 `git status` 获取变更文件列表
   b. 将 `$ARGUMENTS` 中的每个 token 与变更文件列表比对
   c. 匹配变更文件的 token → `$INCLUDE_FILES`（支持精确匹配、文件名匹配、目录前缀匹配）
   d. 不匹配任何变更文件的 token → 拼接为 `$COMMIT_MSG`（按原顺序，空格连接）
   e. 如果所有 token 都不匹配变更文件 → 整个 `$ARGUMENTS` 作为 `$COMMIT_MSG`（与旧行为一致）

**示例：**

| 输入（变更文件含 `commit/SKILL.md`, `share-skills/SKILL.md`） | $INCLUDE_FILES | $SKIP_FILES | $COMMIT_MSG |
|------|---------------|-------------|-------------|
| `fix login bug` | _(空)_ | _(空)_ | `fix login bug` |
| `commit/SKILL.md share-skills/SKILL.md` | `commit/SKILL.md share-skills/SKILL.md` | _(空)_ | _(空，自动起草)_ |
| `commit/SKILL.md update commit skill` | `commit/SKILL.md` | _(空)_ | `update commit skill` |
| `src/a.js src/b.js -- fix bug` | `src/a.js src/b.js` | _(空)_ | `fix bug` |
| `--skip .env --skip node_modules -- update deps` | _(空)_ | `.env node_modules` | `update deps` |
| `src/a.js --skip test/ -- add feature` | `src/a.js` | `test/` | `add feature` |

后续步骤中使用这三个变量。

### 1. 分析变更

运行以下命令了解当前状态：
- `git status` — 查看哪些文件有变更
- `git diff` — 查看具体改动内容
- `git log --oneline -10` — 查看最近提交风格（语言、格式、前缀约定）

**检查 `.gitignore`：** 读取项目根目录的 `.gitignore` 文件（如果存在），解析其中的忽略规则。在后续步骤 4a 展示文件列表时：
- 将匹配 `.gitignore` 规则的文件自动从待提交列表中排除
- 在排除说明中注明 `.gitignore` 规则来源（如 `backlog.md → .gitignore:24`）
- 注意：git 已追踪的文件即使匹配 `.gitignore` 仍会出现在 `git status` 中，必须手动排除

### 1.5 静态代码检查预检（强制）

**在进入后续步骤前，必须执行项目的静态代码检查并确保零 error。**

**发现项目使用的静态检查工具**：
查看 `package.json`（JS/TS 项目）、`Cargo.toml`（Rust 项目）、`pyproject.toml`（Python 项目）、`Makefile` 或其他配置文件，确定项目使用哪种静态检查工具：
- **JavaScript/TypeScript**：ESLint (`npm run lint` / `pnpm lint` / `yarn lint`)
- **Python**：Pylint、Flake8、Ruff (`pylint` / `flake8` / `ruff check`)
- **Rust**：Clippy、rustc (`cargo clippy` / `cargo check`)
- **Go**：go vet、staticcheck (`go vet` / `staticcheck`)
- **Java**：Checkstyle、SpotBugs
- **其他**：查阅项目文档或询问用户

**执行检查**：
使用项目配置的检查命令运行静态分析。如果无法确定命令，询问用户或跳过（但在步骤 4b 确认时提醒）。

**检查结果判定**：
- ✅ **零 errors，有 warnings** → 允许继续（warnings 通常可接受）
- ❌ **有 errors** → **必须立即修复所有 errors 后才能继续**
- ⚠️ **项目未配置静态检查** → 跳过此步骤，但在步骤 4b 确认时提醒用户"项目未配置静态代码检查工具，建议添加"

**修复原则**：
1. 静态检查 errors 必须修复，不得以"功能正常"、"测试通过"、"时间紧迫"为由绕过
2. 修复方式遵循工具提示（如未使用变量加前缀或删除、导入未使用模块等）
3. 修复后重新运行检查命令确认零 errors
4. 若某条规则确实不合理，应告知用户并建议在配置中禁用，但仍需本次修复或正式禁用后才能提交

**强制输出**：
```
✅ §1.5 静态检查预检通过 — <工具名> 0 errors, N warnings [ | 已修复 M 个 errors: 列出修复项]
```

未输出此确认而直接进入步骤 2，视为流程违规。存在未修复的静态检查 errors 而继续提交，视为严重违规。

### 2. 推断提交风格

从 `git log` 中推断项目的提交约定：
- 语言（中文/英文）
- 是否使用前缀（`feat:` / `fix:` / `chore:` 等）
- 简洁程度

起草的提交信息应遵循项目已有风格，不要引入新格式。

### 3. 起草提交信息

- 如果 `$COMMIT_MSG` 不为空，用其作为提交信息的核心内容
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
| antigravity | Antigravity | noreply@google.com |

**模型：**

| 模型名 | 显示名 | 邮箱 |
|--------|--------|------|
| mimo-v2.5-pro | mimo-v2.5-pro | support-mimo@xiaomi.com |
| claude-opus-4-7 | Claude Opus 4.7 | noreply@anthropic.com |
| claude-sonnet-4-6 | Claude Sonnet 4.6 | noreply@anthropic.com |
| claude-haiku-4-5 | Claude Haiku 4.5 | noreply@anthropic.com |
| gemini-3-flash | Gemini 3 Flash | noreply@google.com |
| deepseek-v4-pro | DeepSeek-V4-Pro | noreply@deepseek.com |

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

**4a. 确定待提交文件列表**

根据解析结果确定待提交文件：

1. **`.gitignore` 自动排除：** 读取 `.gitignore` 中的规则，将匹配的文件从变更列表中移除（无论是否已被 git 追踪）。排除时注明规则来源。

2. **显式文件列表**（`$INCLUDE_FILES` 非空）：**只**使用 `$INCLUDE_FILES` 中列出的文件。逐一验证每个文件确实在 `git status` 的变更列表中，如果不存在则警告用户。**硬约束：禁止基于"关联性""完整性""依赖关系"等理由建议或擅自加入未列出的文件。用户说什么就提交什么，不多不少。**
- **排除列表**（`$SKIP_FILES` 非空，`$INCLUDE_FILES` 为空）：在所有变更文件中，先应用 `.gitignore` 排除，再移除 `$SKIP_FILES` 匹配的文件（支持精确文件名和目录前缀匹配）。
- **两者均为空**：先应用 `.gitignore` 排除，然后使用剩余变更文件，并交互式询问用户排除（见下方交互流程）。

整理最终待提交文件列表，以编号列表形式展示给用户：

```
待提交文件列表：
  1. src/foo.js        (modified)
  2. src/bar.ts        (new file)
  3. test/baz.test.mjs (modified)
```

**交互式排除**（仅当 `$INCLUDE_FILES` 和 `$SKIP_FILES` 均为空时）：

询问用户：「是否有不需要提交的文件？请告诉我编号或文件名，没有请回复"无"。」

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
- 如果 `$COMMIT_MSG` 中提到了某个任务编号，同步将该项标记为已完成
- 任务跟踪文件的更新作为独立 commit 提交并推送
