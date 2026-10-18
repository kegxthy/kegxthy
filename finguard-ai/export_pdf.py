"""Source-bearing PDF with escaped text and Chinese CID font."""

import io
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def report_pdf(task):
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    style = ParagraphStyle(
        "BodyCN",
        fontName="STSong-Light",
        fontSize=10,
        leading=15,
        wordWrap="CJK",
        spaceAfter=8,
    )
    story = []

    def add(text):
        story.append(Paragraph(escape(str(text)).replace("\n", "<br/>"), style))

    add("FinGuard AI | 财务风险信号 / Financial risk signals")
    add(task["filename"])
    add(task["id"])
    add(task["updated_at"])
    add(
        "需专业复核。不构成审计结论、信用评级或投资建议。 / Human review required. Not an audit, rating or investment advice."
    )

    def heading(title):
        story.append(Spacer(1, 12))
        add(title)

    heading("Confirmed figures / 已确认数据")
    for f in task["figures"]:
        add(
            f"{f['field']}: {f['value']} × {f['scale']} {f['currency']} | {f['period']} | {f['source_id']}"
        )
    heading("Calculated ratios / 确定性计算")
    for name, ratio in task["result"]["ratios"].items():
        add(
            f"{name}: {ratio['value']} | {ratio['formula']} | Sources: {', '.join(ratio['source_ids'])}"
        )
    heading("Risk signals / 风险信号")
    if not task["result"]["signals"]:
        add(
            "No configured rule triggered; this does not establish absence of risk. / 未触发规则不代表不存在风险。"
        )
    for signal in task["result"]["signals"]:
        add(
            f"{signal['code']} | {signal['severity']} | Sources: {', '.join(signal['source_ids'])}"
        )
        if "threshold" in signal:
            add(
                f"{signal['metric']}: {signal['value']} | {signal['operator']} {signal['threshold']} (rule uses unrounded value)"
            )
    heading(
        "Model observations (not independently verified) / 模型解读（未经独立验证）"
    )
    for o in task["result"]["observations"]:
        add(o["text"] + " | " + ", ".join(o["source_ids"]))
    heading("Limitations / 限制")
    for text in task["warnings"] + task["result"]["limitations"]:
        add(text)
    heading("Tool execution / 工具执行")
    for call in task["result"]["tool_trace"]:
        add(call["tool"] + ": completed / 已执行")
    add("Source evidence / 来源证据")
    for f in task["figures"]:
        add(f["source_id"] + ": " + f["quote"])
    out = io.BytesIO()

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(548, 26, str(doc.page))

    SimpleDocTemplate(
        out, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    return out.getvalue()
