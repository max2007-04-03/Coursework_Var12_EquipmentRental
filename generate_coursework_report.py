import os
import sys
import json
import subprocess
from report_helpers import init_document
from report_part1 import build_front_matter, build_section_1, build_section_2
from report_part2 import build_section_3
from report_part3 import build_section_4, build_section_5, build_conclusions_and_refs, build_appendices


def build_full_docx(root_dir, docx_path, toc_pages=None, total_pages=66):
    doc = init_document()
    build_front_matter(doc, toc_pages=toc_pages, total_pages=total_pages)
    build_section_1(doc, root_dir)
    build_section_2(doc, root_dir)
    build_section_3(doc, root_dir)
    build_section_4(doc, root_dir)
    build_section_5(doc, root_dir)
    build_conclusions_and_refs(doc)
    build_appendices(doc)
    doc.save(docx_path)


def extract_exact_pages_and_export_pdf(docx_path, pdf_path, export_pdf=False):
    ps_script = f"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    try {{
        $doc = $word.Documents.Open("{docx_path}", $false, $false)
        $doc.Repaginate()
        $totalPages = $doc.ComputeStatistics(2)
        $result = @{{ totalPages = $totalPages; headings = @{{}} }}
        $pastToc = $false
        foreach ($p in $doc.Paragraphs) {{
            $txt = $p.Range.Text.Trim()
            if (-not $txt) {{ continue }}
            if ($txt -eq "ПЕРЕЛІК УМОВНИХ СКОРОЧЕНЬ І ТЕРМІНІВ" -and -not ($txt -match "\\t")) {{
                $pastToc = $true
            }}
            if ($pastToc -and -not ($txt -match "\\t")) {{
                $pg = $p.Range.Information(3)
                $clean = $txt -replace "[\\r\\n]+", " "
                if ($clean.Length -le 95 -and -not $result.headings.ContainsKey($clean)) {{
                    $result.headings[$clean] = $pg
                }}
            }}
        }}
        if (${'true' if export_pdf else 'false'}) {{
            $doc.Save()
            $doc.ExportAsFixedFormat("{pdf_path}", 17)
        }}
        $doc.Close($false)
        $result | ConvertTo-Json -Depth 4 -Compress
    }} finally {{
        $word.Quit()
    }}
    """
    proc = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", ps_script],
        capture_output=True, text=True, encoding="utf-8"
    )
    if proc.returncode != 0:
        print("Word COM warning:", proc.stderr)
        return None
    for line in reversed(proc.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    return None


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    docx_path = os.path.join(root_dir, "Пояснювальна_записка_Сливка_АІ-243_Варіант12.docx")
    pdf_path = os.path.join(root_dir, "Пояснювальна_записка_Сливка_АІ-243_Варіант12.pdf")

    print("Pass 1: Generating initial DOCX to compute exact page numbers...")
    build_full_docx(root_dir, docx_path)

    print("Querying Microsoft Word for exact pagination...")
    info = extract_exact_pages_and_export_pdf(docx_path, pdf_path, export_pdf=False)
    if info:
        total_pages = info.get("totalPages", 66)
        headings_map = info.get("headings", {})
        # Нормалізуємо назви додатків (де в заголовку був перенос рядка)
        toc_pages = {}
        for k, v in headings_map.items():
            toc_pages[k] = v
            if k.startswith("ДОДАТОК А"):
                toc_pages["ДОДАТОК А Супровідна документація вебсистеми"] = v
            elif k.startswith("ДОДАТОК Б"):
                toc_pages["ДОДАТОК Б Матриці відповідності та протокол приймання"] = v
            elif k.startswith("ДОДАТОК В"):
                toc_pages["ДОДАТОК В Лістинги ключових модулів та схеми БД"] = v

        print(f"Detected exact total pages: {total_pages}")
        for k in sorted(toc_pages.keys()):
            if any(k.startswith(prefix) for prefix in ["ПЕРЕЛІК", "ВСТУП", "1", "2", "3", "4", "5", "ВИСНОВКИ", "ДОДАТОК"]):
                print(f"  {k} -> p. {toc_pages[k]}")

        print("Pass 2: Rebuilding DOCX with 100% exact page numbers and exporting PDF...")
        build_full_docx(root_dir, docx_path, toc_pages=toc_pages, total_pages=total_pages)
        extract_exact_pages_and_export_pdf(docx_path, pdf_path, export_pdf=True)
        print(f"Successfully saved DOCX and PDF: {pdf_path}")
    else:
        print("Saved DOCX (without Word COM pagination).")


if __name__ == "__main__":
    main()
