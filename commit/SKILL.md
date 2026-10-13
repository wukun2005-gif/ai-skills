---
name: commit
description: Git 提交并推送到当前分支，然后更新项目任务跟踪文件。分析变更、推断提交风格、起草提交信息、commit、push。支持通过参数指定要提交的文件列表（`file1 file2 -- msg`）或排除列表（`--skip file -- msg`）。若本次任务是在 worktree（独立目录）中完成的，提交后自动合并回主目录 main 分支并删除该 worktree 目录。
when_to_use: 用户说"提交"、"commit"、"提交并推送"、"合并回主目录"、"删掉 worktree"
allowed-tools:
  - Bash(git add *)
  - Bash(git commit *)
  - Bash(git push *)
  - Bash(git status *)
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(git merge *)
  - Bash(git fetch *)
  - Bash(git checkout *)
  - Bash(git rev-parse *)
  - Bash(git worktree list*)
  - Bash(git worktree remove*)
  - Bash(git worktree prune*)
  - Bash(git -C * add *)
  - Bash(git -C * commit *)
  - Bash(git -C * push *)
  - Bash(git -C * status *)
  - Bash(git -C * diff *)
  - Bash(git -C * log *)
  - Bash(git -C * merge *)
  - Bash(git -C * fetch *)
  - Bash(git -C * checkout *)
  - Bash(git -C * rev-parse *)
  - Bash(git -C * worktree *)
---

## 提交、推送、更新任务跟踪 流程

按以下步骤执行：

**注意**：如果本次任务是在 worktree（独立目录）中完成的，步骤 6 会把改动合并回主目录 main 并删除该 worktree 目录，**不能跳过**。判断方法见 §6.1。

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

### 1.6 法律合规预检（按条件触发）

**先判断是否触发：** 阅读项目的调研报告、PRD、Dev Plan 和待提交代码，判断本项目是否大量使用了他人的工作（第三方开源库、复制来的开源代码、借用的文档/图片/素材等）。

- 大量使用了他人成果（无论其 license 是 public/MIT/Apache/BSD 还是其他）→ **执行本检查**
- 基本为原创、极少依赖外部成果 → 跳过，但在步骤 4b 确认时说明「未触发法律合规检查」

**检查待提交内容是否有法律风险：**

1. **license 问题**：引入的第三方代码/素材的 license 是否允许在本项目中使用和发布；是否与本项目自身的 license 冲突
2. **OSS 声明问题**：使用了开源代码却缺少应有的声明——license 文本、原版权头、NOTICE / THIRD-PARTY 清单未保留或未随项目上传
3. **版权问题**：是否有复制自他人但未获授权的内容（代码、文档、图片、字体等），包括看似"网上随便拿的"素材
4. **误提交问题**：待提交文件里是否混入了不能公开的内容（他人 proprietary 代码、客户/公司内部资产、无授权素材）

**处理规则：**

- ✅ 无风险，或风险已在本次提交前解决 → 继续
- ❌ 存在未解决的风险 → **必须解决后才能 commit**。解决方式：移除有问题的内容、补齐 license/版权声明、或把处置方式告知用户并等确认。不得以"风险很小""没人查"为由跳过
- 无法判断某项是否有风险 → 列出疑点，询问用户确认后再继续

**强制输出：**
```
✅ §1.6 法律合规预检通过 — 无 license/OSS/版权风险 [ | 已处理: <解决项>]
```
未输出此确认而进入步骤 2，视为流程违规；带着未解决的法律风险提交，视为严重违规。

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
| opencode | opencode | noreply@opencode.ai |

**模型：**

| 模型名 | 显示名 | 邮箱 |
|--------|--------|------|
| mimo-v2.5-pro | mimo-v2.5-pro | support-mimo@xiaomi.com |
| claude-opus-4-7 | Claude Opus 4.7 | noreply@anthropic.com |
| claude-sonnet-4-6 | Claude Sonnet 4.6 | noreply@anthropic.com |
| claude-haiku-4-5 | Claude Haiku 4.5 | noreply@anthropic.com |
| gemini-3-flash | Gemini 3 Flash | noreply@google.com |
| step-5-preview | Step 5 Preview | noreply@stepfun.com |
| deepseek-v4-pro | DeepSeek-V4-Pro | noreply@deepseek.com |
| deepseek-v4-flash-free | DeepSeek-V4-Flash-Free | noreply@deepseek.com |
| glm-5.3-flash | GLM-5.3-Flash | noreply@z.ai |
| mimo-v2.5-free | MiMo-V2.5-Free | support-mimo@xiaomi.com |
| mimo-v2.5-flash-free | MiMo-V2.6-Flash-Free | support-mimo@xiaomi.com |
| mimo-v2.6-flash-free | MiMo-V2.6-Flash-Free | support-mimo@xiaomi.com |
| space-bunny-free | Space Bunny Free | noreply@opencode.ai |

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
9. 系统提示含 "opencode" → `opencode`

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
git push origin <当前分支>
```

当前分支名用 `git rev-parse --abbrev-ref HEAD` 取，**不要硬编码 `main`**——在 worktree 中工作时当前分支是功能分支，推错分支会把别人的 main 或别的工作覆盖掉。

不要使用 `git add -A` 或 `git add .`，只添加与本次变更直接相关的文件。

**4c. 验证 push 成功**

执行 `git status`，确认输出不显示 `ahead N`。若仍显示 `ahead N`，说明 push 未成功，必须排查原因（网络、认证、权限）并重试 `git push origin <当前分支>`，直到验证通过。

### 5. 更新项目任务跟踪

检查项目中是否存在任务跟踪文件（如 `backlog.md`、`TODO.md`、`CHANGELOG.md` 等）：
- 如果存在且有变更，检查是否需要更新对应条目的状态
- 如果 `$COMMIT_MSG` 中提到了某个任务编号，同步将该项标记为已完成
- 任务跟踪文件的更新作为独立 commit 提交并推送

### 6. 合并回主目录并删除 worktree（仅 worktree 场景）

**这一步只在"本次任务是在独立目录（worktree）中完成的"时才执行。** 主目录里直接干活的用户跳过整个 §6。

#### 6.1 判断当前是否在 worktree 中

```bash
git rev-parse --git-dir
git rev-parse --git-common-dir
```

- 两个输出**相同** → 在主目录本身，不是 worktree → 跳过 §6，本流程结束
- 两个输出**不同** → 在 worktree 中（`--git-dir` 会形如 `<主目录>/.git/worktrees/<名字>`）→ 继续 §6.2

取出主目录路径和本次使用的分支：

```bash
git worktree list --porcelain     # 第一条 `worktree <路径>` 记录就是主目录
git rev-parse --abbrev-ref HEAD   # 当前 worktree 的分支名，记为 <WT_BRANCH>
```

记下：
- `<MAIN_DIR>`：主目录路径（来自 `git worktree list --porcelain` 第一条）
- `<WT_BRANCH>`：当前分支名
- `<WT_DIR>`：当前 worktree 目录路径（`git rev-parse --show-toplevel`）

**后续所有针对主目录的命令一律用 `git -C <MAIN_DIR> ...` 执行，不要 `cd` 过去。** 用 `cd` 会让后续命令的工作目录被悄悄改掉。

#### 6.2 合并前必查：主目录有没有别人的痕迹

**这一步是硬性前置检查，必须先跑完再谈合并。**

```bash
git -C <MAIN_DIR> fetch origin
git -C <MAIN_DIR> status --short                      # ① 主目录的未提交改动
git -C <MAIN_DIR> rev-parse --abbrev-ref HEAD          # ② 主目录当前在哪个分支
git -C <MAIN_DIR> log --oneline <WT_BRANCH>..main      # ③ 主目录有、worktree 没有的新提交
git -C <MAIN_DIR> log --oneline origin/main..main      # ④ 主目录有、还没推送的提交
```

按结果处理：

**① `status --short` 有输出（主目录有未提交改动）→ 立即停下**

- 把主目录的未提交文件清单原样报告给用户，说明"主目录有未提交改动，本次不合并"
- **绝对不要碰它们**：不 merge、不 stash、不 checkout、不 add、不 reset、不删文件、不覆盖
- 保留 worktree 目录不删，等用户处理完主目录再说
- 本流程在此结束，等用户下次触发时再继续

**② 主目录不在 `main` 分支 → 停下**

报告主目录当前在哪个分支，问用户是切到 main 还是就在那个分支上合并。等用户回答，不自行切换。

**③ 主目录有 `<WT_BRANCH>` 之外的新提交 → 正常合并**

这属于正常情况：别人（或你自己在主目录里）后来又提交了。直接进入 §6.3 正常 merge，git 会自己处理"两边都改"的部分。**冲突了就按 §6.3 的规则报告，不要自己丢弃任何一边。**

**④ 主目录有未推送提交**

合并前先把它推上去（`git -C <MAIN_DIR> push origin main`），再合并，避免合并结果和未推送提交混在一起说不清。

**全部检查通过 → 进入 §6.3**

#### 6.3 合并

```bash
git -C <MAIN_DIR> merge --no-ff <WT_BRANCH> -m "merge <WT_BRANCH> into main"
```

**合并冲突时的处理规则（硬约束）：**

- `git merge` 冲突时会返回非 0 退出码，并在冲突文件里留下 `<<<<<<<` / `=======` / `>>>>>>>` 标记——**两边的内容都还在文件里，谁都没被丢掉**。此时不要自己去删这些标记。
- 立刻执行 `git -C <MAIN_DIR> status` 和 `git -C <MAIN_DIR> diff --name-only --diff-filter=U`，把冲突文件列出来报告给用户：哪些文件冲突、`<<<<<<<` 上面（main）和下面（worktree）各是什么内容。
- **禁止**：`git merge -X ours` / `-X theirs`、`git checkout --ours/--theirs`、`git reset --hard`、`git merge --abort`、或任何"挑一边留下"的写法。
- 不自行改写冲突文件的内容交给用户决定。报告完就停，等用户指示。
- 用户决定怎么解之后：`git -C <MAIN_DIR> add <冲突文件>` → `git -C <MAIN_DIR> commit` → `git -C <MAIN_DIR> push origin main`。

**合并成功后**：

```bash
git -C <MAIN_DIR> push origin main
git -C <MAIN_DIR> log --oneline -5    # 确认合并提交已产生
```

然后报告：合并结果、是否产生 merge commit、main 是否已推送成功。

#### 6.4 删除 worktree 目录

**只有"合并成功且 main 已推送"之后才删。** 前置条件：

```bash
git -C <WT_DIR> status --short        # 必须为空
```

- **有输出** → worktree 里还有没提交的东西，说明合并没覆盖全 → **不要删**，报告剩余改动，保留目录
- **为空** → 执行删除：

```bash
git -C <MAIN_DIR> worktree remove <WT_DIR>
git -C <MAIN_DIR> worktree prune
```

- `worktree remove` 失败时**不要用 `rm -rf` 强删**，把它报的错原样告诉用户（如"contains modified or untracked files"）
- 如果当前 shell 的工作目录正好在被删的 worktree 里，删除后该 shell 会报 `Unable to read current working directory`——先 `cd <MAIN_DIR>` 再继续
- 删除后用 `git worktree list` 确认该条目已消失

最后向用户汇报：主目录 main 的合并结果 + worktree 目录是否已删除。

#### 6.5 全流程硬约束（复述，防止中途忘记）

1. 主目录有未提交改动 → **停，不动**
2. 任何冲突 → **报告，两边都不丢**
3. 合并未成功 → **不删 worktree**
4. 不用 `rm -rf` / `reset --hard` / `-X ours` / `-X theirs` 绕过任何一步
