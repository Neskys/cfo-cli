# cfo-cli documentation

Engineering and product documentation for **cfo-cli**. This index explains what
each document type is for and **when to reach for which** — the part teams
usually forget.

## Document types

| Type | Question it answers | Lives in | When to write one |
|---|---|---|---|
| **PRD** — Product Requirements | *What are we building and why? For whom?* | [`prd/`](prd/) | Before a sizeable feature/product bet; product-facing, not engineering. |
| **RFC** — Request for Comments | *Should we do this? What are the options?* | [`rfcs/`](rfcs/) | To propose a change and gather feedback **before** committing to a design. |
| **ADR** — Architecture Decision Record | *What did we decide, and why?* | [`adr/`](adr/) | Whenever a decision is hard to reverse or future-you will ask "why is it like this?". One decision per file, immutable once accepted. |
| **Tech Spec** | *How exactly will we build it?* | [`specs/`](specs/) | After an RFC is accepted, to detail the implementation. |
| **System Design** | *What does the whole system look like?* (components, communication, data growth, security, dependencies) | [`design/`](design/) | Engineering view of the system as a whole. Distinct from the PRD. |
| **Runbook** | *How do we operate this in production?* | [`runbooks/`](runbooks/) | Operational procedures: releasing, incident handling, recovery. |
| **Post-mortem** | *What happened, and what did we learn?* | [`postmortems/`](postmortems/) | After any incident. **Blameless** — root cause, impact, lessons. |

Other docs: [`GLOSSARY.md`](GLOSSARY.md) (domain terms), [`IDEAS.md`](IDEAS.md)
(uncommitted future ideas). Project conventions live in
[`../CLAUDE.md`](../CLAUDE.md); contribution flow in
[`../CONTRIBUTING.md`](../CONTRIBUTING.md).

## How a feature flows through these docs

```
idea ──► RFC (should we? options) ──► ADR (the decisions taken)
                                  └──► Tech Spec (how to build) ──► code + tests
```

Not every change needs the full chain. A one-line fix needs none; a new command
group typically warrants at least an ADR; a large feature (e.g. the interactive
console) warrants an RFC **and** a Tech Spec.

## Conventions

- **Numbering:** zero-padded, monotonic per type — `RFC-0001`, `ADR-0001`,
  `TS-0001`. Never reuse a number.
- **Status:** every RFC/ADR/Spec carries a status header
  (`Draft` → `Accepted`/`Rejected` → `Superseded by …`).
- **Immutability:** accepted ADRs are not rewritten; supersede them with a new
  ADR and cross-link.
- **Templates:** start from [`templates/`](templates/) — copy, renumber, fill in.
- **Diagrams as code:** prefer Mermaid fenced blocks so diagrams live in version
  control and render on GitHub and the docs site.
