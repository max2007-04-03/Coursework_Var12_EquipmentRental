import os
import docx
from docx import Document
from docx.shared import Pt, Mm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def init_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.left_margin = Mm(25)
    section.right_margin = Mm(15)
    section.top_margin = Mm(20)
    section.bottom_margin = Mm(20)
    section.different_first_page_header_footer = True

    # Нижній колонтитул з номером сторінки по центру (12 pt Times New Roman, без номера на титульному аркуші)
    footer = section.footer
    p_ftr = footer.paragraphs[0]
    p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ftr.paragraph_format.first_line_indent = Mm(0)
    p_ftr.paragraph_format.space_before = Pt(0)
    p_ftr.paragraph_format.space_after = Pt(0)
    run = p_ftr.add_run()
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = "PAGE"
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

    # Базовий стиль Normal за Додатком Б (Times New Roman 14 pt, міжрядковий інтервал 1.5)
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(14)
    style.font.color.rgb = RGBColor(0, 0, 0)
    return doc

def add_body_p(doc, text, bold=False, italic=False, indent_mm=12.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=0, line_spacing=1.5, font_size=14):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.first_line_indent = Mm(indent_mm)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)
        run.bold = bold
        run.italic = italic
        run.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_bullet_p(doc, bold_prefix, rest_text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Mm(12.5)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.5
    if bold_prefix:
        r1 = p.add_run("– " + bold_prefix)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(14)
        r1.bold = True
        r2 = p.add_run(rest_text)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(14)
    else:
        r1 = p.add_run("– " + rest_text)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(14)
    return p

def add_structural_heading(doc, title, page_break=True):
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Mm(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.keep_with_next = True
    run = p.add_run(title.upper())
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_section_heading(doc, num_and_title, page_break=True):
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Mm(12.5)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.keep_with_next = True
    run = p.add_run(num_and_title.upper())
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_subsection_heading(doc, num_and_title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Mm(12.5)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.keep_with_next = True
    run = p.add_run(num_and_title)
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_formula(doc, expr_text, num_str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Mm(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    r1 = p.add_run(expr_text + "        ")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(14)
    r1.italic = True
    r2 = p.add_run(f"({num_str})")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(14)
    return p

def set_cell_bg(cell, hex_color):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    trPr.append(tblHeader)

def add_styled_table(doc, table_num, table_title, headers, rows, col_widths_mm=None, font_size=12):
    # Підпис таблиці зверху ліворуч без абзацного відступу (Додаток Б, с. 31)
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.first_line_indent = Mm(0)
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(4)
    p_cap.paragraph_format.line_spacing = 1.15
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(f"Таблиця {table_num} — {table_title}")
    r_cap.font.name = "Times New Roman"
    r_cap.font.size = Pt(14)

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr_row = table.rows[0]
    set_repeat_table_header(hdr_row)
    for idx, h_text in enumerate(headers):
        cell = hdr_row.cells[idx]
        set_cell_bg(cell, "E2E8F0")
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Mm(0)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(str(h_text))
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)
        run.bold = True

    for r_idx, r_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(r_data):
            cell = row_cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent = Mm(0)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.0
            run = p.add_run(str(val))
            run.font.name = "Times New Roman"
            run.font.size = Pt(font_size)

    if col_widths_mm:
        for row in table.rows:
            for idx, w_mm in enumerate(col_widths_mm):
                if idx < len(row.cells):
                    row.cells[idx].width = Mm(w_mm)

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(6)
    p_sp.paragraph_format.line_spacing = 1.0
    return table

def add_figure(doc, img_path, fig_num, fig_title, width_mm=155):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.first_line_indent = Mm(0)
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        p_img.paragraph_format.keep_with_next = True
        p_img.add_run().add_picture(img_path, width=Mm(width_mm))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.first_line_indent = Mm(0)
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(8)
    p_cap.paragraph_format.line_spacing = 1.15
    run = p_cap.add_run(f"Рисунок {fig_num} — {fig_title}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)

def add_screenshot_placeholder(doc, fig_num, fig_title, instruction_hint):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    set_cell_bg(cell, "FAFAFA")
    cell.text = ""
    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.first_line_indent = Mm(0)
    p1.paragraph_format.space_before = Pt(18)
    p1.paragraph_format.space_after = Pt(4)
    r1 = p1.add_run(f"[ Вставте сюди ваш скріншот для Рисунка {fig_num} ]")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    r1.bold = True

    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.first_line_indent = Mm(0)
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(18)
    r2 = p2.add_run(f"Що сфотографувати: {instruction_hint}")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(11)
    r2.italic = True

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.first_line_indent = Mm(0)
    p_cap.paragraph_format.space_before = Pt(4)
    p_cap.paragraph_format.space_after = Pt(8)
    p_cap.paragraph_format.line_spacing = 1.15
    run = p_cap.add_run(f"Рисунок {fig_num} — {fig_title}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)

def add_code_listing(doc, listing_num, listing_title, code_text):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_cap.paragraph_format.first_line_indent = Mm(0)
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.line_spacing = 1.15
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(f"Лістинг {listing_num} — {listing_title}")
    r_cap.font.name = "Times New Roman"
    r_cap.font.size = Pt(14)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    cell = tbl.rows[0].cells[0]
    set_cell_bg(cell, "F8FAFC")
    cell.text = ""
    lines = code_text.strip("\r\n").split("\n")
    for idx, line in enumerate(lines):
        p = cell.paragraphs[0] if idx == 0 else cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.first_line_indent = Mm(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0.5)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(10.5)

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(6)
    p_sp.paragraph_format.line_spacing = 1.0
