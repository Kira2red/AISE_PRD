#!/usr/bin/env python3
"""爱测评线上页面采集脚本（playwright + 本机 Chrome）
登录 adminAica / 123456，抓取题目管理列表页 + 录入题目表单各题型态的
截图 / 渲染DOM / 关键元素样式，存入采集目录，供 demo 严格还原线上样式。
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

BASE = "https://aica.test.iceping.org.cn"
OUT = "/Users/kira2red/Documents/AISE_PRD/AISE_PRD/PRD/20260826 爱测评题目录入增强/线上采集"
os.makedirs(OUT, exist_ok=True)

USER = os.environ.get("AICA_USER", "adminAica")
PWD = os.environ.get("AICA_PWD", "123456")

async def dump(page, name, save_html=True, full_page=True):
    """截图 + 保存渲染后 HTML"""
    await page.wait_for_timeout(1500)
    shot = os.path.join(OUT, f"{name}.png")
    await page.screenshot(path=shot, full_page=full_page)
    if save_html:
        html = await page.evaluate("document.documentElement.outerHTML")
        open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(html)
    print(f"[OK] {name} -> {shot}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome", headless=False,
            args=["--window-size=1600,1000"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1600, "height": 1000},
            locale="zh-CN",
        )
        page = await ctx.new_page()

        # 1. 登录页
        await page.goto(f"{BASE}/login", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)
        await dump(page, "00_登录页")
        # 找登录表单并填入
        # 爱测评登录：用户名/密码 + 登录按钮（jeecg 风格）
        for sel in ['input[placeholder*="用户名"]', 'input[placeholder*="账号"]', 'input[name="username"]']:
            el = await page.query_selector(sel)
            if el:
                await el.fill(USER)
                break
        for sel in ['input[placeholder*="密码"]', 'input[name="password"]', 'input[type="password"]']:
            el = await page.query_selector(sel)
            if el:
                await el.fill(PWD)
                break
        await page.wait_for_timeout(500)
        await dump(page, "01_登录页_已填")
        # 点登录按钮
        clicked = False
        for sel in ['button[type="submit"]', 'button:has-text("登录")', '.login-button']:
            try:
                await page.click(sel, timeout=3000)
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            print("!! 未找到登录按钮，请人工检查")
        await page.wait_for_timeout(6000)
        print("登录后 URL:", page.url)
        await dump(page, "02_登录后")

        # 2. 题目管理列表页
        await page.goto(f"{BASE}/manage/questionManage", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        await dump(page, "10_题目管理列表")

        # 3. 录入题目表单
        await page.goto(f"{BASE}/manage/questionManage/questionForm?back=back", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        await dump(page, "20_录入题目_默认态")

        # 3.1 勾选 AISE题库 → AISE级别出现
        try:
            await page.click('label:has-text("AISE题库")', timeout=3000)
            await page.wait_for_timeout(1200)
            await dump(page, "21_录入题目_AISE题库勾选")
        except Exception as e:
            print("勾选AISE题库失败:", e)

        # 3.2 各题型态
        types = {
            "22_录入题目_单选": "单选",
            "23_录入题目_图形化编程": "图形化编程",
            "24_录入题目_编程OJ": "编程OJ",
            "25_录入题目_编程": "编程",
            "26_录入题目_填空": "填空",
        }
        for name, t in types.items():
            try:
                await page.click(f'text="{t}"', timeout=3000)
                await page.wait_for_timeout(2500)
                await dump(page, name)
            except Exception as e:
                print(f"切换题型[{t}]失败:", e)

        # 4. 图形化编程操作页（Scratch3，测试按钮目标路径）
        try:
            await page.goto(f"{BASE}/scratch3/index.html?scene=create&role=teacher", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            await dump(page, "30_scratch3操作页")
        except Exception as e:
            print("scratch3 页失败:", e)

        # 5. 知识标签树（点开知识标签字段）
        try:
            await page.goto(f"{BASE}/manage/questionManage/questionForm?back=back", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(2500)
            await page.click('text="请选择知识标签"', timeout=3000)
            await page.wait_for_timeout(2500)
            await dump(page, "27_知识标签树展开")
        except Exception as e:
            print("知识标签树展开失败:", e)

        # 6. 收集关键计算样式
        styles = await page.evaluate("""() => {
          const grab = (sel, props) => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const cs = getComputedStyle(el);
            const r = {};
            props.forEach(p => r[p] = cs[p]);
            return r;
          };
          return {
            bodyBg: grab('body', ['backgroundColor','fontFamily','fontSize','color']),
            header: grab('.ant-layout-header', ['backgroundColor','height','display']),
            questionForm: grab('.questionForm', ['backgroundColor','padding','margin']),
            questionTypeBox: grab('.questionTypeBox', ['display','gap','flexWrap']),
            questionType: grab('.questionType', ['borderRadius','padding','border','fontSize']),
            questionTypeActive: grab('.questionTypeActive', ['backgroundColor','color','border']),
            separatorBox: grab('.separatorsListBox', ['backgroundColor','padding','borderRadius','border']),
            card: grab('.questionCard', ['backgroundColor','borderRadius','padding','boxShadow']),
            footer: grab('.questionCard.fotter', ['display','justifyContent','gap','padding']),
          };
        }""")
        open(os.path.join(OUT, "key_styles.json"), "w", encoding="utf-8").write(json.dumps(styles, ensure_ascii=False, indent=2))
        print("关键样式已存:", styles)

        await browser.close()

asyncio.run(main())
