# ADR-0006: PEP 639 license metadata + PyPI Trusted Publishing

- **Status:** Accepted
- **Date:** 2026-06
- **Deciders:** Xavier Potrony

## Context and problem statement

Preparing for a public v1.0 on PyPI, we need (a) license metadata that current
tooling accepts and (b) a release process that is secure and reproducible.

## Decision drivers

- Forward-compatible packaging metadata (modern `twine`/PyPI reject the old
  free-text `License:` field combined with a license classifier).
- No long-lived publishing secret to store or leak.
- Releases gated on the test suite; reproducible from a tag.

## Considered options

- **License:** legacy `license = {text = "MIT"}` + classifier **vs** PEP 639
  `license = "MIT"` + `license-files`.
- **Publishing auth:** a stored PyPI API token **vs** Trusted Publishing (OIDC).

## Decision

Adopt **PEP 639**: `license = "MIT"` plus `license-files = ["LICENSE"]`, dropping
the now-conflicting `License :: OSI Approved` classifier (build emits a clean
`License-Expression: MIT`). Publish via **PyPI Trusted Publishing (OIDC)** in
`release.yml`: a `v*.*.*` tag triggers a build that re-runs the test gate,
verifies the tag matches `cfo.__version__`, `twine check`s, and uploads with no
stored token.

## Consequences

- **Positive:** clean metadata that passes `twine check`; no API token to manage
  or rotate; tamper-resistant, CI-gated releases.
- **Negative / trade-offs:** one-time setup on PyPI (register the trusted
  publisher) and a `pypi` GitHub Environment; documented in the release runbook.
- **Follow-ups:** see [Release runbook](../runbooks/RELEASE.md).
