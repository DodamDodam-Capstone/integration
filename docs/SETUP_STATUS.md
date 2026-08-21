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
- [x] `development` -> `main` source, target, PR, commit, actor, attempt, and
      duration rendered correctly in all four repository channels
- [x] Merged-PR rerun fallback completed successfully in all four repositories
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

### Development promotion and integration verification

- The first promotion test proved that an approval from the most recent pusher
  is rejected by `require_last_push_approval`. Those test PRs were closed and
  recreated with separate pusher and reviewer identities.
- The initial `development` -> `main` promotions passed required CI, received a
  distinct Integration Bot approval, and squash-merged:
  [frontend #6](https://github.com/DodamDodam-Capstone/frontend/pull/6),
  [backend #5](https://github.com/DodamDodam-Capstone/backend/pull/5),
  [ai #5](https://github.com/DodamDodam-Capstone/ai/pull/5), and
  [integration #5](https://github.com/DodamDodam-Capstone/integration/pull/5).
- The Slack metadata hardening was promoted through the same protected flow:
  [frontend #7](https://github.com/DodamDodam-Capstone/frontend/pull/7),
  [backend #6](https://github.com/DodamDodam-Capstone/backend/pull/6),
  [ai #6](https://github.com/DodamDodam-Capstone/ai/pull/6), and
  [integration #9](https://github.com/DodamDodam-Capstone/integration/pull/9).
- The three component promotions dispatched successfully and produced Bot PRs
  [integration #10](https://github.com/DodamDodam-Capstone/integration/pull/10),
  [#11](https://github.com/DodamDodam-Capstone/integration/pull/11), and
  [#12](https://github.com/DodamDodam-Capstone/integration/pull/12). Each was
  updated onto the latest integration `main`, rebuilt, approved, and merged.
- `components.lock.json` now records the exact component merge commits:
  frontend `8e973e292671b4c30f6ce47a5652bef5b7bfcc5b`, backend
  `9efc10d73772f7ca7a59ff336916f0f42b33a3e5`, and AI
  `f599be0f03b583947180b445ba28f1d3d62daecd`.
- A component promotion creates an integration PR; an integration repository
  promotion intentionally does not create a self-referential PR.

### Clean handoff baseline

- [x] Initial Dependabot PRs closed without merging major Action upgrades
- [x] Obsolete setup and promotion test PRs closed
- [x] Component Bot PRs merged and their temporary branches removed manually
- [x] Automatic head-branch deletion remains disabled
- [x] Every repository contains only `main` and `development`
- [x] Every repository has zero open pull requests

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

- [ ] Review newly recreated Dependabot pull requests when they appear. The
      initialization PRs were closed for a clean handoff because they contained
      unreviewed major-version Action upgrades. Prioritize
      `actions/create-github-app-token` v3 and `actions/checkout` v7: current
      pinned versions run successfully but GitHub emits a Node.js 20
      deprecation warning.
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
