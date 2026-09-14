# Intelligent Automation Case Orchestrator v1.0

[![CI](https://github.com/jhostinpastorl-blip/intelligent-automation-case-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/jhostinpastorl-blip/intelligent-automation-case-orchestrator/actions/workflows/ci.yml)

Reference project for **guarded Intelligent Automation** in document-driven enterprise workflows.

The core principle is:

> **LLM recommendation != authorization != execution**

The model interprets unstructured content and returns typed business intent. Deterministic code evaluates policy. Human approval is required for configured risk conditions. Only an application-owned worker can execute an allow-listed tool or hand the approved intent to an API/RPA orchestration layer.

## Business problem
Operations teams receive semi-structured invoices and similar documents. Traditional RPA handles deterministic UI steps well but is brittle for variable language. A fully autonomous AI agent is too risky for enterprise side effects. This project combines both approaches without letting the model control enterprise systems directly.

## Architecture
```text
Document -> FastAPI -> LLM function calling -> Pydantic -> Policy
                                             |
                                             +-> Human approval
                                                     |
                                                     v
                                               Async execution
                                                     |
                                                     v
                                            Controlled tool layer
                                                     |
                                                     v
                                      Automation Orchestrator -> API/RPA
```

## Demonstrated capabilities
- FastAPI + Pydantic contracts
- structured function/tool calling
- prompt/data separation
- deterministic guardrails
- human-in-the-loop
- SQL persistence
- PostgreSQL-compatible state model
- Redis-backed asynchronous dispatch
- execution worker
- append-only audit events
- token/cost telemetry
- optional OpenTelemetry/OTLP tracing
- health/readiness probes
- API-key protection
- versioned evaluation dataset
- regression evaluation gate
- Alembic migrations
- Docker/Compose
- CI configuration
- ADRs for architectural trade-offs

## Why no RAG / multi-agent / MCP?
Because this use case does not need them. RAG would be justified if the workflow had to retrieve enterprise knowledge; multi-agent planning if execution required dynamic open-ended planning; MCP if multiple AI clients needed standardized access to shared tools/resources. Adding them only as keywords would weaken the project.

## Local validation
```bash
pip install -e .[dev]
python scripts/evaluate.py
pytest
```

The deterministic reference evaluation currently defines five regression scenarios: normal low-value processing, high-value review, missing fields, prompt-injection marker and unsupported currency.

## Distributed mode
```text
CASE_DATABASE_URL=postgresql+psycopg://...
DISPATCH_BACKEND=redis
REDIS_URL=redis://...
```

Run:
```bash
docker compose up --build
```

## LLM provider
Default tests use a deterministic fake provider. An OpenAI-compatible provider can be configured with:
```text
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://...
LLM_API_KEY=...
LLM_MODEL=...
LLM_INPUT_COST_PER_MILLION=...
LLM_OUTPUT_COST_PER_MILLION=...
```
The provider is constrained to `submit_structured_case`; that function only returns typed data.

## Integration with Enterprise Automation Orchestrator
After approval, the controlled tool layer may submit an automation request to [Enterprise Automation Orchestrator](https://github.com/jhostinpastorl-blip/enterprise-automation-orchestrator). That project owns retries, API/RPA routing and downstream execution reliability.

## Security scope
Current reference controls include API-key protection, tool allow-list, state validation, schema validation and human approval. Production would still require OAuth/OIDC, RBAC, managed secrets, private networking, PII controls, approval identity, retention policy and security scanning.

## Portfolio interpretation
This project demonstrates Intelligent Automation engineering and AI/software integration. Together with `enterprise-automation-orchestrator`, it supports a positioning beyond RPA-only development while remaining technically defensible. It does not by itself prove formal Lead or Architect seniority.
