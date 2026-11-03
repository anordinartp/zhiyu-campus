# -*- coding: utf-8 -*-
"""Round 1 revision of the 知屿校园 report.

Adds the missing requirements material (role matrix, use-case list, core
use-case specifications, non-functional requirements), repairs the data-model
inconsistencies, and adds captions to every table.  The source document is
never modified: the result is written to a new file.
"""
import copy
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

SRC = r"C:\Users\saxtul\Downloads\知屿校园-需求分析与建模实验报告(5).docx"
OUT_DIR = r"C:\Users\saxtul\Documents\ds harness区\知屿校园"
OUT = os.path.join(OUT_DIR, "知屿校园-需求分析与建模实验报告-第1轮修订.docx")

BODY_PT = 10.5
CELL_PT = 9.0

DOC = None  # set in main()


# --------------------------------------------------------------- xml helpers
def new_para(text="", *, style="Normal", size=BODY_PT, bold=False, align=None,
             space_before=None, space_after=None):
    p = DOC.add_paragraph()
    p.style = style
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    if space_before is not None:
        pf.space_before = Pt(space_before)
    if space_after is not None:
        pf.space_after = Pt(space_after)
    if text:
        run = p.add_run(text)
        run.font.size = Pt(size)
        if bold:
            run.font.bold = True
    return p


def para_before(anchor, text="", **kwargs):
    p = new_para(text, **kwargs)
    anchor.addprevious(p._p)
    return p


def caption(anchor, text):
    return para_before(anchor, text, align=WD_ALIGN_PARAGRAPH.CENTER, size=9.0)


def add_run(para, text, *, size=BODY_PT, bold=False):
    run = para.add_run(text)
    run.font.size = Pt(size)
    if bold:
        run.font.bold = True
    return run


def set_cell_text(tc, text, *, bold=False):
    """Replace a cell's text while keeping its tcPr (borders, margins, width)."""
    paras = tc.findall(qn("w:p"))
    for extra in paras[1:]:
        tc.remove(extra)
    p = paras[0]
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    if bold:
        rPr.append(OxmlElement("w:b"))
    for tag in ("w:sz", "w:szCs"):
        el = OxmlElement(tag)
        el.set(qn("w:val"), str(int(CELL_PT * 2)))
        rPr.append(el)
    run.append(rPr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    run.append(t)
    p.append(run)
    pPr = p.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        p.insert(0, pPr)
    jc = pPr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        pPr.append(jc)
    jc.set(qn("w:val"), "center")


def build_table(template_tbl, headers, rows, widths):
    tbl = copy.deepcopy(template_tbl)
    trs = tbl.findall(qn("w:tr"))
    if len(trs) < 2:
        raise ValueError("template needs a header and at least one body row")
    body_tr = copy.deepcopy(trs[1])
    for tr in trs[2:]:
        tbl.remove(tr)
    for _ in range(len(rows) - 1):
        tbl.append(copy.deepcopy(body_tr))

    grid = tbl.find(qn("w:tblGrid"))
    cols = grid.findall(qn("w:gridCol"))
    if len(cols) != len(headers):
        raise ValueError("template has %d columns, need %d" % (len(cols), len(headers)))
    for gc, w in zip(cols, widths):
        gc.set(qn("w:w"), str(w))

    all_trs = tbl.findall(qn("w:tr"))
    if len(all_trs) != len(rows) + 1:
        raise ValueError("row count mismatch")
    for i, (tr, values) in enumerate(zip(all_trs, [headers] + rows)):
        cells = tr.findall(qn("w:tc"))
        if len(cells) != len(headers):
            raise ValueError("cell count mismatch")
        for tc, val, w in zip(cells, values, widths):
            tcPr = tc.find(qn("w:tcPr"))
            if tcPr is None:
                tcPr = OxmlElement("w:tcPr")
                tc.insert(0, tcPr)
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW")
                tcPr.insert(0, tcW)
            tcW.set(qn("w:w"), str(w))
            tcW.set(qn("w:type"), "dxa")
            set_cell_text(tc, val, bold=(i == 0))
        # keep rows whole and repeat the header when a table breaks across pages
        trPr = tr.find(qn("w:trPr"))
        if trPr is None:
            trPr = OxmlElement("w:trPr")
            tr.insert(0, trPr)
        if trPr.find(qn("w:cantSplit")) is None:
            trPr.append(OxmlElement("w:cantSplit"))
        if i == 0 and trPr.find(qn("w:tblHeader")) is None:
            trPr.append(OxmlElement("w:tblHeader"))
    return tbl


def mark_rows(tbl):
    """Repeat the header row and keep rows whole on tables that may split."""
    for i, tr in enumerate(tbl.findall(qn("w:tr"))):
        trPr = tr.find(qn("w:trPr"))
        if trPr is None:
            trPr = OxmlElement("w:trPr")
            tr.insert(0, trPr)
        if trPr.find(qn("w:cantSplit")) is None:
            trPr.append(OxmlElement("w:cantSplit"))
        if i == 0 and trPr.find(qn("w:tblHeader")) is None:
            trPr.append(OxmlElement("w:tblHeader"))


# ------------------------------------------------------------------- content
ROLE_HEAD = ["功能", "学生", "教师", "管理员"]
ROLE_ROWS = [
    ["注册登录与个人资料", "✓", "✓", "✓"],
    ["创建或加入聊天室", "✓", "✓", "✓"],
    ["聊天室成员与权限管理", "仅本人创建的聊天室", "仅本人创建的聊天室", "全部聊天室"],
    ["消息收发", "✓", "✓", "✓"],
    ["发帖、回帖", "✓", "✓", "✓"],
    ["点赞、收藏", "✓", "✓", "✓"],
    ["编辑或删除内容", "仅本人内容", "仅本人内容", "任意内容（审核处置）"],
    ["举报内容", "✓", "✓", "✓"],
    ["统一检索与浏览", "✓", "✓", "✓"],
    ["标签与板块维护", "—", "—", "✓"],
    ["违规内容审核处置", "—", "—", "✓"],
    ["查看行为与热度统计", "仅个人数据", "仅个人数据", "全站数据"],
]

UC_HEAD = ["编号", "用例名称", "主要参与者", "对应加工", "优先级"]
UC_ROWS = [
    ["UC-01", "用户注册与登录", "用户", "1", "P0"],
    ["UC-02", "创建或加入聊天室", "用户", "2.1", "P0"],
    ["UC-03", "消息收发", "用户", "2.2", "P0"],
    ["UC-04", "聊天室成员与权限管理", "用户（群主/被授权者）", "2.3", "P1"],
    ["UC-05", "聊天室标签分类", "用户、管理员", "2.4、4", "P1"],
    ["UC-06", "发帖", "用户", "3.1", "P0"],
    ["UC-07", "回帖与互动（点赞、收藏）", "用户", "3.2", "P0"],
    ["UC-08", "板块与标签聚合浏览", "用户", "3.3、3.4", "P1"],
    ["UC-09", "统一检索与排序", "用户", "6.1、6.2", "P0"],
    ["UC-10", "AI 内容处理（摘要、打标、违规识别）", "系统（AI 智能体）、大模型服务", "5.1、5.2、5.3", "P0"],
    ["UC-11", "违规内容预警与审核处置", "管理员", "5.3、4", "P0"],
    ["UC-12", "标签与板块维护", "管理员", "4", "P1"],
    ["UC-13", "举报内容（二期）", "用户、管理员", "4", "P2"],
    ["UC-14", "行为采集与个性化推荐", "用户、系统", "7", "P2"],
]

NFR_HEAD = ["类别", "编号", "需求描述", "度量与验收标准"]
NFR_ROWS = [
    ["性能", "NFR-01", "在线消息端到端时延", "同一聊天室内 P95 ≤ 1 s"],
    ["性能", "NFR-02", "统一检索响应时间", "100 万条索引规模下 P95 ≤ 500 ms"],
    ["性能", "NFR-03", "AI 单条内容处理时长", "摘要与打标合计 ≤ 5 s；处理队列积压 ≤ 1000 条"],
    ["并发", "NFR-04", "并发承载能力", "≥ 500 在线用户，读峰值 200 QPS 不超时"],
    ["可用性", "NFR-05", "核心功能可用性", "≥ 99.5%/月；大模型服务不可用时降级且不影响内容入库"],
    ["安全", "NFR-06", "口令与令牌", "口令加盐哈希（bcrypt/Argon2）；访问令牌 ≤ 2 h，刷新令牌 ≤ 7 d"],
    ["安全", "NFR-07", "访问控制", "RBAC + 资源归属校验；越权访问一律返回 403 并留痕"],
    ["安全", "NFR-08", "内容安全", "违规内容 100% 进入拦截或人工审核；置信度 < 0.8 转人工"],
    ["隐私", "NFR-09", "个人信息保护", "行为日志脱敏存储，仅用于热度与推荐，不外泄明文"],
    ["合规", "NFR-10", "内容留存与申诉", "内容留存 ≥ 180 天；支持举报与申诉受理"],
    ["可维护", "NFR-11", "接口与测试", "对外接口提供 OpenAPI 3.0 文档；核心服务单元测试覆盖率 ≥ 60%"],
    ["易用性", "NFR-12", "操作效率", "核心功能 ≤ 3 次点击到达；适配主流移动端浏览器"],
    ["可扩展", "NFR-13", "可配置与可替换", "标签与板块可配置；检索引擎、模型供应商经适配层可替换"],
]

DD_HEAD = ["类型", "实体 / 关联实体", "主键", "属性"]
DD_ROWS = [
    ["实体", "用户", "用户ID",
     "昵称、学号/工号、密码哈希、头像、角色（学生/教师/管理员）、行为积分、注册时间、状态（正常/禁用）"],
    ["关联", "用户兴趣标签", "用户ID＋标签ID", "权重、更新时间"],
    ["实体", "聊天室", "聊天室ID",
     "名称、简介、创建者ID、创建时间、成员数、状态（正常/禁言/关闭）"],
    ["关联", "聊天室成员", "聊天室ID＋用户ID", "身份（群主/管理员/成员）、加入时间、是否禁言"],
    ["实体", "消息", "消息ID",
     "内容、类型（文本/图片/文件）、发送者ID、聊天室ID、发送时间、是否被AI处理"],
    ["实体", "帖子", "帖子ID",
     "标题、正文、作者ID、板块ID、发布时间、浏览数、点赞数、收藏数、状态（正常/待审/删除）"],
    ["实体", "回帖", "回帖ID", "内容、帖子ID、作者ID、父回帖ID、回复时间、点赞数"],
    ["实体", "标签", "标签ID", "标签名称、类型（聊天室/博客通用）、创建者ID、热度、创建时间"],
    ["实体", "板块", "板块ID", "名称、简介、管理员ID、排序号、创建时间"],
    ["关联", "聊天室标签", "聊天室ID＋标签ID", "创建时间"],
    ["关联", "帖子标签", "帖子ID＋标签ID", "创建时间"],
    ["关联", "板块标签", "板块ID＋标签ID", "排序号"],
    ["关联", "点赞", "用户ID＋目标类型＋目标ID", "点赞时间"],
    ["关联", "收藏", "用户ID＋帖子ID", "收藏时间"],
    ["实体", "举报（二期）", "举报ID",
     "举报人ID、目标类型（消息/帖子/回帖）、目标ID、举报理由、证据截图、"
     "状态（待处理/成立/不成立）、处理人ID、处理结果、举报时间、处理时间"],
    ["实体", "行为记录", "行为ID",
     "用户ID、行为类型（浏览/发言/发帖/点赞/收藏/停留）、目标类型、目标ID、发生时间、停留时长"],
    ["实体", "AI处理结果", "处理ID",
     "目标类型（消息/帖子）、目标ID、摘要、情感倾向、违规判定、置信度、处理时间"],
    ["关联", "AI标签结果", "处理ID＋标签ID", "置信度、来源（模型自动/人工修正）"],
]

REL_HEAD = ["序号", "联系", "参与实体", "类型", "说明"]
REL_ROWS = [
    ["1", "加入", "用户—聊天室", "M:N", "经“聊天室成员”关联实体实现，含身份、加入时间与禁言状态"],
    ["2", "发送", "用户—消息", "1:N", "一个用户可发送多条消息"],
    ["3", "包含", "聊天室—消息", "1:N", "一个聊天室包含多条消息"],
    ["4", "发布", "用户—帖子", "1:N", "一个用户可发布多个帖子"],
    ["5", "回复", "用户—回帖", "1:N", "一个用户可发表多条回帖"],
    ["6", "含有", "帖子—回帖", "1:N", "一个帖子含有多条回帖"],
    ["7", "自嵌套", "回帖—回帖", "1:N", "一条回帖可作为其他回帖的父回帖（父回帖ID 自引用）"],
    ["8", "标注", "聊天室—标签", "M:N", "经“聊天室标签”关联实体实现，标签用于给聊天室分类"],
    ["9", "标注", "帖子—标签", "M:N", "经“帖子标签”关联实体实现，一个帖子可带多个标签"],
    ["10", "聚合", "板块—标签", "M:N", "经“板块标签”关联实体实现，板块聚合标签形成主题社区"],
    ["11", "归属", "板块—帖子", "1:N", "帖子归属某个板块"],
    ["12", "关注", "用户—标签", "M:N", "经“用户兴趣标签”关联实体实现，权重用于个性化推荐"],
    ["13", "点赞", "用户—帖子/回帖", "M:N", "经“点赞”关联实体记录明细；同一用户对同一目标仅一次"],
    ["14", "收藏", "用户—帖子", "M:N", "经“收藏”关联实体记录明细，支持“我的收藏”"],
    ["15", "举报", "用户—消息/帖子/回帖", "1:N", "一条内容可被多次举报，由管理员统一处置"],
    ["16", "产生", "用户—行为记录", "1:N", "用户行为被逐条记录，用于行为感知与推荐"],
    ["17", "生成", "消息—AI处理结果", "1:1", "每条消息对应一条 AI 摘要/打标结果"],
    ["18", "生成", "帖子—AI处理结果", "1:1", "每个帖子对应一条 AI 摘要/打标结果"],
    ["19", "标注", "AI处理结果—标签", "M:N", "经“AI标签结果”关联实体实现，承载模型自动打标与置信度"],
]

STORE_DESC = {
    "D1": "账号、密码哈希、角色与状态，以及“用户兴趣标签”关联记录",
    "D2": "聊天室、聊天室成员（身份/加入时间/禁言）与聊天消息",
    "D3": "帖子、回帖、点赞与收藏明细",
    "D4": "标签、板块，以及“聊天室标签”“帖子标签”“板块标签”三张关联记录",
    "D5": "浏览、发言、发帖、点赞、收藏、停留时长等行为记录",
    "D6": "AI 生成的摘要、情感倾向、违规判定与自动标签（含“AI标签结果”关联记录）",
}

D7_ROW = ["数据存储", "D7 举报与审核表（二期扩展）",
          "举报记录与审核处置结果（举报人、目标、理由、状态、处置人与处置结果）"]

USE_CASES = [
    ("UC-01　用户注册与登录", [
        ("参与者", "用户"),
        ("前置条件", "用户可访问平台；网络可用。"),
        ("基本流", [
            "用户在注册页填写昵称、学号/工号与密码并提交；",
            "系统校验学号/工号唯一性与口令强度；",
            "系统对口令加盐哈希后写入 D1，账号状态置为“正常”；",
            "用户以学号/工号与口令登录；",
            "系统校验凭据并签发访问令牌（含用户ID与角色）；",
            "前端保存令牌并跳转首页，登录状态保持 2 小时。",
        ]),
        ("备选流", [
            "2a 学号/工号已存在：提示“账号已注册”，返回注册页；",
            "2b 口令强度不足：提示规则并返回注册页；",
            "5a 凭据错误连续 5 次：账号锁定 10 分钟；",
            "5b 账号状态为“禁用”：提示联系管理员。",
        ]),
        ("后置条件", "用户记录持久化于 D1；用户获得有效访问令牌。"),
        ("业务规则", "口令 ≥ 8 位且含字母与数字；访问令牌 2 小时过期，凭刷新令牌续期（≤ 7 天）。"),
    ]),
    ("UC-03　消息收发", [
        ("参与者", "用户（聊天室成员）"),
        ("前置条件", "已登录；已加入目标聊天室；聊天室状态为“正常”。"),
        ("基本流", [
            "用户进入聊天室，输入消息并发送（文本/图片/文件）；",
            "系统校验登录态、成员身份与禁言状态；",
            "系统将消息写入 D2，并更新聊天室最后活跃时间；",
            "系统向在线成员实时推送新消息；",
            "系统将消息投递至 AI 智能体处理队列（加工 5.1，异步）；",
            "系统返回发送成功并在会话中显示该消息。",
        ]),
        ("备选流", [
            "2a 非聊天室成员：提示先加入聊天室；",
            "2b 用户被禁言或聊天室已关闭：拒绝发送并提示剩余禁言时间；",
            "5a AI 队列不可用：消息仍保存成功，标记“待处理”，由补偿任务重试。",
        ]),
        ("后置条件", "消息持久化于 D2；在线成员可见；消息进入 AI 处理流程。"),
        ("业务规则", "文本 ≤ 2000 字，图片 ≤ 10 MB；同一用户 1 秒内的相同内容按幂等处理。"),
    ]),
    ("UC-06　发帖", [
        ("参与者", "用户"),
        ("前置条件", "已登录；目标板块存在；用户未被限制发帖。"),
        ("基本流", [
            "用户选择板块，填写标题、正文并可选择标签后提交；",
            "系统校验标题与正文非空、长度合规，并进行敏感词初筛；",
            "系统将帖子写入 D3，状态置“正常”（命中敏感词则置“待审”）；",
            "系统异步触发 AI 摘要与自动打标（加工 5.2），结果写入 D6；",
            "系统返回发布成功并跳转至帖子详情。",
        ]),
        ("备选流", [
            "2a 内容为空或超长：提示校验失败，保留已填内容；",
            "2b 命中敏感词：帖子置“待审”，仅作者可见，等待管理员处置；",
            "4a AI 服务超时：摘要与标签留空并标记“待处理”，由重试任务补齐。",
        ]),
        ("后置条件", "帖子持久化于 D3；索引建立后可被检索；进入审核与推荐流程。"),
        ("业务规则", "标题 ≤ 100 字，正文 ≤ 20000 字，标签 ≤ 5 个。"),
    ]),
    ("UC-09　统一检索与排序", [
        ("参与者", "用户（游客可检索公开内容）"),
        ("前置条件", "检索服务与内容索引可用。"),
        ("基本流", [
            "用户输入关键词或选择标签后提交检索；",
            "系统解析检索条件（分词、标签过滤、范围限定）并构造查询；",
            "系统在 D6 内容索引中检索聊天室、帖子与用户三类对象；",
            "系统按“相关度 × 热度 × 行为偏好”加权排序，并过滤违规与待审内容；",
            "系统返回结果列表（含摘要、标签与命中片段）；",
            "系统将本次检索与点击行为写入 D5。",
        ]),
        ("备选流", [
            "2a 关键词为空或仅含停用词：提示输入有效关键词；",
            "3a 索引无命中：返回“未找到”并推荐热门内容；",
            "3b 索引服务不可用：降级为数据库模糊查询，并提示“结果可能不全”。",
        ]),
        ("后置条件", "返回结果列表；D5 新增行为记录用于热度与推荐计算。"),
        ("业务规则", "单次返回 ≤ 20 条；检索 P95 ≤ 500 ms。"),
    ]),
    ("UC-10　AI 智能体内容处理", [
        ("参与者", "系统（AI 智能体）；协作者：大模型服务"),
        ("前置条件", "消息或帖子已入库；AI 处理队列可用。"),
        ("基本流", [
            "智能体从队列取出待处理内容（消息来自 D2、帖子来自 D3）；",
            "智能体组装提示词，调用大模型服务的内容理解接口；",
            "大模型返回摘要、情感倾向、违规判定与建议标签；",
            "智能体校验返回结构，并过滤低置信度标签；",
            "智能体将摘要、情感倾向、违规判定与自动标签写入 D6；",
            "智能体将被处理内容标记为“已处理”；",
            "若判定为违规，智能体生成预警并推送管理员（转 UC-11）。",
        ]),
        ("备选流", [
            "2a 大模型服务超时或限流：指数退避重试 3 次，仍失败则置“待处理”并告警；",
            "4a 返回结构非法或摘要为空：丢弃本次结果，内容置“待处理”；",
            "7a 预警推送失败：写入待推送表，由定时任务补发。",
        ]),
        ("后置条件", "D6 生成摘要、标签与违规判定；违规内容进入人工审核队列。"),
        ("业务规则", "单条处理 ≤ 5 s；违规判定置信度 < 0.8 时转人工复核，不自动处置。"),
    ]),
    ("UC-11　违规内容预警与审核处置", [
        ("参与者", "管理员"),
        ("前置条件", "管理员已登录并具备审核权限；存在 AI 预警或被举报的内容。"),
        ("基本流", [
            "管理员打开审核台，按时间、类型与置信度筛选待处理内容；",
            "系统展示原文、AI 摘要、违规判定与置信度、命中标签；",
            "管理员判定“成立/不成立”，并选择处置动作（删除/隐藏/警告作者/恢复）；",
            "系统更新内容状态（正常/待审/删除）并写入 D3，记录处置人与时间；",
            "系统更新举报与审核记录，状态置“已处理”；",
            "系统通知内容作者处置结果。",
        ]),
        ("备选流", [
            "2a 内容已被作者删除：标记“已失效”，流程结束；",
            "3a 管理员误判：24 小时内可撤销，恢复原状态并留痕；",
            "4a 批量处置：支持多选同类内容一次性处理。",
        ]),
        ("后置条件", "违规内容状态更新；审核留痕可追溯。"),
        ("业务规则", "处置操作需二次确认；所有处置写入不可篡改的审核日志。"),
    ]),
]


# --------------------------------------------------------------------- build
def main():
    global DOC
    doc = Document(SRC)
    DOC = doc

    # anchors captured before insertion, so later index shifts don't matter
    tbl_external = doc.tables[0]._tbl
    tbl_process = doc.tables[1]._tbl
    tbl_dict = doc.tables[2]._tbl
    tbl_rel = doc.tables[3]._tbl
    tpl4 = doc.tables[1]._tbl
    tpl5 = doc.tables[3]._tbl

    p_dict_intro = doc.paragraphs[29]
    p_er_intro = doc.paragraphs[31]
    p_last_note = doc.paragraphs[38]

    h1_dfd = None
    for p in doc.paragraphs:
        if p.style.name == "Heading 1" and p.text.strip().startswith("二、"):
            h1_dfd = p._p
            break
    if h1_dfd is None:
        raise SystemExit("找不到“二、数据流程图”标题")

    # ---- 表 1 caption + refreshed data-store descriptions ----------------
    caption(tbl_external, "表 1  外部实体与数据存储")
    for row in doc.tables[0].rows[1:]:
        name = row.cells[1].text.strip()
        for key, desc in STORE_DESC.items():
            if name.startswith(key):
                set_cell_text(row.cells[2]._tc, desc)

    # D7 is new: clone the last data-store row so borders and cell metrics match.
    # It is a phase-two extension, so the DFD pages keep showing D1-D6 only.
    t0 = doc.tables[0]
    new_tr = copy.deepcopy(t0.rows[-1]._tr)
    t0.rows[-1]._tr.addnext(new_tr)
    for tc, val in zip(new_tr.findall(qn("w:tc")), D7_ROW):
        set_cell_text(tc, val)
    mark_rows(t0._tbl)

    # ---- 1.4 角色与功能权限 ----------------------------------------------
    para_before(h1_dfd, "1.4 角色与功能权限", style="Heading 2", space_before=10.0)
    para_before(h1_dfd,
                "平台设有学生、教师与管理员三类全局角色。学生与教师在内容侧权限相同，"
                "差异仅体现为身份标识与教研类板块的推荐权重；管理员承担标签、板块维护与违规内容处置。"
                "聊天室内的成员管理权由聊天室创建者授予，属于资源级权限，与全局角色正交。")
    caption(h1_dfd, "表 2  角色与功能权限矩阵")
    h1_dfd.addprevious(build_table(tpl4, ROLE_HEAD, ROLE_ROWS, [2100, 1400, 1400, 2244]))
    para_before(h1_dfd,
                "注：“✓”表示该角色具备此项权限，“—”表示不具备；"
                "聊天室内的成员与禁言管理仅对本人创建或经创建者授权的聊天室生效。",
                size=9.0)

    # ---- 1.5 功能需求清单 ------------------------------------------------
    para_before(h1_dfd, "1.5 功能需求清单", style="Heading 2", space_before=10.0)
    para_before(h1_dfd,
                "依据业务流程与数据流图的加工划分，整理出 14 项功能需求（用例）。"
                "P0 为必须实现的核心功能，P1 为重要功能，P2 为可延后功能；"
                "“对应加工”列给出与数据流图加工的映射关系。其中举报与审核（UC-13）属二期扩展，"
                "不计入本期实现范围。")
    caption(h1_dfd, "表 3  功能需求（用例）清单")
    h1_dfd.addprevious(build_table(tpl5, UC_HEAD, UC_ROWS, [950, 2050, 1450, 950, 1744]))

    # ---- 1.6 核心用例描述 ------------------------------------------------
    para_before(h1_dfd, "1.6 核心用例描述", style="Heading 2", space_before=10.0)
    para_before(h1_dfd,
                "对 6 个 P0 级用例给出结构化描述，涵盖参与者、前置条件、基本流、备选流、"
                "后置条件与业务规则；其余用例可在详细设计阶段按同一模板补充。")
    for title, fields in USE_CASES:
        p = para_before(h1_dfd, "", space_before=8.0)
        add_run(p, title, bold=True)
        for label, value in fields:
            if isinstance(value, list):
                p = para_before(h1_dfd, "", space_after=0)
                add_run(p, label + "：", bold=True)
                for step in value:
                    para_before(h1_dfd, step, space_after=0)
            else:
                p = para_before(h1_dfd, "", space_after=0)
                add_run(p, label + "：", bold=True)
                add_run(p, value)

    # ---- 1.7 非功能需求 --------------------------------------------------
    para_before(h1_dfd, "1.7 非功能需求", style="Heading 2", space_before=10.0)
    para_before(h1_dfd,
                "非功能需求是后续测试与验收的依据，按下表逐条给出可度量的指标；"
                "未达标项在测试阶段记为缺陷。")
    caption(h1_dfd, "表 4  非功能需求")
    h1_dfd.addprevious(build_table(tpl4, NFR_HEAD, NFR_ROWS, [900, 900, 2900, 2444]))

    # 表 5 caption ----------------------------------------------------
    caption(tbl_process, "表 5  第一层数据流图的加工与数据流")
    mark_rows(tbl_process)

    # ---- 三、数据字典 ----------------------------------------------------
    caption(tbl_dict, "表 6  数据字典")
    new_dict = build_table(tpl4, DD_HEAD, DD_ROWS, [700, 1500, 1900, 3044])
    tbl_dict.addprevious(new_dict)
    tbl_dict.getparent().remove(tbl_dict)

    for r in p_dict_intro.runs[1:]:
        r._element.getparent().remove(r._element)
    p_dict_intro.runs[0].text = (
        "下表按实体与关联实体列出属性清单：主键在“主键”列单独标明，"
        "关联实体采用复合主键并以“＋”连接；外键属性在关联实体中只保留引用，不再重复存储。"
    )

    tail = doc.add_paragraph()
    tr = tail.add_run("说明：成员数、浏览数、点赞数、收藏数与热度为冗余计数字段，"
                      "其唯一数据源是明细表与行为记录，由触发器或定时任务维护，"
                      "出现不一致时以明细为准重建。")
    tr.font.size = Pt(9.0)
    new_dict.addnext(tail._p)

    # ---- 四、E-R 模型 ----------------------------------------------------
    add_run(p_er_intro,
            "下图给出主要实体与联系；收藏、点赞、举报、回帖自嵌套等治理与互动类联系见“表 7”，"
            "完整图件将在设计阶段统一补全。")
    caption(tbl_rel, "表 7  E-R 模型中的联系")
    new_rel = build_table(tpl5, REL_HEAD, REL_ROWS, [600, 900, 1900, 800, 2944])
    tbl_rel.addprevious(new_rel)
    tbl_rel.getparent().remove(tbl_rel)

    # ---- 五、建模说明：追加两条 -------------------------------------------
    cursor = p_last_note._p
    for text in (
        "5. 关联实体的处理：M:N 联系一律转换为独立的关联实体（聊天室成员、聊天室标签、"
        "帖子标签、板块标签、点赞、收藏、用户兴趣标签、AI标签结果）；1:N 联系在“多”端实体中保留外键；"
        "回帖的层次关系通过“父回帖ID”自引用实现，不再另设联系实体。",
        "6. 冗余计数的约定：列表页与热度排序所需的计数（成员数、浏览数、点赞数、收藏数、热度）"
        "以冗余字段维护，避免每次聚合查询；其唯一数据源仍是明细表与行为日志，"
        "出现不一致时以明细为准重建。",
    ):
        np = new_para(text)
        cursor.addnext(np._p)
        cursor = np._p

    # ---- 让 2.2 与自检结论与新增的 D7 保持一致 ------------------------------
    def rewrite(needle, new_text):
        for p in doc.paragraphs:
            if needle in p.text:
                if p.runs:
                    p.runs[0].text = new_text
                    for extra in p.runs[1:]:
                        extra._element.getparent().remove(extra._element)
                return True
        return False

    if not rewrite("并补充 6 个数据存储 D1～D6",
                   "第一层图把加工 0 分解为 7 个加工：1 用户与权限管理、2 聊天室管理、3 博客管理、"
                   "4 标签管理、5 智能体处理、6 检索服务、7 行为感知与推荐；并补充 6 个数据存储 D1～D6。"
                   "另有 D7 举报与审核表属二期扩展，不在本图展开，将在概要设计的数据库设计中细化。"):
        raise SystemExit("未找到 2.2 中关于数据存储数量的句子")

    if not rewrite("4. 自检结论",
                   "4. 自检结论：D1～D6 六个数据存储均既有写入也有读取"
                   "（如 D2 由加工 2 写入、由加工 2/5 读取）；每个加工既有输入也有输出；"
                   "外部实体之间不直接交换数据流。二期扩展的 D7 举报与审核表由加工 4 读写，校验规则相同。"):
        raise SystemExit("未找到建模说明中的自检结论")

    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
