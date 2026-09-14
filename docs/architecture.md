# Architecture

## Design goal
Use AI for probabilistic interpretation while keeping business authorization and enterprise execution deterministic, auditable and replaceable.

```text
Untrusted document
      |
      v
FastAPI intake
      |
      v
LLM structured function call
      |
      v
Pydantic validation
      |
      v
Policy engine
      |
      +--> Human review when required
      |
      v
Approved intent
      |
      v
Redis/database dispatch
      |
      v
Execution worker
      |
      v
Application-owned tool
      |
      +--> Enterprise Automation Orchestrator -> API / RPA
```

## Trust boundaries
- Document text is untrusted data.
- Model output is untrusted until schema and policy validation pass.
- Human approval is an explicit authorization event.
- Tools are application-owned and allow-listed.
- The separate Automation Orchestrator owns downstream API/RPA reliability.

## Deliberate exclusions
RAG, MCP and multi-agent planning are not present because the current workflow does not require knowledge retrieval, standardized cross-client tool exposure or open-ended planning.
