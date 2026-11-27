import argparse
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)


def inline(text):
    value = escape(text)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    return value


def styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=17, spaceAfter=10, textColor=colors.HexColor("#1F3864")),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#1F3864")),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=10.5, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=9, leading=12, spaceAfter=5),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontSize=7.5, leading=9.5),
        "note": ParagraphStyle("note", parent=base["BodyText"], fontSize=8, textColor=colors.HexColor("#7F6000")),
        "code": ParagraphStyle("code", parent=base["Code"], fontSize=7, leading=8.5, backColor=colors.HexColor("#F2F2F2")),
    }


def separador(row):
    return re.fullmatch(r"[\s:\-|]+", row.strip().strip("|")) is not None


def tabla(rows, style):
    cabeceras = [cell.strip() for cell in rows[0].strip().strip("|").split("|")]
    data_rows = rows[2:] if len(rows) > 1 and separador(rows[1]) else rows[1:]
    cells = [[Paragraph(inline(cell), style) for cell in cabeceras]]
    for row in data_rows:
        values = [cell.strip() for cell in row.strip().strip("|").split("|")]
        values += [""] * (len(cabeceras) - len(values))
        cells.append([Paragraph(inline(value), style) for value in values[:len(cabeceras)]])
    width = letter[0] - 4 * cm
    table = Table(cells, colWidths=[width / len(cabeceras)] * len(cabeceras), repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B0B0")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def convertir(ruta):
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    style = styles()
    story = []
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if linea.startswith("```"):
            lenguaje = linea[3:].strip()
            bloque = []
            i += 1
            while i < len(lineas) and not lineas[i].startswith("```"):
                bloque.append(lineas[i])
                i += 1
            i += 1
            if lenguaje == "mermaid":
                story.append(Paragraph("Diagrama Mermaid: disponible en docs/arquitectura.md", style["note"]))
            else:
                story.append(XPreformatted("\n".join(bloque), style["code"]))
            story.append(Spacer(1, 5))
            continue
        if linea.startswith("|") and i + 1 < len(lineas) and lineas[i + 1].startswith("|"):
            bloque = []
            while i < len(lineas) and lineas[i].startswith("|"):
                bloque.append(lineas[i])
                i += 1
            story.append(tabla(bloque, style["small"]))
            story.append(Spacer(1, 6))
            continue
        cabecera = re.match(r"^(#{1,3})\s+(.*)$", linea)
        if cabecera:
            nivel = len(cabecera.group(1))
            story.append(Paragraph(inline(cabecera.group(2)), style[f"h{nivel}"]))
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", linea):
            items = []
            while i < len(lineas) and re.match(r"^\s*[-*]\s+", lineas[i]):
                texto = re.sub(r"^\s*[-*]\s+", "", lineas[i])
                items.append(ListItem(Paragraph(inline(texto), style["body"])))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", start="-", leftIndent=14))
            continue
        if re.match(r"^\s*\d+\.\s+", linea):
            items = []
            while i < len(lineas) and re.match(r"^\s*\d+\.\s+", lineas[i]):
                texto = re.sub(r"^\s*\d+\.\s+", "", lineas[i])
                items.append(ListItem(Paragraph(inline(texto), style["body"])))
                i += 1
            story.append(ListFlowable(items, bulletType="1", leftIndent=14))
            continue
        if not linea.strip():
            i += 1
            continue
        parrafo = [linea.strip()]
        i += 1
        while i < len(lineas) and lineas[i].strip() and not lineas[i].startswith(("```", "|", "#")) and not re.match(r"^\s*([-*]|\d+\.)\s+", lineas[i]):
            parrafo.append(lineas[i].strip())
            i += 1
        story.append(Paragraph(inline(" ".join(parrafo)), style["body"]))
    return story


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.1 * cm, "CCU4 Grupo 4 · BORRADOR · Johana (SRE)")
    canvas.drawRightString(letter[0] - 2 * cm, 1.1 * cm, f"Página {doc.page}")
    canvas.restoreState()


def main():
    parser = argparse.ArgumentParser(description="Genera el PDF editable del reporte final.")
    parser.add_argument("--input", default="docs/CCU4-FinalProject-4.md")
    parser.add_argument("--output", default="CCU4-FinalProject-4.pdf")
    args = parser.parse_args()

    destino = Path(args.output)
    destino.parent.mkdir(parents=True, exist_ok=True)
    documento = SimpleDocTemplate(
        str(destino),
        pagesize=letter,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title="CCU4 Final Project 4 (BORRADOR)",
        author="Johana - Site Reliability Engineer",
    )
    documento.build(convertir(Path(args.input)), onFirstPage=pie, onLaterPages=pie)
    print(f"PDF generado: {destino}")


if __name__ == "__main__":
    main()
