# Runbook: cutting a release

- **Owner:** maintainer
- **Last reviewed:** 2026-06-01

> How to publish a new version of cfo-cli to PyPI. Automated by
> `.github/workflows/release.yml` (Trusted Publishing). See
> [ADR-0006](../adr/ADR-0006-pep639-trusted-publishing.md) for the why.

## Scope

Publishing a tagged version to PyPI. Not covered: feature development, hotfix
branching policy.

## Prerequisites (one-time setup)

1. A PyPI account that owns (or will own) the `cfo-cli` project.
2. Register the **Trusted Publisher** at
   <https://pypi.org/manage/account/publishing/>:
   - Project: `cfo-cli` · Owner: `Neskys` · Repo: `cfo-cli`
   - Workflow: `release.yml` · Environment: `pypi`
3. In GitHub → Settings → Environments, create an environment named **`pypi`**
   (optionally with required reviewers to gate each publish).

## Procedure

1. **Make sure `main` is green** (CI passing) and you're on it:
   ```bash
   git checkout main && git pull origin main
   ```
2. **Bump the version in both files — they must match** (the workflow enforces it):
   - `pyproject.toml` → `version = "X.Y.Z"`
   - `cfo/__init__.py` → `__version__ = "X.Y.Z"`
3. **Move the CHANGELOG** `[Unreleased]` items under a new `## [X.Y.Z]` heading and
   update the compare links at the bottom.
4. **Commit** the bump:
   ```bash
   git commit -am "release: vX.Y.Z" && git push origin main
   ```
5. **Tag and push** (this triggers the release workflow):
   ```bash
   git tag vX.Y.Z && git push origin vX.Y.Z
   ```
6. **Watch the Actions run.** The workflow re-runs the test gate, verifies the tag
   matches `cfo.__version__`, builds sdist+wheel, `twine check`s, and publishes.

## Verification

- The Actions run for the tag is green, `publish` job included.
- The version appears at <https://pypi.org/project/cfo-cli/>.
- A clean install works:
  ```bash
  pip install --no-cache-dir cfo-cli==X.Y.Z && cfo version
  ```

## Rollback / recovery

**A PyPI version is permanent — you cannot overwrite it.** If a release is bad:

1. **Yank** the broken version on PyPI (hides it from new installs without
   breaking pins): project → Manage → Releases → *Yank*.
2. **Fix forward:** bump to the next patch (`X.Y.Z+1`), repeat the procedure.
3. Never attempt to re-upload the same version number.

## Common failures

| Symptom | Likely cause | Action |
|---|---|---|
| `Tag vX does not match package version Y` | Forgot to bump one of the two files | Fix the file, delete & re-push the tag. |
| `twine check` fails on metadata | Stale build tooling | The workflow uses `pip install -U build twine`; re-run. |
| `publish` step: OIDC / permission error | Trusted publisher or `pypi` environment not set up | Complete the one-time setup above. |
| Tests fail in the release run | A regression slipped onto `main` | Fix on `main`, re-tag. |

## Escalation

If publishing is blocked by PyPI itself (name dispute, account issue), contact
PyPI support; do not work around it with a different package name without an ADR.
