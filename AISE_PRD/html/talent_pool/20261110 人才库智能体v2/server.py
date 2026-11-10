#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人才库智能体（AI人才大脑）演示 v2 —— 本地全链路 Demo 服务端
零第三方依赖（Python3 标准库），真实调用大模型（与 Hermes 同款 GLM）。

角色：学员/家长端 与 教研员端 分账号登录。
启动：python3 server.py  →  http://localhost:8090
模型配置读取：环境变量 GLM_API_KEY，或 ~/.hermes/.env
"""
import base64
import hashlib
import json
import mimetypes
import os
import re
import threading
import time
import urllib.request
import urllib.error
import zlib
from datetime import datetime
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WWW_DIR = os.path.join(BASE_DIR, 'www')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
DATA_PATH = os.path.join(BASE_DIR, 'data.json')
SAMPLES_DIR = os.path.join(BASE_DIR, 'samples')
os.makedirs(UPLOAD_DIR, exist_ok=True)

PORT = int(os.environ.get('PORT', '8090'))

# ---------------------------------------------------------------- 模型配置
GLM_BASE = os.environ.get('GLM_BASE', 'https://open.bigmodel.cn/api/coding/paas/v4')
TEXT_MODEL = os.environ.get('GLM_TEXT_MODEL', 'glm-5.3-flash')
VISION_MODEL = os.environ.get('GLM_VISION_MODEL', 'glm-4.5v')


def load_api_key():
    key = os.environ.get('GLM_API_KEY', '')
    if key:
        return key
    env_path = os.path.expanduser('~/.hermes/.env')
    if os.path.exists(env_path):
        for line in open(env_path, encoding='utf-8', errors='ignore'):
            line = line.strip()
            if line.startswith('GLM_API_KEY='):
                return line.split('=', 1)[1].strip()
    return ''


API_KEY = load_api_key()
MODEL_INFO = {'configured': bool(API_KEY), 'text_model': TEXT_MODEL, 'vision_model': VISION_MODEL}


def chat(messages, model=None, temperature=0.4, max_tokens=1500, image_b64=None, retries=2):
    """调用 GLM OpenAI 兼容接口；image_b64 提供时消息自动转为多模态。"""
    if not API_KEY:
        raise RuntimeError('未配置 GLM_API_KEY（环境变量或 ~/.hermes/.env）')
    msgs = []
    for m in messages:
        if image_b64 and m['role'] == 'user':
            msgs.append({'role': m['role'], 'content': [
                {'type': 'text', 'text': m['content']},
                {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + image_b64}},
            ]})
        else:
            msgs.append({'role': m['role'], 'content': m['content']})
    payload = {
        'model': model or TEXT_MODEL,
        'messages': msgs,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    req = urllib.request.Request(
        GLM_BASE + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'},
        method='POST')
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'] or ''
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError('模型调用失败：%s' % last_err)


def chat_stream(messages, model=None, temperature=0.4, max_tokens=1500):
    """流式调用 GLM（SSE），逐段 yield 增量文本。"""
    if not API_KEY:
        raise RuntimeError('未配置 GLM_API_KEY（环境变量或 ~/.hermes/.env）')
    payload = {
        'model': model or TEXT_MODEL,
        'messages': [{'role': m['role'], 'content': m['content']} for m in messages],
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stream': True,
    }
    req = urllib.request.Request(
        GLM_BASE + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'},
        method='POST')
    with urllib.request.urlopen(req, timeout=120) as resp:
        for raw_line in resp:
            line = raw_line.decode('utf-8').strip()
            if not line.startswith('data:'):
                continue
            body = line[5:].strip()
            if body == '[DONE]':
                break
            try:
                chunk = json.loads(body)
                delta = (chunk.get('choices') or [{}])[0].get('delta', {}).get('content')
            except Exception:  # noqa: BLE001
                delta = None
            if delta:
                yield delta


def extract_json(text):
    """从模型输出中提取 JSON（容忍 ``` 包裹与前后杂文字）。"""
    text = text.strip()
    m = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.S)
    if m:
        text = m.group(1)
    else:
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


# ---------------------------------------------------------------- 业务规则（提示词与输出契约，依据 PRD V1.1 第 4 章）

VALID_TAG_HINTS = '程序设计、生成式人工智能、算法思维、创意设计、逻辑思维、数据思维、计算思维、问题解决'
BAD_TAG_WORDS = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'py', 'js', 'java', 'c', 'cpp', 'html', 'css', 'txt', 'md',
                 '文件', '代码', '图片', '文档', '报告', '作品', '网页', '程序', '游戏', '海报', '插画', '未命名',
                 'image', 'code', 'file', 'project', 'untitled'}

REVIEW_SYSTEM = (
    '你是人工智能人才库的作品审核智能体，审核对象是中小学生的作品。'
    '请只输出 JSON（不要其他文字），字段：'
    '{"conclusion":"通过或驳回","reason":"一句话理由","tags":["标签1","标签2"],'
    '"score":0到100整数,"comment":"两句话评语","understanding":"对作品内容的理解摘要"}。'
    'tags 必须是人工智能教育方向的能力标签（如：%s），'
    '禁止使用文件格式（如PDF、PNG）、作品名称或文件名。'
    '评分锚点：60分=基本完成但质量一般；80分=完整且质量良好；90分以上=完整且有亮点创意。'
    '内容过于简单、残缺、明显敷衍的建议驳回。评语面向学生与家长，语气友好具体。'
) % VALID_TAG_HINTS

REPORT_SYSTEM = (
    '你是人工智能人才库的画像分析智能体，分析对象是中小学生。'
    '基于给定数据生成个人画像分析，只输出 JSON：'
    '{"summary":"120字内的总体评价，概括整体水平与最突出的特点",'
    '"examComment":"考试成绩表现的一句话小结",'
    '"knowledgeComment":"知识点掌握情况的一句话小结，点名最薄弱项",'
    '"radarComment":"四个能力维度表现的一句话小结",'
    '"errorComment":"错误归因的一句话小结，按错误类型给改进方向",'
    '"workComment":"入库作品表现的一句话小结",'
    '"strengths":["优势1"],"weaknesses":["短板1"],'
    '"suggestions":["建议1（附练习方向）","建议2"]}。'
    '各 comment 控制在 60 字内、面向家长的具体表述，不写空话。'
    '成长建议原则：优先补齐关键短板，难度递进，定期巩固，每条建议附可执行的练习方向；'
    '不含培训课程推销。语言面向小学生与家长，友好易懂。'
)

QA_SYSTEM_TMPL = (
    '你是人工智能人才库的问答助手，服务对象是中小学生及其家长与教研员。'
    '你只允许基于【人才库数据】回答问题，数据如下：\n【人才库数据】\n{context}\n\n'
    '规则：\n'
    '1. 只回答与人才库数据相关的问题（学员的测评成绩、逐题作答、知识点掌握情况、'
    '作品评价、成长画像、简历材料）。数据中没有的信息要如实说明人才库暂无相关记录，禁止编造。\n'
    '2. 与人才库无关的请求（写作文、写代码、做题、闲聊、时事新闻等一切代办或创作类请求）一律拒绝。\n'
    '3. 打探他人隐私（住址、联系方式、身份证号等）或要求生成不当内容的请求一律拒绝。\n'
    '4. 拒绝时输出 scope=refuse，answer 以「该问题超出人才库服务范围。」开头，'
    '随后一句话说明可提问的范围（测评成绩、知识点掌握、作品评价、成长建议）。\n'
    '5. 回答精炼友好（200字内），适合小学生与家长阅读。\n{extra}\n'
    '只输出 JSON：{{"scope":"answer或refuse","answer":"你的回答"}}'
)

QA_OWN_ONLY = (
    '6. 本次你是学员本人端的助手，数据中只有提问学员本人的记录：'
    '任何关于其他学员的问题、以及打探人才库里还有哪些学员的问题，一律拒绝（scope=refuse），'
    '且不得透露任何其他学员的信息。\n'
)


def clean_tags(tags, work_name=''):
    """标签强制过滤：剔除格式词/作品名/占位词，去重，单标签 2-12 字，最多 4 个。"""
    out, seen = [], set()
    name_lc = (work_name or '').lower()
    for t in tags or []:
        if not isinstance(t, str):
            continue
        t = t.strip()
        if not (2 <= len(t) <= 12):
            continue
        if t.lower() in BAD_TAG_WORDS:
            continue
        if t.lower() in name_lc or name_lc in t.lower():
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= 4:
            break
    return out


def extract_pdf_text(path):
    """尽力而为的 PDF 文本层抽取（FlateDecode 流内 Tj 文本）；失败返回空串。"""
    try:
        raw = open(path, 'rb').read()
        texts = []
        for m in re.finditer(rb'stream\r?\n(.*?)endstream', raw, re.S):
            chunk = m.group(1)
            try:
                chunk = zlib.decompress(chunk)
            except Exception:  # noqa: BLE001
                pass
            for tm in re.finditer(rb'\(((?:[^()\\]|\\.)*)\)\s*Tj', chunk):
                s = tm.group(1).decode('utf-8', errors='ignore')
                s = s.replace('\\(', '(').replace('\\)', ')').replace('\\\\', '\\')
                if s.strip():
                    texts.append(s)
        return ''.join(texts)[:6000]
    except Exception:  # noqa: BLE001
        return ''


def ai_review_work(work):
    """作品审核智能体：按类型差异化阅读 → 输出契约 JSON。"""
    name = work['name']
    desc = work.get('desc') or ''
    fpath = os.path.join(UPLOAD_DIR, work['filename'])
    try:
        if work['type'] == 'image':
            b64 = base64.b64encode(open(fpath, 'rb').read()).decode()
            user = ('请分析这幅图片作品（作品名：%s）。判断其作为中小学生人工智能学习成果的质量是否可以入库，'
                    '并从画面内容生成 2-4 个特长标签。作者描述：%s' % (name, desc))
            raw = chat([{'role': 'system', 'content': REVIEW_SYSTEM},
                        {'role': 'user', 'content': user}],
                       model=VISION_MODEL, image_b64=b64, max_tokens=2000)
        elif work['type'] == 'pdf':
            text = extract_pdf_text(fpath)
            user = '作品类型：PDF；作品名：%s。作者描述：%s。' % (name, desc)
            if text:
                user += '\nPDF 正文如下：\n' + text
            else:
                user += '\n（PDF 正文解析失败，请基于名称与描述判断）'
            raw = chat([{'role': 'system', 'content': REVIEW_SYSTEM},
                        {'role': 'user', 'content': user}])
        else:  # code
            code = open(fpath, encoding='utf-8', errors='ignore').read()[:8000]
            user = ('作品类型：代码；作品名：%s。作者描述：%s。代码内容如下：\n```\n%s\n```'
                    % (name, desc, code))
            raw = chat([{'role': 'system', 'content': REVIEW_SYSTEM},
                        {'role': 'user', 'content': user}])
        r = extract_json(raw)
        score = r.get('score', 0)
        try:
            score = max(0, min(100, int(score)))
        except Exception:  # noqa: BLE001
            score = 0
        return {
            'conclusion': '驳回' if r.get('conclusion') == '驳回' else '通过',
            'reason': r.get('reason', ''),
            'tags': clean_tags(r.get('tags'), name),
            'score': score,
            'comment': r.get('comment', ''),
            'understanding': r.get('understanding', ''),
        }
    except Exception as e:  # noqa: BLE001
        return {'error': str(e)}


def build_student_context(stu, data, brief=False):
    """组装单个学生的画像数据清单（画像分析 / 问答共用）。"""
    parts = ['学生：%s（%s，%s）' % (stu['name'], stu['grade'], stu['school'])]
    aise = stu.get('aise')
    if aise:
        ex = '; '.join('%s %s分/满分%s（%s）' % (e['name'], e['score'], e['total'], e['date']) for e in aise['exams'])
        parts.append('AISE 测评记录：' + ex)
        kn = '; '.join('%s 掌握%d%%%s' % (k['point'], k['mastery'], ('，错误类型：' + k['errType']) if k['errType'] else '')
                       for k in aise['knowledge'])
        parts.append('知识点掌握：' + kn)
        if not brief and aise.get('answers'):
            ans = '; '.join('%s：%s%s' % (a['q'], '答对' if a['result'] == '对' else '答错',
                                          ('（' + a['errType'] + '）') if a.get('errType') else '')
                            for a in aise['answers'])
            parts.append('最近一次测评逐题作答：' + ans)
    else:
        parts.append('AISE 测评记录：暂未关联 AISE 测评数据')
    works = [w for w in data['works'] if w['studentId'] == stu['id'] and w['status'] == 'approved']
    for w in works:
        arc = w.get('archive') or {}
        if arc:
            parts.append('入库作品《%s》：标签%s，%d分，评语：%s' % (w['name'], '、'.join(arc['tags']), arc['score'], arc['comment']))
    mats = []
    for mod, key in [('社会实践', 'social'), ('专利软著', 'patents'), ('其他荣誉', 'honors')]:
        for it in stu.get('materials', {}).get(key, []):
            if it.get('review') == 'approved':
                mats.append(it['name'] + ('（' + it['time'] + '，' + it['honor'] + '）' if it.get('time') else ''))
    if mats:
        parts.append('简历材料：' + '; '.join(mats))
    return '\n'.join(parts)


def ai_generate_report(stu, data):
    """画像分析智能体：数据清单 → 输出契约 JSON。"""
    ctx = build_student_context(stu, data)
    raw = chat([{'role': 'system', 'content': REPORT_SYSTEM},
                {'role': 'user', 'content': '请基于以下人才库数据生成画像分析：\n' + ctx}],
               max_tokens=3000)
    return extract_json(raw)


def ai_qa(context, question, own_only=False):
    sysmsg = QA_SYSTEM_TMPL.format(context=context, extra=QA_OWN_ONLY if own_only else '')
    raw = chat([{'role': 'system', 'content': sysmsg},
                {'role': 'user', 'content': question}], max_tokens=1200)
    try:
        r = extract_json(raw)
    except Exception:  # noqa: BLE001
        # 输出被截断等解析失败：提高预算重试一次，并要求精简回答
        raw = chat([{'role': 'system', 'content': sysmsg},
                    {'role': 'user', 'content': question + '（回答控制在 200 字内）'}], max_tokens=2500)
        r = extract_json(raw)
    scope = r.get('scope', 'refuse')
    if scope not in ('answer', 'refuse'):
        scope = 'refuse'
    answer = (r.get('answer') or '').strip()
    if scope == 'answer' and not answer:
        # scope=answer 但内容为空：再重试一次，仍为空则给默认口径
        try:
            raw = chat([{'role': 'system', 'content': sysmsg},
                        {'role': 'user', 'content': question + '（回答控制在 150 字内，直接给出答案）'}],
                       max_tokens=2000)
            r2 = extract_json(raw)
            answer = (r2.get('answer') or '').strip()
        except Exception:  # noqa: BLE001
            pass
        if not answer:
            answer = '人才库中暂时没有能回答这个问题的记录。'
    return {'scope': scope, 'answer': answer}


QA_STREAM_TMPL = (
    '你是人工智能人才库的问答助手，服务对象是中小学生及其家长与教研员。'
    '你只允许基于【人才库数据】回答问题，数据如下：\n【人才库数据】\n{context}\n\n'
    '规则：\n'
    '1. 只回答与人才库数据相关的问题（学员的测评成绩、逐题作答、知识点掌握情况、'
    '作品评价、成长画像、简历材料）。数据中没有的信息要如实说明人才库暂无相关记录，禁止编造。\n'
    '2. 与人才库无关的请求（写作文、写代码、做题、闲聊、时事新闻等一切代办或创作类请求）一律拒绝。\n'
    '3. 打探他人隐私（住址、联系方式、身份证号等）或要求生成不当内容的请求一律拒绝。\n'
    '4. 拒绝时第一行输出 [SCOPE:refuse]，正文以「该问题超出人才库服务范围。」开头，'
    '随后一句话说明可提问的范围（测评成绩、知识点掌握、作品评价、成长建议）。\n'
    '5. 回答精炼友好（200字内），适合小学生与家长阅读。\n{extra}\n'
    '输出格式（严格遵守）：第一行输出且仅输出 [SCOPE:answer] 或 [SCOPE:refuse]，'
    '随后另起一行直接输出回答正文。不要 JSON，不要代码块，不要任何额外说明。'
)


def ai_qa_stream(context, question, own_only=False):
    """流式问答：先 yield {'type':'scope'}，再逐段 yield {'type':'delta'}，最后 {'type':'done'}。"""
    sysmsg = QA_STREAM_TMPL.format(context=context, extra=QA_OWN_ONLY if own_only else '')
    msgs = [{'role': 'system', 'content': sysmsg}, {'role': 'user', 'content': question}]
    buf = ''
    scope = None
    emitted = False
    try:
        for delta in chat_stream(msgs, max_tokens=1200):
            buf += delta
            if scope is None:
                m = re.match(r'^\s*\[SCOPE:(answer|refuse)\]', buf)
                if m:
                    scope = m.group(1)
                    yield {'type': 'scope', 'scope': scope}
                    rest = buf[m.end():]
                    if rest.strip('\n'):
                        emitted = True
                        yield {'type': 'delta', 'text': rest.lstrip('\n')}
                elif len(buf) > 24:
                    break  # 开头不符合契约 → 放弃流式，走兜底
            else:
                emitted = True
                yield {'type': 'delta', 'text': delta}
    except Exception:  # noqa: BLE001
        if scope is None:
            raise
        yield {'type': 'delta', 'text': '\n（输出中断）'}
    if scope is None:
        # 兜底：非流式老链路（scope/answer JSON 契约，含截断重试）
        r = ai_qa(context, question, own_only=own_only)
        yield {'type': 'scope', 'scope': r['scope']}
        if r['answer']:
            emitted = True
            yield {'type': 'delta', 'text': r['answer']}
        scope = r['scope']
    if scope == 'answer' and not emitted:
        yield {'type': 'delta', 'text': '人才库中暂时没有能回答这个问题的记录。'}
    yield {'type': 'done', 'scope': scope}


def qa_stream_response(handler, ctx, q, own_only, role_label):
    """以 SSE 形式把流式问答写回客户端。"""
    handler.send_response(200)
    handler.send_header('Content-Type', 'text/event-stream; charset=utf-8')
    handler.send_header('Cache-Control', 'no-cache')
    handler.send_header('Connection', 'close')
    handler.end_headers()

    def send(obj):
        handler.wfile.write(('data: ' + json.dumps(obj, ensure_ascii=False) + '\n\n').encode('utf-8'))
        handler.wfile.flush()

    scope_label_answer = role_label
    scope_final = 'answer'
    try:
        for ev in ai_qa_stream(ctx, q, own_only=own_only):
            if ev['type'] == 'scope':
                scope_final = ev['scope']
                send({'t': 'scope', 'scope': ev['scope']})
            elif ev['type'] == 'delta':
                send({'t': 'delta', 'text': ev['text']})
            else:
                send({'t': 'done', 'scopeLabel': scope_label_answer if scope_final == 'answer' else '已拦截'})
    except Exception as e:  # noqa: BLE001
        send({'t': 'error', 'message': '模型调用失败：%s' % e})
    # 记录问答日志
    try:
        data = load_data()
        data.setdefault('qaLog', []).append({'time': now_str(), 'role': 'teacher' if role_label == '全库数据' else 'student', 'q': q, 'scope': scope_final})
        save_data(data)
    except Exception:  # noqa: BLE001
        pass


ANALYTICS_AI_TMPL = (
    '你是人工智能人才库的数据分析智能体，面向教研员解读渠道学员的整体数据看板。'
    '基于给定聚合数据，只输出 JSON：'
    '{"summary":"80字内的整体解读（覆盖规模、水平、突出特点）",'
    '"channelComment":"渠道对比的一句话解读",'
    '"knowledgeComment":"知识点掌握的一句话解读，点名最薄弱的知识点",'
    '"radarComment":"能力维度均值的一句话解读",'
    '"errorComment":"错误归因的一句话解读，给教学改进方向",'
    '"tagComment":"作品特长标签分布的一句话解读"}。'
    '各字段 60 字内，客观具体、有洞察（如对比、归因、可执行建议），不写空话，不推销课程。'
)


ANALYTICS_CACHE_PATH = os.path.join(BASE_DIR, 'analytics_cache.json')


def _analytics_fp(out):
    """数据指纹：聚合结果变化即缓存失效。"""
    key = json.dumps({k: out[k] for k in ('totals', 'knowledge', 'radarAvg', 'errorDist', 'tagDist', 'gradeDist', 'channels')},
                     ensure_ascii=False, sort_keys=True)
    return hashlib.md5(key.encode('utf-8')).hexdigest()[:16]


def analytics_cache_get(out):
    try:
        cache = json.load(open(ANALYTICS_CACHE_PATH, encoding='utf-8'))
        return cache.get(_analytics_fp(out))
    except Exception:  # noqa: BLE001
        return None


def analytics_cache_put(out, ai):
    try:
        cache = {}
        if os.path.exists(ANALYTICS_CACHE_PATH):
            cache = json.load(open(ANALYTICS_CACHE_PATH, encoding='utf-8'))
        cache[_analytics_fp(out)] = ai
        with open(ANALYTICS_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:  # noqa: BLE001
        pass


def ai_analytics_comment(out):
    agg = {
        '范围': out['channel'], '总量': out['totals'], '渠道对比': out['channels'],
        '知识点掌握': out['knowledge'], '能力均值': out['radarAvg'],
        '错误归因': out['errorDist'], '作品标签分布': out['tagDist'], '评级分布': out['gradeDist'],
    }
    raw = chat([{'role': 'system', 'content': ANALYTICS_AI_TMPL},
                {'role': 'user', 'content': json.dumps(agg, ensure_ascii=False)}], max_tokens=1500)
    r = extract_json(raw)
    for k in ('summary', 'channelComment', 'knowledgeComment', 'radarComment', 'errorComment', 'tagComment'):
        r.setdefault(k, '')
    return r


def compute_analytics(data, channel):
    stus = [s for s in data['students'] if not channel or s.get('channel') == channel]
    rows = []
    for stu in stus:
        approved = [w for w in data['works'] if w['studentId'] == stu['id'] and w['status'] == 'approved']
        aise = stu.get('aise') or {}
        exams = aise.get('exams') or []
        kn = aise.get('knowledge') or []
        scores = [e['score'] for e in exams]
        weak = [k['point'] for k in kn if k['mastery'] < 60]
        rows.append({
            'id': stu['id'], 'name': stu['name'], 'grade': stu['grade'], 'school': stu['school'],
            'channel': stu.get('channel') or '未标注', 'aiseLinked': bool(stu.get('aise')),
            'examCount': len(exams), 'totalQuestions': sum(e.get('questionCount', 0) for e in exams),
            'avgExamScore': round(sum(scores) / len(scores)) if scores else None,
            'bestScore': max(scores) if scores else None,
            'weakPoints': weak, 'workCount': len(approved),
            'workAvg': round(sum((w.get('archive') or {}).get('score', 0) for w in approved) / len(approved)) if approved else None,
            'tags': stu['card']['tags'],
        })
    # 聚合
    all_scores = [r['avgExamScore'] for r in rows if r['avgExamScore'] is not None]
    exam_total = sum(r['examCount'] for r in rows)
    q_total = sum(r['totalQuestions'] for r in rows)
    work_rows = [w for w in data['works'] if w['status'] == 'approved'
                 and any(r['id'] == w['studentId'] for r in rows)]
    # 知识点聚合
    kn_agg = {}
    for stu in stus:
        for k in (stu.get('aise') or {}).get('knowledge') or []:
            a = kn_agg.setdefault(k['point'], {'sum': 0, 'n': 0, 'weak': 0})
            a['sum'] += k['mastery']; a['n'] += 1
            if k['mastery'] < 60: a['weak'] += 1
    knowledge = [{'point': p, 'avg': round(v['sum'] / v['n']), 'students': v['n'], 'weak': v['weak']}
                  for p, v in sorted(kn_agg.items(), key=lambda x: -(x[1]['sum'] / x[1]['n']))]
    # 雷达均值
    radar_sums = {}
    for stu in stus:
        for k, v in (stu['card'].get('radar') or {}).items():
            radar_sums.setdefault(k, []).append(v)
    radarAvg = {k: round(sum(v) / len(v)) for k, v in radar_sums.items()}
    # 错误归因
    err_map = {}
    for stu in stus:
        for k in (stu.get('aise') or {}).get('knowledge') or []:
            if k.get('errType'): err_map[k['errType']] = err_map.get(k['errType'], 0) + 1
        for a in (stu.get('aise') or {}).get('answers') or []:
            if a.get('result') == '错' and a.get('errType'):
                err_map[a['errType']] = err_map.get(a['errType'], 0) + 1
    # 标签分布（入库作品 + 人才卡）
    tag_dist = {}
    for w in work_rows:
        for t in (w.get('archive') or {}).get('tags', []):
            tag_dist[t] = tag_dist.get(t, 0) + 1
    grade_dist = {}
    for stu in stus:
        for e in (stu.get('aise') or {}).get('exams') or []:
            grade_dist[e.get('grade', '其他')] = grade_dist.get(e.get('grade', '其他'), 0) + 1
    # 渠道对比
    channels = []
    for ch in sorted({s.get('channel') or '未标注' for s in data['students']}):
        cs = [s for s in data['students'] if (s.get('channel') or '未标注') == ch]
        cworks = [w for w in data['works'] if w['status'] == 'approved' and w['studentId'] in {x['id'] for x in cs}]
        cscores = []
        for s in cs:
            for e in (s.get('aise') or {}).get('exams') or []:
                cscores.append(e['score'])
        channels.append({'channel': ch, 'students': len(cs), 'works': len(cworks),
                          'avgScore': round(sum(cscores) / len(cscores)) if cscores else None,
                          'aiseRate': round(100 * sum(1 for x in cs if x.get('aise')) / len(cs))})
    return {
        'channel': channel or '全部渠道', 'channels': channels,
        'totals': {'studentCount': len(stus), 'workCount': len(work_rows),
                    'examCount': exam_total, 'questionTotal': q_total,
                    'avgScore': round(sum(all_scores) / len(all_scores)) if all_scores else None,
                    'aiseLinked': sum(1 for s in stus if s.get('aise'))},
        'students': rows, 'knowledge': knowledge, 'radarAvg': radarAvg,
        'errorDist': err_map, 'tagDist': tag_dist, 'gradeDist': grade_dist,
    }


# ---------------------------------------------------------------- 数据读写

_data_lock = threading.Lock()


def load_data():
    with _data_lock:
        return json.load(open(DATA_PATH, encoding='utf-8'))


def save_data(data):
    with _data_lock:
        tmp = DATA_PATH + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_PATH)


def reset_data():
    import importlib.util
    spec = importlib.util.spec_from_file_location('seed_data', os.path.join(BASE_DIR, 'seed_data.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = {
        'users': mod.data['users'], 'sessions': {}, 'students': mod.data['students'],
        'works': mod.data['works'], 'reports': mod.data['reports'], 'qaLog': [],
    }
    save_data(data)
    return data


def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def run_review(work_id):
    """后台预审线程：更新 aiStatus 与 ai 结论；失败置 failed（降级人工）。"""
    data = load_data()
    work = next((w for w in data['works'] if w['id'] == work_id), None)
    if not work:
        return
    result = ai_review_work(work)
    data = load_data()
    work = next((w for w in data['works'] if w['id'] == work_id), None)
    if not work:
        return
    if 'error' in result:
        work['aiStatus'] = 'failed'
        work['aiError'] = result['error']
    else:
        work['aiStatus'] = 'done'
        work['ai'] = result
    save_data(data)


def run_report(student_id):
    data = load_data()
    stu = next((s for s in data['students'] if s['id'] == student_id), None)
    if not stu:
        return
    try:
        content = ai_generate_report(stu, data)
        data = load_data()
        data.setdefault('reports', {})[student_id] = {
            'generatedAt': now_str(), 'model': TEXT_MODEL, 'content': content}
        save_data(data)
    except Exception as e:  # noqa: BLE001
        data = load_data()
        data.setdefault('reports', {})[student_id] = {
            'generatedAt': now_str(), 'model': TEXT_MODEL, 'error': str(e)}
        save_data(data)


# ---------------------------------------------------------------- multipart 解析（标准库实现）

def parse_multipart(body, boundary):
    """返回 (fields: dict, files: list[{field,filename,data}])"""
    fields, files = {}, []
    delim = b'--' + boundary
    for part in body.split(delim):
        part = part.strip(b'\r\n')
        if not part or part == b'--':
            continue
        if b'\r\n\r\n' not in part:
            continue
        head, _, content = part.partition(b'\r\n\r\n')
        headers = head.decode('utf-8', errors='ignore')
        name_m = re.search(r'name="([^"]*)"', headers)
        if not name_m:
            continue
        name = name_m.group(1)
        file_m = re.search(r'filename="([^"]*)"', headers)
        if file_m:
            files.append({'field': name, 'filename': os.path.basename(file_m.group(1)), 'data': content})
        else:
            fields[name] = content.decode('utf-8', errors='ignore')
    return fields, files


# ---------------------------------------------------------------- HTTP Handler

EXT_TYPE = {'.py': 'code', '.js': 'code', '.java': 'code', '.c': 'code', '.cpp': 'code',
            '.html': 'code', '.css': 'code', '.txt': 'code', '.md': 'code',
            '.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.webp': 'image', '.pdf': 'pdf'}
MAX_SIZE = 10 * 1024 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = 'TalentPoolDemo/2.0'

    def log_message(self, format, *args):  # noqa: A002,N803
        pass  # 安静模式

    # ---- 基础输出 ----
    def send_json(self, obj, status=200, set_cookie=None):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        if set_cookie:
            self.send_header('Set-Cookie', set_cookie)
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path):
        if not os.path.isfile(path):
            self.send_json({'error': 'not found'}, 404)
            return
        ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        ext = os.path.splitext(path)[1]
        charset_map = {'.html': 'text/html; charset=utf-8',
                        '.css': 'text/css; charset=utf-8',
                        '.js': 'application/javascript; charset=utf-8'}
        if ext in charset_map:
            ctype = charset_map[ext]
        body = open(path, 'rb').read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    # ---- 会话 ----
    def current_user(self):
        c = cookies.SimpleCookie(self.headers.get('Cookie', ''))
        sid = c['sid'].value if 'sid' in c else None
        if not sid:
            return None
        data = load_data()
        return data['sessions'].get(sid)

    def read_body_json(self):
        n = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(n).decode('utf-8')) if n else {}

    def read_body_multipart(self):
        n = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(n)
        ct = self.headers.get('Content-Type', '')
        m = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', ct)
        if not m:
            return None, None
        boundary = (m.group(1) or m.group(2)).strip()
        return parse_multipart(body, boundary.encode('utf-8'))

    # ---- 路由 ----
    def do_GET(self):  # noqa: N802
        path = self.path.split('?')[0]
        try:
            if not path.startswith('/api/'):
                if path == '/':
                    path = '/login.html'
                self.send_file(os.path.join(WWW_DIR, path.lstrip('/').replace('..', '')))
                return
            self.handle_api('GET', path)
        except Exception as e:  # noqa: BLE001
            self.send_json({'error': str(e)}, 500)

    def do_POST(self):  # noqa: N802
        path = self.path.split('?')[0]
        try:
            self.handle_api('POST', path)
        except Exception as e:  # noqa: BLE001
            self.send_json({'error': str(e)}, 500)

    def handle_api(self, method, path):
        user = self.current_user()
        data = load_data()

        # ---- 公开接口 ----
        if method == 'GET' and path == '/api/meta':
            return self.send_json({'model': MODEL_INFO, 'port': PORT})
        if method == 'POST' and path == '/api/login':
            body = self.read_body_json()
            u = next((x for x in data['users'] if x['user'] == body.get('user')
                      and x['password'] == body.get('password')), None)
            if not u:
                return self.send_json({'error': '账号或密码不正确'}, 401)
            sid = 's%d' % int(time.time() * 1000)
            data['sessions'][sid] = {'user': u['user'], 'role': u['role'],
                                      'studentId': u.get('studentId'), 'label': u['label']}
            save_data(data)
            return self.send_json({'ok': True, 'role': u['role']},
                                  set_cookie='sid=%s; Path=/' % sid)
        if method == 'POST' and path == '/api/logout':
            c = cookies.SimpleCookie(self.headers.get('Cookie', ''))
            if 'sid' in c:
                data['sessions'].pop(c['sid'].value, None)
                save_data(data)
            return self.send_json({'ok': True}, set_cookie='sid=; Path=/; Max-Age=0')
        if not user:
            return self.send_json({'error': '未登录'}, 401)

        # ---- 通用 ----
        if method == 'GET' and path == '/api/me':
            return self.send_json({'user': user['user'], 'role': user['role'],
                                    'label': user['label'], 'studentId': user.get('studentId')})

        # ---- 学员/家长端 ----
        if user['role'] == 'student':
            sid_ = user['studentId']
            if method == 'GET' and path == '/api/student/works':
                mine = [w for w in data['works'] if w['studentId'] == sid_]
                out = [{'id': w['id'], 'name': w['name'], 'desc': w['desc'], 'type': w['type'],
                        'status': w['status'], 'submittedAt': w['submittedAt'],
                        'reason': (w.get('review') or {}).get('reason', '') if w['status'] == 'rejected' else '',
                        'tags': (w.get('archive') or {}).get('tags', []) if w['status'] == 'approved' else []}
                       for w in sorted(mine, key=lambda x: x['submittedAt'], reverse=True)]
                return self.send_json({'works': out})
            if method == 'GET' and path == '/api/student/profile':
                stu = next(s for s in data['students'] if s['id'] == sid_)
                approved = [w for w in data['works'] if w['studentId'] == sid_ and w['status'] == 'approved']
                card_tags = list(dict.fromkeys(
                    sum([list((w.get('archive') or {}).get('tags', [])) for w in approved], []))) or stu['card']['tags']
                return self.send_json({'student': public_student(stu, full=True), 'cardTags': card_tags,
                                        'works': [{'name': w['name'], 'tags': (w.get('archive') or {}).get('tags', []),
                                                   'score': (w.get('archive') or {}).get('score'), 'comment': (w.get('archive') or {}).get('comment')}
                                                  for w in approved]})
            if method == 'POST' and path == '/api/works':
                fields, files = self.read_body_multipart()
                if fields is None:
                    return self.send_json({'error': '请求格式错误'}, 400)
                name = (fields.get('name') or '').strip()
                desc = (fields.get('desc') or '').strip()
                f = next((x for x in files if x['field'] == 'file'), None)
                if not name:
                    return self.send_json({'error': '请填写作品名称'}, 400)
                if not f or not f['filename']:
                    return self.send_json({'error': '请选择作品文件'}, 400)
                if len(f['data']) > MAX_SIZE:
                    return self.send_json({'error': '文件大小不能超过 10MB'}, 400)
                ext = os.path.splitext(f['filename'])[1].lower()
                wtype = EXT_TYPE.get(ext)
                if not wtype:
                    return self.send_json({'error': '以下文件格式不支持：%s' % (ext or '（无扩展名）')}, 400)
                wid = 'w_%d' % int(time.time() * 1000)
                safe_store = '%s_%s' % (wid, f['filename'])
                open(os.path.join(UPLOAD_DIR, safe_store), 'wb').write(f['data'])
                work = {'id': wid, 'studentId': sid_, 'name': name, 'desc': desc, 'type': wtype,
                         'filename': safe_store, 'origName': f['filename'],
                         'status': 'reviewing', 'aiStatus': 'processing', 'ai': None,
                         'submittedAt': now_str()}
                data['works'].append(work)
                save_data(data)
                threading.Thread(target=run_review, args=(wid,), daemon=True).start()
                return self.send_json({'ok': True, 'work': {'id': wid, 'status': 'reviewing'}})
            if method == 'GET' and path == '/api/student/report':
                stu = next(s for s in data['students'] if s['id'] == sid_)
                if stu.get('aise') is None:
                    return self.send_json({'empty': True})
                rep = data.get('reports', {}).get(sid_)
                return self.send_json({'report': rep, 'student': public_student(stu, full=True)})
            if method == 'POST' and path == '/api/student/report/generate':
                stu = next(s for s in data['students'] if s['id'] == sid_)
                if stu.get('aise') is None:
                    return self.send_json({'empty': True})
                threading.Thread(target=run_report, args=(sid_,), daemon=True).start()
                return self.send_json({'ok': True, 'generating': True})
            if method == 'POST' and path == '/api/qa/stream':
                body = self.read_body_json()
                q = (body.get('question') or '').strip()
                if not q:
                    return self.send_json({'error': '请输入问题'}, 400)
                stu = next(s for s in data['students'] if s['id'] == sid_)
                ctx = build_student_context(stu, data)
                qa_stream_response(self, ctx, q, own_only=True, role_label='本人数据')
                return None
            if method == 'POST' and path == '/api/qa':
                body = self.read_body_json()
                q = (body.get('question') or '').strip()
                if not q:
                    return self.send_json({'error': '请输入问题'}, 400)
                stu = next(s for s in data['students'] if s['id'] == sid_)
                ctx = build_student_context(stu, data)
                r = ai_qa(ctx, q, own_only=True)
                data.setdefault('qaLog', []).append({'time': now_str(), 'role': 'student', 'q': q, 'scope': r['scope']})
                save_data(data)
                r['scopeLabel'] = '本人数据' if r['scope'] == 'answer' else '已拦截'
                return self.send_json(r)

        # ---- 教研员端 ----
        if user['role'] == 'teacher':
            if method == 'GET' and path == '/api/admin/queue':
                out = []
                for w in sorted(data['works'], key=lambda x: x['submittedAt'], reverse=True):
                    stu = student_by_id(data, w['studentId'])
                    out.append({'id': w['id'], 'name': w['name'], 'student': stu['name'],
                                 'studentId': w['studentId'], 'type': w['type'], 'submittedAt': w['submittedAt'],
                                 'status': w['status'], 'aiStatus': w['aiStatus'],
                                 'aiSummary': ai_summary(w)})
                return self.send_json({'works': out})
            if method == 'GET' and path.startswith('/api/admin/work/'):
                wid = path.rsplit('/', 1)[-1]
                w = next((x for x in data['works'] if x['id'] == wid), None)
                if not w:
                    return self.send_json({'error': '作品不存在'}, 404)
                stu = student_by_id(data, w['studentId'])
                preview = work_preview(w)
                return self.send_json({'work': w, 'student': {'name': stu['name'], 'grade': stu['grade'], 'school': stu['school']},
                                        'preview': preview})
            if method == 'POST' and path == '/api/admin/review':
                body = self.read_body_json()
                w = next((x for x in data['works'] if x['id'] == body.get('id')), None)
                if not w or w['status'] != 'reviewing':
                    return self.send_json({'error': '作品不存在或已审完'}, 400)
                action = body.get('action')
                if action == 'approve':
                    arc = w.get('ai') or {}
                    w['archive'] = {'tags': arc.get('tags', []), 'score': arc.get('score', 0), 'comment': arc.get('comment', '')}
                    w['review'] = {'by': user['label'], 'action': '确认通过', 'reason': '', 'at': now_str()}
                    w['status'] = 'approved'
                elif action == 'approve_modified':
                    tags = clean_tags(body.get('tags', []), w['name'])
                    w['archive'] = {'tags': tags, 'score': clamp_score(body.get('score')),
                                     'comment': (body.get('comment') or '').strip()}
                    w['review'] = {'by': user['label'], 'action': '修改后通过', 'reason': '', 'at': now_str(),
                                    'edited': True}
                    w['status'] = 'approved'
                elif action == 'reject':
                    reason = (body.get('reason') or '').strip()
                    if not reason:
                        return self.send_json({'error': '驳回必须填写原因'}, 400)
                    w['review'] = {'by': user['label'], 'action': '驳回', 'reason': reason, 'at': now_str()}
                    w['status'] = 'rejected'
                else:
                    return self.send_json({'error': '未知操作'}, 400)
                w['reviewedAt'] = now_str()
                # 通过则更新人才卡标签（合并去重）+ 重置画像报告触发重新生成提示
                if w['status'] == 'approved':
                    stu = student_by_id(data, w['studentId'])
                    merged = list(dict.fromkeys(
                        list(stu['card']['tags']) + list(w['archive']['tags'])))[:6]
                    stu['card']['tags'] = merged
                save_data(data)
                return self.send_json({'ok': True})
            if method == 'POST' and path == '/api/admin/repreview':
                body = self.read_body_json()
                w = next((x for x in data['works'] if x['id'] == body.get('id')), None)
                if not w:
                    return self.send_json({'error': '作品不存在'}, 404)
                w['aiStatus'] = 'processing'
                w['ai'] = None
                save_data(data)
                threading.Thread(target=run_review, args=(w['id'],), daemon=True).start()
                return self.send_json({'ok': True})
            if method == 'GET' and path == '/api/admin/library':
                out = []
                for stu in data['students']:
                    approved = [w for w in data['works'] if w['studentId'] == stu['id'] and w['status'] == 'approved']
                    out.append({'id': stu['id'], 'name': stu['name'], 'grade': stu['grade'], 'school': stu['school'],
                                 'aiseLinked': bool(stu.get('aise')), 'workCount': len(approved),
                                 'tags': stu['card']['tags']})
                return self.send_json({'students': out})
            if method == 'GET' and path.startswith('/api/admin/student/'):
                stid = path.rsplit('/', 1)[-1]
                stu = next((s for s in data['students'] if s['id'] == stid), None)
                if not stu:
                    return self.send_json({'error': '学员不存在'}, 404)
                works = [w for w in data['works'] if w['studentId'] == stid and w['status'] == 'approved']
                return self.send_json({'student': public_student(stu, full=True),
                                        'works': [{'name': w['name'], 'archive': w.get('archive')} for w in works]})
            if method == 'POST' and path == '/api/qa/stream':
                body = self.read_body_json()
                q = (body.get('question') or '').strip()
                if not q:
                    return self.send_json({'error': '请输入问题'}, 400)
                ctx = '\n\n'.join(build_student_context(s, data, brief=len(data['students']) > 2) for s in data['students'])
                qa_stream_response(self, ctx, q, own_only=False, role_label='全库数据')
                return None
            if method == 'POST' and path == '/api/qa':
                body = self.read_body_json()
                q = (body.get('question') or '').strip()
                if not q:
                    return self.send_json({'error': '请输入问题'}, 400)
                ctx = '\n\n'.join(build_student_context(s, data, brief=len(data['students']) > 2) for s in data['students'])
                r = ai_qa(ctx, q)
                data.setdefault('qaLog', []).append({'time': now_str(), 'role': 'teacher', 'q': q, 'scope': r['scope']})
                save_data(data)
                r['scopeLabel'] = '全库数据' if r['scope'] == 'answer' else '已拦截'
                return self.send_json(r)
            if method == 'GET' and path == '/api/admin/analytics':
                from urllib.parse import parse_qs, urlparse
                qs = parse_qs(urlparse(self.path).query)
                channel = (qs.get('channel') or [''])[0]
                out = compute_analytics(data, channel)
                cached = analytics_cache_get(out)
                if cached:
                    out['ai'] = cached
                return self.send_json(out)
            if method == 'POST' and path == '/api/admin/analytics/ai-comment':
                body = self.read_body_json()
                channel = (body.get('channel') or '').strip()
                out = compute_analytics(data, channel)
                ai = analytics_cache_get(out)
                if not ai:
                    try:
                        ai = ai_analytics_comment(out)
                        analytics_cache_put(out, ai)
                    except Exception as e:  # noqa: BLE001
                        return self.send_json({'error': 'AI 点评生成失败：%s' % e}, 500)
                return self.send_json({'ai': ai})
            if method == 'GET' and path.startswith('/api/admin/report/'):
                stid = path.rsplit('/', 1)[-1]
                stu = next((s for s in data['students'] if s['id'] == stid), None)
                if not stu:
                    return self.send_json({'error': '学员不存在'}, 404)
                if stu.get('aise') is None:
                    return self.send_json({'empty': True, 'student': public_student(stu, full=True)})
                return self.send_json({'report': data.get('reports', {}).get(stid),
                                        'student': public_student(stu, full=True)})
            if method == 'POST' and path == '/api/admin/report/generate':
                body = self.read_body_json()
                stid = body.get('studentId')
                stu = next((s for s in data['students'] if s['id'] == stid), None)
                if not stu:
                    return self.send_json({'error': '学员不存在'}, 404)
                if stu.get('aise') is None:
                    return self.send_json({'empty': True})
                threading.Thread(target=run_report, args=(stid,), daemon=True).start()
                return self.send_json({'ok': True, 'generating': True})
            if method == 'POST' and path == '/api/demo/reset':
                sessions = data.get('sessions', {})
                reset_data()
                fresh = load_data()
                fresh['sessions'] = sessions  # 保留当前登录会话，避免演示中被踢回登录页
                save_data(fresh)
                # 预置队列中「预审中」的作品触发真实预审，演示时能看到结论出来
                for w in fresh['works']:
                    if w.get('aiStatus') == 'processing':
                        threading.Thread(target=run_review, args=(w['id'],), daemon=True).start()
                return self.send_json({'ok': True})
            if method == 'POST' and path == '/api/demo/toggle_aise':
                stu = next(s for s in data['students'] if s['id'] == 'stu_li')
                stu['aise'] = None if stu['aise'] else build_default_aise()
                save_data(data)
                return self.send_json({'aiseLinked': bool(stu['aise'])})

        return self.send_json({'error': '无权访问该接口'}, 403)


def build_default_aise():
    """从种子模块取 pristine AISE 数据（运行时 data.json 里的可能已被演示开关置空）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location('seed_data', os.path.join(BASE_DIR, 'seed_data.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    stu = next(s for s in mod.data['students'] if s['id'] == 'stu_li')
    return json.loads(json.dumps(stu['aise'], ensure_ascii=False))


def student_by_id(data, sid_):
    return next(s for s in data['students'] if s['id'] == sid_)


def public_student(stu, full=False):
    d = {'id': stu['id'], 'name': stu['name'], 'grade': stu['grade'], 'school': stu['school'],
         'aiseLinked': bool(stu.get('aise')), 'card': stu['card'], 'materials': stu.get('materials', {}),
         'basic': stu.get('basic', {})}
    if full:
        d['aise'] = stu.get('aise')
    return d


def ai_summary(w):
    a = w.get('ai')
    if not a:
        return ''
    return '%s · %d分 · %s' % (a['conclusion'], a['score'], '、'.join(a['tags']) or '无标签')


def clamp_score(v):
    try:
        return max(0, min(100, int(v)))
    except Exception:  # noqa: BLE001
        return 0


def work_preview(w):
    """作品原文预览信息。"""
    fpath = os.path.join(UPLOAD_DIR, w['filename'])
    if not os.path.isfile(fpath):
        sp = os.path.join(SAMPLES_DIR, w['filename'])
        if os.path.isfile(sp):
            fpath = sp
        else:
            return {'kind': 'none'}
    if w['type'] == 'image':
        b64 = base64.b64encode(open(fpath, 'rb').read()).decode()
        return {'kind': 'image', 'b64': b64}
    if w['type'] == 'pdf':
        return {'kind': 'pdf', 'text': extract_pdf_text(fpath)[:2000],
                 'url': '/api/none'}
    code = open(fpath, encoding='utf-8', errors='ignore').read()[:6000]
    return {'kind': 'code', 'text': code}


if __name__ == '__main__':
    if not os.path.exists(DATA_PATH):
        reset_data()
    print('人才库智能体 Demo v2 启动：http://localhost:%d' % PORT)
    print('模型：%s（图片 %s）｜ key %s' % (TEXT_MODEL, VISION_MODEL, '已配置' if API_KEY else '未配置！'))
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
