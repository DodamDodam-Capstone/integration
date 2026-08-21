# GitHub Collaboration and CI Workflow

Last reviewed: 2026-08-22

## Repository roles

- `frontend`: React client source and frontend CI
- `backend`: Spring Boot source and backend CI
- `ai`: Python AI service source and AI CI
- `integration`: immutable component versions, Docker Compose, and integration CI

The integration repository never copies application source. It records full
commit SHAs in `components.lock.json` and checks out those exact revisions for
validation.

## Branch flow

Normal work follows:

```text
feature/* or fix/* -> development -> main
```

Urgent fixes branch from `main`, merge back to `main`, and are then synchronized
to `development`.

`main` and `development` are protected in every repository. Non-admin users
must use pull requests. Repository administrators retain an emergency bypass.
Force pushes and deletion are blocked only for these two protected branches.
Other branches may be deleted manually, but are not deleted automatically after
merge.

## Pull request titles

Use:

```text
<any Gitmoji> <type>(optional-scope): <description>
```

Examples:

```text
🚀 feat: add login flow
🐛 feat: add user profile lookup
:sparkles: fix(auth): refresh expired tokens
```

The Gitmoji is not semantically paired with the type. The accepted types are
`feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`, `security`,
`revert`, `style`, `build`, and `deps`.

## Required pull request conditions

- One approving review
- Dismiss stale approvals after new commits
- Approval of the most recent reviewable push
- Resolve all conversations
- Bring the branch up to date
- Pass repository quality CI
- Pass `gitmoji-conventional-title`
- Squash merge only

## Component promotion

Merging `frontend`, `backend`, or `ai` to `main` sends a
`component-main-updated` event to the integration repository. The Integration
Bot updates the matching entry in `components.lock.json`, reuses the component's
bot branch when a PR is already open, and enables squash auto-merge. Auto-merge
still waits for required checks and a human approval.

## Development versions

Runtime versions intentionally remain owned by each project:

- Frontend: `.nvmrc` or `.node-version`
- Backend: `.java-version`
- AI: `.python-version`

The current repositories contain no application source. Their workflows report
readiness successfully. When project source is added without its version file
or lockfile/build wrapper, CI fails with an actionable message.

## Slack notifications

| Repository | Channel |
| --- | --- |
| frontend | `#frontend-actions` |
| backend | `#backend-actions` |
| ai | `#ai-actions` |
| integration | `#integration-actions` |

Each repository stores only the Incoming Webhook for its own channel in the
`SLACK_WEBHOOK_URL` Actions secret. Notifications run from a separate
`workflow_run` workflow and never check out pull-request code.

## Out of scope for the initial setup

- AWS, ECR, ECS, and production deployment
- Production secrets and environments
- Database provisioning and migration execution
- GPU/model execution infrastructure
- Actual Docker integration build before Dockerfiles and Compose are added

See [SETUP_STATUS.md](SETUP_STATUS.md) for the review checklist.

