import pathlib

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from model.component import ComponentType, ReportComponent
from model.report_config import ReportConfig

_PAGE_WIDTH = A4[0]
_MARGINS = inch
_USABLE_WIDTH = _PAGE_WIDTH - 2 * _MARGINS

_cell_style = ParagraphStyle(
    "table_cell", fontSize=8, leading=9, wordWrap="CJK"
)
_header_style = ParagraphStyle(
    "table_header", fontSize=8, leading=9, wordWrap="CJK",
    textColor=colors.whitesmoke, fontName="Helvetica-Bold",
)


def _col_widths(df) -> list[float]:
    """Distribute usable page width proportionally by max content length per column."""
    lengths = []
    for col in df.columns:
        max_data_len = df[col].str.len().max()
        lengths.append(max(len(str(col)), int(max_data_len) if max_data_len == max_data_len else 1))
    total = sum(lengths) or 1
    return [_USABLE_WIDTH * (l / total) for l in lengths]


def _table_data(df) -> list[list[Paragraph]]:
    header = [Paragraph(str(col), _header_style) for col in df.columns]
    rows = [
        [Paragraph(str(v), _cell_style) for v in row]
        for row in df.itertuples(index=False)
    ]
    return [header] + rows


class ReportDocument:
    def build(self, config: ReportConfig, output_path: pathlib.Path):
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=_MARGINS,
            rightMargin=_MARGINS,
            topMargin=_MARGINS,
            bottomMargin=_MARGINS,
        )
        styles = getSampleStyleSheet()
        story = []

        for component in config.components:
            if component.type == ComponentType.TITLE:
                if component.text:
                    story.append(Paragraph(component.text, styles["Title"]))
                    story.append(Spacer(1, 0.2 * inch))

            elif component.type == ComponentType.TEXT_BLOCK:
                if component.text:
                    story.append(Paragraph(component.text, styles["Normal"]))
                    story.append(Spacer(1, 0.15 * inch))

            elif component.type == ComponentType.TABLE:
                if component.dataframe is not None and not component.dataframe.empty:
                    df = component.dataframe.astype(str)
                    table = Table(_table_data(df), colWidths=_col_widths(df))
                    table.setStyle(TableStyle([
                        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#4a4a4a")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                        ("TOPPADDING",     (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING",  (0, 0), (-1, -1), 2),
                        ("LEFTPADDING",    (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING",   (0, 0), (-1, -1), 0),
                        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 0.1 * inch))

        if not story:
            story.append(Spacer(1, 1))
        doc.build(story)
