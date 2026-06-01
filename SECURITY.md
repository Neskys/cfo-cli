# Security Policy

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately via GitHub's **[Private vulnerability reporting](https://github.com/Neskys/cfo-cli/security/advisories/new)**
(Security tab → *Report a vulnerability*), or email **xavipotrony@gmail.com** with
the details and, if possible, a minimal reproduction.

You can expect an acknowledgement within a few days. Once a fix is ready it will
ship as a patch release and the issue will be credited (unless you prefer to
remain anonymous).

## Supported versions

cfo-cli is pre-1.0 and single-maintained; security fixes target the **latest
released version**. Please upgrade to the newest version before reporting.

## Threat model (summary)

cfo-cli is a **local-first CLI** with no server and no cloud component. The
relevant surfaces are:

| Surface | Exposure | Mitigation |
|---|---|---|
| **Local data** (`~/.cfo/data.db`, `config.json`) | Financial data + API keys at rest | Lives only under the OS user's home; never transmitted except for the explicit FX/AI calls below. |
| **API keys** | Stored in `~/.cfo/config.json` | Sent only to the matching provider; never logged. Treat the file as a secret; OS file permissions apply. |
| **AI requests** | Aggregated figures sent to a hosted provider | **Aggregated data only** — never raw transactions ([ADR-0004](docs/adr/ADR-0004-multi-provider-aggregated-ai.md)). The `local` provider keeps everything on-device. |
| **FX rate fetch** | Outbound HTTP to a third-party API | Response is validated before use; failures fall back to cached rates. |
| **Supply chain** | Installation from PyPI | Published via **Trusted Publishing (OIDC)** — no long-lived token; releases gated on CI ([ADR-0006](docs/adr/ADR-0006-pep639-trusted-publishing.md)). |
| **Optional SDKs** | `reportlab`, `anthropic`, `openai` | Lazy-imported behind extras, reducing the default attack surface. |

### Out of scope

- Encryption-at-rest of `~/.cfo/` (rely on OS/disk encryption). If you share a
  machine, protect your user account.
- Multi-user access control (cfo-cli is single-user by design).

## Good practices for users

- Keep `~/.cfo/config.json` private; it may contain API keys.
- Prefer the **`local`** AI provider for maximum privacy (nothing leaves the
  machine).
- Keep cfo-cli updated to receive fixes.
