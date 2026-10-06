"""Styled PDF export: title page, linked TOC, headed sections, footers."""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                HRFlowable)
from reportlab.platypus.tableofcontents import TableOfContents as TOCClass

ACCENT = HexColor("#0284c7")


def _styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle("DocTitle", parent=base["Title"], fontSize=22, textColor=ACCENT,
                           spaceAfter=4 * mm, alignment=TA_CENTER)
    h1 = ParagraphStyle("H1", parent=base["Heading1"], fontSize=15, textColor=ACCENT,
                        spaceBefore=6 * mm, spaceAfter=3 * mm, keepWithNext=True)
    h2 = ParagraphStyle("H2", parent=base["Heading2"], fontSize=12.5, textColor=HexColor("#0f172a"),
                        spaceBefore=4 * mm, spaceAfter=2 * mm, keepWithNext=True)
    h3 = ParagraphStyle("H3", parent=base["Heading3"], fontSize=11, textColor=HexColor("#334155"),
                        spaceBefore=3 * mm, spaceAfter=2 * mm)
    normal = ParagraphStyle("Body", parent=base["Normal"], fontSize=10, leading=14,
                            spaceAfter=2 * mm)
    toc_h = ParagraphStyle("TOCH", parent=base["Normal"], fontSize=13, textColor=ACCENT,
                           spaceAfter=2 * mm)
    return title, h1, h2, h3, normal, toc_h


class DocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style in ("H1", "H2"):
                level = 0 if style == "H1" else 1
                text = flowable.getPlainText()
                self.notify("TOCEntry", (level, text, self.page))
                try:
                    key = f"h{self.page}-{abs(hash(text)) % 99999}"
                    self.canv.bookmarkPage(key)
                except Exception:
                    pass


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#64748b"))
    canvas.drawCentredString(A4[0] / 2, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def md_to_story(md: str, title: str):
    title_s, h1, h2, h3, normal, toc_h = _styles()
    story = [Paragraph(title, title_s), HRFlowable(width="100%", color=ACCENT),
             Spacer(1, 4 * mm)]
    story += [Paragraph("Table of Contents", toc_h)]
    toc = TOCClass()
    toc.levelStyles = [
        ParagraphStyle("toc0", fontSize=11, leading=14, leftIndent=0),
        ParagraphStyle("toc1", fontSize=10, leading=13, leftIndent=12),
    ]
    story += [toc, Spacer(1, 4 * mm)]
    for line in (md or "").splitlines():
        s = line.strip()
        if not s:
            story.append(Spacer(1, 2 * mm))
        elif s.startswith("# "):
            story.append(Paragraph(re.sub(r"^#+\s*", "", s), h1))
        elif s.startswith("## "):
            story.append(Paragraph(re.sub(r"^#+\s*", "", s), h2))
        elif s.startswith("### "):
            story.append(Paragraph(re.sub(r"^#+\s*", "", s), h3))
        elif s.startswith(("- ", "* ")):
            story.append(Paragraph("• " + s[2:], normal))
        else:
            # escape minimal HTML chars for Paragraph
            esc = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(esc, normal))
    return story


def make_pdf(md: str, out_path: str, title: str = "Study Notes"):
    doc = DocTemplate(out_path, pagesize=A4,
                      topMargin=18 * mm, bottomMargin=18 * mm,
                      leftMargin=16 * mm, rightMargin=16 * mm,
                      title=title, author="Generation System")
    doc.build(md_to_story(md, title), onFirstPage=_footer, onLaterPages=_footer)
    return out_path
