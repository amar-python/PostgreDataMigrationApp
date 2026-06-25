# scripts/

Independent build and test runners. Each can be triggered on its own —
local (PowerShell or Bash) or in GitHub Actions.

## What's here

| File | Purpose | Sibling CI workflow |
| --- | --- | --- |
| `build.ps1` | Windows: build the migration runner Docker image | `.github/workflows/build.yml` |
| `build.sh` | Linux/Mac/Cloud Shell: same | `.github/workflows/build.yml` |
| `test.ps1` | Windows: run pytest + SQL suite + evals | `.github/workflows/test.yml` |
| `test.sh` | Linux/Mac/Cloud Shell: same | `.github/workflows/test.yml` |

## Common recipes

### Local — just build the image

```powershell
.\scripts\build.ps1
```

```bash
./scripts/build.sh
```

Default: local `docker build`, tag `dev`, no push. Add `--acr-build` /
`-UseAcrBuild` if you don't have Docker installed locally.

### Local — full validation before pushing

```powershell
.\scripts\test.ps1                  # all three layers
.\scripts\test.ps1 -OnlyPython      # quick check, no PG needed
.\scripts\test.ps1 -SkipSql         # python + evals, skip SQL suite
```

```bash
./scripts/test.sh
./scripts/test.sh --only-python
./scripts/test.sh --skip-sql
```

### Build and push to ACR in one go

```powershell
.\scripts\build.ps1 -UseAcrBuild -AcrName acrtedev7u8hql -Tag $(git rev-parse --short HEAD)
```

```bash
./scripts/build.sh --acr-build --acr acrtedev7u8hql --push -t $(git rev-parse --short HEAD)
```

### CI — trigger via GitHub web UI

| Workflow | When to use |
| --- | --- |
| **Build (image)** — `build.yml` | After code changes; produces a new image tag |
| **Test (all layers)** — `test.yml` | After build; or any time to verify the deployed env still works |

Open <https://github.com/amar-python/PostgreDataMigrationApp/actions>,
pick the workflow, click **Run workflow**, fill in inputs (defaults are
sensible), click the green button.

## Decision rules

| Situation | Run this |
| --- | --- |
| Pulled new code, no infra changes | `build` only |
| Updated only test fixtures | `test` only |
| Updated `build/csv/validator.py` or any source | `build` then `test` |
| Updated `infra/terraform/*` | `azure-infra-deploy.yml` (separate workflow) |
| End-of-day sanity check | `test -OnlyPython` |
| Before a release | `build` → `test` (full) → manual eyeball |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | All selected layers passed |
| `1` | At least one layer failed |
| `2` | Prereq missing (docker/az/pytest) — fix the env, re-run |

## What each layer covers

| Layer | What it asserts | Needs PG? |
| --- | --- | --- |
| `pytest -m unit` | Python validator correctness (~75 tests) | No |
| SQL test suite | 5 suites x ~87 assertions: schema, indexes, business rules | Yes |
| Tier P evals | 23 CSV validator scenarios end-to-end | No |
| Tier I evals | Idempotency: deploy twice, identical row counts | Yes |
| Tier S evals | SQL suite integration: 85/85 PASS post-deploy | Yes |

## Relationship to the other workflows

| Workflow | Owner / scope |
| --- | --- |
| `build.yml` (new) | Just the deployable image. Manual. |
| `test.yml` (new) | Just the validation layers. Manual. |
| `azure-infra-deploy.yml` (existing) | Terraform plan/apply/destroy for Dev infra |
| `azure-migration-run.yml` (existing) | One-shot: build + deploy + run migration (legacy end-to-end) |
| `azure-prod-*.yml` (existing) | Prod variants with reviewer gates |

The new `build` + `test` workflows give you composable building blocks.
The original `azure-migration-run.yml` still works as a single-button
end-to-end run if you want that.
