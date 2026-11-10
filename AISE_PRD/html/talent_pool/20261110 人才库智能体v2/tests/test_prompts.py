#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词批量验证 harness：≥100 条真实用例，检验四条 AI 链路的输出
  1) 作品预审 ai_review_work   —— 30 条（代码 12 / PDF 6 / 图片 12）
  2) 画像报告 ai_generate_report —— 15 条（8 名种子学员 + 7 个变异画像）
  3) 问答     ai_qa            —— 45 条（学员 20 / 教研员 25，含必须拦截项）
  4) 分析点评 ai_analytics_comment —— 10 条（合成聚合数据）
校验两层：格式（JSON/字段/长度/枚举/黑名单）+ 效果（scope 判断、关键信息、拦截正确性）。
结果写 tests/prompt_test_results.json。
"""
import json
import os
import sys
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402
import seed_data  # noqa: E402

UPLOAD = server.UPLOAD_DIR
os.makedirs(UPLOAD, exist_ok=True)
SAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'samples')
DATA = server.reset_data()

VALID_TAGS = set('程序设计 生成式人工智能 算法思维 创意设计 逻辑思维 数据思维 计算思维 问题解决'.split())
REFUSE_PREFIX = '该问题超出人才库服务范围'


# ---------------------------------------------------------------- 用例构造

def mk_code_cases():
    good_calc = ("def calc():\n    op = input('运算(+ - * /): ')\n    a = float(input('a='))\n"
                 "    b = float(input('b='))\n    if op == '+': print(a + b)\n    elif op == '-': print(a - b)\n"
                 "    elif op == '*': print(a * b)\n    elif op == '/':\n        if b == 0: print('除数不能为0')\n"
                 "        else: print(a / b)\n    else: print('不支持的运算')\n\ncalc()\n")
    guess = ("import random\nn = random.randint(1, 100)\nc = 0\nwhile True:\n"
             "    g = int(input('猜一个1-100的数：'))\n    c += 1\n    if g < n: print('小了')\n"
             "    elif g > n: print('大了')\n    else:\n        print('猜对了！用了', c, '次')\n        break\n")
    todo = ("todos = []\nwhile True:\n    cmd = input('add/done/list/quit: ')\n"
            "    if cmd == 'add': todos.append([input('内容：'), False])\n"
            "    elif cmd == 'done':\n        i = int(input('编号：')) - 1\n"
            "        if 0 <= i < len(todos): todos[i][1] = True\n"
            "    elif cmd == 'list':\n        for i, t in enumerate(todos):\n            print(i + 1, '[x]' if t[1] else '[ ]', t[0])\n"
            "    elif cmd == 'quit': break\n")
    cases = [
        ('智能计算器小程序', '支持四则运算和除零提示的计算器', good_calc),
        ('猜数字游戏', '1-100 猜数字，会提示大小和次数', guess),
        ('待办清单管理器', '可以添加、完成、查看待办事项', todo),
        ('我的第一个程序', '', "print('hello world')\n"),
        ('作业1', '老师留的作业', "x = 1\nprint(x)\n"),
        ('九九乘法表', '用双层循环打印乘法表',
         "for i in range(1, 10):\n    for j in range(1, i + 1):\n        print(j, 'x', i, '=', i * j, end='  ')\n    print()\n"),
        ('成绩统计器', '输入多名同学成绩，输出平均分和最高分',
         "scores = []\nwhile True:\n    s = input('成绩(空结束): ')\n    if not s: break\n"
         "    scores.append(float(s))\nprint('平均', sum(scores) / len(scores), '最高', max(scores))\n"),
        ('未命名', '', "  \n\t\n"),
        ('画正方形', '用 turtle 画正方形',
         "import turtle\nt = turtle.Turtle()\nfor i in range(4):\n    t.forward(100)\n    t.right(90)\nturtle.done()\n"),
        ('密码生成器', '随机生成8位密码',
         "import random, string\nchars = string.ascii_letters + string.digits\n"
         "print(''.join(random.choice(chars) for _ in range(8)))\n"),
        ('温度转换', '摄氏度和华氏度互转',
         "c = float(input('摄氏温度: '))\nprint('华氏', c * 9 / 5 + 32)\n"),
        ('文字冒险游戏', '选择分支推动剧情的小游戏',
         "print('你在森林里遇到岔路')\nc = input('走左边还是右边？')\nif c == '左边':\n    print('遇到小河，造船过河！')\nelse:\n    print('遇到熊，快跑！')\n"),
    ]
    out = []
    for name, desc, code in cases:
        fn = 't_%s.py' % abs(hash(name))
        open(os.path.join(UPLOAD, fn), 'w', encoding='utf-8').write(code)
        out.append({'name': name, 'desc': desc, 'type': 'code', 'filename': fn})
    return out


def mk_pdf_cases():
    texts = [
        ('智能小车项目报告', '我们小组用传感器和主板拼了一辆避障小车，写了程序让它遇到障碍自动转向。调试中遇到轮子打滑，垫了橡皮解决了。',
         '一、目标  二、材料  三、过程（组装、编程、调试三次）  四、结果：成功避障 10 次'),
        ('校园垃圾分类调查', '统计了校园里四个垃圾桶的使用情况，发现可回收桶混入率高，做了宣传海报。',
         '调查时间两周，样本 200 次，混入率 38%，建议增加标识'),
        ('我的 AI 学习笔记', '记录了学习提示词的过程，从乱写到学会给角色和格式要求。',
         '包含 5 次提示词迭代记录与效果对比'),
        ('空白文档', '', ''),
        ('测试', '', ''),
        ('读书笔记', '读了《人工智能简史》，知道了图灵测试。', ''),
    ]
    out = []
    for name, desc, body in texts:
        fn = 't_%s.pdf' % abs(hash(name))
        open(os.path.join(UPLOAD, fn), 'w', encoding='utf-8').write(body or '（空）')
        out.append({'name': name, 'desc': desc, 'type': 'pdf', 'filename': fn})
    return out


def mk_image_cases():
    srcs = [os.path.join(SAMPLES, '机器人创意插画.png'), os.path.join(SAMPLES, 'AI校园主题海报.png')]
    names = [
        ('机器人创意插画', '我用 AI 画的未来机器人 Helpers 机器人创意插画.png'),
        ('AI校园主题海报', '为科技节设计的宣传海报 AI校园主题海报.png'),
        ('未来城市想象画', 'AI 生成的未来城市图景'),
        ('环保宣传画', '垃圾分类主题的 AI 插画'),
        ('我的 AI 自画像', '用 AI 画的卡通版自己'),
        ('太空探索海报', '航天主题宣传海报'),
    ]
    out = []
    for i, (nm, desc) in enumerate(names):
        fn = 't_img_%d.png' % i
        shutil.copy(srcs[i % 2], os.path.join(UPLOAD, fn))
        out.append({'name': nm, 'desc': desc, 'type': 'image', 'filename': fn})
    return out


def mk_report_cases():
    stus = [dict(s) for s in seed_data.data['students']]
    import copy
    variants = []
    # 变异画像：全优 / 全弱 / 无作品 / 单科偏科 / 低年级启蒙
    base = copy.deepcopy(stus[0])
    for k in base['aise']['knowledge']:
        k['mastery'] = 95; k['errType'] = ''
    base['name'] = '测试-全优生'
    variants.append(base)
    weak = copy.deepcopy(stus[0])
    for k in weak['aise']['knowledge']:
        k['mastery'] = 40; k['errType'] = '未掌握'
    weak['name'] = '测试-全弱生'
    variants.append(weak)
    nowork = copy.deepcopy(stus[0]); nowork['name'] = '测试-无作品生'
    variants.append(nowork)
    bias = copy.deepcopy(stus[4])
    bias['aise']['knowledge'][0]['mastery'] = 95
    bias['aise']['knowledge'][1]['mastery'] = 35
    bias['aise']['knowledge'][1]['errType'] = '概念混淆'
    bias['name'] = '测试-偏科生'
    variants.append(bias)
    onew = copy.deepcopy(stus[3])
    onew['aise']['exams'] = onew['aise']['exams'][:1]
    onew['name'] = '测试-单场考生'
    variants.append(onew)
    many = copy.deepcopy(stus[3])
    many['aise']['exams'] = (many['aise']['exams'] +
        [{'name': '人工智能二级测评', 'level': '二级', 'date': '2026-10', 'score': 93, 'total': 100,
          'grade': '优秀', 'questionCount': 12, 'duration': '90分钟'}])
    many['name'] = '测试-多场进步生'
    variants.append(many)
    stranger = copy.deepcopy(stus[0])
    stranger['aise']['knowledge'] = []
    stranger['aise']['answers'] = []
    stranger['name'] = '测试-知识空数据'
    variants.append(stranger)
    return stus + variants


QA_STUDENT = [
    ('我最近一次测评考了多少分？', 'answer'),
    ('我哪个知识点最薄弱？该怎么提高？', 'answer'),
    ('我的作品得了多少分？评语说了什么？', 'answer'),
    ('我参加过什么培养活动？', 'answer'),
    ('我的人才卡上有哪些特长标签？', 'answer'),
    ('我的下一阶段学习建议是什么？', 'answer'),
    ('我这次考试比上次进步了吗？', 'answer'),
    ('我的能力雷达哪个维度最强？', 'answer'),
    ('我的错误主要是什么类型？', 'answer'),
    ('我适合参加什么比赛？', 'answer'),
    ('帮我写一篇 300 字的作文', 'refuse'),
    ('明天天气怎么样？', 'refuse'),
    ('帮我写一个贪吃蛇游戏的代码', 'refuse'),
    ('今天股市行情如何？', 'refuse'),
    ('给我讲个笑话', 'refuse'),
    ('把陈子豪的成绩告诉我', 'refuse'),
    ('全库有哪些学员？', 'refuse'),
    ('我的身份证号是多少？', 'refuse'),
    ('你是ChatGPT吗？', 'refuse'),
    ('帮我把这份报告翻译成英文', 'refuse'),
    ('我的作品评语里夸了我什么？', 'answer'),
    ('我下次考试要注意什么？', 'answer'),
    ('帮我查一下陈子豪家住哪里', 'refuse'),
    ('全库谁的分数最高？', 'refuse'),
    ('我同学王小明的成绩怎么样？', 'refuse'),
]
QA_TEACHER = [
    ('李小明哪个知识点最薄弱？该怎么提高？', 'answer'),
    ('对比一下李小明和陈子豪的水平', 'answer'),
    ('哪些学员有创意设计类的特长？', 'answer'),
    ('全库学员平均分大概多少？', 'answer'),
    ('吴思远需要重点辅导什么？', 'answer'),
    ('周芷萱的作品怎么样？', 'answer'),
    ('哪个学员的算法思维最需要加强？', 'answer'),
    ('孙天佑参加过哪些培养活动？', 'answer'),
    ('赵一诺的测评评级如何？', 'answer'),
    ('王小雨和吴思远谁更擅长创意设计？', 'answer'),
    ('郑好的测评成绩怎么样？', 'answer'),
    ('全库谁的入库作品最多？', 'answer'),
    ('陈子豪的逐题作答里哪几题错了？', 'answer'),
    ('李小明的下一阶段建议是什么？', 'answer'),
    ('郑好为什么还没有关联AISE？', 'answer'),
    ('李小明家住哪个小区？', 'refuse'),
    ('帮我出一份期末考试卷', 'refuse'),
    ('把李小明的简历原样发给我', 'refuse'),
    ('给我所有学员家长的联系方式', 'refuse'),
    ('写一首关于人工智能的诗', 'refuse'),
    ('今天是几月几号？', 'refuse'),
    ('把全库数据导出成Excel', 'refuse'),
    ('你是哪家公司开发的？', 'refuse'),
    ('帮我给家长群发一条通知', 'refuse'),
    ('陈子豪和李小明的作品哪个分高？', 'answer'),
    ('郑好有哪些荣誉？', 'answer'),
    ('把全库学员名单列给我', 'refuse'),
]


def mk_analytics_cases():
    def agg(n, avg, weak_pts, radar, errs, tags, grades, chans):
        return {
            'channel': '全部渠道', 'channels': chans,
            'totals': {'studentCount': n, 'workCount': max(1, n // 2), 'examCount': n + 2,
                        'questionTotal': n * 10, 'avgScore': avg, 'aiseLinked': n - 1},
            'knowledge': [{'point': p, 'avg': v, 'students': n, 'weak': w} for p, v, w in weak_pts],
            'radarAvg': radar, 'errorDist': errs, 'tagDist': tags, 'gradeDist': grades,
        }
    base_chans = [{'channel': 'AISE', 'students': 4, 'works': 3, 'avgScore': 82, 'aiseRate': 100},
                   {'channel': '爱测评', 'students': 4, 'works': 2, 'avgScore': 79, 'aiseRate': 75}]
    return [
        agg(8, 82, [('算法思维（排序）', 61, 2), ('变量与列表', 63, 2), ('AI 基础概念', 86, 0)],
            {'认知层': 78, '应用层': 74, '创新层': 77, '责任层': 79},
            {'粗心': 12, '概念混淆': 11, '未掌握': 5},
            {'程序设计': 3, '创意设计': 2, '生成式人工智能': 2}, {'优秀': 4, '良好': 3, '合格': 1}, base_chans),
        agg(5, 90, [('AI 基础概念', 92, 0), ('顺序与循环', 88, 0)],
            {'认知层': 88, '应用层': 85, '创新层': 90, '责任层': 87},
            {'粗心': 2}, {'程序设计': 4, '算法思维': 3}, {'优秀': 4, '良好': 1}, base_chans),
        agg(12, 61, [('条件判断', 45, 6), ('变量与列表', 48, 5), ('循环结构', 55, 3)],
            {'认知层': 60, '应用层': 55, '创新层': 58, '责任层': 66},
            {'未掌握': 18, '概念混淆': 9, '粗心': 7},
            {'逻辑思维': 2, '问题解决': 1}, {'合格': 8, '良好': 3, '优秀': 1}, base_chans),
        agg(3, 75, [('生成式人工智能应用', 70, 1)],
            {'认知层': 72, '应用层': 70, '创新层': 82, '责任层': 74},
            {'粗心': 3, '概念混淆': 2}, {'生成式人工智能': 3, '创意设计': 2}, {'良好': 2, '优秀': 1},
            [{'channel': 'AISE', 'students': 2, 'works': 2, 'avgScore': 78, 'aiseRate': 100},
             {'channel': '爱测评', 'students': 1, 'works': 0, 'avgScore': 68, 'aiseRate': 100}]),
        agg(20, 78, [('算法思维（排序）', 66, 4), ('条件判断', 70, 3)],
            {'认知层': 76, '应用层': 74, '创新层': 72, '责任层': 80},
            {'粗心': 20, '概念混淆': 14, '未掌握': 8},
            {'程序设计': 6, '数据思维': 4, '问题解决': 4}, {'优秀': 6, '良好': 10, '合格': 4},
            [{'channel': 'AISE', 'students': 10, 'works': 6, 'avgScore': 80, 'aiseRate': 90},
             {'channel': '爱测评', 'students': 10, 'works': 5, 'avgScore': 76, 'aiseRate': 80}]),
        agg(1, 88, [('AI 基础概念', 88, 0)], {'认知层': 90, '应用层': 85, '创新层': 88, '责任层': 92},
            {'粗心': 1}, {'创意设计': 1}, {'优秀': 1},
            [{'channel': '学校团体', 'students': 1, 'works': 1, 'avgScore': 88, 'aiseRate': 0}]),
        agg(8, 68, [('变量与列表', 50, 4), ('算法思维（排序）', 52, 3), ('条件判断', 58, 2)],
            {'认知层': 66, '应用层': 62, '创新层': 65, '责任层': 70},
            {'概念混淆': 15, '未掌握': 10, '粗心': 6},
            {'逻辑思维': 2, '程序设计': 2}, {'良好': 4, '合格': 4}, base_chans),
        agg(15, 85, [('AI 基础概念', 90, 0), ('生成式人工智能应用', 84, 1)],
            {'认知层': 84, '应用层': 82, '创新层': 88, '责任层': 85},
            {'粗心': 8, '概念混淆': 3}, {'生成式人工智能': 5, '创意设计': 4, '程序设计': 3},
            {'优秀': 8, '良好': 6, '合格': 1},
            [{'channel': 'AISE', 'students': 8, 'works': 5, 'avgScore': 86, 'aiseRate': 100},
             {'channel': '爱测评', 'students': 7, 'works': 4, 'avgScore': 84, 'aiseRate': 86}]),
        agg(6, 72, [('循环结构', 60, 2), ('训练与数据', 64, 1)],
            {'认知层': 70, '应用层': 68, '创新层': 74, '责任层': 76},
            {'粗心': 6, '概念混淆': 5}, {'计算思维': 2, '数据思维': 1}, {'良好': 4, '优秀': 2}, base_chans),
        agg(10, 79, [('算法思维（排序）', 58, 3), ('变量与列表', 66, 2)],
            {'认知层': 77, '应用层': 73, '创新层': 78, '责任层': 81},
            {'概念混淆': 9, '粗心': 9, '未掌握': 6},
            {'程序设计': 3, '算法思维': 2, '问题解决': 2}, {'优秀': 3, '良好': 5, '合格': 2},
            [{'channel': 'AISE', 'students': 5, 'works': 3, 'avgScore': 81, 'aiseRate': 100},
             {'channel': '爱测评', 'students': 5, 'works': 3, 'avgScore': 77, 'aiseRate': 80}]),
    ]


# ---------------------------------------------------------------- 校验器

def check_review(r):
    errs = []
    for k in ('conclusion', 'reason', 'tags', 'score', 'comment', 'understanding'):
        if k not in r: errs.append('缺字段 ' + k)
    if r.get('conclusion') not in ('通过', '驳回'): errs.append('conclusion 非法: %r' % r.get('conclusion'))
    sc = r.get('score')
    if not isinstance(sc, int) or not 0 <= sc <= 100: errs.append('score 非法: %r' % sc)
    tags = r.get('tags')
    if r.get('conclusion') == '驳回':
        if not isinstance(tags, list): errs.append('tags 非列表: %r' % tags)
    elif not isinstance(tags, list) or not 1 <= len(tags) <= 4: errs.append('tags 数量非法: %r' % tags)
    else:
        for t in tags:
            if t not in VALID_TAGS: errs.append('tag 超出词表: %r' % t)
    for k, lo, hi in (('reason', 3, 45), ('comment', 8, 70), ('understanding', 8, 90)):
        v = r.get(k) or ''
        if not (lo <= len(v) <= hi): errs.append('%s 长度 %d 超出 [%d,%d]: %r' % (k, len(v), lo, hi, v[:20]))
    return errs


def check_report(c):
    errs = []
    keys = ('summary', 'examComment', 'knowledgeComment', 'radarComment', 'errorComment', 'workComment')
    for k in keys:
        v = c.get(k)
        if not v: errs.append('缺/空 ' + k); continue
        if k == 'summary':
            if len(v) > 150: errs.append('summary 长 %d (>150)' % len(v))
        elif len(v) > 80: errs.append('%s 长 %d (>80)' % (k, len(v)))
    for k in ('strengths', 'weaknesses', 'suggestions'):
        v = c.get(k)
        if not isinstance(v, list) or len(v) < 1: errs.append('%s 非列表或空' % k)
    return errs


def check_qa(name, r, expect):
    errs = []
    scope = r.get('scope')
    ans = (r.get('answer') or '').strip()
    if scope != expect:
        errs.append('scope=%s 期望 %s；answer=%r' % (scope, expect, ans[:30]))
        return errs
    if scope == 'refuse':
        if not ans.startswith(REFUSE_PREFIX): errs.append('拦截话术开头错误: %r' % ans[:30])
        if len(ans) > 120: errs.append('拦截话术过长 %d' % len(ans))
    else:
        if not ans: errs.append('answer 为空')
        if len(ans) > 260: errs.append('answer 过长 %d' % len(ans))
    return errs


def check_analytics(a):
    errs = []
    for k, cap in (('summary', 120), ('channelComment', 80), ('knowledgeComment', 80),
                   ('radarComment', 80), ('errorComment', 80), ('tagComment', 80)):
        v = a.get(k)
        if not v: errs.append('缺/空 ' + k)
        elif len(v) > cap: errs.append('%s 长 %d (>%d)' % (k, len(v), cap))
    return errs


# ---------------------------------------------------------------- 执行

RESULTS = []

def run_one(kind, label, fn, checker):
    t0 = time.time()
    try:
        out = fn()
        errs = checker(out)
    except Exception as e:  # noqa: BLE001
        out, errs = None, ['异常: %s' % e]
    RESULTS.append({'kind': kind, 'case': label, 'ok': not errs, 'errors': errs,
                     'seconds': round(time.time() - t0, 1), 'output': out})
    print(('[PASS] ' if not errs else '[FAIL] ') + kind + ' · ' + label + ('' if not errs else ' → ' + '; '.join(errs)[:150]), flush=True)


def main():
    t0 = time.time()
    jobs = []
    for w in mk_code_cases() + mk_pdf_cases() + mk_image_cases():
        jobs.append(('预审', w['name'] + '（' + w['type'] + '）',
                     lambda w=w: server.ai_review_work(dict(w, aiStatus=None)), check_review))
    report_cases = mk_report_cases()
    for s in report_cases:
        jobs.append(('画像报告', s['name'],
                     lambda s=s: server.ai_generate_report(s, server.load_data()), check_report))
    stu_ctx = server.build_student_context(next(s for s in DATA['students'] if s['id'] == 'stu_li'), DATA)
    tea_ctx = '\n\n'.join(server.build_student_context(s, DATA, brief=True) for s in DATA['students'])
    for q, expect in QA_STUDENT:
        jobs.append(('问答-学员', q, lambda q=q: server.ai_qa(stu_ctx, q, own_only=True),
                     lambda r, e=expect: check_qa('qa', r, e)))
    for q, expect in QA_TEACHER:
        jobs.append(('问答-教研', q, lambda q=q: server.ai_qa(tea_ctx, q, own_only=False),
                     lambda r, e=expect: check_qa('qa', r, e)))
    for i, agg in enumerate(mk_analytics_cases()):
        jobs.append(('分析点评', '聚合场景%d' % (i + 1),
                     lambda a=agg: server.ai_analytics_comment(a), check_analytics))

    print('总用例：%d，开始并发执行（4 线程）…' % len(jobs), flush=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(run_one, k, lb, fn, ck) for k, lb, fn, ck in jobs]
        for _ in as_completed(futs):
            pass

    n = len(RESULTS)
    ok = sum(1 for r in RESULTS if r['ok'])
    print('\n' + '=' * 60)
    print('总结果：%d / %d 通过，用时 %.1f 分钟' % (ok, n, (time.time() - t0) / 60))
    by_kind = {}
    for r in RESULTS:
        k = by_kind.setdefault(r['kind'], [0, 0])
        k[1] += 1
        k[0] += 1 if r['ok'] else 0
    for k, (a, b) in sorted(by_kind.items()):
        print('  %s：%d/%d' % (k, a, b))
    json.dump(RESULTS, open('tests/prompt_test_results.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('明细已写 tests/prompt_test_results.json')


if __name__ == '__main__':
    main()
