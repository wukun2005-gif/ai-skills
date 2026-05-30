---
name: bug-scan
description: >
  全项目 bug 自查：结合 commit 历史分析 bug-fix 共性模式，静态检查 + 动态运行检查，
  找出测试覆盖盲区，将所有问题写入 backlog.md 并返回 feature ID 列表。
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
- 测试覆盖：Z% 覆盖率，K 个盲区
- 动态运行：P 个运行时问题

🔍 Bug 模式清单：
1. [PATTERN-1] 空值/undefined 未检查 — 出现 5 次
2. [PATTERN-2] 数组越界/空数组 — 出现 3 次
3. ...

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
