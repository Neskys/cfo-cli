# Architecture Decision Records

Each ADR captures one significant, hard-to-reverse decision and the reasoning
behind it, so future contributors understand *why* the system is the way it is.
Format: [MADR](https://adr.github.io/madr/). Accepted ADRs are immutable —
supersede, don't rewrite.

| # | Decision | Status |
|---|---|---|
| [0001](ADR-0001-local-first-sqlite.md) | Local-first SQLite storage | Accepted |
| [0002](ADR-0002-layered-service-architecture.md) | Layered architecture with a service layer | Accepted |
| [0003](ADR-0003-numbered-migrations.md) | Numbered, append-only migrations | Accepted |
| [0004](ADR-0004-multi-provider-aggregated-ai.md) | Multi-provider AI, aggregated data only | Accepted |
| [0005](ADR-0005-lazy-imports-optional-extras.md) | Lazy SDK imports behind optional extras | Accepted |
| [0006](ADR-0006-pep639-trusted-publishing.md) | PEP 639 license + PyPI Trusted Publishing | Accepted |

New ADRs start from [`../templates/ADR-0000-template.md`](../templates/ADR-0000-template.md).
