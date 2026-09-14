from app.models import ExtractedCase, ToolCall

ALLOWED_TOOLS = {"create_invoice_case"}


def evaluate_policy(extraction: ExtractedCase) -> tuple[bool, list[str], ToolCall | None]:
    reasons = []

    required = {
        "supplier": extraction.supplier,
        "invoice_number": extraction.invoice_number,
        "invoice_date": extraction.invoice_date,
        "currency": extraction.currency,
        "total_amount": extraction.total_amount,
    }
    missing = [name for name, value in required.items() if value in (None, "")]
    if missing:
        reasons.append(f"missing_required_fields:{','.join(sorted(missing))}")

    if extraction.currency not in {None, "USD", "EUR", "PEN"}:
        reasons.append("unsupported_currency")
    if extraction.confidence < 0.80:
        reasons.append("low_confidence")
    if "prompt_injection_marker" in extraction.risk_flags:
        reasons.append("prompt_injection_marker")
    if extraction.total_amount is not None and extraction.total_amount >= 10_000:
        reasons.append("high_value_requires_approval")

    if extraction.recommended_action not in ALLOWED_TOOLS:
        reasons.append("tool_not_allowlisted")
        return True, reasons, None

    return bool(reasons), reasons, ToolCall(
        tool_name=extraction.recommended_action,
        arguments={
            "supplier": extraction.supplier,
            "invoice_number": extraction.invoice_number,
            "currency": extraction.currency,
            "total_amount": extraction.total_amount,
            "purchase_order": extraction.purchase_order,
        },
    )
