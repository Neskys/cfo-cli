"""PDF report writer. reportlab is imported lazily so CSV works without it."""

from datetime import date
from pathlib import Path


class PDFNotAvailable(Exception):
    """Raised when a PDF export is requested but reportlab is not installed."""


def write_pdf(datasets, path, title="cfo-cli financial report") -> Path:
    """Render datasets to a PDF: cover page, one table per section, page numbers."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
        )
    except ImportError:
        raise PDFNotAvailable(
            "PDF export needs 'reportlab'. Install it with: pip install reportlab"
        )

    path = Path(path)
    styles = getSampleStyleSheet()
    story = [Spacer(1, 6 * cm), Paragraph(title, styles["Title"]),
             Paragraph(date.today().isoformat(), styles["Normal"]), PageBreak()]

    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ])
    for i, ds in enumerate(datasets):
        story.append(Paragraph(ds["title"], styles["Heading1"]))
        story.append(Spacer(1, 0.3 * cm))
        data = [ds["headers"]] + [[str(c) for c in row] for row in ds["rows"]]
        table = Table(data, repeatRows=1)
        table.setStyle(table_style)
        story.append(table)
        if i < len(datasets) - 1:
            story.append(PageBreak())

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    frame = Frame(2 * cm, 2 * cm, A4[0] - 4 * cm, A4[1] - 4 * cm, id="main")
    doc = BaseDocTemplate(str(path), pagesize=A4)
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=_footer)])
    doc.build(story)
    return path
