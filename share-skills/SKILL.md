---
name: share-skills
description: 将 skills 分发/同步到本机所有已安装的 AI 编码工具（Cursor、CodeBuddy、Windsurf、TRAE、Antigravity、Kiro、Qoder、Cline、VS Code 等）。
when_to_use: 用户说"共享 skills"、"同步 skills"、"share skills"、"分发 skills"
argument-hint: [--list | --add <skill> | --sync]
---

## Skills 跨工具分发流程

### 0. 参数解析

- **无参数** 或 `--sync`：全量同步所有 skills 到所有已安装工具
- `--list`：列出可共享的 skills，不做分发
- `--add <skill>`：仅分发指定的单个 skill

### 1. 发现可共享的 skills

扫描 `~/.ai-skills/` 目录，每个子目录就是一个 skill：

```
~/.ai-skills/
├── <skill-name>/SKILL.md
```

读取每个 SKILL.md 的 frontmatter，提取 `name` 和 `description`，形成列表。

### 2. 检测已安装的 AI 工具

采用全量扫描 + 注册表比对机制，**不硬编码任何工具路径**。

#### 2.1 全量扫描

执行以下扫描命令，**枚举系统上所有 AI 工具目录和 IDE 扩展目录**。只排除明确的系统目录，不得用关键词过滤（会漏掉新工具）：

```bash
# 扫描 ~/.* 下所有目录
# 核心逻辑：不按目录名匹配，而是按目录内容检测
# 一个目录"像 AI 工具"的判断依据：包含 .md 规则/指令文件，或包含 SKILL.md，或包含 package.json
ls -d ~/.* 2>/dev/null | while read dir; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  # 只排除明确的系统/缓存目录
  case "$name" in
    .Trash|.DS_Store|.ssh|.gnupg|.npm|.yarn|.gradle|.m2|.docker|.vagrant|.ansible|.oh-my-zsh|.nvm|.pyenv|.rbenv|.cargo|.rustup|.volta|.bun|.node_modules) continue ;;
  esac
  # 内容检测：查找目录内包含 .md 文件或 package.json 的子目录
  # .md 文件排除 README/CHANGELOG/LICENSE/CONTRIBUTING 等非指令文件
  find "$dir" -maxdepth 3 \( \
    \( -name "*.md" -type f ! -name "README*" ! -name "CHANGELOG*" ! -name "LICENSE*" ! -name "CONTRIBUTING*" ! -name "CODE_OF_CONDUCT*" \) -o \
    \( -name "SKILL.md" -type f \) -o \
    \( -name "package.json" -type f \) \
  \) 2>/dev/null | while read file; do
    dirname "$file"
  done | sort -u | while read subdir; do
    count=$(ls "$subdir" 2>/dev/null | wc -l | tr -d ' ')
    echo "FOUND|$name|$subdir|$count"
  done
done
```

**关键区别**：旧方案用 `-name "skills"` 等精确名称匹配，会漏掉 `builtInSkills`、`skill`（单数）、`agents`、`subagents` 等变体。新方案检测目录内容（是否有 `.md` 指令文件或 `package.json`），与目录名无关。

同时扫描：
- `/Applications/` 下的 IDE 应用
- `~/Library/Application Support/` 下的 IDE 配置目录
- VS Code 扩展内部的 skills 目录（如 `~/.vscode/extensions/*/skills/`、`~/.vscode/extensions/*/builtInSkills/`）

**禁止**：不得按目录名匹配（如 `-name "skills"`），必须按内容检测。新工具的目录名不可预测（可能是 `builtInSkills`、`skill`、`agents`、`subagents` 等任意名称）。

#### 2.2 与注册表比对

读取 `~/.ai-skills/share-skills/registry.json`，将扫描结果分为三类：

1. **已注册且存在**：注册表中有，且 `detect_path` 存在 → 标记为"已安装"
2. **已注册但不存在**：注册表中有，但 `detect_path` 不存在 → 标记为"已卸载"（不自动删除，报告中提示）
3. **未注册但存在**：注册表中没有，但扫描发现了含 `extensions/plugins/packages/skills/workflows/rules` 子目录的目录 → 标记为"新发现"

#### 2.3 自动注册新工具

扫描发现的未注册工具目录**直接自动写入 `registry.json`，不询问用户**。推断规则：

1. **工具名**：从目录名提取（去掉开头的 `.`）
2. **格式**：默认 `agent-skills`（如果子目录名含 `workflows` 则为 `markdown-workflow`，含 `rules` 则为 `markdown-merge`）
3. **分发方式**：默认 `symlink`（如果子目录名含 `workflows` 则为 `copy`）
4. **skills_dir**：取扫描发现的第一个匹配子目录

写入 `registry.json` 后，在分发阶段自动同步 skills。仅在同步报告中列出新注册的工具供用户事后确认。

#### 2.4 展示检测结果

汇总所有已安装工具（已注册 + 新发现），向用户展示确认：

### 3. 分发 skills

根据注册表中每个工具的 `format` 和 `method` 字段自动选择分发策略。以下按格式分类说明：

#### 3a. Agent Skills 格式（method: symlink）

适用于注册表中 `format: "agent-skills"` 的工具。直接创建 symlink，一个 skill 对应一个目录：

```bash
ln -s ~/.ai-skills/<skill> <skills_dir>/<skill>
```

如果目标已存在同名目录，检查是否是 symlink：
- 是 symlink 且指向正确 → 跳过
- 是 symlink 但指向错误 → 删除重建
- 不是 symlink → 备份后替换为 symlink

#### 3b. Agent Skills 格式（method: copy）

适用于注册表中 `format: "agent-skills", method: "copy"` 的工具（如 VS Code）。在 skills 目录下创建 SKILL.md 副本：

```bash
mkdir -p <skills_dir>/<skill>
cp ~/.ai-skills/<skill>/SKILL.md <skills_dir>/<skill>/SKILL.md
```

如果目标已存在，检查内容是否相同：
- 内容相同 → 跳过
- 内容不同 → 覆盖更新

#### 3c. Markdown Workflow 格式（method: copy）

适用于注册表中 `format: "markdown-workflow"` 的工具（如 Windsurf、Antigravity）。在 skills 目录下生成 `.md` 文件：

```markdown
---
<frontmatter 字段，从注册表的 frontmatter 配置读取>
description: <从 SKILL.md frontmatter 的 description 字段提取>
---

<SKILL.md 的正文内容>
```

文件名：`<skill-name>.md`

注意：如果注册表中有 `limits`（如 Antigravity 的 description 250 字符、body 12000 字符），需按限制截断。description 和正文中不能包含 `---`（会被误解析为 frontmatter 分隔符）。

#### 3d. Markdown Merge 格式（method: merge）

适用于注册表中 `format: "markdown-merge"` 的工具（如 Cline）。将所有 skills 合并到一个配置文件：

```markdown
# Shared Skills

## <skill-name>

<SKILL.md 正文内容>

---

## <next-skill-name>

...
```

重建整个文件，不追加（避免重复内容）。

#### 3e. Claude Code 插件（method: none）

适用于注册表中标记为 `method: "none"` 的工具（如 TRAE）。无需操作，这些工具通过 Claude Code 插件自动读取 `~/.claude/skills/`。

#### 3f. 新工具（注册表外）

对于 §2.3 中新注册的工具，如果用户指定了自定义分发逻辑，在分发时按用户指定的方式处理。如果用户未指定具体格式，询问用户后决定。

### 4. 报告分发结果

展示每个工具的分发情况：
- 工具名
- 分发的 skills 列表
- 分发方式（symlink / 复制 / 跳过）
- 任何错误或警告

### 5. 注册表维护

工具注册表位于 `~/.ai-skills/share-skills/registry.json`。每次运行 `/share-skills` 时：

1. **自动更新**：§2 发现的新工具在用户确认后自动写入注册表
2. **失效清理**：如果注册表中某个工具的 `detect_path` 已不存在，标记为"已卸载"但不自动删除（避免误删），在分发报告中提示用户
3. **手动编辑**：用户可直接编辑 `registry.json` 调整工具配置（如修改 skills 目录路径、添加自定义格式）

### 6. 注意事项

- **TRAE** 无需操作：已有 Claude Code 插件，自动读取 `~/.claude/skills/`
- **Windsurf** 使用 workflow 格式，如果 SKILL.md 中有 `allowed-tools` 等 Agent Skills 专有字段，会在 Windsurf 中被忽略但不影响使用
- **Antigravity** 使用 workflow 格式，description 最多 250 字符、正文最多 12000 字符，内容中不能含 `---`
- **Kiro** 使用 Agent Skills 标准，SKILL.md 格式与本项目一致，symlink 即可；另有 steering 文件（`~/.kiro/steering/*.md`）用于项目规范
- **Qoder** 使用 Agent Skills 标准，SKILL.md 格式与本项目一致，symlink 即可；另有 rules（`.qoder/rules/`）用于项目规则
- **Cline** 的 `.clinerules` 是项目级文件，需要在每个项目中创建
- **VS Code Copilot** 的 skills 是项目级副本，修改全局 skill 后需重新运行 `--sync` 更新
- 新增 skill 后运行 `--sync` 即可同步到所有工具
