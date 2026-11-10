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
        "aiseLinked": True,
        "card": {
            "tags": ["程序设计", "逻辑思维"],
            "radar": {"认知层": 82, "应用层": 74, "创新层": 88, "责任层": 90}
        },
        "aise": {
            "exams": [
                {"name": "人工智能启蒙级测评", "level": "启蒙级", "date": "2026-05", "score": 88, "total": 100, "grade": "优秀"},
                {"name": "人工智能一级测评", "level": "一级", "date": "2026-09", "score": 82, "total": 100, "grade": "良好"}
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
        "aiseLinked": False,
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
        "aiseLinked": True,
        "card": {"tags": ["程序设计", "算法思维"], "radar": {"认知层": 88, "应用层": 90, "创新层": 76, "责任层": 72}},
        "aise": {
            "exams": [{"name": "人工智能一级测评", "level": "一级", "date": "2026-09", "score": 91, "total": 100, "grade": "优秀"}],
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
    }
]

works = [
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
        "generatedAt": ts(7),
        "model": "seed",
        "content": {
            "summary": "李小明同学对人工智能基础概念掌握扎实，程序设计作品结构清晰，创新与责任意识突出；循环类知识掌握优秀，短板集中在算法思维与列表概念，粗心失分需引起注意。",
            "strengths": ["AI 基础概念与循环结构掌握扎实（92%）", "作品能完整实现功能并做边界处理", "创新层、责任层维度表现突出"],
            "weaknesses": ["算法思维（排序）掌握率 45%，冒泡排序概念存在混淆", "列表索引概念未掌握（58%）", "条件判断存在粗心失分"],
            "suggestions": ["优先补齐排序算法：先从冒泡排序的逐步演示入手，配合生活化例子（排队换位置）", "列表与索引：用编号抽屉的比喻练习索引取值", "每次答题后留 2 分钟检查，针对粗心错题做标记重做", "保持每月一次作品创作，把排序算法用到小游戏中巩固"]
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
