---
name: demo
description: 一键生成竞赛级项目演示。自动发现项目 features，规划 90s~5min 高光 demo 流程，生成可执行演示脚本。强制：交互元素坐标零误差、重要 feature 完整演示、独白不超过 2 句即配动作。
when_to_use: 用户说"demo"、"演示"、"一键演示"、"自动demo"、"生成demo"、"竞赛demo"、"参赛演示"、"做demo"、"录demo"
argument-hint: [<时长> | --features <编号> | --list]
---

## 一键自动 Demo 流程

> **核心原则：评委的时间是金子。90 秒到 5 分钟内，让评委看完想见你。**

### 0. 参数解析

从 `$ARGUMENTS` 中提取：

- **时长**：数字 + 单位（`90s`、`2min`、`5min`），默认 `3min`
- `--features <编号>`：指定演示的 feature 编号（逗号分隔），如 `1,3,5`
- `--list`：仅列出可演示的 feature，不生成脚本

时长硬限制：**最短 90 秒，最长 5 分钟**。超出范围时提示用户并取边界值。

---

### 1. 项目发现

自动扫描当前项目，按优先级依次读取以下文档，提取所有 feature：

1. `backlog.md` 或 `BACKLOG.md`
2. `PRD.md` 或 `prd.md`
3. `DESIGN.md` 或 `design.md`
4. `README.md`（features / capabilities 章节）
5. `docs/` 目录下所有 `.md` 文件
6. `DevPlan.md` 或 `dev-plan.md`

**Feature 提取规则：**
- 含 `[✅]` 标记的已完成 feature 优先
- 含 `###` 或 `##` 标题 + 描述文本的条目
- 每个 feature 记录：序号、标题、一句话摘要、关键交互点

如果找不到任何文档，向用户确认项目亮点后手动录入。

---

### 2. Feature 筛选与排序

#### 2.1 筛选

- 用户指定 `--features` → 只用指定编号
- 未指定 → 自动选择**高光 feature**（按以下优先级）
  1. 有视觉冲击力的功能（动画、图表、实时渲染）
  2. 解决核心痛点的功能（与项目定位直接相关）
  3. 技术上有亮点的功能（AI、跨平台、实时同步等）
  4. 差异化功能（竞品没有的）

#### 2.2 排序

Demo 流程按 **"开场 → 高潮 → 收尾"** 三幕结构排列：

| 阶段 | 时长占比 | 目的 |
|------|---------|------|
| **Phase In（开场）** | 10% | 一句话点题 + 项目全景 |
| **核心 Feature 逐一演示** | 75% | 按震撼力降序排列，最炸的放第 2~3 个 |
| **Phase Out（收尾）** | 15% | 总结价值 + Call to Action |

#### 2.3 时长分配

每个 feature 的时长 = (总时长 × 75%) / feature 数量。
**重要 feature 时长 × 1.5**，次要 feature 时长 × 0.7，但每个 feature 至少 15 秒。

---

### 3. Demo 脚本设计（核心规则）

#### 3.1 叙事规则（铁律）

**独白限制：连续旁白/叙述不得超过 2 句话。第 2 句结束后必须立即跟一个 demo 动作。**

```
❌ 错误示例：
  "这个功能可以帮你管理任务。它支持拖拽排序，还支持标签过滤。
   你还可以设置优先级。每个任务都有独立的详情页。"  ← 4 句独白，观众走神

✅ 正确示例：
  "一句话：拖拽管理你的任务。"  ← 旁白
  [拖拽一个任务到新位置]        ← 动作
  "标签过滤也是一秒的事。"       ← 旁白
  [点击标签，列表即时筛选]       ← 动作
```

#### 3.2 交互精度规则（铁律）

**任何需要点击、拖拽、定位的交互元素，坐标必须零误差。**

- 使用**语义选择器**（CSS selector、test-id、aria-label）而非坐标
- 如果必须用坐标，必须先**锚定参考点**再计算偏移
- **禁止估算坐标**，必须通过实际测量或 DOM 查询获得
- 拖拽操作：起点和终点都必须精确到像素
- 每个交互操作前添加 `wait_for_element` 等待，防止元素未加载就点击

```
❌ 错误：click(350, 200)  ← 硬编码坐标，分辨率一变就废
✅ 正确：click('[data-testid="start-button"]')  ← 语义选择器
✅ 正确：click(ANCHOR.offset(dx, dy))  ← 锚定 + 偏移
```

#### 3.3 完整性规则

**重要 feature 必须完整演示，不能半途跳转。**

- 每个 feature 的核心路径必须走完
- 如果 feature 包含多步操作（如 storyboard 播放），必须播放到自然结束
- 演示一个 feature 时，不能因为赶时间而跳过关键步骤
- 宁可减少 feature 数量，也不要把重要 feature 演示得残缺不全

```
❌ 错误：演示 storyboard "大家看一下效果..." [快进到结尾]
✅ 正确：完整播放 storyboard，旁白配合关键节点解说
```

#### 3.4 状态复原规则（铁律）

**任何改变了系统状态的 demo 步骤，结束时必须根据后续步骤的需求决定重置策略——而非一刀切全部重置。**

这条规则适用于所有会改变系统状态的操作，包括但不限于：

- **过滤器操作**：选择/切换分类过滤器、情绪过滤器、标签过滤器、搜索条件等
- **视图切换**：切换排序方式、显示模式、布局方式等
- **数据操作**：新增/编辑/删除条目、修改设置、切换用户等
- **导航跳转**：进入详情页后需返回列表页、展开面板后需收起等

**重置策略（必须在脚本设计阶段规划）：**

在设计 demo 脚本时，对每个改变状态的步骤，**先看后面的步骤需要什么**，再决定重置哪些、保留哪些：

| 后续步骤情况 | 重置策略 |
|-------------|---------|
| 后续步骤需要干净的全量视图 | **全量重置**：恢复到该步骤进入前的初始状态 |
| 后续步骤依赖当前过滤结果（如先选分类再在该分类下演示排序） | **保留过滤，重置其他**：保留过滤器，只重置视图/排序等无关状态 |
| 后续步骤要切换到另一个过滤条件（如从"开心"切到"悲伤"） | **先重置当前，再让后续步骤设定新条件**：确保不会残留旧过滤 |
| 后续步骤就是 Phase Out 收尾 | **全量重置**：收尾前系统必须回到干净状态 |

**设计要求：**
- 脚本设计阶段必须画出**状态流转图**：每个步骤进入时的系统状态 → 步骤中改变了什么 → 步骤结束时保留/重置什么 → 下一个步骤进入时的状态
- 复原操作在旁白/动作切换的间隙完成，不额外占用时长
- 优先使用"反向操作"复原（如点击了分类 A → 再点击取消），无法反向则显式重置

```
❌ 错误 1（一刀切不考虑后续）：
  [点击"情绪：开心"过滤器]          ← 改变了过滤状态
  [展示过滤后的粒子]
  [取消"情绪：开心"过滤]            ← 全量重置
  [点击"情绪：开心"过滤器]          ← 下一步又选了同一个过滤，重复操作浪费时间

❌ 错误 2（完全不重置）：
  [点击"情绪：开心"过滤器]          ← 改变了过滤状态
  [展示过滤后的粒子]
  "接下来看排序功能..."             ← 过滤器残留，后续演示数据不全

✅ 正确（根据后续步骤智能决定）：
  步骤 A：演示"情绪过滤"
    [点击"情绪：开心"过滤器]        ← 改变过滤
    [展示过滤后的粒子]
    "效果就是这样。"                 ← 旁白
    [取消"情绪：开心"过滤]          ← 全量重置（因为下一步需要干净视图）
  步骤 B：演示"分类过滤 + 排序联动"
    [点击"工作"分类过滤器]          ← 设定新过滤
    [展示工作分类粒子]
    [切换排序为"时间倒序"]           ← 改变排序
    [展示排序效果]
    "排序和分类可以叠加使用。"       ← 旁白
    [重置排序为默认]                 ← 只重置排序，保留"工作"过滤（因为下一步要在工作分类下演示搜索）
  步骤 C：演示"分类内搜索"
    [在"工作"分类下输入搜索关键词]   ← 复用了步骤 B 设定的过滤
    ...
    [取消搜索 + 取消"工作"过滤]      ← 全量重置（下一步或收尾需要干净状态）
```

#### 3.5 开场与收尾规则

**Phase In（开场）：**
- 第 1 秒：黑屏或项目 Logo，停留 1~2 秒让观众聚焦
- 第 2~3 秒：一句话 Hook（"你有没有遇到过..."或"想象一下..."）
- 第 4~5 秒：项目全景画面（整体 UI 或架构图）
- 然后进入第一个 feature

**Phase Out（收尾）：**
- 最后一个 feature 演示完毕后，切换到总结画面
- 一句话总结核心价值
- Call to Action（"欢迎试用"、"GitHub 链接"等）
- 停留 2~3 秒，不要突然黑屏

---

### 4. 脚本生成

根据项目类型，选择合适的演示载体并生成脚本。

#### 4.1 载体选择

| 项目类型 | 载体 | 输出文件 |
|---------|------|---------|
| Web 应用 | Playwright (Python) | `demo.py` |
| CLI 工具 | VHS tape + Python 模拟 | `demo.tape` + `demo_shell.py` |
| 桌面应用 | Playwright / Appium | `demo.py` |
| 有现有 demo 脚本 | 复用并扩展 | 覆盖原文件 |

#### 4.2 生成 Playwright 脚本（Web 应用）

```python
# demo.py — 自动生成，勿手动编辑
# 用法：python demo.py [--duration 180] [--headless]

import asyncio
import argparse
from playwright.async_api import async_playwright

# ─── 配置 ───
BASE_URL = "http://localhost:3000"  # 自动从项目配置中读取
DURATION_SECONDS = 180  # 默认 3 分钟

async def phase_in(page):
    """开场：让观众聚焦"""
    await page.goto(BASE_URL)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)  # Logo / 全景停留
    # ... 一句话 Hook（字幕叠加）

async def demo_feature_1(page):
    """Feature 1: [标题]"""
    # 旁白：第 1 句
    await page.click('[data-testid="..."]')  # 语义选择器，非坐标
    await page.wait_for_selector('[data-testid="result"]')
    # 旁白：第 2 句
    await page.click('[data-testid="action"]')  # 立即配动作
    await asyncio.sleep(1)

async def phase_out(page):
    """收尾：总结 + CTA"""
    await page.screenshot(path="demo_final.png")
    # 总结字幕
    await asyncio.sleep(3)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=180)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=args.headless)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await phase_in(page)
        await demo_feature_1(page)
        # ... 更多 feature
        await phase_out(page)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 4.3 生成 VHS 脚本（CLI 工具）

```tape
Output demo.gif

Set FontSize 18
Set Width 1280
Set Height 720
Set Padding 30
Set WindowBar Colorful
Set BorderRadius 10
Set Theme "Catppuccin Mocha"

Hide
Type "python3 demo_shell.py"
Enter
Show

Sleep <总秒数>s
```

`demo_shell.py` 的生成规则与 `fake_shell.py` 相同，但加入：
- Phase In：先清屏，显示项目名 + 一句话 Hook
- 每个 feature 间用 ANSI 颜色分隔
- Phase Out：总结 + 链接

#### 4.4 自检清单（生成后必跑）

脚本生成后，逐项检查：

1. **时长校验**：脚本总时长是否在 [90s, 5min] 范围内
2. **独白检查**：扫描所有旁白文本，连续超过 2 句的全部标记为 ERROR
3. **坐标检查**：所有 `click(x, y)` 形式的调用必须改为语义选择器或锚定偏移
4. **完整性检查**：重要 feature 的演示步骤是否完整（无 `# TODO`、`# skip`）
5. **等待检查**：每次交互前是否有 `wait_for_*` 调用
6. **Phase In/Out**：开头和结尾是否存在且不突兀
7. **状态复原检查**：每个改变系统状态的步骤，结束时的重置策略是否根据后续步骤的需求精确设计（全量重置 / 保留部分 / 先重置再由后续设定），而非一刀切
8. **可执行检查**：脚本语法无误，依赖已声明

任何 ERROR 必须修复后才能交付。WARNING 提示用户确认。

---

### 5. 交付

1. 将生成的脚本文件写入项目根目录（或 `.github/` 目录）
2. 输出摘要：

```
✅ Demo 脚本已生成：
   📄 demo.py（Playwright 自动化）
   ⏱️  时长：3 分钟（6 个 feature）
   🎬 结构：Phase In → Feature 1~4 → Phase Out
   🔍 自检：7/7 通过

   运行：python demo.py
   预览：python demo.py --headless
```

3. 如果用户要求立即运行，先检查运行环境（Playwright 是否安装、服务是否启动），然后执行

---

### 6. 常见项目类型的 Demo 亮点模板

以下模板供自动选择 feature 时参考：

**Web 应用（SaaS）：**
- 核心工作流完整走一遍（注册 → 核心操作 → 结果）
- 实时协作 / 数据可视化的视觉冲击
- 移动端响应式展示

**CLI 工具：**
- 一行命令完成复杂任务的"魔法感"
- Before/After 对比
- 多工具联动（pipe）

**AI/ML 项目：**
- 实时推理效果（输入 → 输出，秒级响应）
- 与基线模型的对比
- 边界 case 展示（不是只秀最佳 case）

**开发者工具：**
- 5 分钟从零开始的 Quick Start
- 与现有工作流的无缝集成
- 性能对比数据

---

### 附录：Anti-Patterns（踩坑即扣分）

| ❌ Anti-Pattern | ✅ 正确做法 |
|----------------|-----------|
| 旁白念 4~5 句才开始操作 | 每 2 句旁白必须跟一个动作 |
| 硬编码像素坐标 | 语义选择器 + wait_for |
| Feature 演示半途跳过 | 完整演示或干脆不放 |
| 开头直接进入功能 | Phase In：Logo + Hook |
| 结尾突然黑屏 | Phase Out：总结 + CTA |
| 只秀最佳 case | 展示真实场景含边界 case |
| 演示时碰到 bug | 生成后必须自检 + 试运行 |
| 评委 30 秒还不知道项目干嘛 | 第 5 秒前必须点明项目价值 |
| 改了过滤器/状态后直接下一步 | 每步结束时根据后续步骤需求精确决定重置策略 |
| 一刀切重置所有状态（即使下一步复用） | 先分析后续步骤依赖，保留需要的、重置多余的 |
