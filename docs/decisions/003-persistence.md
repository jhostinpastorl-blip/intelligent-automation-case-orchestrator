# ADR 003: Persist workflow state, audit and usage

## Status
Accepted

Persist case lifecycle, append-only audit events and token/cost usage in SQL.

SQLite is the local reference implementation. Production should use managed persistent SQL and migrations.
