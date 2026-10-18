"""Validated evidence, Decimal arithmetic, and transparent screening rules."""

from decimal import Decimal, InvalidOperation, localcontext
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

FIELDS = (
    "revenue",
    "net_profit",
    "operating_cash_flow",
    "accounts_receivable",
    "current_assets",
    "current_liabilities",
    "total_assets",
    "total_liabilities",
)


class Figure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    value: str = Field(max_length=60)
    period: str = Field(min_length=1, max_length=80)
    currency: str = Field(min_length=1, max_length=20)
    scale: int = Field(default=1)
    source_id: str = Field(min_length=1, max_length=300)
    quote: str = Field(min_length=1, max_length=1500)

    @field_validator("field")
    @classmethod
    def known_field(cls, value):
        if value not in FIELDS:
            raise ValueError("Unknown field")
        return value

    @field_validator("value")
    @classmethod
    def number(cls, value):
        try:
            number = Decimal(value)
        except InvalidOperation:
            raise ValueError("Invalid decimal")
        if not number.is_finite() or abs(number) > Decimal("1e20"):
            raise ValueError("Number out of bounds")
        if number.as_tuple().exponent < -12:
            raise ValueError("Maximum 12 decimal places")
        return str(number)

    @field_validator("scale")
    @classmethod
    def unit(cls, value):
        if value not in (1, 1000, 10000, 1000000, 100000000, 1000000000):
            raise ValueError("Unsupported scale")
        return value


def verify(figures, sources):
    """Check verbatim evidence and number presence; human still verifies table semantics."""
    valid, rejected = [], []
    for raw in figures:
        try:
            f = Figure.model_validate(raw)
            source = next(s for s in sources if s["id"] == f.source_id)
            if f.quote not in source["text"]:
                raise ValueError("Quote absent from source")
            numbers = re.findall(r"\(?-?\d[\d,]*(?:\.\d+)?\)?", f.quote)
            values = [
                Decimal(n.replace(",", "").replace("(", "-").replace(")", ""))
                for n in numbers
            ]
            if Decimal(f.value) not in values:
                raise ValueError("Value absent from quote")
            valid.append(f.model_dump())
        except (ValueError, StopIteration, TypeError):
            rejected.append(
                "Extraction rejected: invalid schema, source, quote, or number"
            )
    return valid, rejected


RATIOS = {
    "current_ratio": ("current_assets", "current_liabilities"),
    "debt_to_assets": ("total_liabilities", "total_assets"),
    "cash_to_profit": ("operating_cash_flow", "net_profit"),
    "receivables_to_revenue": ("accounts_receivable", "revenue"),
}


def calculate(figures):
    by_field = {}
    for f in figures:
        by_field.setdefault(f["field"], []).append(f)
    ratios, missing = {}, []
    for name, (a, b) in RATIOS.items():
        if len(by_field.get(a, [])) != 1 or len(by_field.get(b, [])) != 1:
            missing.append(f"{name}: missing or ambiguous inputs")
            continue
        x, y = by_field[a][0], by_field[b][0]
        if (x["period"], x["currency"]) != (y["period"], y["currency"]):
            missing.append(f"{name}: period/currency mismatch")
            continue
        denominator = Decimal(y["value"]) * y["scale"]
        if denominator <= 0:
            missing.append(f"{name}: denominator must be positive")
            continue
        with localcontext() as context:
            context.prec = 80
            value = Decimal(x["value"]) * x["scale"] / denominator
            rounded = str(value.quantize(Decimal(".0001")))
        ratios[name] = {
            "value": rounded,
            "unrounded": str(value),
            "formula": f"{a} / {b}",
            "inputs": [a, b],
            "source_ids": list(dict.fromkeys([x["source_id"], y["source_id"]])),
        }
    return ratios, missing


def screen(figures, ratios):
    signals = []
    for name, op, threshold, code in (
        ("current_ratio", "lt", "1", "LIQUIDITY"),
        ("debt_to_assets", "gt", ".70", "LEVERAGE"),
        ("receivables_to_revenue", "gt", ".35", "RECEIVABLES"),
    ):
        if name in ratios:
            v = Decimal(ratios[name]["unrounded"])
            if (op == "lt" and v < Decimal(threshold)) or (
                op == "gt" and v > Decimal(threshold)
            ):
                signals.append(
                    {
                        "code": code,
                        "severity": "medium",
                        "metric": name,
                        "threshold": threshold,
                        "operator": op,
                        **ratios[name],
                    }
                )
    by = {f["field"]: f for f in figures}
    if all(k in by for k in ("net_profit", "operating_cash_flow")):
        p, c = by["net_profit"], by["operating_cash_flow"]
        if (p["period"], p["currency"]) == (c["period"], c["currency"]) and Decimal(
            c["value"]
        ) < 0 < Decimal(p["value"]):
            signals.append(
                {
                    "code": "CASH_PROFIT_DIVERGENCE",
                    "severity": "high",
                    "source_ids": [p["source_id"], c["source_id"]],
                }
            )
    return signals
