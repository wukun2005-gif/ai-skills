---
name: bug-scan
description: >
  全项目 bug 自查：结合 commit 历史分析 bug-fix 共性模式，静态检查 + 死 Feature 检测 + 动态运行检查，
  找出测试覆盖盲区和零价值死代码，将所有问题写入 backlog.md 并返回 feature ID 列表。
when_to_use: 用户说"自查bugs"、"bug扫描"、"bug审查"、"找bug"、"查bug"、"bug scan"、"全面检查"
---

## 全项目 Bug 自查流程

> **核心理念：不只找 bug，更要找 bug 的根因模式。一个模式修复一次，胜过十个 bug 逐个修。**

### 0. 项目全景理解

**先理解项目，再找 bug。** 从零开始阅读，不依赖任何先验知识。

#### 0.1 文档阅读

依次阅读以下文件（若存在）：

1. **`README.md`** — 项目简介、功能列表、使用方式
2. **`DESIGN.md`** — 架构设计、技术栈、接口定义
3. **`PRD.md`** / **`requirements.md`** — 产品需求
4. **`backlog.md`** / **`TODO.md`** — 已有 backlog 和待办
5. **`CLAUDE.md`** / **`.cursorrules`** / **`.clinerules`** — 项目开发规范

记录：项目目标、技术栈、架构模式、已知问题。

#### 0.2 全量文件清单（不限于源码）

**关键：bug 不只藏在源码里。** 配置错误、prompt 注入、shell 注入、schema 断裂、fixture 过期——这些都不是传统源码文件，但同样会产生 bug。

```bash
# 全量文件清单（排除 node_modules/.git/dist/build），按扩展名分组统计
find . -type f ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" ! -path "*/build/*" \
  | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -30

# 分类扫描，确保每个类别都被覆盖：
# 1. 源代码
find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \
  -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.vue" -o -name "*.svelte" \
  -o -name "*.html" -o -name "*.css" -o -name "*.scss" -o -name "*.mjs" -o -name "*.cjs" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" ! -path "*/build/*" \
  ! -name "*.test.*" ! -name "*.spec.*" ! -name "*.d.ts" | wc -l

# 2. 测试代码（包括测试框架/基础设施/fixture）
find . -type f \( -name "*.test.*" -o -name "*.spec.*" -o -name "*_test.*" -o -name "test_*" \
  -o -name "setup.*" -o -name "globalSetup.*" -o -name "*fixture*" -o -name "*mock*" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" | head -50

# 3. 配置文件（项目配置、构建配置、编辑器配置、环境变量）
find . -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" \
  -o -name "*.config.*" -o -name ".*rc" -o -name ".*rc.*" -o -name ".env*" \
  -o -name "tsconfig*" -o -name "vite.config*" -o -name "vitest*config*" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" | head -30

# 4. Shell 脚本和工具脚本
find . -type f \( -name "*.sh" -o -name "*.bash" -o -name "*.zsh" -o -name "Makefile" \
  -o -name "Dockerfile" -o -name "docker-compose*" -o -name "Procfile" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"

# 5. AI Prompt 模板（AI 项目特有）
find . -type f \( -name "*prompt*" -o -name "*template*" \) \
  \( -name "*.md" -o -name "*.txt" -o -name "*.j2" -o -name "*.hbs" -o -name "*.mustache" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"

# 6. Schema / 类型定义（验证层）
find . -type f \( -name "*schema*" -o -name "*types*" -o -name "*interface*" \) \
  \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" -o -name "*.go" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" ! -name "*.d.ts"

# 7. 静态资源和文档
find . -type f \( -name "*.pdf" -o -name "*.png" -o -name "*.jpg" -o -name "*.gif" \
  -o -name "*.svg" -o -name "*.md" -o -name "*.txt" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" | wc -l
```

**扫描完成后的检查清单**（必须逐项确认）：

| 类别 | 是否已扫描 | 典型遗漏风险 |
|------|-----------|-------------|
| 源代码 | ☐ | 入口文件、核心模块、API/路由 |
| 测试代码 + 测试框架 | ☐ | setup/fixture/mock 是否有 bug |
| 配置文件 | ☐ | .env 泄露、tsconfig 错误、构建配置 |
| Shell/工具脚本 | ☐ | shell 注入、路径拼接错误 |
| AI Prompt 模板 | ☐ | prompt 注入、变量未替换、与 schema 不匹配 |
| Schema/类型定义 | ☐ | schema 定义了但 handler 没校验 |
| 静态资源/文档 | ☐ | 文档描述 vs 代码实现不一致 |

---

### 1. Commit 历史分析（核心差异化）

**这是本 skill 最独特的部分：从历史 bug-fix 中提取共性模式。**

#### 1.1 提取 Bug-Fix Commit

```bash
# 获取所有 bug-fix 相关的 commit（中英文关键词）
git log --oneline --all --no-merges | grep -iE "fix|bug|patch|hotfix|修复|缺陷|issue|error"

# 如果 commit 过多，只取最近 100 条
git log --oneline --all --no-merges -100 | grep -iE "fix|bug|patch|hotfix|修复|缺陷|issue|error"
```

#### 1.2 分析每个 Bug-Fix Commit

对每个 bug-fix commit，提取：

```bash
# commit 详细信息
git show <hash> --stat

# 具体改动内容
git show <hash>
```

分析维度：
- **改动文件**：哪些文件被修改？
- **改动类型**：是新增检查、修改逻辑、还是重构？
- **Bug 类型**：空值检查？边界条件？并发问题？类型错误？逻辑错误？
- **修复模式**：加 if 判断？加 try-catch？改循环条件？加锁？

#### 1.3 提取 Bug 模式清单

将所有 bug-fix 归类为模式，例如：

| 模式 ID | 模式名称 | 出现次数 | 典型 commit | 典型文件 |
|---------|---------|---------|-------------|---------|
| PATTERN-1 | 空值/undefined 未检查 | 5 | abc123 | src/utils.js |
| PATTERN-2 | 数组越界/空数组 | 3 | def456 | src/parser.js |
| PATTERN-3 | 异步竞态条件 | 2 | ghi789 | src/api.js |

**参考基准：高频 Bug 模式（从大量项目提炼）**

以下是跨项目反复出现的高频模式，可作为归类参考。如果项目 commit 命中这些模式，优先标记：

| 模式 | 典型表现 | 检查命令 |
|------|---------|---------|
| **持久化缺失** | store 更新只改内存，刷新后数据丢失 | `grep -rn "set\|update" --include="*Slice.ts" .` 检查是否有 IDB 写入 |
| **JSON 解析无防护** | JSON.parse 无 try-catch，外部数据损坏时白屏 | `grep -rn "JSON.parse" --include="*.ts" --include="*.tsx" .` |
| **组件卸载后 setState** | 用户导航离开后异步操作继续执行 | `grep -rn "setState\|set[A-Z]" --include="*.tsx" .` 检查是否有 isMountedRef |
| **null/undefined 防护缺失** | 访问嵌套属性崩溃 | `grep -rn "\!\." --include="*.ts" --include="*.tsx" .` 扫描非空断言 |
| **死代码** | 写了函数/组件/配置但从未被调用 | 见 §2.4 死代码专项检测 |
| **console.log 残留** | 生产环境泄露调试信息 | `grep -rn "console\." --include="*.ts" --include="*.tsx" .` |
| **React Key 不稳定** | key 用 index 或可编辑字段，导致重挂载 | `grep -rn "key={i}" --include="*.tsx" .` |
| **useEffect 依赖不稳定** | 每次渲染创建新引用，导致无限循环 | 检查 useEffect 依赖数组中是否有 `.filter()`、`.map()` 等 |

#### 1.4 标记高风险文件

**高风险文件** = 被多次 bug-fix 的文件。这些文件很可能还有未发现的 bug。

```bash
# 统计每个文件被 bug-fix 的次数
git log --oneline --all --no-merges | grep -iE "fix|bug" | awk '{print $1}' | while read hash; do
  git show --stat --format='' "$hash" | awk '{print $1}'
done | sort | uniq -c | sort -rn | head -20
```

#### 1.5 检查模式是否已彻底修复

对每个 bug 模式：
1. 找到所有相关文件
2. 检查这些文件中是否还有类似的代码模式
3. 如果还有 → 标记为"模式未彻底修复"，生成 backlog 条目

---

### 2. 静态代码检查

#### 2.1 项目静态检查工具检测

```bash
# 检测项目类型和对应的静态检查工具
if [ -f "package.json" ]; then
  # JavaScript/TypeScript 项目
  cat package.json | grep -E "eslint|lint|prettier"
elif [ -f "Cargo.toml" ]; then
  # Rust 项目
  echo "cargo clippy / cargo check"
elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
  # Python 项目
  echo "ruff / flake8 / pylint"
elif [ -f "go.mod" ]; then
  # Go 项目
  echo "go vet / staticcheck"
fi
```

#### 2.2 运行静态检查

根据检测结果运行对应的静态检查命令。收集所有 errors 和 warnings。

**重要：Monorepo / 多子项目必须逐一检查。** 根项目的静态检查不会自动覆盖子项目。

```bash
# TypeScript 项目：根 tsc 可能不检查子项目，必须分别检查每个 tsconfig
# 检查所有 tsconfig 文件
find . -name "tsconfig*.json" ! -path "*/node_modules/*" ! -path "*/.git/*" ! -name "tsconfig.tsbuildinfo"

# 对每个 tsconfig 分别运行类型检查
for tsconfig in $(find . -name "tsconfig.json" -o -name "tsconfig.build.json" \
  ! -path "*/node_modules/*" ! -path "*/.git/*"); do
  echo "=== Checking: $tsconfig ==="
  npx tsc --noEmit -p "$tsconfig" 2>&1 | tail -10
done

# Python 项目：检查每个子目录的 pyproject.toml / setup.py
find . -name "pyproject.toml" -o -name "setup.py" \
  ! -path "*/node_modules/*" ! -path "*/.git/*" | while read f; do
  echo "=== Checking: $f ==="
  dir=$(dirname "$f")
  cd "$dir" && ruff check . 2>&1 | tail -10; cd -
done

# Go 项目：检查所有 go.mod
find . -name "go.mod" ! -path "*/vendor/*" ! -path "*/node_modules/*" | while read f; do
  echo "=== Checking: $f ==="
  dir=$(dirname "$f")
  cd "$dir" && go vet ./... 2>&1 | tail -10; cd -
done
```

#### 2.3 代码模式扫描

**关键规则：每个模式的扫描结果必须写入 backlog，不能只计数不记录。** 如果某个模式发现了 N 处问题，至少生成一个 backlog 条目汇总该模式（可以合并为一个条目，但必须写入）。

扫描以下代码模式（这些模式容易产生 bug）：

```bash
# TODO/FIXME/HACK/XXX 注释
grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.{js,ts,jsx,tsx,py,go,rs}" . | grep -v node_modules

# 空 catch 块（静默吞掉错误，是 bug 的温床）
grep -rn "catch.*{" --include="*.{js,ts,jsx,tsx}" . | grep -v node_modules | head -30
# 进一步检查 catch 块是否为空（只有 { } 没有处理逻辑）
grep -rn "catch.*{" --include="*.ts" --include="*.tsx" --include="*.js" . \
  | grep -v node_modules | while IFS=: read file line content; do
    next=$((line + 1))
    catch_body=$(sed -n "${next}p" "$file" 2>/dev/null | tr -d '[:space:]')
    if [ "$catch_body" = "}" ] || [ -z "$catch_body" ]; then
      echo "EMPTY_CATCH: $file:$line"
    fi
  done

# 硬编码的魔法数字
grep -rn "[^a-zA-Z_][0-9]\{3,\}[^a-zA-Z_]" --include="*.{js,ts,jsx,tsx,py}" . | grep -v node_modules | head -20

# console.log 遗留（生产代码不应有）
grep -rn "console\.log\|console\.error\|console\.warn" --include="*.{js,ts,jsx,tsx}" . | grep -v node_modules | grep -v test

# 未使用的变量（ESLint 规则 no-unused-vars）
# 已在静态检查工具中覆盖
```

**扫描完成后，必须为以下模式生成 backlog 条目（如果发现了问题）：**

| 模式 | Backlog 格式 | 优先级 |
|------|-------------|--------|
| 空 catch 块 > 5 处 | `[CodeSmell] 空 catch 块批量修复 — 静默吞掉错误导致问题难以排查` | P1 |
| console.log 遗留 > 0 处 | `[CodeSmell] 生产代码中遗留 console.log — 可能泄露调试信息` | P2 |
| TODO/FIXME > 10 处 | `[CodeSmell] 积压的 TODO/FIXME — 技术债务清单` | P2 |
| 硬编码魔法数字 > 10 处 | `[CodeSmell] 硬编码魔法数字 — 可读性差，应提取为常量` | P3 |

#### 2.4 死 Feature / 死代码检测

**找出"写了但没人用"的 feature：代码实现了功能，但从未被调用、未接入入口、或已被替代代码绕过，对用户零价值。**

##### 调用方三问（快速检查入口）

**根因**：从"实现方"出发写代码，会导致写了函数没人调、写了配置没被读、迁移了新端没清理旧端。

在执行详细的死代码检测前，先用三个问题快速定位问题区域：

| 问题 | 检查方法 | 典型问题 |
|------|---------|---------|
| **1. 这个代码谁调用？** | `grep -r "函数名/组件名" --include="*.ts" --include="*.tsx"` | 函数/组件/export 写了但无调用方 |
| **2. 调用链路完整吗？** | 从 UI → API → 逻辑端到端 trace | 配置 UI 写了但配置没被读取、参数传递断裂 |
| **3. 旧代码还有谁在用？** | `grep -r "旧函数名"` 确认无调用方后删除 | 迁移后旧代码残留、替代实现并存 |

**快速扫描命令**：

```bash
# 问题 1：找 export 但未被 import 的符号
# 提取所有 export，检查是否被其他文件 import
grep -rn "^export \(function\|const\|class\|interface\|type\)" --include="*.ts" --include="*.tsx" . \
  | grep -v node_modules | grep -v "\.d\.ts" | grep -v "\.test\." | grep -v "\.spec\." \
  | while IFS=: read file line content; do
    symbol=$(echo "$content" | sed -n 's/.*export \(function\|const\|class\) \+\([a-zA-Z_][a-zA-Z0-9_]*\).*/\2/p')
    if [ -n "$symbol" ]; then
      count=$(grep -r "$symbol" --include="*.ts" --include="*.tsx" . | grep -v node_modules | grep -v "$file" | grep -v "\.d\.ts" | wc -l)
      if [ "$count" -eq 0 ]; then
        echo "DEAD_EXPORT: $file:$line — $symbol (0 imports)"
      fi
    fi
  done

# 问题 2：找配置读取但未传递的模式
grep -rn "settings\.\|config\.\|readSettings" --include="*.ts" --include="*.tsx" . | grep -v node_modules | head -30

# 问题 3：找迁移后残留的旧代码
# 如果有 MIGRATE 类型的 commit，检查旧模块是否还有调用
git log --oneline | grep -i "migrate\|迁移" | head -10
```

**判定标准**：
- 函数/组件 0 个调用方 → **死代码**，P1
- 配置读取后未传递给执行函数 → **配置未生效**，P0
- 迁移后旧模块仍有调用 → **需确认是双路径还是遗漏**，P1
- 迁移后旧模块无调用但未删除 → **死代码应清理**，P2

##### 2.4.1 扫描入口点，建立调用图

```bash
# 找到所有入口文件（main/entry/index/app/server 等）
find . -type f \( -name "main.*" -o -name "entry.*" -o -name "index.*" \
  -o -name "app.*" -o -name "server.*" -o -name "cli.*" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" \
  ! -name "*.test.*" ! -name "*.spec.*" ! -name "*.d.ts"

# 找到所有 export 但从未被 import 的模块/函数
# （先列出所有 export，再检查是否被其他文件 import）
```

##### 2.4.2 识别死 Feature 的典型特征

逐个检查以下模式：

| 模式 | 检测方法 | 说明 |
|------|---------|------|
| **无入口的页面/路由** | grep 路由定义，检查是否被导航/菜单引用 | 有页面组件但没有路由指向它 |
| **无调用的 CLI 命令** | grep 命令注册，检查是否在 help/docs 中列出 | 注册了命令但用户发现不了 |
| **export 未被 import** | 对每个 export symbol，grep 整个项目看是否有 import | 工具函数/类写了但没人用 |
| **功能开关永关** | grep feature flag/配置项，检查默认值和调用分支 | feature flag 默认 false，且没有开启路径 |
| **被注释掉的调用** | grep 被注释的 import/调用 | 曾经接入过，后来被注释而非删除 |
| **替代实现并存** | 两个模块实现相同功能，只有一条路径被调用 | 新实现替代了旧的，旧代码未清理 |
| **入口文件未引用的子模块** | 从入口文件 trace 依赖树，未被触及的模块 | 子模块存在但整个依赖链断裂 |
| **import 了但从未调用** | 某文件 import 了模块/函数，但该文件的实际执行路径中从未调用它；可能是接入了一半、重构后残留、或被替代路径绕过 | 比"export 未被 import"更隐蔽：import 存在，编译不报错，但运行时该代码是死的 |
| **枚举/状态机只实现了部分值** | 枚举类型定义了 N 个值，但代码只读写其中少数几个；状态机设计了完整流转，但实际只有几个转换被编码 | 设计完整、实现残缺，用户在中间阶段看不到状态反馈 |
| **标签映射与枚举不匹配** | 存在 enum→label 的映射表（如 WORKFLOW_LABELS），但 key 与实际 enum 成员对不上 | 即使状态被推进，显示的也是原始值而非人类可读标签 |

##### 2.4.3 枚举/状态机缺口专项检测

**这是设计-实现 gap 的典型表现：类型系统定义了完整的状态空间，但业务代码只触及了其中一小部分。**

**Step 1：找到所有枚举和状态机定义**

```bash
# TypeScript/JavaScript — 找 enum 定义和联合类型
grep -rn "enum\s\+\w\+" --include="*.ts" --include="*.tsx" . | grep -v node_modules
grep -rn "type\s\+\w\+\s*=" --include="*.ts" --include="*.tsx" . | grep -v node_modules | grep "|"

# Python — 找 Enum 类和 Literal 类型
grep -rn "class\s\+\w\+.*Enum" --include="*.py" . | grep -v node_modules
grep -rn "Literal\[" --include="*.py" . | grep -v node_modules

# Go — 找 const iota 块
grep -rn "const\s\+(" --include="*.go" . | grep -v vendor
grep -rn "iota" --include="*.go" . | grep -v vendor

# 通用 — 找设计文档中定义的状态机
grep -rn "状态机\|state machine\|workflow.*state\|状态流转" --include="*.md" . | head -20
```

**Step 2：对每个枚举/状态机，统计值的实际使用率**

```bash
# 对枚举的每个成员，grep 项目看是否被赋值或匹配
# 例：假设枚举有 empty, case-ready, documents-uploaded, text-extracted, text-confirmed, opinion-analyzed
# 对每个值检查：
grep -rn '"case-ready"\|CaseStatus\.caseReady\|case_ready' --include="*.ts" --include="*.tsx" . | grep -v node_modules | grep -v "\.d\.ts"
grep -rn '"documents-uploaded"\|CaseStatus\.documentsUploaded' --include="*.ts" --include="*.tsx" . | grep -v node_modules | grep -v "\.d\.ts"
# ... 逐个检查

# 高效方法：提取枚举所有成员，批量检查
# 1. 从 enum 定义中提取所有成员名
# 2. 对每个成员名 grep 项目（排除定义文件本身）
# 3. 只出现 1 次（定义处）= 死值
```

**Step 3：检查状态推进逻辑是否完整**

```bash
# 找所有对状态字段的赋值操作
grep -rn "workflowState\s*=" --include="*.ts" --include="*.tsx" . | grep -v node_modules
grep -rn "status\s*=" --include="*.ts" --include="*.tsx" . | grep -v node_modules | grep -v "loading\|error\|success"
grep -rn "setState\|setStatus\|updateState" --include="*.ts" --include="*.tsx" . | grep -v node_modules

# 检查是否有"透传旧状态"的模式（典型反模式）
grep -rn "currentCase.*workflowState.*??.*empty\|existing.*status" --include="*.ts" --include="*.tsx" . | grep -v node_modules
```

**Step 4：检查标签映射与枚举的匹配度**

```bash
# 找 label/显示名 映射表
grep -rn "LABEL\|label.*=\|display.*name\|_LABELS\|_NAMES\|statusText\|statusLabel" --include="*.ts" --include="*.tsx" . | grep -v node_modules

# 对比映射表的 key 和枚举成员，列出不匹配项
```

**判定标准：**
- 枚举成员在项目中仅出现 1 次（仅定义处）→ **死枚举值**，P1
- 状态机设计了 N 个转换，代码只实现了 <50% → **状态机缺口**，P1
- 标签映射表的 key 与枚举成员不一致 → **标签错位**，P1（用户可见问题）
- 状态赋值处使用 `?? oldState` 透传模式 → **状态推进被跳过**，P1

##### 2.4.4 死代码专项检测（AI 辅助开发最高优先级）

**这是 AI 辅助开发最常见的问题模式：AI 写了完整的代码实现，但没有确保它被实际调用、配置被实际使用、参数被实际传递。** 这类问题的特点是：代码本身质量高、实现完整、编译通过，但运行时完全无效。

**重要：发现死代码后，必须仔细调查其存在原因，再决定处理方式（清理删除 / 集成被调用 / 移植后被调用 / 保留待定），不能一刀切删除。**

**Step 1：检测"配置驱动的功能未生效"模式**

用户在 UI 配置了选项，但代码忽略了配置，始终使用默认值。

```bash
# 找所有配置读取点（settings/config 读取）
grep -rn "settings\.\|config\.\|readSettings\|getConfig" --include="*.ts" --include="*.tsx" . | grep -v node_modules

# 对每个配置读取点，追踪配置值是否被传递给实际执行的函数
# 例：settings.knowledgeProviders 被读取，但 embedConfig 未被使用

# 找所有函数签名中以下划线开头的参数（表示"未使用"的约定）
grep -rn "function.*(_[a-zA-Z]" --include="*.ts" --include="*.tsx" . | grep -v node_modules
grep -rn "=>.*\b_[a-zA-Z]" --include="*.ts" --include="*.tsx" . | grep -v node_modules

# 找所有被赋值但从未传递的变量
# 配置读取 → 赋值给变量 → 变量从未被使用
```

**判定标准：**
- 配置值被读取并赋给变量，但该变量从未被传递给实际执行函数 → **配置未生效**，P0
- 函数参数以下划线开头（如 `_embedConfig`）但调用方仍在传递参数 → **参数被忽略**，P1
- UI 允许用户配置选项，但代码始终使用硬编码默认值 → **配置误导用户**，P0

**Step 2：检测"本地实现被绕过"模式**

有本地算法/功能实现，但调用链直接跳过了它。

```bash
# 找所有实现了"本地"逻辑的函数（本地算法、本地模型、fallback 等）
grep -rn "local\|Local\|本地\|fallback\|降级" --include="*.ts" --include="*.tsx" . | grep -v node_modules

# 对每个本地实现，检查是否被实际调用
# 例：reranker.ts 实现了本地重排序，但 search API 直接返回向量相似度结果

# 找所有"if 有远程配置则用远程，else 直接返回"的模式（缺少本地 fallback）
grep -rn "if.*baseUrl\|if.*apiKey\|if.*remote" --include="*.ts" --include="*.tsx" . | grep -v node_modules
```

**判定标准：**
- 有本地实现，但 `if (remoteConfig) { ... } else { return default; }` 跳过了本地实现 → **本地实现未接入**，P0
- 有 fallback 逻辑但 fallback 路径从未被执行（因为条件永远为真/假） → **死 fallback**，P1

**Step 3：检测"API 端点未被前端调用"模式**

后端实现了 API，但前端没有调用；或者前端调用了错误的端点。

```bash
# 找所有 API 端点定义
grep -rn "router\.\(get\|post\|put\|delete\)\|app\.\(get\|post\|put\|delete\)" --include="*.ts" --include="*.js" . | grep -v node_modules

# 找所有前端 fetch/axios 调用
grep -rn "fetch(\|axios\.\|\.get(\|\.post(" --include="*.ts" --include="*.tsx" . | grep -v node_modules

# 对比：哪些后端端点没有对应的前端调用
```

**Step 4：检测"设计文档与实现不一致"模式**

设计文档描述了功能 A/B/C，但代码只实现了 A。

```bash
# 找设计文档中描述的功能点
grep -rn "支持\|应该\|需要\|shall\|should\|must\|设计" --include="*.md" . | head -50

# 对比代码实现：设计文档说"支持本地/远程"，检查代码是否真的支持
```

**Step 5：检测"参数传递断裂"模式**

函数 A 读取配置，函数 B 执行逻辑，但 A 没有把配置传递给 B。

```bash
# 找所有函数调用，检查参数是否完整
# 例：injectKnowledge({ query, systemPrompt, config, embedConfig })
# 但 retrieve() 的第三个参数被命名为 _embedConfig（未使用）

# 找所有"读取配置 → 构建参数 → 调用函数"的链路
# 检查参数是否真的被传递和使用
```

##### 2.4.5 import 未调用专项检测

**典型场景：模块被 import 了，编译通过，但实际运行时从未被执行。** 常见于"接入了一半"、"重构后残留"、"新实现替代旧实现但 import 未清理"等情况。比"export 未被 import"更隐蔽，因为 import 语句本身存在，静态分析工具通常不会报错。

**Step 1：找出所有 import 语句**

```bash
# TypeScript/JavaScript — 找所有 import 语句
grep -rn "^import\s" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" . \
  | grep -v node_modules | grep -v "\.d\.ts" | grep -v dist

# Python — 找所有 import 语句
grep -rn "^import\s\|^from\s.*import" --include="*.py" . | grep -v node_modules | grep -v __pycache__

# Go — 找所有 import 块（需解析 import 后的实际使用）
grep -rn "^import\|^\s\"" --include="*.go" . | grep -v vendor
```

**Step 1.5：检查 import 引用的模块文件是否存在**

**这是比"import 未调用"更严重的问题：import 指向一个已被删除或从未创建的文件。** 编译器通常会报错，但在以下情况下可能被忽略：monorepo 中只检查了部分子项目、使用了 path alias 但 alias 配置错误、或 import 被 try-catch 包裹。

```bash
# 对每个 import 语句，提取目标路径，验证文件是否存在
grep -rn "from ['\"]\.\." --include="*.ts" --include="*.tsx" --include="*.js" . \
  | grep -v node_modules | grep -v "\.d\.ts" | grep -v dist \
  | while IFS=: read file line content; do
    # 提取 import 路径
    target=$(echo "$content" | sed -n "s/.*from ['\"]\(.*\)['\"].*/\1/p")
    if [ -n "$target" ] && echo "$target" | grep -q "^\."); then
      # 相对路径：基于当前文件目录解析
      dir=$(dirname "$file")
      resolved="$dir/$target"
      # 尝试多种扩展名
      found=0
      for ext in ".ts" ".tsx" ".js" ".jsx" "/index.ts" "/index.tsx" "/index.js"; do
        if [ -f "${resolved}${ext}" ]; then found=1; break; fi
      done
      if [ "$found" -eq 0 ]; then
        echo "BROKEN_IMPORT: $file:$line — $target (file not found)"
      fi
    fi
  done
```

**判定标准：**
- Import 指向不存在的文件 → **断裂的 import**，P0（编译/运行时必定失败）
- Import 指向存在但已被标记为废弃（deprecated）的模块 → **过期依赖**，P1

**Step 2：对每个 import，检查被导入的符号是否在该文件中被实际调用/使用**

```bash
# 方法：对每个 import 行提取导入的符号名，在同一文件中搜索该符号的使用（排除 import 行本身）
# 例：假设 retriever.ts 有 "import { rerank } from './reranker'"
# 则在 retriever.ts 中搜索 rerank 的使用（排除 import 行）：
grep -n "rerank" retriever.ts | grep -v "^.*import"

# 批量检测思路（伪代码）：
# 对每个源文件 F：
#   提取 F 中所有 import 的符号列表 [s1, s2, s3, ...]
#   对每个符号 si：
#     在 F 中 grep si，排除 import 行
#     如果匹配数 == 0 → si 是 import 了但从未调用的死符号
```

**Step 3：区分"真死"和"假死"**

import 了但未调用，不一定是死代码，需排除以下情况：

| 情况 | 判断方法 | 处理 |
|------|---------|------|
| **类型导入** | `import type { X }` 或仅在类型注解中使用 | 不是死代码，排除 |
| **副作用导入** | `import './polyfill'` 无具名符号 | 不是死代码，排除 |
| **re-export** | 导入后又 export 出去 | 不是死代码，排除 |
| **动态使用** | 通过反射、字符串拼接、eval 等使用 | 需人工判断，标记为"待确认" |

**判定标准：**
- 文件 A import 了符号 X，但 A 中 X 的唯一出现就是 import 行 → **import 未调用**，P1
- 该符号在其他文件中被正常调用 → 问题出在 A 的 import 多余，或 A 应该调用但忘了
- 该符号在所有文件中都只出现在 import 行 → 整个模块是死代码，P0

**典型真实案例：**
- `retriever.ts` import 了 `rerank`、`hybridSearch`，但 `retrieve()` 函数从未调用它们，实际检索流程只走纯余弦相似度
- `vectorStore.ts`、`bm25Search.ts`、`annIndex.ts` 被 import 但对应的检索增强功能从未接入实际 pipeline
- 这些属于"功能写了但接入了一半"，设计文档有记录但代码未跟上

##### 2.4.6 分析每个死 Feature 的处置

对发现的每个死 feature，判断：

1. **已有替代代码** → 标记为"死代码应清理"
   - 证据：新模块实现了相同功能，且新模块已被调用
   - backlog 条目：清理死代码，删除未使用的旧实现

2. **import 了但从未调用** → 标记为"import 未调用 / 功能未接入"
   - 证据：文件 A import 了符号 X，但 A 的执行路径中从未调用 X；X 本身实现完整
   - 判断：如果 X 在其他文件中被调用 → A 的 import 多余应清理；如果 X 在所有文件中都未被调用 → 整个模块是死代码
   - backlog 条目：接入调用链（功能漏接）或删除 import 和模块（死代码清理）

3. **功能漏接** → 标记为"feature 未接入"
   - 证据：代码逻辑完整，有 UI/命令/API 定义，但缺少调用链
   - backlog 条目：补全调用链，将 feature 接入用户可用的入口

4. **实验性/预留代码** → 标记为"未完成 feature"
   - 证据：代码有 TODO 标记，或实现明显不完整
   - backlog 条目：决定是完成还是删除

##### 2.4.7 验证手段

```bash
# 对可疑的死模块，验证其依赖链
# 从入口文件开始，trace import/require 链
# 未出现在链中的模块 = 死代码

# 检查 git log 看该文件最后一次被"使用"是什么时候
git log --oneline -5 -- <file>
# 如果最后一次改动是 "remove" / "refactor" / "cleanup"，大概率已被替代

# 检查是否有"替代者"
# 如果文件 A 和文件 B 实现了类似功能，grep 看谁被 import
```

##### 2.4.8 写入 Backlog 格式

死代码问题统一使用 `[DeadCode]` 维度标签：

```markdown
### [BUG-XXX] [DeadCode] 问题标题

**来源**: 死代码检测
**问题**: [具体描述，说明这段代码为什么没有被调用]
**处置判断**: [需调查后决定，见下方处置选项]
**证据**:
- `path/to/dead-file`: [说明为什么不被调用]
- `path/to/caller`: [如果有的话，说明替代路径或应该调用的位置]
**改动范围**:
- `path/to/file`: [具体改动描述]
**验证方式**:
1. [具体可执行的验证步骤]
2. [预期结果]
```

**处置选项**（必须仔细调查后再选择）：

| 处置方式 | 适用场景 | 调查要点 |
|---------|---------|---------|
| **清理删除** | 代码已被替代、功能已废弃、设计残留 | 确认无任何调用路径，git log 显示已被替代 |
| **集成被调用** | 代码实现完整且有价值，但调用链断裂 | 确认功能有价值，找到正确的调用位置 |
| **移植后被调用** | 代码在错误的位置（如客户端逻辑应在服务端） | 确认架构设计意图，找到正确的位置 |
| **保留待定** | 预留设计或实验性功能 | 确认有明确的未来使用计划 |

枚举/状态机缺口的 backlog 示例：

```markdown
### [BUG-XXX] [DeadCode] 状态机仅实现 3/19 个状态，前半程用户无反馈

**来源**: 枚举/状态机缺口检测
**问题**: CaseWorkflowState 定义了 19 个状态，但代码只在 3 处写入（empty、opinion-analyzed、argument-mapped）。中间的 case-ready、documents-uploaded、text-extracted、text-confirmed 从未被赋值，用户上传文件后状态仍显示 "empty"。
**处置判断**: 功能漏接 — 设计完整但实现残缺
**证据**:
- `shared/src/types/domain.ts`: CaseWorkflowState 定义了 19 个状态成员
- `NewCasePage.tsx:24`: 创建案件时写入 "empty"
- `router.tsx:354,543`: 意见分析完成时写入 "opinion-analyzed"
- `CaseSetupPage.tsx`: 上传文件时透传旧状态 `workflowState: (currentCase?.workflowState ?? "empty")`
- `CaseHistoryPanel.tsx:197-204`: WORKFLOW_LABELS 的 6 个 key 中只有 empty 匹配枚举，其余 5 个 key 根本不在枚举中
**改动范围**:
- `CaseSetupPage.tsx`: 文档上传成功后推进到 documents-uploaded
- `CaseBaselineForm.tsx`: 文本提取完成后推进到 text-extracted
- `CaseHistoryPanel.tsx`: 修正 WORKFLOW_LABELS，key 与 CaseWorkflowState 枚举完全对应
**验证方式**:
1. 创建新案件，上传文档后检查状态是否从 empty 变为 documents-uploaded
2. 确认 CaseHistoryPanel 显示中文标签而非原始字符串
```

import 未调用的 backlog 示例：

```markdown
### [BUG-XXX] [DeadCode] re-ranker / hybridSearch 被 import 但从未调用，检索增强功能全部未接入

**来源**: import 未调用检测
**问题**: retriever.ts import 了 rerank、hybridSearch，但 retrieve() 函数从未调用它们。实际检索流程只走纯语义余弦相似度，reranker 的多信号加权排序（语义 0.4 + 关键词 0.25 + 类别 0.15 + 法条引用 0.15 + 深度 0.05）对用户完全不可用。同样的情况还有 bm25Search.ts、annIndex.ts、vectorStore.ts——都 import 了但整个检索增强 pipeline 从未接入。
**处置判断**: 功能漏接 — 模块实现完整，import 存在，但调用链断裂
**证据**:
- `client/src/lib/knowledge/retriever.ts:9`: `import { rerank } from './reranker'`，但 retrieve() 内部从未调用 rerank()
- `client/src/lib/knowledge/retriever.ts`: 同样 import 了 hybridSearch 但未使用
- `client/src/lib/knowledge/reranker.ts`: rerank() 实现完整，5 个信号加权，但零调用
- `client/src/lib/knowledge/bm25Search.ts`: BM25 关键词检索实现完整，但零调用
- `server/src/routes/knowledge.ts`: 实际检索只用余弦相似度（阈值 0.3），无 re-rank 步骤
**改动范围**:
- `client/src/lib/knowledge/retriever.ts`: 在 retrieve() 返回前调用 rerank() 对结果重排序
- 或 `server/src/routes/knowledge.ts`: 在 server 端接入 hybridSearch / rerank
**验证方式**:
1. 在 retrieve() 中添加 rerank() 调用后，检索同一 query 对比 top-K 结果顺序变化
2. 确认 rerank 的权重配置通过 RerankConfig 可调
```

死代码的 backlog 示例（配置未生效 + 本地实现被绕过）：

```markdown
### [BUG-XXX] [DeadCode] RAG 系统 Embedding/Re-ranker 调用逻辑存在设计缺口

**来源**: 死代码检测
**问题**: 以下表格总结了四种情况的实际状态：

| 功能 | 设计意图 | 实际状态 | 需要修复 |
|------|---------|---------|---------|
| Embedding（上传时） | 支持本地/远程 | 只用本地模型 | 是（如需支持远程） |
| Embedding（检索时） | 支持本地/远程 | 只用本地模型 | 是（如需支持远程） |
| Re-ranker（有远程 API） | 调用远程 API | ✅ 正常工作 | 否 |
| Re-ranker（无远程 API） | 使用本地算法 | ❌ 跳过 | 是（Bug） |

**处置判断**: 需调查后决定 — 涉及多个死代码模块，处理方式不同

**证据**:
- 配置未生效：`AgentClient.ts:157-165` 读取 embedding provider 配置，但 `retriever.ts:79` 的 `_embedConfig` 参数未使用
- 本地实现被绕过：`reranker.ts:46-93` 实现了本地重排序，但 `knowledge.ts:665` 直接跳过
- 死代码：`hybridSearch.ts`、`embedder.ts` 远程部分从未被调用

**各模块处置分析**:
- `reranker.ts`（本地重排序）：**集成被调用** — 实现完整，应接入检索流程
- `hybridSearch.ts`（混合检索）：**移植后被调用** — 客户端逻辑应移植到服务端
- `embedder.ts` 远程部分：**需确认** — 如果支持远程 embedding 则集成，否则清理

**改动范围**:
- `server/src/routes/knowledge.ts`: 如果无远程 reranker 配置，使用本地 reranker 逻辑
- `server/src/routes/knowledge.ts`: 如果配置了远程 embedding，使用远程 API
- 或删除 UI 中的 embedding provider 配置（如果不打算支持远程）

**验证方式**:
1. 未配置远程 reranker 时，确认检索结果经过本地重排序
2. 配置远程 embedding 后，确认上传/检索使用远程 API
```

---

#### 2.5 测试框架自身审查

**测试代码本身也是代码，也会有 bug。** 如果测试框架有问题，所有测试结果都不可信。很多人只检查"测试覆盖了什么"，不检查"测试本身是否正确"。

**Step 1：找到所有测试基础设施文件**

```bash
# 测试基础设施 = 不是具体测试用例，而是测试的"脚手架"
find . -type f \( -name "setup.*" -o -name "globalSetup.*" -o -name "teardown.*" \
  -o -name "*fixture*" -o -name "*mock*" -o -name "*helper*" \
  -o -name "*test-utils*" -o -name "*test-helpers*" \) \
  \( -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" -o -name "*.mjs" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"

# 测试配置文件
find . -type f \( -name "vitest*config*" -o -name "jest.config*" -o -name ".mocharc*" \
  -o -name "pytest.ini" -o -name "conftest.py" -o -name "setup.cfg" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"

# 评估/基准测试框架（AI 项目常见）
find . -type f -path "*/evaluation/*" \( -name "*.ts" -o -name "*.js" -o -name "*.py" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"

# E2E / Smoke 测试
find . -type f \( -name "*e2e*" -o -name "*smoke*" -o -name "*playwright*" -o -name "*cypress*" \) \
  \( -name "*.ts" -o -name "*.js" -o -name "*.mjs" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"
```

**Step 2：对每个测试基础设施文件，执行与源码相同的审查**

测试基础设施文件必须与源码同等对待：
- 同样检查空值防护、错误处理、资源泄漏
- 同样检查死代码（未被任何测试用例调用的 helper 函数）
- 同样检查 import 未调用

**Step 3：检查测试可信度**

| 检查项 | 方法 | 风险 |
|--------|------|------|
| **Mock 过度** | grep mock/stub/fake 的使用，检查是否 mock 了被测系统的核心逻辑 | 测试通过但实际功能 broken |
| **测试数据过期** | 检查 fixture 文件的最后修改时间 vs 源码最后修改时间 | fixture 数据不再匹配当前 schema |
| **测试跳过/禁用** | grep `skip`/`xit`/`xdescribe`/`pending`/`@disabled`/`test.skip` | 跳过的测试可能掩盖真实问题 |
| **断言缺失** | 检查测试中是否有 `expect`/`assert`/`should` 调用 | 没有断言的测试永远通过 |
| **测试隔离性** | 检查测试之间是否共享可变状态（全局变量、共享 DB、环境变量） | 测试顺序影响结果 |
| **快照测试腐化** | 如果有 snapshot 测试，检查 snapshot 文件是否被盲目更新 | snapshot 更新掩盖了回归 |

**Step 4：检查测试配置的合理性**

```bash
# 检查测试超时配置是否合理
grep -rn "timeout\|testTimeout\|hookTimeout" --include="*.ts" --include="*.js" --include="*.json" . \
  | grep -v node_modules | grep -i "config\|vitest\|jest"

# 检查覆盖率阈值配置
grep -rn "coverage\|threshold" --include="*.ts" --include="*.js" --include="*.json" . \
  | grep -v node_modules | grep -i "config\|vitest\|jest"

# 检查测试环境配置（是否与生产环境一致）
grep -rn "testEnvironment\|environment\|env" --include="*config*" . \
  | grep -v node_modules | grep -i "test\|vitest\|jest"
```

**判定标准：**
- Mock 了被测系统的核心逻辑 → **测试不可信**，P0
- 测试 fixture 数据与当前 schema 不匹配 → **测试数据过期**，P1
- 存在大量 skip/disabled 测试且无注释说明 → **隐藏的测试债务**，P1
- 测试没有断言 → **假测试**，P0
- 测试之间共享可变状态且无清理 → **测试隔离性差**，P1

---

#### 2.6 AI Prompt 模板审计

**AI 项目特有的风险维度。** Prompt 模板是"代码"——它们控制 AI 的行为，但传统静态分析工具完全忽略它们。

**Step 1：找到所有 prompt 模板**

```bash
# 方法 1：按文件名模式
find . -type f \( -name "*prompt*" -o -name "*template*" -o -name "*system*" \) \
  \( -name "*.md" -o -name "*.txt" -o -name "*.j2" -o -name "*.hbs" -o -name "*.mustache" \
  -o -name "*.ts" -o -name "*.js" -o -name "*.py" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"

# 方法 2：按内容模式（prompt 中常见的标记）
grep -rn "system.*prompt\|SYSTEM_PROMPT\|systemPrompt\|You are\|你的角色\|你是" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.md" . \
  | grep -v node_modules | grep -v "\.test\." | grep -v "\.spec\."

# 方法 3：按目录模式
find . -type d \( -name "prompts" -o -name "templates" -o -name "system" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"
```

**Step 2：对每个 prompt 模板，检查以下问题**

| 检查项 | 方法 | 风险 |
|--------|------|------|
| **变量未替换** | 检查模板中的 `{{var}}`、`{var}`、`${var}`、`%s` 占位符，确认调用方是否全部替换 | 用户看到原始占位符 |
| **Prompt 注入风险** | 检查 prompt 是否包含用户可控输入（如文件名、用户消息、搜索 query），且未做转义/隔离 | 恶意输入覆盖系统指令 |
| **与 Schema 不匹配** | prompt 要求 AI 输出 JSON，但 schema 定义的字段名/类型与 prompt 不一致 | AI 输出被 schema 拒绝，解析失败 |
| **指令矛盾** | 同一个调用链中多个 prompt 的指令相互矛盾（如一个说"简洁"另一个说"详细"） | AI 行为不稳定 |
| **硬编码的模型特定指令** | prompt 中包含特定模型的指令（如"GPT-4"、"Claude"），但项目支持多模型 | 切换模型后行为异常 |
| **Prompt 版本漂移** | prompt 文件有多份副本（如 `prompts/v1/` 和 `prompts/v2/`），只有一份被使用 | 旧版本 prompt 是死代码 |

**Step 3：检查 prompt 与代码的调用链**

```bash
# 对每个 prompt 模板文件，grep 项目找到谁在使用它
# 例：prompt 文件名为 opinion-analysis.md
grep -rn "opinion-analysis\|opinionAnalysis" --include="*.ts" --include="*.tsx" --include="*.js" . \
  | grep -v node_modules | grep -v "\.test\."

# 如果 prompt 内嵌在代码中（字符串常量），检查变量是否被正确传递
grep -rn "systemPrompt\|prompt.*=" --include="*.ts" --include="*.tsx" . \
  | grep -v node_modules | grep -v "\.test\." | head -30
```

**判定标准：**
- Prompt 中有未替换的占位符 → **变量未替换**，P0
- Prompt 直接拼接用户输入而无隔离 → **Prompt 注入**，P0（安全问题）
- Prompt 要求的输出格式与 Zod schema 不一致 → **Schema 不匹配**，P0
- Prompt 文件存在但项目中无任何代码引用 → **死 Prompt**，P2
- 多个 prompt 指令矛盾 → **指令冲突**，P1

---

#### 2.7 Schema-Handler 对齐检查

**Schema 定义了"什么数据是合法的"，但如果 handler 不校验，schema 形同虚设。** 这是 API 项目最常见的安全漏洞之一。

**Step 1：找到所有 schema 定义**

```bash
# Zod schema（TypeScript）
grep -rn "z\.object\|z\.string\|z\.number\|z\.array\|z\.enum" --include="*.ts" --include="*.tsx" . \
  | grep -v node_modules | grep -v "\.test\." | grep -v "\.d\.ts" | head -30

# JSON Schema
find . -type f -name "*schema*" -name "*.json" ! -path "*/node_modules/*" ! -path "*/.git/*"

# Joi / Yup / class-validator（其他验证库）
grep -rn "Joi\.\|yup\.\|@IsString\|@IsNumber\|@ValidateNested" --include="*.ts" --include="*.js" . \
  | grep -v node_modules | head -20

# Pydantic（Python）
grep -rn "BaseModel\|Field(" --include="*.py" . | grep -v node_modules | head -20
```

**Step 2：对每个 schema，检查对应的 handler 是否真正校验**

```bash
# 找到所有 API 路由/endpoint 定义
grep -rn "router\.\(get\|post\|put\|delete\)\|app\.\(get\|post\|put\|delete\)\|@app\.\(get\|post\|put\|delete\)" \
  --include="*.ts" --include="*.js" --include="*.py" . | grep -v node_modules

# 对每个路由，检查是否调用了 schema 的 parse/validate 方法
# 应该看到类似：schema.parse(req.body) 或 schema.safeParse(req.body)
# 如果直接访问 req.body 而没有 parse → 未校验
grep -rn "req\.body\|req\.query\|req\.params\|request\.json\|request\.body" \
  --include="*.ts" --include="*.js" --include="*.py" . | grep -v node_modules | head -30
```

**Step 3：检查 schema 与实际数据流的对齐**

| 检查项 | 方法 | 风险 |
|--------|------|------|
| **Schema 定义了但 handler 未校验** | 对比 schema 文件和 handler 文件，检查 handler 是否调用 parse/validate | 非法数据直接进入业务逻辑 |
| **Handler 校验了但 schema 未定义** | handler 中有手动 if 判断但没有对应的 schema | 校验逻辑分散，容易遗漏 |
| **Schema 字段与数据库不一致** | schema 有字段 A 但数据库表没有列 A（或反过来） | 写入/读取时数据丢失 |
| **Schema 更新后 handler 未同步** | git log 中 schema 文件有更新但 handler 文件没有 | 校验规则与实际处理不一致 |

**判定标准：**
- API handler 直接使用 `req.body` 而无 schema 校验 → **未校验输入**，P0（安全问题）
- Schema 定义了可选字段但 handler 假设必有 → **运行时崩溃**，P1
- Schema 与数据库表结构不一致 → **数据不一致**，P1
- Schema 更新后对应 handler 未同步 → **校验漂移**，P1

---

#### 2.8 Shell 脚本与工具脚本安全审计

**Shell 脚本和工具脚本通常不受 linter 约束，是最容易被忽视的 bug 温床。**

```bash
# 找到所有 shell 脚本
find . -type f \( -name "*.sh" -o -name "*.bash" -o -name "*.zsh" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"

# 找到所有工具脚本（scripts/ 目录或类似）
find . -type d -name "scripts" ! -path "*/node_modules/*" ! -path "*/.git/*"
find . -path "*/scripts/*" \( -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.sh" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"
```

**对每个脚本检查：**

| 检查项 | 方法 | 风险 |
|--------|------|------|
| **Shell 注入** | 检查是否有未引号保护的变量拼接（`$VAR` 而非 `"$VAR"`） | 文件名含空格/特殊字符时执行任意命令 |
| **路径拼接错误** | 检查是否有字符串拼接路径而非 `path.join`/`os.path.join` | 跨平台兼容性、路径遍历 |
| **未检查退出码** | 检查关键命令后是否有 `|| exit`/`set -e` | 命令失败但脚本继续执行 |
| **硬编码路径** | 检查是否有 `/Users/xxx`、`/home/xxx`、`C:\xxx` | 其他环境无法运行 |
| **临时文件竞争** | 检查是否使用 `/tmp/xxx` 固定文件名而非 `mktemp` | 并发执行时数据损坏 |
| **依赖未检查** | 检查是否在使用外部工具前检查其是否存在 | 工具不存在时报不友好的错误 |

**判定标准：**
- Shell 变量未引号保护 → **Shell 注入**，P0
- 关键命令未检查退出码 → **静默失败**，P1
- 硬编码绝对路径 → **可移植性差**，P2
- 使用固定 /tmp 文件名 → **竞争条件**，P1

---

#### 2.9 配置文件安全审计

```bash
# 检查是否有敏感信息泄露在版本控制中
# .env 文件是否在 .gitignore 中
if [ -f ".env" ]; then
  if ! grep -q "\.env" .gitignore 2>/dev/null; then
    echo "WARNING: .env 文件存在但未被 .gitignore 忽略"
  fi
fi

# 检查是否有硬编码的 API key / secret
grep -rn "api[_-]key\|secret\|password\|token\|credential" \
  --include="*.ts" --include="*.js" --include="*.json" --include="*.yaml" --include="*.yml" . \
  | grep -v node_modules | grep -v "\.test\." | grep -v "\.env\." | grep -v "example" \
  | grep -v "process\.env\." | grep -v "import\.meta\.env\." \
  | grep -iE "[=:].*[a-zA-Z0-9]{20,}" | head -20

# 检查构建配置是否有安全问题
# CSP 是否配置、HTTPS 是否强制、CORS 是否过于宽松
grep -rn "cors\|CORS\|Content-Security-Policy\|helmet" \
  --include="*.ts" --include="*.js" . | grep -v node_modules | head -10

# 检查 TypeScript 严格模式是否开启
grep -rn "strict" tsconfig*.json 2>/dev/null
```

**判定标准：**
- .env 文件被提交到 git → **敏感信息泄露**，P0
- 代码中有硬编码的 API key → **密钥泄露**，P0
- CORS 配置为 `*`（允许所有来源）→ **安全风险**，P0
- TypeScript strict 模式未开启 → **类型安全缺失**，P2

---

### 3. 测试覆盖分析

#### 3.1 检测测试框架和测试文件

```bash
# 查找测试文件
find . -type f \( -name "*.test.*" -o -name "*.spec.*" -o -name "*_test.*" -o -name "test_*" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" | head -50

# 检测测试框架
cat package.json | grep -E "jest|mocha|vitest|pytest|go test"
```

#### 3.2 运行测试并收集覆盖率

```bash
# JavaScript/TypeScript（根据 package.json 中的 scripts）
npm test -- --coverage 2>&1 | tail -30

# Python
pytest --cov=. --cov-report=term-missing 2>&1 | tail -30

# Go
go test -cover ./... 2>&1 | tail -30
```

#### 3.3 分析测试盲区

对比源代码文件和测试文件，找出：

- **无测试的模块**：有 `src/foo.js` 但没有 `src/foo.test.js`
- **无测试的函数**：export 的函数但测试中没有调用
- **边界条件未测试**：空输入、超长输入、特殊字符、null/undefined
- **错误处理未测试**：catch 块、错误回调、异常路径

#### 3.4 测试数据与 Fixture 新鲜度

**Fixture 数据过期是"测试通过但实际功能 broken"的常见原因。** Schema 更新了但 fixture JSON 没更新，测试仍然通过（因为旧 fixture 符合旧 schema），但运行时新数据会崩溃。

```bash
# 找到所有 fixture/测试数据文件
find . -type f \( -name "*fixture*" -o -name "*mock-data*" -o -name "*test-data*" \
  -o -name "*sample*" -o -name "*example*" \) \
  \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.csv" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*"

# 对比 fixture 文件和对应 schema 文件的最后修改时间
# 如果 schema 比 fixture 新 → fixture 可能已过期
find . -type f -name "*schema*" \( -name "*.ts" -o -name "*.js" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" \
  -exec sh -c 'echo "SCHEMA: $(stat -f "%Sm" -t "%Y-%m-%d" "$1") $1"' _ {} \;
find . -type f -name "*fixture*" -name "*.json" \
  ! -path "*/node_modules/*" ! -path "*/.git/*" \
  -exec sh -c 'echo "FIXTURE: $(stat -f "%Sm" -t "%Y-%m-%d" "$1") $1"' _ {} \;

# 检查 fixture 文件是否被测试实际使用
# 找到所有引用 fixture 的测试文件
grep -rn "fixture\|loadFixture\|testData\|mockData" --include="*.test.*" --include="*.spec.*" . \
  | grep -v node_modules | head -20
```

**判定标准：**
- Schema 最后修改时间晚于 fixture → **fixture 可能过期**，需人工确认
- Fixture 文件存在但无任何测试引用 → **死 fixture**，P2
- Fixture 数据结构与当前 schema 不匹配 → **fixture 过期**，P1

---

### 4. 动态运行检查

#### 4.1 检测项目启动方式

```bash
# 检测启动命令
cat package.json | grep -A5 '"scripts"'
cat Makefile | grep -E "^[a-z]+:" | head -10
```

#### 4.2 尝试启动项目

```bash
# 安装依赖（如需要）
npm install 2>&1 | tail -5

# 启动项目（后台运行，收集日志）
npm start > /tmp/bug-scan-startup.log 2>&1 &
STARTUP_PID=$!
sleep 5

# 检查启动是否成功
if kill -0 $STARTUP_PID 2>/dev/null; then
  echo "项目启动成功"
  # 检查日志中的 warning/error
  grep -iE "warn|error|exception|fail" /tmp/bug-scan-startup.log | head -20
else
  echo "项目启动失败"
  cat /tmp/bug-scan-startup.log | tail -30
fi

# 清理
kill $STARTUP_PID 2>/dev/null
```

#### 4.3 运行核心功能（如项目可运行）

根据项目类型，尝试运行核心功能并观察是否有运行时错误：
- Web 应用：访问关键页面，检查控制台错误
- CLI 工具：运行核心命令，检查输出
- API 服务：发送测试请求，检查响应

#### 4.4 检查日志和错误输出

```bash
# 检查是否有日志文件
find . -name "*.log" -type f | head -10

# 检查日志中的错误模式
grep -rn "ERROR\|FATAL\|PANIC\|Exception\|Traceback" --include="*.log" . | head -20
```

---

### 5. 综合分析与问题归类

将所有发现归类为以下维度：

| 维度 | 标签 | 说明 | 来源章节 |
|------|------|------|---------|
| Bug | `[Bug]` | 已确认或高概率的 bug | §1, §4 |
| 测试盲区 | `[TestGap]` | 测试覆盖不足的区域 | §3 |
| 测试可信度 | `[TestTrust]` | 测试框架本身的问题导致测试结果不可信 | §2.5 |
| 代码异味 | `[CodeSmell]` | 可能导致未来 bug 的代码模式 | §2.3 |
| 高风险 | `[Risk]` | 基于 commit 历史的高风险区域 | §1 |
| 死代码 | `[DeadCode]` | 代码存在但从未被调用或已被替代（包括 AI 写了但未集成的代码） | §2.4 |
| Prompt 问题 | `[Prompt]` | AI prompt 模板的注入、矛盾、不匹配问题 | §2.6 |
| Schema 断裂 | `[SchemaGap]` | Schema 定义与 handler/数据库/前端不一致 | §2.7 |
| 脚本安全 | `[ScriptSecurity]` | Shell/工具脚本的注入和可靠性问题 | §2.8 |
| 配置安全 | `[ConfigSecurity]` | 配置文件中的敏感信息泄露或错误配置 | §2.9 |
| 断裂的 Import | `[BrokenImport]` | Import 指向不存在的文件或已删除的模块 | §2.4.5 |

#### 优先级定义

| 优先级 | 含义 | 判断标准 |
|--------|------|----------|
| **P0** | 关键 | 影响核心功能可用性、存在安全漏洞、会导致数据丢失 |
| **P1** | 重要 | 显著影响用户体验、有明确的性能瓶颈、影响开发效率 |
| **P2** | 有益 | 提升使用愉悦感、减少重复操作、增强功能完整性 |
| **P3** | 可选 | 长期架构优化、边缘场景完善、未来扩展预留 |

---

### 6. 写入 Backlog

#### 6.1 读取现有 backlog

```bash
# 查找现有 backlog 文件
if [ -f "backlog.md" ]; then
  BACKLOG_FILE="backlog.md"
elif [ -f "BACKLOG.md" ]; then
  BACKLOG_FILE="BACKLOG.md"
elif [ -f "TODO.md" ]; then
  BACKLOG_FILE="TODO.md"
else
  BACKLOG_FILE="backlog.md"
fi
```

#### 6.2 检查重复

读取现有 backlog 内容，检查是否有类似条目：
- 如果已有相同问题的条目 → 合并到现有条目
- 如果是新问题 → 追加新条目

#### 6.3 写入格式

每个 backlog 条目使用以下格式：

```markdown
### [BUG-XXX] [维度] 问题标题

**来源**: commit 历史分析 / 静态检查 / 测试覆盖 / 动态运行
**问题**: [具体描述，从用户/开发者视角]
**风险模式**: [如果是 commit 历史分析发现的，列出相关 commit hash 和模式]
**改动范围**:
- `path/to/file`: [具体改动描述]
**验证方式**:
1. [具体可执行的验证步骤]
2. [预期结果]
```

#### 6.4 写入规则

- 按优先级顺序追加：P0 → P1 → P2 → P3
- 每个问题作为独立条目
- 状态标记为 `[ ]`（未完成）
- 编号连续：BUG-001, BUG-002, ...

---

### 7. 输出报告

```
✅ Bug 扫描完成 — 项目：[项目名]

📊 扫描摘要：
- Commit 历史分析：发现 N 个 bug 模式，M 个高风险文件
- 静态检查：X errors, Y warnings（含子项目逐一检查）
- 死代码检测：D 个死代码模块 / F 个未接入功能
- 断裂的 Import：B 个引用了不存在的文件
- 测试覆盖：Z% 覆盖率，K 个盲区
- 测试可信度：T 个测试框架问题（mock 过度/fixture 过期/断言缺失）
- AI Prompt 审计：P 个 prompt 问题（注入/矛盾/不匹配）
- Schema 对齐：S 个 schema-handler 断裂
- 脚本安全：C 个 shell/工具脚本问题
- 配置安全：G 个配置问题（泄露/错误配置）
- 代码模式：E 个空 catch 块，L 个 console.log 残留
- 动态运行：R 个运行时问题

🔍 Bug 模式清单：
1. [PATTERN-1] 空值/undefined 未检查 — 出现 5 次
2. [PATTERN-2] 数组越界/空数组 — 出现 3 次
3. ...
N. [DEAD-CODE] 死代码 — D 处（需调查后决定处理方式）

📝 写入 backlog.md — 共 Q 条新 feature：
- P0: A 条（关键）
- P1: B 条（重要）
- P2: C 条（有益）
- P3: D 条（可选）

Feature ID 列表：[BUG-001, BUG-002, ..., BUG-XXX]
```

---

### 8. 注意事项

- **这是通用 skill**，适用于任何项目，不假设特定技术栈。条件化检查：如果项目有 X 则检查 Y，没有则跳过
- **不主动修复代码**，只做分析和建议，修复由 dev-iterate 或用户手动完成
- **尊重项目既有架构**，建议应与现有技术栈和设计风格一致
- **测试数据在项目内**，不需要外部测试数据
- **动态运行检查是可选的**，如果项目无法启动（如缺少依赖），跳过此步骤并在报告中说明
- **Commit 历史分析是核心差异化**，务必深入分析，不要浅尝辄止
- **每个 backlog 条目必须有具体的文件引用和改动范围**，不能泛泛而谈
- **扫描结果必须写入 backlog** — 每个模式扫描完后，如果发现了问题，必须生成对应的 backlog 条目。不能只计数不记录
- **Monorepo 必须逐子项目检查** — 根项目的静态检查不覆盖子项目，每个有独立 tsconfig/pyproject/go.mod 的子项目都要单独检查
- **Import 完整性是必检项** — 不仅检查"import 未调用"，还要检查"import 引用的文件是否存在"
- **死代码处理不能一刀切** — 发现死代码后，必须仔细调查其存在原因，再决定处理方式：
  - **清理删除**：代码已被替代、功能已废弃、或从未完成的设计残留
  - **集成被调用**：代码实现完整且有价值，但调用链断裂（如 AI 写了但没接入）
  - **移植后被调用**：代码在错误的位置（如客户端逻辑应在服务端），需要移植到正确位置再接入
  - **保留待定**：代码是预留设计或实验性功能，暂时保留但标记为待决定
- **AI 项目的扫描范围 > 传统项目** — prompt 模板、schema-handler 对齐、测试框架自身都是必须扫描的资产，不能只扫源码
