# Setup Status and Future Review

Last reviewed: 2026-08-22

## Initial GitHub setup

- [x] Initial commits pushed to all four repositories
- [x] `development` branch created in all repositories
- [x] Squash merge enabled; merge and rebase merge disabled
- [x] Automatic head-branch deletion disabled
- [x] `main` and `development` Rulesets active
- [x] Organization-admin bypass configured as `Always allow`
- [x] Gitmoji PR title check registered and required
- [x] Repository quality check registered and required
- [x] Integration Bot installed on exactly the four repositories
- [x] Component main merge creates or updates an integration PR

### Applied identifiers

| Item | Value |
| --- | --- |
| GitHub App | `DodamDodam Integration Bot` |
| GitHub App slug | `dodamdodam-integration-bot` |
| GitHub App ID | `4673621` |
| Frontend Ruleset | `21153783` |
| Backend Ruleset | `21153778` |
| AI Ruleset | `21153782` |
| Integration Ruleset | `21153781` |

The GitHub App has repository metadata read plus Contents and Pull Requests
read/write access. Webhooks are disabled. Its ID and private key are stored as
repository Actions secrets; no private key is committed.

## Slack setup

- [x] `#frontend-actions` created and connected
- [x] `#backend-actions` created and connected
- [x] `#ai-actions` created and connected
- [x] `#integration-actions` created and connected
- [x] Success notification tested in all four channels
- [x] Failure notification tested in `#frontend-actions`
- [x] Webhook URLs stored only as GitHub Actions secrets

Slack App: `DodamDodam GitHub Actions` (`A0BRVD5EF0S`). Each public channel has
its own Incoming Webhook, and each repository stores only its matching URL.

## Verification evidence

- All four readiness CI workflows completed successfully using
  `workflow_dispatch` before application source was present.
- Frontend test PR
  [#4](https://github.com/DodamDodam-Capstone/frontend/pull/4) failed with the
  invalid title `docs: validate automation`, and the failure reached
  `#frontend-actions`.
- Renaming the PR to `📝 docs: validate automation` passed
  `gitmoji-conventional-title`; `frontend-quality` also passed.
- With checks green but no review, GitHub reported `REVIEW_REQUIRED` and blocked
  normal merge. An organization admin then exercised the configured emergency
  bypass and squash-merged the setup document.
- That merge triggered the GitHub App, which created integration PR
  [#3](https://github.com/DodamDodam-Capstone/integration/pull/3), enabled squash
  auto-merge, passed `docker-compose-build` readiness and Gitmoji checks, waited
  for a human approval, and merged automatically after approval.
- Re-dispatching a component SHA that is already locked is idempotent: the sync
  succeeds without creating an empty commit or duplicate pull request.
- The merged source branch remained present, confirming that automatic branch
  deletion is disabled.

## When each project is initialized

### Frontend

- [ ] Add `.nvmrc` or `.node-version`
- [ ] Commit exactly one supported package-manager lockfile
- [ ] Define `lint`, `typecheck`, `test`, and `build` scripts as applicable
- [ ] Add a production Dockerfile when integration build work begins

### Backend

- [ ] Add `.java-version`
- [ ] Commit the Gradle or Maven wrapper
- [ ] Add unit and integration tests
- [ ] Add health and readiness endpoints
- [ ] Add a production Dockerfile

### AI

- [ ] Add `.python-version`
- [ ] Choose and commit `uv.lock`, `requirements.txt`, or `pyproject.toml`
- [ ] Configure Ruff and pytest
- [ ] Document model and dataset provenance
- [ ] Keep large model files and datasets out of Git
- [ ] Add a production Dockerfile

### Integration

- [ ] Add Compose configuration using `.components/frontend`,
      `.components/backend`, and `.components/ai` build contexts
- [ ] Add service health checks
- [ ] Add `docker compose up --wait` smoke testing
- [ ] Add backend-to-AI contract tests
- [ ] Add frontend-to-backend end-to-end tests

## Security and maintenance review

- [x] Pin external Actions to reviewed full commit SHAs
- [ ] Review Dependabot Action updates weekly
- [ ] Enable CodeQL after source languages are present
- [ ] Add secret scanning or Gitleaks policy review
- [ ] Rotate GitHub App private key and Slack webhooks if exposure is suspected
- [ ] Test non-admin direct-push rejection after the first teammate joins
- [ ] Review Ruleset bypass actors after team roles are created
- [ ] Review Slack channel membership after teammates join

## Immediate follow-up review

- [ ] Review the Dependabot pull requests opened during initialization. They
      include major-version Action updates and must not be merged without
      checking release notes and immutable replacement SHAs.
- [ ] Permanently remove the recoverable local GitHub App private-key copy from
      Trash after the setup handoff is accepted. GitHub retains one active key,
      and the working credential is already stored in Actions secrets.
- [ ] Decide whether merged feature branches will be removed manually on a
      sprint cadence; GitHub will intentionally not delete them automatically.
- [ ] Re-run the invalid-title and non-admin direct-push tests with a regular
      organization member after invitations are sent.

## Later AWS phase

- [ ] Decide staging and production topology
- [ ] Add GitHub OIDC; do not store long-lived AWS access keys
- [ ] Add ECR immutable image tags or digests
- [ ] Promote the same tested image digest to production
- [ ] Add deployment concurrency and rollback tests
- [ ] Add CloudWatch and budget alerts
