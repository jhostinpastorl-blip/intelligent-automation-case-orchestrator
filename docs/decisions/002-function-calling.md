# ADR 002: Function calling is a data boundary, not an execution authority

## Status
Accepted

The provider is constrained to `submit_structured_case`. The function returns typed extraction data only.

Enterprise side effects remain application-owned and require deterministic policy plus optional human approval.
