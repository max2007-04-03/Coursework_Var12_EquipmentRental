import os
import sys
from report_helpers import init_document
from report_part1 import build_front_matter, build_section_1, build_section_2
from report_part2 import build_section_3
from report_part3 import build_section_4, build_section_5, build_conclusions_and_refs, build_appendices

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    docx_path = os.path.join(root_dir, "Пояснювальна_записка_Сливка_АІ-243_Варіант12.docx")

    print("Generating Coursework Explanatory Note (.docx)...")
    doc = init_document()
    build_front_matter(doc)
    build_section_1(doc, root_dir)
    build_section_2(doc, root_dir)
    build_section_3(doc, root_dir)
    build_section_4(doc, root_dir)
    build_section_5(doc, root_dir)
    build_conclusions_and_refs(doc)
    build_appendices(doc)

    doc.save(docx_path)
    print(f"Saved DOCX: {docx_path}")

if __name__ == "__main__":
    main()
