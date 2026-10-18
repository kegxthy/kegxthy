"""Offline parser/math/PDF validation on an independently downloaded Apple FY2024 PDF.

Usage: python validate_public_report.py path/to/NASDAQ_AAPL_2024.pdf --pdf /tmp/offline-check.pdf
This is a specific regression check, not general extraction and not live DeepSeek acceptance.
"""

import argparse
import hashlib
import re
from pathlib import Path
from finance import verify, calculate, screen
from workflow import extract
from export_pdf import report_pdf
from task_store import now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annual_report", type=Path)
    parser.add_argument("--pdf", type=Path, required=True)
    args = parser.parse_args()
    data = args.annual_report.read_bytes()
    sources = extract(data, args.annual_report.name)
    source = next(s for s in sources if s["id"] == "page:34")
    assert "CONSOLIDATED BALANCE SHEETS" in source["text"] and "2024" in source["text"]
    figures = []
    for field, label, expected in [
        ("current_assets", "Total current assets", "152987"),
        ("current_liabilities", "Total current liabilities", "176392"),
    ]:
        line = next(
            line.strip() for line in source["text"].splitlines() if label in line
        )
        value = re.search(r"[\d,]+", line[len(label) :]).group().replace(",", "")
        assert value == expected
        figures.append(
            {
                "field": field,
                "value": value,
                "period": "2023-10-01/2024-09-28",
                "scope": "consolidated",
                "line_number": next(
                    i
                    for i, text in enumerate(source["text"].splitlines(), 1)
                    if text.strip() == line
                ),
                "number_index": 0,
                "currency": "USD",
                "scale": 1000000,
                "source_id": source["id"],
                "quote": line,
            }
        )
    valid, bad = verify(figures, sources)
    assert not bad
    ratios, missing = calculate(valid)
    assert ratios["current_ratio"]["value"] == "0.8673"
    task = {
        "id": "offline-parser-math-export-check",
        "filename": args.annual_report.name,
        "updated_at": now(),
        "figures": valid,
        "sources": sources,
        "warnings": [
            "OFFLINE validation only. Two manually specified balance-sheet rows. No model was called.",
            "离线解析、算术与导出检查。未执行模型分析，不是完整财报风险报告。",
        ],
        "result": {
            "ratios": ratios,
            "signals": screen(valid, ratios),
            "limitations": missing,
            "observations": [],
            "tool_trace": [],
        },
    }
    args.pdf.write_bytes(report_pdf(task))
    print(
        {
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_blocks": len(sources),
            "characters": sum(len(s["text"]) for s in sources),
            "source_id": source["id"],
            "current_ratio": ratios["current_ratio"]["value"],
            "pdf_written": True,
        }
    )


if __name__ == "__main__":
    main()
