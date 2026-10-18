"""Actual FY2024 Apple balance-sheet values, not a model-generated fixture.

Source: https://www.annualreports.com/HostedData/AnnualReportArchive/a/NASDAQ_AAPL_2024.pdf
PDF page 34, printed page 31. Currency USD, millions, fiscal 2024 column.
Only short numeric rows are retained; the full annual report is not vendored.
"""

from decimal import Decimal
from finance import verify, calculate, screen

SOURCE = {
    "id": "page:34",
    "text": "Total current assets 152,987 143,566\nTotal current liabilities 176,392 145,308",
}


def test_public_report_verified_arithmetic():
    figures = [
        {
            "field": field,
            "value": value,
            "period": "2023-10-01/2024-09-28",
            "scope": "consolidated",
            "line_number": 1 if field == "current_assets" else 2,
            "number_index": 0,
            "currency": "USD",
            "scale": 1000000,
            "source_id": "page:34",
            "quote": quote,
        }
        for field, value, quote in [
            ("current_assets", "152987", SOURCE["text"].splitlines()[0]),
            ("current_liabilities", "176392", SOURCE["text"].splitlines()[1]),
        ]
    ]
    valid, bad = verify(figures, [SOURCE])
    assert not bad
    ratios, missing = calculate(valid)
    assert ratios["current_ratio"]["value"] == str(
        (Decimal("152987") / Decimal("176392")).quantize(Decimal(".0001"))
    )
    assert ratios["current_ratio"]["value"] == "0.8673"
    assert screen(valid, ratios)[0]["code"] == "LIQUIDITY"
    assert len(missing) == 3
