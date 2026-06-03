---
name: fix-loop
description: >
  自动化 bug 修复循环：运行 /bug-scan 扫描全项目 bug 并写入 backlog，然后运行 /dev-iterate 逐个修复，
  修复完成后再扫描，直到没有任何 bug 被发现为止。每次循环称为一个"轮次"(round)。
when_to_use: 用户说"fix-loop"、"修复循环"、"自动修bug"、"扫描修复"、"bug修复循环"、"全自动修"、"scan and fix"
---

## 自动化 Bug 修复循环

> **核心理念：扫描 → 修复 → 再扫描 → 再修复，直到项目干净。每次轮次都从零扫描，不依赖上一轮的记忆。**

---

### 0. 参数解析

从用户指令中提取以下信息（若不明确，使用默认值）：

- **最大轮次**：可选，默认无限循环直到没有新发现的 bug 为止。用户可指定如 "最多 3 轮"、"5 rounds"。
- **起始阶段**：可选 "scan"（从 bug-scan 开始，默认）或 "fix"（从 dev-iterate 开始，用于上一轮扫描中断后恢复）。
- **Feature 范围透传**：可选，透传给 dev-iterate。如 "只修 P0"、"修 BUG-001 到 BUG-005"。不指定则修复所有发现的 bug。

---

### 1. 循环主流程

```
round = 1
total_bugs_fixed = 0

while round <= max_rounds:
    ┌─────────────────────────────────────────────┐
    │  Task A: /bug-scan                           │
    │  扫描全项目，将 bug 写入 backlog.md           │
    │  输出：新发现的 bug ID 列表                   │
    └─────────────────────────────────────────────┘
                    │
                    ▼
         新发现 bug 数 == 0 ?
            │              │
           YES             NO
            │              │
            ▼              ▼
         结束循环    ┌─────────────────────────────────────┐
                    │  Task B: /dev-iterate                │
                    │  修复本轮发现的所有 bug               │
                    │  输入：本轮 bug ID 列表              │
                    └─────────────────────────────────────┘
                                │
                                ▼
                        total_bugs_fixed += 本轮修复数
                        round += 1
                        回到 Task A
```

> **⚠ 关键原则：每轮修复后必须重新扫描，不能仅凭 backlog 清空就判定完成 — 修复本身可能引入新 bug。只有下一轮 bug-scan 确认无新发现，循环才能结束。**

---

### 2. Task A：Bug 扫描（调用 /bug-scan）

#### 2.1 执行扫描

**以全新上下文调用 /bug-scan skill**，不传递任何上一轮的上下文。bug-scan 会：

1. 从零阅读项目文档和代码
2. 分析 commit 历史提取 bug 模式
3. 执行静态检查、死代码检测、动态运行检查
4. 将所有发现写入 `backlog.md`，编号格式为 `BUG-XXX`

#### 2.2 提取本轮 Bug ID 列表

bug-scan 完成后，从其输出报告中提取 **本轮新写入** 的 bug ID 列表：

```
Feature ID 列表：[BUG-001, BUG-002, ..., BUG-XXX]
```

**关键：不仅取本轮新写入的 ID，也要处理 backlog 中其他的还没有fix的旧 bug。**

判断方法：
1. bug-scan 执行前，记录 backlog.md 中已有的 `BUG-XXX` 编号最大值（如 `prev_max = BUG-015`）
2. bug-scan 执行后，扫描 backlog.md 中所有 `BUG-XXX` 编号
3. 编号 > prev_max 的即为本轮新发现的 bug

```bash
# 扫描前：记录已有最大编号
grep -oP 'BUG-\d+' backlog.md | sort -t'-' -k2 -n | tail -1

# 扫描后：提取新编号
grep -oP 'BUG-\d+' backlog.md | sort -t'-' -k2 -n | awk -F'-' -v max="$prev_max" '$2 > max'
```

#### 2.3 无 Bug → 结束

如果本轮 bug-scan 未发现任何新 bug，而且backlog.md 中也没有未修复的 bug：

```
✅ Fix-Loop 完成 — 项目已干净

📊 循环摘要：
- 总轮次：N 轮
- 总修复 bug 数：M 个
- 最终状态：无 bug 需要fix

🎉 项目通过全量 bug 扫描，无需进一步修复。
```

**结束整个 skill，不再进入 Task B。**

#### 2.4 有 Bug → 进入 Task B

如果发现任何 没有fix的bug，输出本轮摘要后进入 Task B：

```
🔄 Fix-Loop 第 N 轮 — Task A 完成

📊 本轮扫描结果：
- 未修复 bug：K 个（P0: X, P1: Y, P2: Z）
- Bug ID：[BUG-016, BUG-017, ..., BUG-025]

⏳ 进入 Task B：修复以上 K 个 bug...
```

---

### 3. Task B：Bug 修复（调用 /dev-iterate）

#### 3.1 传递 Bug ID 给 dev-iterate

**将本轮发现的 bug ID 列表作为 feature 范围传递给 /dev-iterate skill。**

调用方式：
```
/dev-iterate [bug-id-1, bug-id-2, ..., bug-id-N]
```

dev-iterate 会按其标准流程处理这些 feature：
- 从 backlog 中读取每个 bug 的描述、改动范围、验证方式
- 对每个 bug 执行 Task A（开发修复）→ Task B（测试验证）→ 自检/提交
- 逐个修复，每个修复完成后 commit & push

#### 3.2 等待 dev-iterate 完成

dev-iterate 完成后，记录本轮修复的 bug 数量。

#### 3.3 修复后 → 回到 Task A

**不验证修复结果**（dev-iterate 内部已有完整的测试和自检流程）。直接进入下一轮循环，由下一轮的 bug-scan 来验证修复是否彻底。

---

### 4. 循环控制

#### 4.1 轮次上限

- 默认无限循环，直到没有新发现的 bug 为止。

#### 4.2 异常处理

| 情况 | 处理方式 |
|------|---------|
| bug-scan 执行失败 | 输出错误信息，询问用户是否跳过本轮继续 |
| dev-iterate 执行失败 | 输出错误信息，询问用户是否跳过未修复的 bug 继续下一轮 |
| backlog.md 不存在 | 在第一轮 bug-scan 时自动创建 |
| 发现的 bug 全是误报 | 用户可指定 `--skip-ids=BUG-001,BUG-002` 跳过特定 bug |

#### 4.3 恢复机制

如果循环中断（用户手动停止、异常退出等），可通过参数恢复：

```
/fix-loop --start=fixed    # 从 dev-iterate 开始（跳过本轮 bug-scan）
/fix-loop --start=scan     # 从 bug-scan 开始（默认，重新扫描）
/fix-loop --round=3        # 从第 3 轮开始（需手动指定待修复的 bug ID）
```

---

### 5. 输出格式

#### 5.1 每轮结束时

```
🔄 Fix-Loop 第 N 轮完成

Task A（扫描）：
- 未修复 bug：K 个
- Bug ID：[BUG-XXX, ...]

Task B（修复）：
- 成功修复：X 个
- 修复失败：Y 个
- 跳过：Z 个

累计：总修复 M 个 bug，剩余待处理 J 个
```

#### 5.2 全部完成时

```
✅ Fix-Loop 完成 — 项目已干净

📊 循环摘要：
- 总轮次：N 轮
- 总扫描 bug 数：T 个
- 总修复 bug 数：M 个
- 跳过/误报：S 个
- 最终状态：无 bug 需要fix

📝 每轮详情：
| 轮次 | 未修复 | 修复 | 跳过 | 状态 |
|------|--------|------|------|------|
| 1    | 12     | 10   | 2    | ✅   |
| 2    | 3      | 3    | 0    | ✅   |
| 3    | 0      | -    | -    | ✅ 干净 |

🎉 项目通过全量 bug 扫描，所有已知 bug 已修复。
```

---

### 6. 注意事项

- **不重复扫描**：每轮 bug-scan 从零开始，不依赖上一轮的扫描结果。bug-scan 内部会检查 backlog 中的重复条目并合并。
- **不绕过 dev-iterate 的测试**：bug 修复必须经过 dev-iterate 的完整测试流程，不能因为"看起来简单"就跳过测试。
- **尊重 dev-iterate 的 P0-P10 原则**：所有修复工作遵循 dev-iterate 内嵌的开发工作原则。
- **用户可随时中断**：在任意轮次的任意阶段，用户都可以中断循环。中断后可通过 `--start` 参数恢复。
- **轮次内不手动干预**：除非遇到异常，一轮内的 scan→fix 流程应自动完成，不需要用户中间确认。
