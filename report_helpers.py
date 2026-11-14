import os
import docx
from docx import Document
from docx.shared import Pt, Mm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn


def _disable_spellcheck(run):
    """Вимикає червоні/сині хвилясті підкреслення перевірки орфографії у Word."""
    rPr = run._r.get_or_add_rPr()
    if rPr.find(qn("w:noProof")) is None:
        rPr.append(OxmlElement("w:noProof"))


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
    _disable_spellcheck(run)
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

    # Базовий стиль Normal за Додатком Б (Таблиця Б.1, с. 30: Times New Roman 14 pt, міжрядковий інтервал 1.5)
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(14)
    style.font.color.rgb = RGBColor(0, 0, 0)
    rPr = style.element.get_or_add_rPr()
    rPr.append(parse_xml(f'<w:lang {nsdecls("w")} w:val="uk-UA" w:eastAsia="uk-UA" w:bidi="ar-SA"/>'))
    rPr.append(OxmlElement("w:noProof"))
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
        _disable_spellcheck(run)
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
        _disable_spellcheck(r1)
        r2 = p.add_run(rest_text)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(14)
        _disable_spellcheck(r2)
    else:
        r1 = p.add_run("– " + rest_text)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(14)
        _disable_spellcheck(r1)
    return p


def add_abbr_p(doc, term_bold, expansion_italic, definition_text):
    """Оформлення позиції переліку умовних скорочень за ДСТУ 3008:2015 (без подвійних тире, на 1 сторінці)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Mm(12.5)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.22

    r1 = p.add_run(term_bold)
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(14)
    r1.bold = True
    _disable_spellcheck(r1)

    if expansion_italic:
        r_exp1 = p.add_run(" (англ. ")
        r_exp1.font.name = "Times New Roman"
        r_exp1.font.size = Pt(14)
        _disable_spellcheck(r_exp1)

        r_exp2 = p.add_run(expansion_italic)
        r_exp2.font.name = "Times New Roman"
        r_exp2.font.size = Pt(14)
        r_exp2.italic = True
        _disable_spellcheck(r_exp2)

        r_exp3 = p.add_run(")")
        r_exp3.font.name = "Times New Roman"
        r_exp3.font.size = Pt(14)
        _disable_spellcheck(r_exp3)

    r2 = p.add_run(" — " + definition_text)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(14)
    _disable_spellcheck(r2)
    return p


def add_toc_entry(doc, title_text, page_str, is_top=True):
    """Рядок ЗМІСТУ з вирівнюванням крапок-лідерів та номерів сторінок строго по вертикалі (170 мм)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = Mm(0 if is_top else 5)
    p.paragraph_format.first_line_indent = Mm(0)
    p.paragraph_format.space_before = Pt(2 if is_top else 0)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.22

    tab_stops = p.paragraph_format.tab_stops
    tab_stops.add_tab_stop(Mm(170), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)

    r1 = p.add_run(f"{title_text}\t{page_str}")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(14)
    r1.bold = is_top
    r1.font.color.rgb = RGBColor(0, 0, 0)
    _disable_spellcheck(r1)
    return p


def add_structural_heading(doc, title, page_break=True):
    p = doc.add_paragraph()
    if page_break:
        p.paragraph_format.page_break_before = True
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
    _disable_spellcheck(run)
    return p


def add_section_heading(doc, num_and_title, page_break=True):
    p = doc.add_paragraph()
    if page_break:
        p.paragraph_format.page_break_before = True
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
    _disable_spellcheck(run)
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
    _disable_spellcheck(run)
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
    _disable_spellcheck(r1)
    r2 = p.add_run(f"({num_str})")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(14)
    _disable_spellcheck(r2)
    return p


def set_cell_bg(cell, hex_color):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    trPr.append(tblHeader)


def set_row_cant_split(row):
    """Забороняє розривати рядок таблиці між двома сторінками (Таблиця Б.1, с. 30)."""
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn('w:cantSplit')) is None:
        trPr.append(OxmlElement('w:cantSplit'))


def set_table_cell_margins(table, top_dxa=45, bottom_dxa=45, left_dxa=85, right_dxa=85):
    """Встановлює акуратні внутрішні відступи в комірках таблиці (Таблиця Б.1, с. 30)."""
    tblPr = table._tbl.tblPr
    tblCellMar = parse_xml(
        f'<w:tblCellMar {nsdecls("w")}>'
        f'<w:top w:w="{top_dxa}" w:type="dxa"/>'
        f'<w:left w:w="{left_dxa}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom_dxa}" w:type="dxa"/>'
        f'<w:right w:w="{right_dxa}" w:type="dxa"/>'
        f'</w:tblCellMar>'
    )
    tblPr.append(tblCellMar)


def add_styled_table(doc, table_num, table_title, headers, rows, col_widths_mm=None, font_size=12):
    # Підпис таблиці зверху ліворуч без абзацного відступу (Таблиця Б.1, с. 30–31)
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
    _disable_spellcheck(r_cap)

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_cell_margins(table)

    # Для компактних таблиць (до 8 рядків) тримаємо всі рядки разом, щоб таблиця не розривалася між сторінками!
    keep_all_rows_together = len(rows) <= 8

    hdr_row = table.rows[0]
    set_repeat_table_header(hdr_row)
    set_row_cant_split(hdr_row)
    for idx, h_text in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Mm(0)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.keep_with_next = True
        run = p.add_run(str(h_text))
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)
        run.bold = True
        _disable_spellcheck(run)

    for r_idx, r_data in enumerate(rows):
        row_obj = table.rows[r_idx + 1]
        set_row_cant_split(row_obj)
        row_cells = row_obj.cells
        is_last_row = (r_idx == len(rows) - 1)
        keep_next = (keep_all_rows_together and not is_last_row) or (r_idx == 0 and not is_last_row)

        for c_idx, val in enumerate(r_data):
            cell = row_cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent = Mm(0)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.0
            if keep_next:
                p.paragraph_format.keep_with_next = True
            run = p.add_run(str(val))
            run.font.name = "Times New Roman"
            run.font.size = Pt(font_size)
            _disable_spellcheck(run)

    if col_widths_mm:
        for row in table.rows:
            for idx, w_mm in enumerate(col_widths_mm):
                if idx < len(row.cells):
                    row.cells[idx].width = Mm(w_mm)

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

    # За Таблицею Б.1 (с. 30 методички): Підпис рисунка — під рисунком, 12 pt: Рисунок 3.2 — Назва
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.first_line_indent = Mm(0)
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(8)
    p_cap.paragraph_format.line_spacing = 1.15
    run = p_cap.add_run(f"Рисунок {fig_num} — {fig_title}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    _disable_spellcheck(run)


def add_screenshot_placeholder(doc, fig_num, fig_title, instruction_hint):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_row_cant_split(tbl.rows[0])
    cell = tbl.rows[0].cells[0]
    set_cell_bg(cell, "FAFAFA")
    cell.text = ""
    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.first_line_indent = Mm(0)
    p1.paragraph_format.space_before = Pt(18)
    p1.paragraph_format.space_after = Pt(4)
    p1.paragraph_format.keep_with_next = True
    r1 = p1.add_run(f"[ Вставте сюди ваш скріншот для Рисунка {fig_num} ]")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    r1.bold = True
    _disable_spellcheck(r1)

    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.first_line_indent = Mm(0)
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(18)
    p2.paragraph_format.keep_with_next = True
    r2 = p2.add_run(f"Що сфотографувати: {instruction_hint}")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(11)
    r2.italic = True
    _disable_spellcheck(r2)

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.first_line_indent = Mm(0)
    p_cap.paragraph_format.space_before = Pt(4)
    p_cap.paragraph_format.space_after = Pt(8)
    p_cap.paragraph_format.line_spacing = 1.15
    run = p_cap.add_run(f"Рисунок {fig_num} — {fig_title}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    _disable_spellcheck(run)


def add_code_listing(doc, listing_num, listing_title, code_text):
    # За Таблицею Б.1 (с. 30 методички): моноширинний шрифт 11 pt; інтервал 1,0; збережені відступи
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
    _disable_spellcheck(r_cap)

    lines = code_text.strip("\r\n").split("\n")
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    set_table_cell_margins(tbl, top_dxa=50, bottom_dxa=50, left_dxa=100, right_dxa=100)
    if len(lines) <= 30:
        set_row_cant_split(tbl.rows[0])

    cell = tbl.rows[0].cells[0]
    cell.text = ""
    for idx, line in enumerate(lines):
        p = cell.paragraphs[0] if idx == 0 else cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.first_line_indent = Mm(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(11)
        _disable_spellcheck(run)
