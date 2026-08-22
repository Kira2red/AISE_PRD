#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打包人才库智能体 Demo 分享压缩包。

安全规则（重要）：
- 不打包 .env（含 API key）与 data.json（运行数据）
- 收件人解压即用：默认 Mock 模拟模式全链路演示；自行填 key 后切真实模式

用法：python3 make_package.py
输出：~/Documents/文稿/20260822 人才库智能体Demo/人才库智能体Demo.zip
"""
import os
import shutil
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
PRD_SAMPLES = os.path.expanduser('~/Documents/AISE_PRD/AISE_PRD/PRD/20260806 人才库智能体/示例作品')
OUT_DIR = os.path.expanduser('~/Documents/文稿/20260822 人才库智能体Demo')
PKG = '人才库智能体Demo'
STAGE = os.path.join('/tmp', 'pkg_' + PKG)
ZIP_PATH = os.path.join(OUT_DIR, PKG + '.zip')

os.makedirs(OUT_DIR, exist_ok=True)
if os.path.exists(STAGE):
    shutil.rmtree(STAGE)
os.makedirs(STAGE)

# 1. 服务端与前端（www 全量，不含运行时数据）
shutil.copy(os.path.join(ROOT, 'server.py'), STAGE)
shutil.copytree(os.path.join(ROOT, 'www'), os.path.join(STAGE, 'www'))
shutil.copy(os.path.join(ROOT, '.env.example'), STAGE)
shutil.copy(os.path.join(ROOT, '.gitignore'), STAGE)
shutil.copy(os.path.join(ROOT, '启动演示.command'), STAGE)
shutil.copy(os.path.join(ROOT, '启动演示.bat'), STAGE)

# 2. 测试作品与生成脚本（从需求文件夹复制）
shutil.copytree(PRD_SAMPLES, os.path.join(STAGE, '示例作品'))
shutil.copy(os.path.expanduser('~/Documents/AISE_PRD/AISE_PRD/PRD/20260806 人才库智能体/generate_samples.py'), STAGE)

# 3. 收件人版说明
README = """# 人才库智能体（AI 人才大脑 1.0）演示包

一个本地可跑的全链路演示：上传作品 → 智能体自动预审 → 后台人工终审 → 人才卡与画像分析自动更新。

## 三步跑起来

1. **电脑装有 Python3**（macOS 自带；Windows 到 python.org 下载安装，安装时勾选「Add Python to PATH」）
2. 解压后**双击启动**（浏览器会自动打开）：
   - macOS：双击 `启动演示.command`（首次若提示安全拦截，右键 → 打开）
   - Windows：双击 `启动演示.bat`
3. 或手动启动：终端进入本文件夹，运行 `python3 server.py`，然后浏览器打开 http://localhost:8080/

| 页面 | 地址 | 说明 |
|------|------|------|
| 作品上传（学员端） | http://localhost:8080/ | 上传作品、查看审核状态 |
| 人才卡 | http://localhost:8080/card.html | 动态能力标签 + 四维能力雷达 |
| 画像分析报告 | http://localhost:8080/report.html | 个人画像诊断与成长建议 |
| 审核工作台（后台） | http://localhost:8080/admin.html | AI 预审结论、人工终审、材料审核、留痕 |

## 两种模式

- **Mock 模拟模式（默认）**：未配置 key 时自动启用，全链路照常演示，智能体结论均带「模拟结果」标识
- **真实 AI 模式**：复制 `.env.example` 为 `.env`，填入 `DEEPSEEK_API_KEY=你的key`，重启服务

顶栏徽章会显示当前模式。

## 演示流程建议

1. 学员端上传 `示例作品/` 里的文件（共 8 份：4 代码 + 2 图片 + 2 PDF；「极简网页.html」是低质量作品，可演示驳回）
2. 打开后台，等待预审完成（真实模式约 5-15 秒），查看结论 / 标签 / 得分 / 评语
3. 人工终审：通过（可改标签）、或驳回
4. 回到人才卡与画像分析报告，查看自动更新结果
5. 后台「材料审核」tab 可体验简历材料按条目审核

## 常见问题

- **端口被占用**：`.env` 里改 `PORT=8081`，地址相应变为 http://localhost:8081/
- **提示 python 不存在**：Windows 可试试 `python server.py`；macOS 检查是否装了 Xcode 命令行工具（`xcode-select --install`）
- **想清空演示数据重新来**：删除 `data.json` 后重启，或后台「清空演示数据」按钮
"""

with open(os.path.join(STAGE, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(README)

# 4. 打包（显式清单，确保 .env / data.json / .DS_Store 全部排除）
os.makedirs(STAGE) if not os.path.exists(STAGE) else None
with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(STAGE):
        dirs[:] = [d for d in dirs if d not in ('__pycache__',)]
        for name in files:
            if name in ('.DS_Store',):
                continue
            full = os.path.join(root, name)
            arc = os.path.join(PKG, os.path.relpath(full, STAGE))
            z.write(full, arc)

size_mb = os.path.getsize(ZIP_PATH) / 1024 / 1024
print('已打包:', ZIP_PATH, '(%.1f MB)' % size_mb)

# 5. 安全自检：包内不得出现 key 或运行数据
with zipfile.ZipFile(ZIP_PATH) as z:
    names = z.namelist()
    bad = [n for n in names if n.endswith('.env') or n.endswith('data.json')]
    assert not bad, '包内出现敏感文件: %s' % bad
    assert PKG + '/server.py' in names and PKG + '/www/index.html' in names
print('✓ 安全自检通过：无 .env / data.json，核心文件齐全')
