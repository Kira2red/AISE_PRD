#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成人才库 Demo 测试作品：代码 / 图片 / PDF。仅 PIL + 标准库。"""
import os, zlib, struct
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '示例作品')
os.makedirs(OUT, exist_ok=True)
FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'

# ---------- 1. 代码作品 ----------
calc = '''# 智能计算器小程序
# 支持四则运算的交互式命令行计算器
def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

def div(a, b):
    if b == 0:
        return "错误：除数不能为零"
    return a / b

print("欢迎使用智能计算器")
print("支持运算：+ - * /，输入 q 退出")
while True:
    expr = input("请输入表达式（如 1+2）：").strip()
    if expr.lower() == "q":
        print("再见！")
        break
    for op, fn in [("+", add), ("-", sub), ("*", mul), ("/", div)]:
        if op in expr:
            a, b = expr.split(op)
            result = fn(float(a), float(b))
            print(f"{a} {op} {b} = {result}")
            break
    else:
        print("无法识别该表达式，请重试")
'''
open(os.path.join(OUT, '智能计算器小程序.py'), 'w', encoding='utf-8').write(calc)

guess = '''# 猜数字游戏（AI 提示版）
import random

target = random.randint(1, 100)
print("我想了一个 1-100 之间的数字，你来猜猜看！")
tries = 0
while True:
    try:
        guess = int(input("请输入你的猜测："))
    except ValueError:
        print("请输入数字哦")
        continue
    tries += 1
    if guess < target:
        print("太小了，再大一点")
    elif guess > target:
        print("太大了，再小一点")
    else:
        print(f"恭喜！你用了 {tries} 次猜中了数字 {target}")
        if tries <= 5:
            print("评价：你是猜数字高手！")
        elif tries <= 10:
            print("评价：不错，继续加油！")
        else:
            print("评价：可以试试二分查找法，会更高效")
        break
'''
open(os.path.join(OUT, '猜数字游戏.py'), 'w', encoding='utf-8').write(guess)

gallery = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>我的AI绘画作品集</title>
<style>
body { font-family: sans-serif; background: #1a1a2e; color: #eee; margin: 0; }
header { text-align: center; padding: 32px 16px; background: linear-gradient(135deg, #16213e, #0f3460); }
h1 { margin: 0; font-size: 26px; }
p.sub { color: #aaa; font-size: 14px; margin-top: 8px; }
.filters { text-align: center; padding: 14px; }
.filters button { background: #0f3460; color: #eee; border: 1px solid #533483;
  padding: 8px 18px; margin: 0 6px; border-radius: 20px; cursor: pointer; }
.filters button:hover { background: #533483; }
.gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 18px; padding: 20px; max-width: 1000px; margin: 0 auto; }
.card { background: #16213e; border-radius: 12px; overflow: hidden; }
.card .art { height: 180px; }
.card .info { padding: 12px 14px; font-size: 13px; color: #ccc; }
.card .tag { display: inline-block; background: #533483; border-radius: 10px;
  padding: 2px 10px; font-size: 11px; margin-right: 6px; }
</style>
</head>
<body>
<header>
  <h1>我的 AI 绘画作品集</h1>
  <p class="sub">用生成式人工智能创作的数字艺术作品</p>
</header>
<div class="filters">
  <button>全部</button><button>科幻</button><button>自然</button><button>校园</button>
</div>
<div class="gallery" id="gallery"></div>
<script>
const works = [
  { name: '未来城市', tag: '科幻', c1: '#0f3460', c2: '#533483' },
  { name: '森林之光', tag: '自然', c1: '#1b4332', c2: '#74c69d' },
  { name: '星空漫步', tag: '科幻', c1: '#1a1a2e', c2: '#3a0ca3' },
  { name: '校园晨曦', tag: '校园', c1: '#fb8500', c2: '#ffb703' },
  { name: '深海探秘', tag: '自然', c1: '#023e8a', c2: '#00b4d8' },
  { name: '机器伙伴', tag: '科幻', c1: '#2b2d42', c2: '#8d99ae' },
];
const box = document.getElementById('gallery');
works.forEach(w => {
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = '<div class="art" style="background:linear-gradient(135deg,' + w.c1 + ',' + w.c2 + ')"></div>' +
    '<div class="info"><span class="tag">' + w.tag + '</span>' + w.name + '<br>AI 生成 · 数字艺术</div>';
  box.appendChild(card);
});
</script>
</body>
</html>
'''
open(os.path.join(OUT, 'AI绘画作品集网页.html'), 'w', encoding='utf-8').write(gallery)

simple = '''<!DOCTYPE html>
<html>
<head><title>我的网页</title></head>
<body>
<h1>你好</h1>
</body>
</html>
'''
open(os.path.join(OUT, '极简网页.html'), 'w', encoding='utf-8').write(simple)

# ---------- 2. 图片作品（PIL 绘制） ----------
def poster(path, title, sub, colors, deco):
    img = Image.new('RGB', (960, 640))
    d = ImageDraw.Draw(img)
    for y in range(640):  # 渐变背景
        t = y / 639
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * t)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * t)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * t)
        d.line([(0, y), (960, y)], fill=(r, g, b))
    f1 = ImageFont.truetype(FONT, 64)
    f2 = ImageFont.truetype(FONT, 30)
    f3 = ImageFont.truetype(FONT, 20)
    if deco == 'robot':
        # 机器人
        d.rounded_rectangle([380, 200, 580, 400], 24, fill=(230, 235, 245), outline=(80, 90, 120), width=4)
        d.rectangle([455, 150, 505, 200], fill=(230, 235, 245), outline=(80, 90, 120), width=4)
        d.ellipse([470, 120, 500, 150], fill=(255, 200, 60), outline=(80, 90, 120), width=3)
        d.ellipse([430, 245, 460, 275], fill=(70, 90, 200), outline=(40, 40, 60), width=3)
        d.ellipse([500, 245, 530, 275], fill=(70, 90, 200), outline=(40, 40, 60), width=3)
        d.rounded_rectangle([440, 310, 520, 340], 8, fill=(120, 200, 150))
        for x in [100, 160, 800, 860]:
            d.ellipse([x, 100, x + 30, 130], fill=(255, 240, 180))
    else:
        # 海报装饰
        for i in range(6):
            x = 60 + i * 150
            d.ellipse([x, 430, x + 70, 500], fill=(255, 255, 255, 90))
        d.rounded_rectangle([80, 60, 880, 120], 20, fill=(255, 255, 255))
    tw = d.textlength(title, font=f1)
    d.text(((960 - tw) / 2, 480), title, font=f1, fill=(255, 255, 255))
    sw = d.textlength(sub, font=f2)
    d.text(((960 - sw) / 2, 560), sub, font=f2, fill=(255, 240, 210))
    d.text((40, 600), 'AI 生成 · 学生作品', font=f3, fill=(255, 255, 255))
    img.save(path, 'PNG')

poster(os.path.join(OUT, 'AI校园主题海报.png'), 'AI 校园主题海报', '人工智能 · 创意无限',
       [(90, 60, 200), (30, 140, 220)], 'poster')
poster(os.path.join(OUT, '机器人创意插画.png'), '机器人创意插画', '我的 AI 伙伴',
       [(40, 40, 90), (110, 60, 170)], 'robot')

# ---------- 3. PDF 作品（纯标准库生成文本 PDF） ----------
def make_pdf(path, title, paras):
    def esc(s):
        return s.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')

    content = ['BT /F1 22 Tf 72 770 Td (%s) Tj ET' % esc(title)]
    y = 730
    for p in paras:
        content.append('BT /F1 12 Tf 72 %d Td (%s) Tj ET' % (y, esc(p)))
        y -= 24
    stream = '\n'.join(content)

    objs = []

    def add(obj):
        objs.append(obj)
        return len(objs)

    font_id = add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
    content_id = add('<< /Length %d >>\nstream\n%s\nendstream' % (len(stream), stream))
    pages_id = add('<< /Type /Pages /Kids [0 0 R] /Count 1 >>')  # 占位，稍后回填
    page_id = add('<< /Type /Page /Parent %d 0 R /MediaBox [0 0 612 842] /Contents %d 0 R /Resources << /Font << /F1 %d 0 R >> >> >>'
                  % (pages_id, content_id, font_id))
    objs[pages_id - 1] = '<< /Type /Pages /Kids [%d 0 R] /Count 1 >>' % page_id
    catalog_id = add('<< /Type /Catalog /Pages %d 0 R >>' % pages_id)

    # 组装并精确计算 xref 偏移（字节级）
    out = bytearray()
    out += b'%PDF-1.4\n'
    offsets = []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += ('%d 0 obj\n' % i).encode('latin-1')
        out += obj.encode('latin-1')
        out += b'\nendobj\n'
    xref_pos = len(out)
    out += b'xref\n'
    out += ('0 %d\n' % (len(objs) + 1)).encode('latin-1')
    out += b'0000000000 65535 f \n'
    for off in offsets:
        out += ('%010d 00000 n \n' % off).encode('latin-1')
    out += b'trailer\n'
    out += ('<< /Size %d /Root %d 0 R >>\n' % (len(objs) + 1, catalog_id)).encode('latin-1')
    out += b'startxref\n'
    out += (str(xref_pos) + '\n%%EOF\n').encode('latin-1')
    open(path, 'wb').write(out)

make_pdf(os.path.join(OUT, 'AI项目学习总结报告.pdf'), 'AI Project Learning Summary',
         ['Student: Li Xiaoming   Date: 2026-08',
          'This report summarizes my AI learning project on prompt engineering.',
          '',
          'Project Overview:',
          '  I designed a prompt library for creative writing and image generation,',
          '  covering 30+ scenarios with structured prompts and evaluation criteria.',
          '',
          'Implementation:',
          '  Built a prompt template system and tested it with generative AI tools.',
          '',
          'Achievements:',
          '  Generation quality improved by about 40% after iterative optimization.',
          '  Won second prize in the school AI challenge.',
          '',
          'Reflection:',
          '  Learned how to decompose complex tasks and evaluate AI outputs.'])

make_pdf(os.path.join(OUT, '智能小车项目报告.pdf'), 'Smart Car Project Report',
         ['Student: Li Xiaoming   Date: 2026-06',
          'Project Goal:',
          '  Build a line-following smart car with obstacle avoidance.',
          '',
          'Hardware & Software:',
          '  Controller board, two motors, ultrasonic sensor, Python control logic.',
          '',
          'Key Features:',
          '  - Auto line following with PID control',
          '  - Obstacle detection and emergency stop',
          '  - Manual remote control mode',
          '',
          'Testing Result:',
          '  Completed 5 test tracks; average lap time 42 seconds.',
          '',
          'Future Plan:',
          '  Add camera-based visual navigation.'])

# ---------- 汇总 ----------
print('生成完毕，示例作品目录：', OUT)
for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    print(' - %-28s %6.1f KB' % (f, os.path.getsize(p) / 1024))
