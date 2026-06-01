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

#### 0.2 代码结构扫描

```bash
# 文件结构概览
find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \
  -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.vue" -o -name "*.svelte" \
  -o -name "*.html" -o -name "*.css" -o -name "*.scss" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" ! -path "*/build/*" \
  | head -80
```

重点关注：入口文件、核心模块、API/路由、配置文件、测试文件。

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

#### 2.3 代码模式扫描

扫描以下代码模式（这些模式容易产生 bug）：

```bash
# TODO/FIXME/HACK/XXX 注释
grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.{js,ts,jsx,tsx,py,go,rs}" . | grep -v node_modules

# 空 catch 块
grep -rn "catch.*{" --include="*.{js,ts,jsx,tsx}" . | grep -v node_modules | head -20

# 硬编码的魔法数字
grep -rn "[^a-zA-Z_][0-9]\{3,\}[^a-zA-Z_]" --include="*.{js,ts,jsx,tsx,py}" . | grep -v node_modules | head -20

# console.log 遗留（生产代码不应有）
grep -rn "console\.log\|console\.error\|console\.warn" --include="*.{js,ts,jsx,tsx}" . | grep -v node_modules | grep -v test

# 未使用的变量（ESLint 规则 no-unused-vars）
# 已在静态检查工具中覆盖
```

#### 2.4 死 Feature / 死代码检测

**找出"写了但没人用"的 feature：代码实现了功能，但从未被调用、未接入入口、或已被替代代码绕过，对用户零价值。**

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

##### 2.4.4 import 未调用专项检测

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

##### 2.4.5 分析每个死 Feature 的处置

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

##### 2.4.6 验证手段

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

##### 2.4.7 写入 Backlog 格式

死 feature 问题统一使用 `[DeadCode]` 维度标签：

```markdown
### [BUG-XXX] [DeadCode] 问题标题

**来源**: 死 Feature 检测
**问题**: [具体描述，说明这个 feature 为什么对用户零价值]
**处置判断**: 已有替代 / 功能漏接 / 未完成 feature
**证据**:
- `path/to/dead-file`: [说明为什么不被调用]
- `path/to/caller`: [如果有的话，说明替代路径]
**改动范围**:
- `path/to/file`: [具体改动描述：删除 / 接入入口 / 补全实现]
**验证方式**:
1. [具体可执行的验证步骤]
2. [预期结果]
```

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
- **测试数据检查**：测试数据是否在项目内，是否完整

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

| 维度 | 标签 | 说明 |
|------|------|------|
| Bug | `[Bug]` | 已确认或高概率的 bug |
| 测试盲区 | `[TestGap]` | 测试覆盖不足的区域 |
| 代码异味 | `[CodeSmell]` | 可能导致未来 bug 的代码模式 |
| 高风险 | `[Risk]` | 基于 commit 历史的高风险区域 |

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
- 静态检查：X errors, Y warnings
- 死 Feature 检测：D 个死代码/F 个未接入 feature
- 测试覆盖：Z% 覆盖率，K 个盲区
- 动态运行：P 个运行时问题

🔍 Bug 模式清单：
1. [PATTERN-1] 空值/undefined 未检查 — 出现 5 次
2. [PATTERN-2] 数组越界/空数组 — 出现 3 次
3. ...
N. [DEAD-FEATURE] 死代码/未接入 feature — D 处（应清理 / 应接入）

📝 写入 backlog.md — 共 Q 条新 feature：
- P0: A 条（关键）
- P1: B 条（重要）
- P2: C 条（有益）
- P3: D 条（可选）

Feature ID 列表：[BUG-001, BUG-002, ..., BUG-XXX]
```

---

### 8. 注意事项

- **这是通用 skill**，适用于任何项目，不假设特定技术栈
- **不主动修复代码**，只做分析和建议，修复由 dev-iterate 或用户手动完成
- **尊重项目既有架构**，建议应与现有技术栈和设计风格一致
- **测试数据在项目内**，不需要外部测试数据
- **动态运行检查是可选的**，如果项目无法启动（如缺少依赖），跳过此步骤并在报告中说明
- **Commit 历史分析是核心差异化**，务必深入分析，不要浅尝辄止
- **每个 backlog 条目必须有具体的文件引用和改动范围**，不能泛泛而谈
