#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人才库智能体（AI人才大脑1.0）Demo 本地服务端
仅 Python3 标准库，零依赖。启动：python3 server.py
模式：
  - 真实模式：项目目录 .env 中配置 DEEPSEEK_API_KEY 时，智能体预审真实调用 DeepSeek V4 Flash
  - Mock 模式：未配置 key 时，返回显式标注「模拟结果」的预设结论，全链路照常演示
共享时请勿附带 .env 文件（见 README）。
"""
import json, os, re, base64, time, threading, uuid, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urlreq, error as urlerr

ROOT = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(ROOT, 'www')
DATA_FILE = os.path.join(ROOT, 'data.json')


# ---------- 配置 ----------
def load_env():
    env = {}
    p = os.path.join(ROOT, '.env')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()
API_KEY = ENV.get('DEEPSEEK_API_KEY') or os.environ.get('DEEPSEEK_API_KEY') or ''
TEXT_MODEL = ENV.get('DEEPSEEK_MODEL', 'deepseek-v4-flash')
VISION_MODEL = ENV.get('DEEPSEEK_VISION_MODEL', 'deepseek-v4-flash-vision-exp')
PORT = int(ENV.get('PORT') or os.environ.get('PORT') or 8080)
MODE = 'real' if API_KEY else 'mock'

MAX_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXT = {
    'code': ['py', 'js', 'java', 'c', 'cpp', 'html', 'css', 'txt', 'md'],
    'image': ['png', 'jpg', 'jpeg', 'webp'],
    'pdf': ['pdf'],
}
CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
    '.pdf': 'application/pdf', '.py': 'text/plain; charset=utf-8',
    '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8',
    '.java': 'text/plain; charset=utf-8', '.c': 'text/plain; charset=utf-8',
    '.cpp': 'text/plain; charset=utf-8',
}

# 模拟的 AISE 测评数据（已关联用户的画像分析数据源；真实平台由研发对接）
AISE_BASE = {
    'name': '李小明',
    'exam_records': [
        {'module': '智能工具实操', 'level': '三级', 'date': '2026-03-15'},
        {'module': '程序设计', 'level': '二级', 'date': '2025-11-02'},
        {'module': '生成式人工智能', 'level': '二级', 'date': '2026-05-24'},
    ],
    'answer_stats': [
        {'topic': '程序设计基础', 'mastery': 78, 'error': '粗心'},
        {'topic': '数据结构', 'mastery': 55, 'error': '未掌握'},
        {'topic': '算法思维', 'mastery': 66, 'error': '概念混淆'},
        {'topic': '生成式AI工具使用', 'mastery': 84, 'error': '粗心'},
        {'topic': '提示词工程', 'mastery': 61, 'error': '概念混淆'},
    ],
}

DB = {
    'works': [], 'materials': [], 'audits': [],
    'aise_linked': True, 'report': None, 'radar': None,
}
LOCK = threading.Lock()


def save():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(DB, f, ensure_ascii=False, indent=1)


def load():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding='utf-8') as f:
                DB = json.load(f)
        except Exception:
            pass


# ---------- 大模型 ----------
def chat(messages, model=None, temperature=0.4, image_b64=None):
    """OpenAI 兼容接口调用（DeepSeek）。失败抛异常。"""
    if not API_KEY:
        raise RuntimeError('未配置 DEEPSEEK_API_KEY')
    model = model or TEXT_MODEL
    msgs = [dict(m) for m in messages]
    if image_b64:
        mime = 'image/png'
        msgs.append({
            'role': 'user',
            'content': [{'type': 'image_url', 'image_url': {'url': 'data:%s;base64,%s' % (mime, image_b64)}}],
        })
    body = json.dumps({'model': model, 'messages': msgs, 'temperature': temperature,
                       'max_tokens': 2000}).encode('utf-8')
    req = urlreq.Request('https://api.deepseek.com/chat/completions', data=body, headers={
        'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY})
    with urlreq.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode('utf-8'))['choices'][0]['message']['content']


# 标签清洗：过滤非能力标签（文件格式、作品名、通用占位词）
BAD_TAGS = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'py', 'js', 'java', 'c', 'cpp', 'html', 'css',
            'txt', 'md', 'doc', 'docx', 'ppt', 'pptx', '未命名', 'unnamed', 'untitled', '作品',
            '文件', '代码', '图片', '文档', 'image', 'code', 'file'}


def sanitize_tags(tags, work=None):
    """清洗 AI 生成标签：去重、去格式词/作品名/占位词、限长。"""
    out = []
    name = (work or {}).get('name', '')
    stem = ((work or {}).get('filename', '') or '').rsplit('.', 1)[0]
    for t in tags or []:
        t = str(t).strip()
        if not t:
            continue
        if t.lower() in BAD_TAGS:
            continue
        if name and (t == name or (len(t) > 1 and t in name)):
            continue
        if stem and (t == stem or (len(t) > 1 and t in stem)):
            continue
        if len(t) < 2 or len(t) > 12:
            continue
        if t not in out:
            out.append(t)
    return out[:4]


def extract_json(text):
    """容错提取 LLM 输出中的 JSON 对象。"""
    m = re.search(r'\{[\s\S]*\}', text)
    if not m:
        raise ValueError('未找到 JSON：' + text[:200])
    return json.loads(m.group(0))


# ---------- 智能体预审（真实） ----------
def real_review(work):
    typ = work['type']
    desc = work.get('desc') or ''
    name = work['name']
    if typ == 'image':
        # 图片走视觉模型：用文件名+描述提示，图片以 data URL 附上
        user_msg = ('请分析这幅图片作品（作品名：%s）。判断其作为中小学生人工智能学习成果'
                    '的质量是否可以入库，并从画面内容生成 2-4 个特长标签。' % name)
        if desc:
            user_msg += ' 作者描述：' + desc
        sys_msg = ('你是人工智能人才库的作品审核智能体。请只输出 JSON（不要其他文字），字段：'
                   '{"conclusion":"通过或驳回","reason":"一句话理由","tags":["标签1","标签2"],'
                   '"score":0到100整数,"comment":"两句话评语","understanding":"对作品内容的理解摘要"}。'
                   'tags 必须是人工智能教育方向的能力标签（如：程序设计、生成式人工智能、算法思维、'
                   '创意设计、逻辑思维），禁止使用文件格式（如PDF）、作品名称或文件名。')
        try:
            raw = chat([{'role': 'system', 'content': sys_msg},
                        {'role': 'user', 'content': user_msg}],
                       model=VISION_MODEL, image_b64=work['content_b64'])
        except Exception:
            # 视觉模型不可用则降级：仅凭文字信息分析
            raw = chat([{'role': 'system', 'content': sys_msg},
                        {'role': 'user', 'content': user_msg + '（图片内容无法读取，请基于名称与描述判断）'}])
        return extract_json(raw)
    content = ''
    if typ == 'code':
        try:
            content = base64.b64decode(work['content_b64']).decode('utf-8', errors='replace')
        except Exception:
            pass
        content = content[:8000]
        user_msg = ('作品类型：代码；作品名：%s。' % name)
        if desc:
            user_msg += '作者描述：%s。' % desc
        user_msg += '代码内容如下：\n```\n%s\n```' % content if content else ('代码内容无法读取，请基于名称与描述判断：' + name)
    else:  # pdf
        # Demo 阶段 PDF 不解析正文（生产环境由研发实现文本层/OCR 解析），基于名称与描述分析
        user_msg = ('作品类型：PDF；作品名：%s。' % name)
        if desc:
            user_msg += '作者描述：%s。' % desc
        user_msg += '（Demo 环境不解析 PDF 正文，请基于名称与描述判断）'
    sys_msg = ('你是人工智能人才库的作品审核智能体。请只输出 JSON（不要其他文字），字段：'
               '{"conclusion":"通过或驳回","reason":"一句话理由","tags":["标签1","标签2"],'
               '"score":0到100整数,"comment":"两句话评语","understanding":"对作品内容的理解摘要"}。'
               'tags 必须是人工智能教育方向的能力标签（如：程序设计、生成式人工智能、算法思维、'
               '创意设计、逻辑思维），禁止使用文件格式（如PDF）、作品名称或文件名。')
    return extract_json(chat([{'role': 'system', 'content': sys_msg},
                              {'role': 'user', 'content': user_msg}]))


# ---------- 智能体预审（模拟） ----------
def mock_review(work):
    samples = {
        'code': {'conclusion': '通过', 'reason': '代码结构完整、逻辑清晰，具备基本可运行性',
                 'tags': ['程序设计', '逻辑思维'], 'score': 82,
                 'comment': '代码规范，函数拆分合理，注释完整；建议补充异常处理与边界条件测试。',
                 'understanding': '一个命令行计算器程序：实现加减乘除四则运算、循环交互与输入校验，约 60 行代码。'},
        'image': {'conclusion': '通过', 'reason': '画面内容完整、主题清晰，构图合理',
                  'tags': ['生成式人工智能', '创意设计'], 'score': 76,
                  'comment': '主题表达明确，风格统一；细节层次可再丰富。',
                  'understanding': '一幅生成式 AI 创作的数字插画：以校园人工智能课堂为主题，包含机器人助教与学生互动元素。'},
        'pdf': {'conclusion': '通过', 'reason': '文档结构完整，章节组织清晰',
                'tags': ['技术写作', '总结归纳'], 'score': 70,
                'comment': '结构清晰、要点完整；排版细节可再优化。',
                'understanding': '一份项目学习总结文档：包含项目背景、实现过程、成果展示与反思四部分。'},
    }
    r = dict(samples.get(work['type'], samples['pdf']))
    r['mock'] = True
    r['reason'] = '【模拟结果】' + r['reason']
    r['comment'] = '【模拟结果】' + r['comment']
    r['understanding'] = '【模拟结果】' + r['understanding']
    return r


def review_work(work):
    with LOCK:
        work['status'] = 'reviewing'
        save()
    try:
        time.sleep(2)  # 模拟异步耗时
        result = real_review(work) if MODE == 'real' else mock_review(work)
        result.setdefault('mock', False)
        # 标签清洗：只保留人工智能教育方向的能力标签
        result['tags'] = sanitize_tags(result.get('tags'), work)
        with LOCK:
            work['ai'] = result
            work['status'] = 'ai_done'
            save()
    except Exception as e:
        with LOCK:
            work['ai_error'] = str(e)[:300]
            work['status'] = 'ai_failed'
            save()


def mock_material_check(m):
    text = json.dumps(m['fields'], ensure_ascii=False)
    issues = []
    mtime = (m['fields'].get('时间') or '')
    if mtime:
        mm = re.match(r'^(\d{4})年(?:(\d{1,2})月)?$', mtime)
        if not mm:
            issues.append('时间格式不规范（建议如"2025年8月"）')
        else:
            if int(mm.group(1)) > 2027:
                issues.append('时间疑似晚于当前，请核对')
            if mm.group(2) and not (1 <= int(mm.group(2)) <= 12):
                issues.append('月份不规范（应为 1-12）')
    if re.search(r'\d{17,18}[0-9Xx]', text) or re.search(r'1[3-9]\d{9}', text):
        issues.append('内容疑似包含证件号/手机号等敏感信息，请注意脱敏')
    ok = not issues
    return {'conclusion': '通过' if ok else '驳回', 'issues': issues,
            'comment': '【模拟结果】字段填写规范，与档案记录一致。' if ok else '【模拟结果】发现问题：' + '；'.join(issues),
            'mock': True}


def real_material_check(m):
    text = json.dumps(m['fields'], ensure_ascii=False)
    sys_msg = ('你是人才库简历材料审核智能体。仅检查：规范性（必填完整、时间格式如"2025年8月"）、'
               '一致性（与档案矛盾）、敏感信息（证件号/手机号）。无法验证真实性。'
               '请只输出 JSON：{"conclusion":"通过或驳回","issues":["问题1"],"comment":"一句话意见"}')
    return extract_json(chat([{'role': 'system', 'content': sys_msg},
                              {'role': 'user', 'content': '材料字段：' + text}]))


def check_material(m):
    with LOCK:
        m['status'] = 'checking'
        save()
    try:
        time.sleep(1.5)
        r = real_material_check(m) if MODE == 'real' else mock_material_check(m)
        r.setdefault('mock', False)
        with LOCK:
            m['ai'] = r
            m['status'] = 'ai_done'
            save()
    except Exception as e:
        with LOCK:
            m['ai_error'] = str(e)[:300]
            m['status'] = 'ai_failed'
            save()


# ---------- 画像分析 ----------
def build_radar():
    """能力雷达：四维。基础 AISE 数据 + 已通过作品评价的加成。"""
    works = [w for w in DB['works'] if w.get('status') == 'approved']
    base = {'认知层': 68, '应用层': 74, '创新层': 62, '责任层': 80}
    if works:
        avg = sum((w['review'].get('score') or 70) for w in works) / len(works)
        base['应用层'] = min(100, base['应用层'] + int((avg - 70) / 6))
        base['创新层'] = min(100, base['创新层'] + len(works) * 2)
        base['认知层'] = min(100, base['认知层'] + len(works))
    return {k: min(100, max(0, v)) for k, v in base.items()}


def mock_report(radar):
    tags = approved_tags()
    works = [w for w in DB['works'] if w.get('status') == 'approved']
    ws = ('已入库作品 %d 件，集中于：%s。' % (len(works), '、'.join(tags))) if works else '暂未入库作品。'
    return {
        'mock': True,
        'summary': '【模拟结果】李小明同学人工智能基础扎实，应用能力突出。' + ws +
                   '综合画像显示：应用层与责任层表现良好，认知层与创新层为相对短板，建议加强算法思维训练与创新实践。',
        'strengths': ['生成式AI工具使用熟练（掌握度 84%）', '程序设计基础扎实（掌握度 78%）', '实践活动参与积极'],
        'weaknesses': ['数据结构掌握不足（55%）：错误多因知识点未掌握', '算法思维存在概念混淆（66%）'],
        'suggestions': ['优先补齐数据结构短板：结合编程练习巩固基础概念', '算法思维按难度递进训练：先熟练基础算法再进阶',
                        '定期巩固：每月完成 1 次综合练习并复盘错题', '创新层提升方向：参与项目创作类实践活动'],
    }


def real_report(radar):
    tags = approved_tags()
    works = [w for w in DB['works'] if w.get('status') == 'approved']
    evals = [{'name': w['name'], 'tags': sanitize_tags((w['review'] or {}).get('tags', []), w),
              'score': (w['review'] or {}).get('score'), 'comment': (w['review'] or {}).get('comment')} for w in works]
    data = {
        '测评记录': AISE_BASE['exam_records'],
        '知识点统计': AISE_BASE['answer_stats'],
        '能力雷达': radar,
        '特长标签': tags,
        '已入库作品评价': evals,
        '简历材料': [m['fields'] for m in DB['materials'] if m.get('status') == 'approved'],
    }
    sys_msg = ('你是人工智能人才库的画像分析智能体。基于给定数据生成个人画像分析，只输出 JSON：'
               '{"summary":"150字内的总体画像","strengths":["优势1"],"weaknesses":["短板1"],'
               '"suggestions":["建议1","建议2"]}')
    return extract_json(chat([{'role': 'system', 'content': sys_msg},
                              {'role': 'user', 'content': json.dumps(data, ensure_ascii=False)[:6000]}]))


def approved_tags():
    tags = []
    for w in DB['works']:
        if w.get('status') == 'approved':
            for t in sanitize_tags((w.get('review') or {}).get('tags', []), w):
                if t not in tags:
                    tags.append(t)
    return tags


def generate_report(force=False):
    with LOCK:
        if DB['report'] and not force:
            return DB['report']
        radar = build_radar()
        DB['radar'] = radar
        if not DB['aise_linked']:
            DB['report'] = {'linked': False}
        else:
            try:
                r = real_report(radar) if MODE == 'real' else mock_report(radar)
                r.setdefault('mock', False)
                r['linked'] = True
                r['generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                DB['report'] = r
            except Exception as e:
                DB['report'] = {'linked': True, 'error': str(e)[:300]}
        save()
        return DB['report']


# ---------- HTTP ----------
class Handler(BaseHTTPRequestHandler):
    server_version = 'TalentPoolDemo/1.0'

    def log_message(self, format, *args):
        pass  # 安静模式

    def send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode('utf-8'))
        except Exception:
            return None

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/health':
            return self.send_json({'mode': MODE, 'model': TEXT_MODEL, 'port': PORT,
                                   'vision_model': VISION_MODEL})
        if path == '/api/works':
            return self.send_json(user_view())
        if path == '/api/admin/works':
            return self.send_json(admin_view())
        if path == '/api/admin/materials':
            return self.send_json(DB['materials'])
        if path == '/api/materials':
            return self.send_json(material_user_view())
        if path == '/api/audits':
            return self.send_json(DB['audits'])
        if path == '/api/profile':
            return self.send_json(self.profile())
        if path.startswith('/api/admin/works/') and len(path.split('/')) == 5:
            wid = path.split('/')[-1]
            with LOCK:
                w = next((x for x in DB['works'] if x['id'] == wid), None)
            return self.send_json(w if w else {'error': 'not found'}, 200 if w else 404)
        if path.startswith('/api/files/'):
            return self.serve_file_content(path.split('/')[-1])
        return self.serve_static(path)

    def do_POST(self):
        path = self.path.split('?')[0]
        body = self.read_body()
        if body is None:
            return self.send_json({'error': '请求体不是合法 JSON'}, 400)
        if path == '/api/works':
            return self.create_work(body)
        if path == '/api/materials':
            return self.create_material(body)
        if path == '/api/profile/report':
            generate_report(force=True)
            return self.send_json(self.profile())
        if path == '/api/admin/link':
            with LOCK:
                DB['aise_linked'] = bool(body.get('linked'))
                DB['report'] = None
                save()
            return self.send_json({'linked': DB['aise_linked']})
        if path == '/api/admin/reset':
            with LOCK:
                DB['works'] = []
                DB['materials'] = []
                DB['audits'] = []
                DB['report'] = None
                save()
            return self.send_json({'ok': True})
        m = re.match(r'^/api/admin/works/([^/]+)/review$', path)
        if m:
            return self.review_work_api(m.group(1), body)
        m = re.match(r'^/api/admin/works/([^/]+)/retry$', path)
        if m:
            return self.retry_work(m.group(1))
        m = re.match(r'^/api/admin/materials/([^/]+)/review$', path)
        if m:
            return self.review_material_api(m.group(1), body)
        return self.send_json({'error': 'not found'}, 404)

    # ---- 业务 ----
    def create_work(self, body):
        name = (body.get('name') or '').strip()
        typ = body.get('type') or ''
        desc = (body.get('desc') or '').strip()
        filename = (body.get('filename') or '').strip()
        content_b64 = body.get('content_b64') or ''
        if not name:
            return self.send_json({'error': '请填写作品名称'}, 400)
        if typ not in ALLOWED_EXT:
            return self.send_json({'error': '作品类型仅支持：代码 / 图片 / PDF'}, 400)
        if not filename or not content_b64:
            return self.send_json({'error': '请选择作品文件'}, 400)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in ALLOWED_EXT[typ]:
            return self.send_json({'error': '以下文件格式不支持：.%s' % ext}, 400)
        try:
            raw = base64.b64decode(content_b64)
        except Exception:
            return self.send_json({'error': '文件内容解析失败'}, 400)
        if len(raw) > MAX_SIZE:
            return self.send_json({'error': '文件大小不能超过 10MB'}, 400)
        w = {'id': uuid.uuid4().hex[:12], 'name': name, 'type': typ, 'desc': desc,
             'filename': filename, 'size': len(raw), 'content_b64': content_b64,
             'status': 'pending', 'created': time.strftime('%Y-%m-%d %H:%M:%S'),
             'ai': None, 'ai_error': None, 'review': None}
        with LOCK:
            DB['works'].insert(0, w)
            save()
        threading.Thread(target=review_work, args=(w,), daemon=True).start()
        return self.send_json(user_item(w))

    def retry_work(self, wid):
        with LOCK:
            w = next((x for x in DB['works'] if x['id'] == wid), None)
            if not w:
                return self.send_json({'error': 'not found'}, 404)
            w['status'] = 'pending'
            w['ai_error'] = None
            save()
        threading.Thread(target=review_work, args=(w,), daemon=True).start()
        return self.send_json({'ok': True})

    def review_work_api(self, wid, body):
        action = body.get('action')
        if action not in ('approve', 'reject'):
            return self.send_json({'error': 'action 仅支持 approve / reject'}, 400)
        with LOCK:
            w = next((x for x in DB['works'] if x['id'] == wid), None)
            if not w:
                return self.send_json({'error': 'not found'}, 404)
            review = {'action': action, 'reason': (body.get('reason') or '').strip(),
                      'tags': body.get('tags') if isinstance(body.get('tags'), list) else [],
                      'score': body.get('score'),
                      'comment': (body.get('comment') or '').strip(),
                      'reviewer': '管理员', 'time': time.strftime('%Y-%m-%d %H:%M:%S')}
            # 人工未修改标签时，默认采纳 AI 生成的标签
            if action == 'approve' and not review['tags'] and w.get('ai') and w['ai'].get('tags'):
                review['tags'] = list(w['ai']['tags'])
            prev = json.dumps({'ai': w.get('ai'), 'review': w.get('review')}, ensure_ascii=False)
            w['review'] = review
            w['status'] = 'approved' if action == 'approve' else 'rejected'
            DB['audits'].append({'time': review['time'], 'actor': 'admin', 'target': 'work',
                                 'work_id': wid, 'work_name': w['name'], 'action': action,
                                 'before': prev, 'after': json.dumps(review, ensure_ascii=False)})
            if action == 'approve':
                DB['report'] = None  # 画像数据变化，报告缓存失效
            save()
        return self.send_json({'ok': True})

    def create_material(self, body):
        module = body.get('module') or ''
        fields = body.get('fields') or {}
        if module not in ('practice', 'patent', 'honor'):
            return self.send_json({'error': '模块仅支持：社会实践/专利软著/其他荣誉'}, 400)
        m = {'id': uuid.uuid4().hex[:10], 'module': module, 'fields': fields,
             'status': 'checking', 'ai': None, 'ai_error': None,
             'created': time.strftime('%Y-%m-%d %H:%M:%S'), 'review': None}
        with LOCK:
            DB['materials'].insert(0, m)
            save()
        threading.Thread(target=check_material, args=(m,), daemon=True).start()
        return self.send_json({'ok': True, 'id': m['id']})

    def review_material_api(self, mid, body):
        action = body.get('action')
        if action not in ('approve', 'reject'):
            return self.send_json({'error': 'action 仅支持 approve / reject'}, 400)
        with LOCK:
            m = next((x for x in DB['materials'] if x['id'] == mid), None)
            if not m:
                return self.send_json({'error': 'not found'}, 404)
            m['review'] = {'action': action, 'time': time.strftime('%Y-%m-%d %H:%M:%S')}
            m['status'] = 'approved' if action == 'approve' else 'rejected'
            save()
        return self.send_json({'ok': True})

    def profile(self):
        with LOCK:
            linked = DB['aise_linked']
            tags = approved_tags()
            works = [{'name': w['name'], 'type': w['type'],
                      'score': w['review'].get('score') if w['review'] else None}
                     for w in DB['works'] if w.get('status') == 'approved']
        return {'linked': linked, 'tags': tags, 'works': works,
                'radar': DB.get('radar') or build_radar(),
                'report': DB.get('report') or generate_report()}

    # ---- 视图 ----
    def serve_static(self, path):
        if path == '/':
            path = '/index.html'
        rel = path.lstrip('/')
        fp = os.path.normpath(os.path.join(WWW, rel))
        if not fp.startswith(WWW) or not os.path.isfile(fp):
            return self.send_json({'error': 'not found'}, 404)
        ext = os.path.splitext(fp)[1].lower()
        data = open(fp, 'rb').read()
        self.send_response(200)
        self.send_header('Content-Type', CONTENT_TYPES.get(ext, 'application/octet-stream'))
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_file_content(self, wid):
        with LOCK:
            w = next((x for x in DB['works'] if x['id'] == wid), None)
        if not w:
            return self.send_json({'error': 'not found'}, 404)
        ext = os.path.splitext(w['filename'])[1].lower()
        ctype = CONTENT_TYPES.get(ext, 'application/octet-stream')
        if w['type'] == 'code':
            ctype = 'text/plain; charset=utf-8'
        data = base64.b64decode(w['content_b64'])
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        # RFC 5987 编码文件名，支持中文文件名
        from urllib.parse import quote
        self.send_header('Content-Disposition', "inline; filename*=UTF-8''" + quote(w['filename']))
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


# 前台状态映射：只暴露 审核中 / 审核完成 / 未通过（决策 #9/#11）
def user_status(w):
    if w['status'] in ('pending', 'reviewing', 'ai_done', 'ai_failed'):
        return '审核中'
    if w['status'] == 'approved':
        return '审核完成'
    if w['status'] == 'rejected':
        return '未通过'
    return w['status']


def user_item(w):
    return {'id': w['id'], 'name': w['name'], 'type': w['type'],
            'status': user_status(w),
            'reject_reason': (w['review'] or {}).get('reason', '') if w['status'] == 'rejected' else '',
            'created': w['created']}


def user_view():
    return [user_item(w) for w in DB['works']]


def admin_view():
    out = []
    for w in DB['works']:
        item = user_item(w)
        item['status'] = w['status']
        item['ai'] = w['ai']
        item['ai_error'] = w['ai_error']
        item['desc'] = w.get('desc', '')
        item['filename'] = w['filename']
        item['size'] = w['size']
        out.append(item)
    return out


def material_user_view():
    out = []
    for m in DB['materials']:
        if m['status'] in ('approved', 'rejected'):
            out.append({'id': m['id'], 'module': m['module'], 'fields': m['fields'],
                        'status': '已通过' if m['status'] == 'approved' else '未通过'})
        else:
            out.append({'id': m['id'], 'module': m['module'], 'fields': m['fields'], 'status': '审核中'})
    return out


def main():
    load()
    print('=' * 52)
    print('  人才库智能体 Demo 服务端')
    print('  模式：%s（%s）' % ('真实模式' if MODE == 'real' else 'Mock 模拟模式',
                              TEXT_MODEL if MODE == 'real' else '未配置 DEEPSEEK_API_KEY'))
    print('  地址：http://localhost:%d' % PORT)
    print('    - 用户端：http://localhost:%d/         （作品上传 / 我的作品）' % PORT)
    print('    - 人才卡：http://localhost:%d/card.html' % PORT)
    print('    - 画像分析：http://localhost:%d/report.html' % PORT)
    print('    - 后台审核：http://localhost:%d/admin.html' % PORT)
    print('  Ctrl+C 停止服务')
    print('=' * 52)
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止')


if __name__ == '__main__':
    main()
