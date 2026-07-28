from __future__ import annotations

import json
from pathlib import Path

from tools.build_layout_masters import ROOT, write_layout_master


OUTPUT = ROOT / "Reference Corpus" / "derived" / "layout-masters"
RUNTIME_OUTPUT = ROOT / "Resources" / "layout-master-runtime.json"
CORPUS = ROOT / "Reference Corpus" / "a-level"

REFERENCES = {
    ("accounting_aqa", "1"): (
        "aqa-accounting",
        "aqa/accounting/accounting-7127/question-papers/AQA-71271-QP-JUN25.PDF",
        "aqa/accounting/accounting-7127/mark-schemes/AQA-71271-MS-JUN25.PDF",
    ),
    ("accounting_aqa", "2"): (
        "aqa-accounting",
        "aqa/accounting/accounting-7127/question-papers/AQA-71272-QP-JUN25.PDF",
        "aqa/accounting/accounting-7127/mark-schemes/AQA-71272-MS-JUN25.PDF",
    ),
    ("business_aqa", "1"): (
        "aqa-business",
        "aqa/business/business-7132/question-papers/AQA-71321-QP-JUN25.PDF",
        "aqa/business/business-7132/mark-schemes/AQA-71321-MS-JUN25.PDF",
    ),
    ("business_aqa", "2"): (
        "aqa-business",
        "aqa/business/business-7132/question-papers/AQA-71322-QP-JUN25.PDF",
        "aqa/business/business-7132/mark-schemes/AQA-71322-MS-JUN25.PDF",
    ),
    ("business_aqa", "3"): (
        "aqa-business",
        "aqa/business/business-7132/question-papers/AQA-71323-QP-JUN25.PDF",
        "aqa/business/business-7132/mark-schemes/AQA-71323-MS-JUN25.PDF",
    ),
    ("economics_aqa", "1"): (
        "aqa-economics",
        "aqa/economics/economics-7136/question-papers/AQA-71361-QP-JUN25.PDF",
        "aqa/economics/economics-7136/mark-schemes/AQA-71361-MS-JUN25.PDF",
    ),
    ("economics_aqa", "2"): (
        "aqa-economics",
        "aqa/economics/economics-7136/question-papers/AQA-71362-QP-JUN25.PDF",
        "aqa/economics/economics-7136/mark-schemes/AQA-71362-MS-JUN25.PDF",
    ),
    ("economics_aqa", "3"): (
        "aqa-economics",
        "aqa/economics/economics-7136/question-papers/AQA-71363-QP-JUN25.PDF",
        "aqa/economics/economics-7136/mark-schemes/AQA-71363-MS-JUN25.PDF",
    ),
    ("computer_science", "1"): (
        "aqa-computer-science",
        "aqa/computer-science/computer-science-7517/question-papers/AQA-75171-QP-JUN25.PDF",
        "aqa/computer-science/computer-science-7517/mark-schemes/AQA-75171-MS-JUN25.PDF",
    ),
    ("computer_science", "2"): (
        "aqa-computer-science",
        "aqa/computer-science/computer-science-7517/question-papers/AQA-75172-QP-JUN25.PDF",
        "aqa/computer-science/computer-science-7517/mark-schemes/AQA-75172-MS-JUN25.PDF",
    ),
    ("computer_science_ocr", "1"): (
        "ocr-computer-science",
        "ocr/computer-science/computer-science-h046-h446-from-2015/question-papers/726571-question-paper-computer-systems.pdf",
        "ocr/computer-science/computer-science-h046-h446-from-2015/mark-schemes/726741-mark-scheme-computer-systems.pdf",
    ),
    ("computer_science_ocr", "2"): (
        "ocr-computer-science",
        "ocr/computer-science/computer-science-h046-h446-from-2015/question-papers/726572-question-paper-algorithms-and-programming.pdf",
        "ocr/computer-science/computer-science-h046-h446-from-2015/mark-schemes/726742-mark-scheme-algorithms-and-programming.pdf",
    ),
    ("economics_ocr", "1"): (
        "ocr-economics",
        "ocr/economics/economics-h060-h460-from-2019/question-papers/726591-question-paper-microeconomics.pdf",
        "ocr/economics/economics-h060-h460-from-2019/mark-schemes/726756-mark-scheme-microeconomics.pdf",
    ),
    ("economics_ocr", "2"): (
        "ocr-economics",
        "ocr/economics/economics-h060-h460-from-2019/question-papers/726592-question-paper-macroeconomics.pdf",
        "ocr/economics/economics-h060-h460-from-2019/mark-schemes/726757-mark-scheme-macroeconomics.pdf",
    ),
    ("economics_ocr", "3"): (
        "ocr-economics",
        "ocr/economics/economics-h060-h460-from-2019/question-papers/726593-question-paper-themes-in-economics.pdf",
        "ocr/economics/economics-h060-h460-from-2019/mark-schemes/726758-mark-scheme-themes-in-economics.pdf",
    ),
    ("economics", "1"): (
        "edexcel-economics",
        "pearson-edexcel/economics-a-2015/al15-economics-a/question-papers/9ec0-01-que-20240516.pdf",
        "pearson-edexcel/economics-a-2015/al15-economics-a/mark-schemes/9ec0-01-rms-20240815.pdf",
    ),
    ("economics", "2"): (
        "edexcel-economics",
        "pearson-edexcel/economics-a-2015/al15-economics-a/question-papers/9ec0-02-que-20240521.pdf",
        "pearson-edexcel/economics-a-2015/al15-economics-a/mark-schemes/9ec0-02-rms-20240815.pdf",
    ),
    ("economics", "3"): (
        "edexcel-economics",
        "pearson-edexcel/economics-a-2015/al15-economics-a/question-papers/9ec0-03-que-20240608.pdf",
        "pearson-edexcel/economics-a-2015/al15-economics-a/mark-schemes/9ec0-03-rms-20240815.pdf",
    ),
}


def main() -> int:
    registry: dict[str, object] = {
        "schema_version": 1,
        "derived_reference_data_only": True,
        "copyrighted_text_included": False,
        "papers": {},
    }
    papers = registry["papers"]
    assert isinstance(papers, dict)
    for (subject, paper), (family, question, scheme) in REFERENCES.items():
        destination = OUTPUT / family / f"paper-{paper}"
        question_output = destination / "question-paper.json"
        scheme_output = destination / "mark-scheme.json"
        write_layout_master(
            CORPUS / question,
            question_output,
            family=family,
            paper=paper,
            document_role="question-paper",
        )
        write_layout_master(
            CORPUS / scheme,
            scheme_output,
            family=family,
            paper=paper,
            document_role="mark-scheme",
        )
        question_payload = json.loads(question_output.read_text(encoding="utf-8"))
        scheme_payload = json.loads(scheme_output.read_text(encoding="utf-8"))
        papers[f"{subject}:{paper}"] = {
            "family": family,
            "question-paper": {
                "page_count": len(question_payload["pages"]),
                "page_boxes": [
                    page["boxes"] for page in question_payload["pages"]
                ],
            },
            "mark-scheme": {
                "page_count": len(scheme_payload["pages"]),
                "page_boxes": [
                    page["boxes"] for page in scheme_payload["pages"]
                ],
            },
        }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    RUNTIME_OUTPUT.write_text(
        json.dumps(registry, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(REFERENCES) * 2} masters for {len(REFERENCES)} papers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
