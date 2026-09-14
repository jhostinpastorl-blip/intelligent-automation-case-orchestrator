import os
from typing import Any

import httpx

from app.models import ToolCall


def execute_tool(call: ToolCall) -> dict[str, Any]:
    if call.tool_name != "create_invoice_case":
        raise ValueError(f"Tool '{call.tool_name}' is not executable")

    orchestrator_url = os.getenv("AUTOMATION_ORCHESTRATOR_URL")
    if not orchestrator_url:
        return {
            "tool": call.tool_name,
            "status": "simulated_success",
            "external_reference": f"SIM-{call.arguments.get('invoice_number') or 'UNKNOWN'}",
        }

    payload = {
        "process": "invoice_case_creation",
        "target": os.getenv("AUTOMATION_TARGET", "erp"),
        "execution_channel": os.getenv("AUTOMATION_EXECUTION_CHANNEL", "api"),
        "payload": call.arguments,
        "idempotency_key": f"invoice-{call.arguments.get('invoice_number') or 'unknown'}",
        "max_attempts": 3,
    }
    headers = {}
    if os.getenv("AUTOMATION_ORCHESTRATOR_API_KEY"):
        headers["X-API-Key"] = os.environ["AUTOMATION_ORCHESTRATOR_API_KEY"]

    response = httpx.post(
        f"{orchestrator_url.rstrip('/')}/automation-requests",
        json=payload,
        headers=headers,
        timeout=10.0,
    )
    response.raise_for_status()
    body = response.json()
    return {
        "tool": call.tool_name,
        "status": "submitted_to_automation_orchestrator",
        "request_id": body["request_id"],
        "orchestrator_status": body["status"],
    }
