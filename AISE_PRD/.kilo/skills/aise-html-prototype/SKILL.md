---
name: aise-html-prototype
description: >
  为 AISE 平台创建可交互的 HTML demo 文件，用于需求讨论阶段快速可视化。
  触发场景：用户要求做 demo、做页面、做 HTML、实现页面前端 demo、写页面原型时使用。
  生成文件位置：/Users/didi/Documents/AISE/AISE_PRD/html/{端}/
---

# AISE HTML Demo 快速原型

根据需求讨论结论生成可交互的 HTML 原型文件，聚焦交互验证而非生产代码。

## 工作流

```
1. 确定端（admin/user/exam/iceping/org_admin/issuance）
2. 确定文件命名（按 AISE 页面命名规范）
3. 确定视觉风格（按端对应的 CSS 范式）
4. 生成 HTML → 用户审查 → 精确微调 → 更新关联 PRD 章节
```

## AISE HTML 工程规范

### 文件命名

```
{端}/{序号}_{页面中文名称}.html
```

- admin/user/exam/iceping/org_admin：2 位数字序号，如 `html/admin/26_证书模板管理.html`
- issuance：中文前缀，如 `html/issuance/签发中心_证书仪表盘.html`
- 子页面/变体用下划线后缀：`_详情`、`_独立页`、`_标准字体`

### 各端 CSS 范式（严格按此执行）

| 端 | 框架 | 配色主色 | 背景色 | 字体 |
|----|------|---------|--------|------|
| admin | Tailwind CDN | `#3b82f6`（blue-500） | `#F8FAFC` | Inter + JetBrains Mono |
| user | Tailwind CDN | `#0066FF`（brand-600） | `#F4F8FB` | Inter（300-800） |
| exam | **纯 CSS**（无 Tailwind） | `#4fc3f7` / `#66bb6a` | 圆点渐变 `#b2ebf2` | Comic Sans / 幼圆 |
| iceping | **纯 CSS**（无 Tailwind） | `#4F46E5` CSS 变量体系 | `#F3F4F6` | Inter |
| org_admin | Tailwind CDN | `#3b82f6`（blue-500） | `bg-slate-50` | Inter（300-700） |
| issuance | Tailwind CDN | `#3370FF`（飞书蓝） | `#F5F6F7` | Inter + JetBrains Mono |

**issuance 端特殊配色（飞书/莱克风格）**：
- 顶栏：`#1F2329`（深色导航）
- 主色：`#3370FF` → hover `#2860D8`
- 文字：`#1F2329` / `#646A73` / `#8F959E`（三级灰度）
- 边框：`#E5E6EB`
- 成功：`#00B578`，警告：`#FF7D00`，失败：`#F54A45`

### CDN 依赖（按需引入）

```html
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
```

### 文件模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{页面名称} - AISE 后台</title>
    <!-- CDN 引入 -->
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Inter', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] },
                    colors: { brand: { ... } },
                    boxShadow: { 'card': '...' }
                }
            }
        }
    </script>
    <style>
        /* 页面自有样式 */
    </style>
</head>
<body class="...">
    <!-- 内容 -->
    <script>
        // 页面交互逻辑
    </script>
</body>
</html>
```

## 微调响应策略

当用户给出简短反馈时，按以下规则精确响应：

| 用户反馈 | 响应策略 |
|---------|---------|
| "排版乱了" / "截图有问题" | 检查 CSS 布局结构（flex/grid 是否缺方向声明、宽度/高度约束是否正确） |
| "太丑" / 布局相关 | 检查列表/卡片布局（瀑布流用 `columns`、均匀高度用 `grid`） |
| "不正式" / "太活泼" | 调配色方案（issuance → 飞书风格，其他端 → 往 admin 端靠拢） |
| 交互方式不适用 | 讨论替代方案：侧边窗 → 全屏弹窗 → 独立页面 |
| "XX 可能很多" | 扩充数据条数 + 优化筛选交互（下拉 → 搜索式输入框 / 多选标签） |
| 仅改 demo 不改 PRD | 只动 HTML 文件，不动 PRD 文档 |

## 设计偏好（已知的 Kira2red 习惯）

- 卡片列表优先瀑布流（`columns` + `break-inside: avoid`），高度不强制对齐
- 大列表筛选用搜索式多选输入框，不用传统 select 下拉
- 数据表格行数 ≥ 5 条，覆盖全状态
- 弹窗/向导优先居中全屏（95vw × 90vh），不用侧边抽屉
- 删除/禁用的危险操作需二次确认（`confirm()` 弹窗或自定义确认弹窗）
- beforeunload 拦截未保存内容
- 预备测与 AISE 测评分 Tab 处理，不混在同一列表

## 约束

- HTML demo 是交互验证工具，不是生产代码。不需要考虑路由、状态管理、API 对接。
- 生成 demo 后，如涉及 PRD 更新，使用 `2red-product-monster-prd` skill 按共享层+模块层格式追加 PRD 章节。
- 文件放在 `/Users/didi/Documents/AISE/AISE_PRD/html/{端}/` 目录下。
- 修改已有 HTML 时，先读文件确认当前内容，再做针对性编辑。
- 创建新端（如 issuance）时，同步创建目录。
