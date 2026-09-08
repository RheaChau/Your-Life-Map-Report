#!/usr/bin/env python3
"""Render a structured Chinese BaZi/Ziwei report JSON to an A4 PDF."""
import argparse
import json
import os
import re
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, PageBreak, Spacer,
    Table, TableStyle, KeepTogether
)
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


def register_cjk_font():
    candidates = [
        ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
        ("/Library/Fonts/Arial Unicode.ttf", 0),
        ("/System/Library/Fonts/Supplemental/NISC18030.ttf", 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
        ("/System/Library/Fonts/AppleSDGothicNeo.ttc", 0),
    ]
    for font_path, index in candidates:
        if not os.path.exists(font_path):
            continue
        try:
            pdfmetrics.registerFont(TTFont("ReportCJK", font_path, subfontIndex=index))
            return "ReportCJK"
        except Exception:
            continue
    # Keeps the script usable on minimal systems; caller gets a clear warning.
    return "Helvetica"


ARDOR_INK = colors.HexColor("#244A3C")
ARDOR_GREEN = colors.HexColor("#2F5D50")
ARDOR_SAGE = colors.HexColor("#DDEBE4")


def labels_for(data):
    labels = data.get("labels") or {}
    language = str(data.get("language") or data.get("locale") or "zh-CN").lower()
    defaults = {
        "cover_title": "八字 × 紫微", "cover_subtitle": "人生主题参考报告", "usage": "使用说明", "code": "代号", "generated": "生成日期", "confidence": "置信度",
        "usage_body": "本报告把传统术语翻译成可讨论、可观察的生活倾向。它不替代专业诊疗、心理支持、投资顾问或现实中的沟通与判断。",
        "input_summary": "输入摘要", "calendar": "历法", "solar": "公历", "lunar": "农历",
        "birth_date": "出生日期", "birth_time": "出生时间", "gender": "性别", "birth_place": "出生地",
        "current_location": "目前所在地", "time_window": "时间窗口", "as_of": "截至日期",
        "next_3_years": "未来 3 年", "next_3_months": "未来 3 个月", "chart_summary": "排盘摘要",
        "bazi_pillars": "八字四柱", "day_master": "日主", "wuxing": "五行与旺衰",
        "ziwei": "紫微摘要", "dayun": "十年大运", "basis": "盘面依据", "plain": "解读",
        "crosscheck": "交叉印证", "actions": "可执行建议", "cautions": "补充提醒",
        "disclaimer_title": "免责声明", "reading_note": "整体阅读说明",
        "disclaimer": "本报告基于传统八字与紫微斗数理论框架，仅供文化研究与娱乐参考，不构成医疗、投资、婚姻、法律或其他人生决策依据。命运由个人选择与客观环境共同塑造。",
        "footer": "传统文化参考 · 隐私优先"
    }
    if language.startswith("en"):
        defaults.update({"cover_title": "BaZi × Ziwei", "cover_subtitle": "Life Themes Reference Report", "usage": "How to read",
                         "usage_body": "This report translates traditional terms into discussable life tendencies. It does not replace medical, psychological, financial, or legal advice.",
                         "input_summary": "Input summary", "calendar": "Calendar", "solar": "Solar", "lunar": "Lunar", "code": "Code", "generated": "Generated", "confidence": "Confidence",
                         "birth_date": "Birth date", "birth_time": "Birth time", "gender": "Gender", "birth_place": "Birth place",
                         "current_location": "Current location", "time_window": "Time window", "as_of": "As of",
                         "next_3_years": "Next 3 years", "next_3_months": "Next 3 months", "chart_summary": "Chart summary",
                         "bazi_pillars": "BaZi pillars", "day_master": "Day Master", "wuxing": "Wu Xing and balance",
                         "ziwei": "Ziwei summary", "dayun": "Ten-year luck cycles", "basis": "Chart basis", "plain": "Reading",
                         "crosscheck": "Cross-check", "actions": "Practical actions", "cautions": "Additional notes",
                         "disclaimer_title": "Disclaimer", "reading_note": "How to read this report", "disclaimer": "This report uses traditional BaZi and Ziwei frameworks for cultural and entertainment reference only. It is not medical, investment, relationship, legal, or other decision advice.",
                         "footer": "Cultural reference · Privacy first"})
    defaults.update(labels)
    return defaults


def safe(value):
    if value is None:
        return ""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline_markup(text):
    text = safe(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text


def paragraphs(text, style):
    if text is None:
        return []
    lines = str(text).splitlines() or [""]
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            out.append(Spacer(1, 1.8 * mm))
        elif line.startswith(("- ", "• ", "* ")):
            out.append(Paragraph("• " + inline_markup(line[2:]), style))
        else:
            out.append(Paragraph(inline_markup(line), style))
            out.append(Spacer(1, 1 * mm))
    return out


class ReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename, font_name, labels=None, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates([PageTemplate(id="report", frames=frame, onPage=self._footer)])
        self.font_name = font_name
        self.labels = labels or {}

    def _footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(self.font_name, 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(18 * mm, 10 * mm, self.labels.get("footer", "传统文化参考 · 隐私优先"))
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
        canvas.restoreState()


def make_styles(font):
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("TitleCN", parent=base["Title"], fontName=font, fontSize=23,
                                 leading=31, alignment=TA_CENTER, textColor=ARDOR_INK, spaceAfter=8 * mm),
        "subtitle": ParagraphStyle("SubtitleCN", parent=base["Normal"], fontName=font, fontSize=10,
                                    leading=16, alignment=TA_CENTER, textColor=ARDOR_GREEN, spaceAfter=7 * mm),
        "h1": ParagraphStyle("H1CN", parent=base["Heading1"], fontName=font, fontSize=15.2,
                             leading=20, textColor=ARDOR_INK, spaceBefore=4 * mm, spaceAfter=2.2 * mm),
        "h2": ParagraphStyle("H2CN", parent=base["Heading2"], fontName=font, fontSize=11.2,
                             leading=15, textColor=ARDOR_GREEN, spaceBefore=2.4 * mm, spaceAfter=1.5 * mm),
        "body": ParagraphStyle("BodyCN", parent=base["BodyText"], fontName=font, fontSize=9.2,
                                leading=14.5, textColor=ARDOR_INK, spaceAfter=1 * mm),
        "small": ParagraphStyle("SmallCN", parent=base["BodyText"], fontName=font, fontSize=8,
                                 leading=12, textColor=ARDOR_GREEN),
        "label": ParagraphStyle("LabelCN", parent=base["BodyText"], fontName=font, fontSize=8.5,
                                 leading=13, textColor=ARDOR_GREEN),
        "callout": ParagraphStyle("CalloutCN", parent=base["BodyText"], fontName=font, fontSize=9,
                                   leading=15, textColor=ARDOR_INK, leftIndent=3 * mm, rightIndent=3 * mm),
    }


def two_col_table(rows, styles):
    data = [[Paragraph(inline_markup(k), styles["label"]), Paragraph(inline_markup(v), styles["body"])] for k, v in rows if v not in (None, "", [])]
    if not data:
        return Spacer(1, 1)
    t = Table(data, colWidths=[35 * mm, 135 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), ARDOR_SAGE),
        ("BOX", (0, 0), (-1, -1), 0.5, ARDOR_GREEN),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, ARDOR_SAGE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    return t


def chart_table(chart, styles, labels):
    if not chart:
        return Spacer(1, 1)
    rows = []
    pillars = chart.get("bazi_pillars") or chart.get("pillars")
    if pillars:
        rows.append((labels["bazi_pillars"], "　".join(map(str, pillars))))
    for key, label_key in (("day_master", "day_master"), ("wuxing_summary", "wuxing"), ("ziwei_summary", "ziwei")):
        if chart.get(key):
            rows.append((labels[label_key], chart[key]))
    dayun = chart.get("dayun") or []
    if dayun:
        rows.append((labels["dayun"], "；".join(f"{d.get('period', '')}（{d.get('age', '')}）{d.get('theme', '')}" for d in dayun)))
    return two_col_table(rows, styles)


def build_report(data, output, max_pages=4):
    font = register_cjk_font()
    labels = labels_for(data)
    styles = make_styles(font)
    doc = ReportDocTemplate(output, font, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm, title=labels["cover_subtitle"], labels=labels)
    story = []
    code = data.get("subject_code") or "未命名代号"
    generated = data.get("generated_at") or datetime.now().strftime("%Y-%m-%d")
    story.extend([Spacer(1, 22 * mm), Paragraph(inline_markup(labels["cover_title"]), styles["title"]),
                  Paragraph(inline_markup(labels["cover_subtitle"]), styles["subtitle"]),
                  Paragraph(inline_markup(f"{labels['code']}: {code}  |  {labels['generated']}: {generated}"), styles["subtitle"])])
    method = data.get("method") or ("Traditional BaZi and Ziwei cross-check" if str(data.get("language") or "").lower().startswith("en") else "传统八字与紫微斗数综合印证")
    story.append(Paragraph(inline_markup(method), styles["small"]))
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph(inline_markup(labels["usage"]), styles["h1"]))
    story.extend(paragraphs(labels["usage_body"], styles["callout"]))

    display = data.get("display_birth") or {}
    if display:
        story.append(Paragraph(inline_markup(labels["input_summary"]), styles["h1"]))
        story.append(two_col_table([
            (labels["calendar"], labels["lunar"] if display.get("calendar") == "lunar" else labels["solar"]),
            (labels["birth_date"], display.get("date")), (labels["birth_time"], display.get("time")),
            (labels["gender"], display.get("gender")), (labels["birth_place"], display.get("birth_place")),
            (labels["current_location"], display.get("current_location")),
        ], styles))
    story.append(PageBreak())
    forecast = data.get("forecast") or {}
    if forecast:
        story.append(Paragraph(inline_markup(labels["time_window"]), styles["h1"]))
        y = forecast.get("next_3_years") or {}
        m = forecast.get("next_3_months") or {}
        story.append(two_col_table([
            (labels["as_of"], forecast.get("anchor_date") or data.get("as_of_date")),
            (labels["next_3_years"], f"{y.get('start', '')} 至 {y.get('end', '')}（{', '.join(map(str, y.get('years', [])))}）"),
            (labels["next_3_months"], f"{m.get('start', '')} 至 {m.get('end', '')}"),
        ], styles))
    story.append(Paragraph(inline_markup(labels["chart_summary"]), styles["h1"]))
    story.append(chart_table(data.get("chart") or {}, styles, labels))

    overall_note = data.get("overall_note") or data.get("confidence_note")
    if overall_note:
        story.append(Paragraph(inline_markup(labels.get("reading_note", "整体阅读说明")), styles["h2"]))
        story.extend(paragraphs(overall_note, styles["body"]))

    section_gap = 4 * mm  # one readable blank line between adjacent modules
    for section_index, section in enumerate(data.get("sections") or []):
        if section_index:
            story.append(Spacer(1, section_gap))
        title = section.get("title") or "未命名模块"
        section_intro = [Paragraph(inline_markup(title), styles["h1"])]
        if section.get("basis"):
            section_intro.append(Paragraph(inline_markup(labels["basis"]), styles["h2"]))
            section_intro.extend(paragraphs(section.get("basis"), styles["body"]))
        story.append(KeepTogether(section_intro))
        if section.get("content"):
            story.append(Paragraph(inline_markup("解读" if not str(data.get("language") or "").lower().startswith("en") else "Reading"), styles["h2"]))
            story.extend(paragraphs(section.get("content"), styles["body"]))
        if section.get("evidence"):
            story.append(Paragraph(inline_markup(labels["crosscheck"]), styles["h2"]))
            story.extend(paragraphs(section.get("evidence"), styles["body"]))
        actions = section.get("actions") or []
        if actions:
            story.append(Paragraph(inline_markup(labels["actions"]), styles["h2"]))
            story.extend(paragraphs("\n".join(f"- {x}" for x in actions), styles["body"]))
        cautions = section.get("cautions") or []
        if cautions:
            story.append(Paragraph(inline_markup(labels["cautions"]), styles["h2"]))
            story.extend(paragraphs("\n".join(f"- {x}" for x in cautions), styles["body"]))

    disclaimer = data.get("disclaimer") or labels["disclaimer"]
    disclaimer_style = ParagraphStyle(
        "DisclaimerHeading", parent=styles["h1"], fontSize=12.5, leading=16,
        spaceBefore=1.5 * mm, spaceAfter=1 * mm
    )
    story.append(KeepTogether([
        Paragraph(inline_markup(labels["disclaimer_title"]), disclaimer_style),
        *paragraphs(disclaimer, styles["callout"]),
    ]))
    doc.build(story)
    if PdfReader is None:
        raise RuntimeError("缺少 pypdf，无法核验 A4 页数；请安装 pypdf 后重试")
    pages = len(PdfReader(output).pages)
    if pages > max_pages:
        try:
            os.unlink(output)
        except OSError:
            pass
        raise RuntimeError(f"PDF 共 {pages} 页，超过上限 {max_pages} 页；请先压缩报告内容")
    return font


def main():
    parser = argparse.ArgumentParser(description="Render report.json to a Chinese A4 PDF")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()
    try:
        with open(args.input, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        font = build_report(data, args.output, args.max_pages)
        if font == "Helvetica":
            print("警告：未找到可用中文字体，PDF 可能无法显示中文。", file=sys.stderr)
    except Exception as exc:
        print(f"PDF 渲染失败：{exc}", file=sys.stderr)
        sys.exit(1)
    print(os.path.abspath(args.output))


if __name__ == "__main__":
    main()
