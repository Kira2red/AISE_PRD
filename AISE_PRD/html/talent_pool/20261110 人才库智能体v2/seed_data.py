# -*- coding: utf-8 -*-
"""生成演示种子数据 data.json（首次启动时若无数据则调用本脚本逻辑）"""
import json, os, time
from datetime import datetime, timedelta

NOW = datetime.now()

def ts(days_ago, h=10, m=30):
    t = NOW - timedelta(days=days_ago)
    return t.strftime('%Y-%m-%d') + ' %02d:%02d:00' % (h, m)

students = [
    {
        "id": "stu_li",
        "name": "李小明",
        "grade": "四年级",
        "school": "阳光小学",
        "channel": "爱测评",
        "aiseLinked": True,
        "basic": {
            "gender": "男",
            "birth": "2015年3月12日",
            "hometown": "北京市海淀区",
            "idCardMasked": "110108********0011",
            "joinTime": "2026年2月",
            "cardNo": "AISE-RL-2026-000118"
        },
        "card": {
            "tags": ["程序设计", "逻辑思维"],
            "radar": {"认知层": 82, "应用层": 74, "创新层": 88, "责任层": 90}
        },
        "aise": {
            "exams": [
                {"name": "人工智能启蒙级测评", "level": "启蒙级", "date": "2026-05", "score": 88, "total": 100, "grade": "优秀", "questionCount": 10, "duration": "45分钟"},
                {"name": "人工智能一级测评", "level": "一级", "date": "2026-09", "score": 82, "total": 100, "grade": "良好", "questionCount": 10, "duration": "60分钟"}
            ],
            "activities": [
                {"name": "技术融合应用", "date": "2026年3月12日", "result": "合格"},
                {"name": "创新实践评定", "date": "2026年6月20日", "result": "合格"},
                {"name": "生成式人工智能应用实践", "date": "2026年10月18日", "result": "良好"}
            ],
            "knowledge": [
                {"point": "AI 基础概念", "mastery": 85, "errType": ""},
                {"point": "顺序与循环", "mastery": 92, "errType": ""},
                {"point": "条件判断", "mastery": 75, "errType": "粗心"},
                {"point": "变量与列表", "mastery": 58, "errType": "未掌握"},
                {"point": "算法思维（排序）", "mastery": 45, "errType": "概念混淆"}
            ],
            "answers": [
                {"q": "第1题·单选：什么是人工智能", "result": "对", "errType": ""},
                {"q": "第2题·单选：生活中的人工智能应用", "result": "对", "errType": ""},
                {"q": "第3题·单选：循环结构的执行次数", "result": "对", "errType": ""},
                {"q": "第4题·判断：传感器是机器的“眼睛”", "result": "对", "errType": ""},
                {"q": "第5题·单选：条件判断语句的作用", "result": "错", "errType": "粗心"},
                {"q": "第6题·填空：变量赋值结果", "result": "对", "errType": ""},
                {"q": "第7题·填空：列表的索引从几开始", "result": "错", "errType": "概念混淆"},
                {"q": "第8题·单选：冒泡排序的基本思想", "result": "错", "errType": "概念混淆"},
                {"q": "第9题·实操：编写猜数字游戏循环", "result": "对", "errType": ""},
                {"q": "第10题·判断：人工智能会代替所有人", "result": "错", "errType": "未掌握"}
            ]
        },
        "materials": {
            "social": [
                {"name": "区青少年宫 AI 冬令营", "time": "2026年1月", "honor": "优秀营员", "review": "approved"}
            ],
            "patents": [],
            "honors": [
                {"name": "校科技节创意编程比赛", "time": "2026年6月", "honor": "二等奖", "review": "approved"}
            ]
        }
    },
    {
        "id": "stu_wang",
        "name": "王小雨",
        "grade": "五年级",
        "school": "实验小学",
        "channel": "爱测评",
        "aiseLinked": False,
        "basic": {"gender": "女", "birth": "2014年11月2日", "hometown": "北京市朝阳区",
                   "idCardMasked": "110105********0226", "joinTime": "2026年3月", "cardNo": "AISE-RL-2026-000207"},
        "card": {"tags": ["创意设计"], "radar": {"认知层": 70, "应用层": 66, "创新层": 85, "责任层": 80}},
        "aise": None,
        "materials": {
            "social": [{"name": "市少儿绘画大赛", "time": "2026年4月", "honor": "三等奖", "review": "approved"}],
            "patents": [], "honors": []
        }
    },
    {
        "id": "stu_chen",
        "name": "陈子豪",
        "grade": "六年级",
        "school": "光明学校",
        "channel": "AISC",
        "aiseLinked": True,
        "basic": {"gender": "男", "birth": "2013年8月19日", "hometown": "北京市海淀区",
                   "idCardMasked": "110108********0533", "joinTime": "2026年1月", "cardNo": "AISE-RL-2026-000312"},
        "card": {"tags": ["程序设计", "算法思维"], "radar": {"认知层": 88, "应用层": 90, "创新层": 76, "责任层": 72}},
        "aise": {
            "exams": [{"name": "人工智能一级测评", "level": "一级", "date": "2026-09", "score": 91, "total": 100, "grade": "优秀", "questionCount": 10, "duration": "60分钟"}],
            "activities": [{"name": "技术融合应用", "date": "2026年4月15日", "result": "优秀"}],
            "knowledge": [
                {"point": "顺序与循环", "mastery": 95, "errType": ""},
                {"point": "变量与列表", "mastery": 88, "errType": ""},
                {"point": "算法思维（排序）", "mastery": 80, "errType": ""}
            ],
            "answers": []
        },
        "materials": {"social": [], "patents": [], "honors": [
            {"name": "区信息学奥赛（小学组）", "time": "2026年5月", "honor": "一等奖", "review": "approved"}
        ]}
    },
    {
        "id": "stu_zhao", "name": "赵一诺", "grade": "三年级", "school": "阳光小学", "channel": "爱测评",
        "aiseLinked": True,
        "basic": {"gender": "女", "birth": "2016年6月1日", "hometown": "北京市丰台区",
                   "idCardMasked": "110106********0118", "joinTime": "2026年4月", "cardNo": "AISE-RL-2026-000415"},
        "card": {"tags": ["逻辑思维"], "radar": {"认知层": 76, "应用层": 62, "创新层": 70, "责任层": 84}},
        "aise": {
            "exams": [{"name": "人工智能启蒙级测评", "level": "启蒙级", "date": "2026-06", "score": 79, "total": 100, "grade": "良好", "questionCount": 10, "duration": "45分钟"}],
            "activities": [],
            "knowledge": [
                {"point": "AI 基础概念", "mastery": 82, "errType": ""},
                {"point": "顺序与循环", "mastery": 71, "errType": "粗心"},
                {"point": "条件判断", "mastery": 48, "errType": "概念混淆"}
            ],
            "answers": []
        },
        "materials": {"social": [], "patents": [], "honors": []}
    },
    {
        "id": "stu_sun", "name": "孙天佑", "grade": "五年级", "school": "光明学校", "channel": "AISC",
        "aiseLinked": True,
        "basic": {"gender": "男", "birth": "2014年2月27日", "hometown": "北京市西城区",
                   "idCardMasked": "110102********0195", "joinTime": "2026年2月", "cardNo": "AISE-RL-2026-000451"},
        "card": {"tags": ["程序设计", "数据思维"], "radar": {"认知层": 84, "应用层": 86, "创新层": 72, "责任层": 68}},
        "aise": {
            "exams": [
                {"name": "人工智能启蒙级测评", "level": "启蒙级", "date": "2026-04", "score": 84, "total": 100, "grade": "良好", "questionCount": 10, "duration": "45分钟"},
                {"name": "人工智能一级测评", "level": "一级", "date": "2026-08", "score": 86, "total": 100, "grade": "优秀", "questionCount": 10, "duration": "60分钟"}
            ],
            "activities": [{"name": "创新实践评定", "date": "2026年7月2日", "result": "良好"}],
            "knowledge": [
                {"point": "顺序与循环", "mastery": 90, "errType": ""},
                {"point": "条件判断", "mastery": 78, "errType": ""},
                {"point": "变量与列表", "mastery": 69, "errType": "粗心"},
                {"point": "算法思维（排序）", "mastery": 58, "errType": "未掌握"}
            ],
            "answers": []
        },
        "materials": {"social": [], "patents": [], "honors": []}
    },
    {
        "id": "stu_zhou", "name": "周芷萱", "grade": "六年级", "school": "实验小学", "channel": "爱测评",
        "aiseLinked": True,
        "basic": {"gender": "女", "birth": "2013年12月8日", "hometown": "北京市海淀区",
                   "idCardMasked": "110108********0642", "joinTime": "2026年3月", "cardNo": "AISE-RL-2026-000489"},
        "card": {"tags": ["生成式人工智能", "创意设计"], "radar": {"认知层": 80, "应用层": 78, "创新层": 92, "责任层": 86}},
        "aise": {
            "exams": [{"name": "人工智能一级测评", "level": "一级", "date": "2026-09", "score": 87, "total": 100, "grade": "优秀", "questionCount": 10, "duration": "60分钟"}],
            "activities": [{"name": "生成式人工智能应用实践", "date": "2026年10月11日", "result": "优秀"}],
            "knowledge": [
                {"point": "AI 基础概念", "mastery": 93, "errType": ""},
                {"point": "生成式人工智能应用", "mastery": 88, "errType": ""},
                {"point": "条件判断", "mastery": 66, "errType": "粗心"}
            ],
            "answers": []
        },
        "materials": {"social": [{"name": "市青少年 AI 创意营", "time": "2026年8月", "honor": "优秀营员", "review": "approved"}],
                       "patents": [], "honors": [{"name": "区中小学生电脑作品评选", "time": "2026年6月", "honor": "二等奖", "review": "approved"}]}
    },
    {
        "id": "stu_wu", "name": "吴思远", "grade": "四年级", "school": "光明学校", "channel": "AISC",
        "aiseLinked": True,
        "basic": {"gender": "男", "birth": "2015年9月30日", "hometown": "北京市东城区",
                   "idCardMasked": "110101********0327", "joinTime": "2026年5月", "cardNo": "AISE-RL-2026-000533"},
        "card": {"tags": ["逻辑思维"], "radar": {"认知层": 68, "应用层": 60, "创新层": 64, "责任层": 75}},
        "aise": {
            "exams": [{"name": "人工智能启蒙级测评", "level": "启蒙级", "date": "2026-07", "score": 64, "total": 100, "grade": "合格", "questionCount": 10, "duration": "45分钟"}],
            "activities": [],
            "knowledge": [
                {"point": "AI 基础概念", "mastery": 70, "errType": ""},
                {"point": "顺序与循环", "mastery": 55, "errType": "概念混淆"},
                {"point": "条件判断", "mastery": 42, "errType": "未掌握"},
                {"point": "变量与列表", "mastery": 38, "errType": "未掌握"}
            ],
            "answers": []
        },
        "materials": {"social": [], "patents": [], "honors": []}
    },
    {
        "id": "stu_zheng", "name": "郑好", "grade": "五年级", "school": "实验二小", "channel": "学校团体",
        "aiseLinked": False,
        "basic": {"gender": "男", "birth": "2014年7月14日", "hometown": "北京市昌平区",
                   "idCardMasked": "110114********0269", "joinTime": "2026年6月", "cardNo": "AISE-RL-2026-000560"},
        "card": {"tags": ["问题解决"], "radar": {"认知层": 72, "应用层": 75, "创新层": 68, "责任层": 80}},
        "aise": None,
        "materials": {"social": [{"name": "校科技社团 AI 兴趣班", "time": "2026年5月", "honor": "结业", "review": "approved"}],
                       "patents": [], "honors": []}
    }
]

works = [
    # —— 新增学员的已入库作品（演示看板数据密度） ——
    {
        "id": "w_arch_3", "studentId": "stu_chen",
        "name": "单词记忆小助手", "desc": "用 Python 做的单词背诵小工具",
        "type": "code", "filename": "猜数字游戏.py",
        "status": "approved", "aiStatus": "done",
        "ai": {"conclusion": "通过", "reason": "功能完整，交互清晰", "tags": ["程序设计", "问题解决"], "score": 88,
                "comment": "数据组织合理，交互提示友好。", "understanding": "单词记忆练习小工具，支持词库读取与随机抽词练习。"},
        "archive": {"tags": ["程序设计", "问题解决"], "score": 88, "comment": "数据组织合理，交互提示友好。"},
        "submittedAt": ts(12), "reviewedAt": ts(11),
        "review": {"by": "王老师", "action": "确认通过", "at": ts(11)}
    },
    {
        "id": "w_arch_4", "studentId": "stu_sun",
        "name": "班级图书角统计表", "desc": "用表格统计班级图书角的借阅情况",
        "type": "pdf", "filename": "智能小车项目报告.pdf",
        "status": "approved", "aiStatus": "done",
        "ai": {"conclusion": "通过", "reason": "数据整理完整，有分析结论", "tags": ["数据思维", "问题解决"], "score": 81,
                "comment": "数据分类清晰，有简单的对比分析。", "understanding": "班级图书借阅统计报告，含分类汇总与借阅趋势。"},
        "archive": {"tags": ["数据思维", "问题解决"], "score": 81, "comment": "数据分类清晰，有简单的对比分析。"},
        "submittedAt": ts(10), "reviewedAt": ts(9),
        "review": {"by": "王老师", "action": "确认通过", "at": ts(9)}
    },
    {
        "id": "w_arch_5", "studentId": "stu_zhou",
        "name": "AI 诗画作品集", "desc": "用生成式 AI 创作的诗配画作品集",
        "type": "image", "filename": "机器人创意插画.png",
        "status": "approved", "aiStatus": "done",
        "ai": {"conclusion": "通过", "reason": "创意突出，画面完整", "tags": ["生成式人工智能", "创意设计"], "score": 90,
                "comment": "提示词运用熟练，画面与诗歌主题呼应。", "understanding": "生成式 AI 创作的诗配画作品集，主题统一。"},
        "archive": {"tags": ["生成式人工智能", "创意设计"], "score": 90, "comment": "提示词运用熟练，画面与诗歌主题呼应。"},
        "submittedAt": ts(8), "reviewedAt": ts(7),
        "review": {"by": "王老师", "action": "确认通过", "at": ts(7)}
    },
    {
        "id": "w_arch_6", "studentId": "stu_wang",
        "name": "我的 AI 绘画日记", "desc": "记录我用 AI 画画的日记和作品",
        "type": "image", "filename": "AI校园主题海报.png",
        "status": "approved", "aiStatus": "done",
        "ai": {"conclusion": "通过", "reason": "画面完整，有创作过程记录", "tags": ["创意设计", "生成式人工智能"], "score": 83,
                "comment": "创作记录真实完整，画面表现力好。", "understanding": "AI 绘画练习日记，含多幅练习作品与创作说明。"},
        "archive": {"tags": ["创意设计", "生成式人工智能"], "score": 83, "comment": "创作记录真实完整，画面表现力好。"},
        "submittedAt": ts(6), "reviewedAt": ts(5),
        "review": {"by": "王老师", "action": "确认通过", "at": ts(5)}
    },
    # —— 已入库（归档）作品：李小明 2 份 ——
    {
        "id": "w_arch_1", "studentId": "stu_li",
        "name": "智能计算器小程序", "desc": "用 Python 做的命令行计算器，支持四则运算和除零提示",
        "type": "code", "filename": "智能计算器小程序.py",
        "status": "approved", "aiStatus": "done",
        "ai": {"conclusion": "通过", "reason": "程序结构完整，函数划分清晰，有除零保护",
                "tags": ["程序设计", "逻辑思维"], "score": 85,
                "comment": "四则运算拆分合理，边界处理到位。可以继续尝试支持括号与优先级。",
                "understanding": "一个命令行四则运算计算器，按运算符切分表达式并调用对应函数计算，对除零做了容错处理，含循环交互入口。"},
        "archive": {"tags": ["程序设计", "逻辑思维"], "score": 85,
                     "comment": "四则运算拆分合理，边界处理到位。可以继续尝试支持括号与优先级。"},
        "submittedAt": ts(20), "reviewedAt": ts(19),
        "review": {"by": "王老师", "action": "确认通过", "at": ts(19)}
    },
    {
        "id": "w_arch_2", "studentId": "stu_li",
        "name": "猜数字游戏", "desc": "带 AI 提示的猜数字小游戏",
        "type": "code", "filename": "猜数字游戏.py",
        "status": "approved", "aiStatus": "done",
        "ai": {"conclusion": "通过", "reason": "游戏逻辑完整，有次数统计与范围提示",
                "tags": ["程序设计", "算法思维"], "score": 82,
                "comment": "循环与条件使用正确，提示逻辑对小学生友好。",
                "understanding": "随机生成 1-100 目标数的猜数字游戏，循环读取输入并按大小给提示，统计尝试次数。"},
        "archive": {"tags": ["程序设计", "算法思维"], "score": 82,
                     "comment": "循环与条件使用正确，提示逻辑对小学生友好。"},
        "submittedAt": ts(15), "reviewedAt": ts(14),
        "review": {"by": "王老师", "action": "确认通过", "at": ts(14)}
    },
    # —— 待审队列：教研员端演示 ——
    {
        "id": "w_pend_1", "studentId": "stu_chen",
        "name": "AI绘画作品集网页", "desc": "用 HTML 做的我的 AI 绘画作品集页面",
        "type": "code", "filename": "AI绘画作品集网页.html.txt",
        "status": "reviewing", "aiStatus": "done",
        "ai": {"conclusion": "通过", "reason": "页面结构完整，有作品展示区与说明文字",
                "tags": ["创意设计", "生成式人工智能"], "score": 80,
                "comment": "版面清晰，图文搭配合理。建议给每幅作品补充创作思路说明。",
                "understanding": "一个展示 AI 绘画作品的静态网页，含标题、作品卡片列表与简单介绍。"},
        "submittedAt": ts(2)
    },
    {
        "id": "w_pend_2", "studentId": "stu_li",
        "name": "校园 AI 海报", "desc": "我设计的 AI 主题校园海报",
        "type": "image", "filename": "AI校园主题海报.png",
        "status": "reviewing", "aiStatus": "done",
        "ai": {"conclusion": "通过", "reason": "主题鲜明，画面元素与人工智能校园场景契合",
                "tags": ["创意设计", "生成式人工智能"], "score": 86,
                "comment": "构图完整，色彩明快，主题表达清楚。",
                "understanding": "以人工智能校园为主题的海报，包含机器人、书本、校园等视觉元素。"},
        "submittedAt": ts(1)
    },
    {
        "id": "w_pend_3", "studentId": "stu_wang",
        "name": "极简网页", "desc": "",
        "type": "code", "filename": "极简网页.html.txt",
        "status": "reviewing", "aiStatus": "done",
        "ai": {"conclusion": "驳回", "reason": "内容过于简单，仅一个空页面框架，无法体现学习成果",
                "tags": [], "score": 25,
                "comment": "作品内容量过少，缺少实质性创作。建议补充页面内容后重新提交。",
                "understanding": "仅含空页面骨架的 HTML 文件，无可见内容。"},
        "submittedAt": ts(3)
    },
    {
        "id": "w_pend_4", "studentId": "stu_chen",
        "name": "智能小车项目报告", "desc": "我们小组做智能小车的项目报告",
        "type": "pdf", "filename": "智能小车项目报告.pdf",
        "status": "reviewing", "aiStatus": "processing",
        "ai": None,
        "submittedAt": ts(0)
    }
]

report = {
    "stu_li": {
        "generatedAt": "2026-11-10 23:12:09",
        "model": "glm-5.3-flash",
        "content": {
            "summary": "李小明整体表现良好，两次测评均达80分以上，编程实操是突出亮点：能独立完成计算器和猜数字游戏。基础概念与循环掌握扎实，但排序算法、列表索引等新内容明显薄弱，是当前最需补齐的方向。",
            "examComment": "启蒙级88分、一级82分，均属良好水平；一级测评中排序和列表题失分，成绩略有回落，属内容变难所致。",
            "knowledgeComment": "顺序与循环掌握92%最扎实，AI基础概念85%也不错；算法思维（排序）仅45%是最薄弱项，变量与列表58%也需补。",
            "radarComment": "四个维度中程序设计和AI认知表现突出，逻辑思维良好，算法思维明显偏弱，整体发展还不够均衡。",
            "errorComment": "三类错误各有对策：排序和索引是概念混淆，要重新学定义；条件题因粗心失分，需养成读题检查习惯；AI伦理题未掌握，可结合生活实例讲解。",
            "workComment": "两个入库作品82~85分，四则运算拆分合理、边界处理好，循环条件运用正确；评语建议下一步挑战括号与优先级功能。",
            "strengths": [
                "编程实操能力强，能独立完成计算器小程序和猜数字游戏",
                "顺序与循环结构掌握扎实（92%），作品代码逻辑清晰",
                "实践经历丰富，获AI冬令营优秀营员和校科技节创意编程二等奖"
            ],
            "weaknesses": [
                "算法思维薄弱，排序概念仅掌握45%，冒泡排序基本思想不清晰",
                "变量与列表掌握58%，列表索引从0开始等规则容易混淆",
                "做题存在粗心现象，条件判断题因审题不细失分"
            ],
            "suggestions": [
                "补齐最弱项：用10张卡片亲手模拟冒泡排序，每天排一遍并说出比较、交换的步骤，一周后能独立讲清排序过程",
                "巩固列表概念：用Scratch做一个'点名小列表'，练习添加元素、读取第0个和最后一个元素，记住索引从0开始",
                "进阶挑战：给计算器小程序增加括号与乘除优先级支持，在改作品的过程中同时练算法思维和细心度",
                "定期巩固：每两周整理一次错题本，条件判断题先读题两遍再作答，逐步减少粗心失分"
            ]
        }
    }
}

data = {
    "users": [
        {"user": "xiaoming", "password": "123456", "role": "student", "studentId": "stu_li", "label": "学员 / 家长 · 李小明"},
        {"user": "wang", "password": "123456", "role": "teacher", "label": "教研员 · 王老师"}
    ],
    "sessions": {},
    "students": students,
    "works": works,
    "reports": report,
    "qaLog": []
}

if __name__ == '__main__':
    path = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('data.json written:', path)
