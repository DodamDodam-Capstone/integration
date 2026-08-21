# Setup Status and Future Review

Last reviewed: 2026-08-22

## Initial GitHub setup

- [ ] Initial commits pushed to all four repositories
- [ ] `development` branch created in all repositories
- [ ] Squash merge enabled; merge and rebase merge disabled
- [ ] Automatic head-branch deletion disabled
- [ ] `main` and `development` Rulesets active
- [ ] Admin bypass configured as `Always allow`
- [ ] Gitmoji PR title check registered and required
- [ ] Repository quality check registered and required
- [ ] Integration Bot installed on the four repositories
- [ ] Component main merge creates or updates an integration PR

## Slack setup

- [ ] `#frontend-actions` created and connected
- [ ] `#backend-actions` created and connected
- [ ] `#ai-actions` created and connected
- [ ] `#integration-actions` created and connected
- [ ] Success notification tested
- [ ] Failure notification tested
- [ ] Webhook URLs stored only as GitHub Actions secrets

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

- [ ] Pin external Actions to reviewed full commit SHAs
- [ ] Review Dependabot Action updates weekly
- [ ] Enable CodeQL after source languages are present
- [ ] Add secret scanning or Gitleaks policy review
- [ ] Rotate GitHub App private key and Slack webhooks if exposure is suspected
- [ ] Test non-admin direct-push rejection after the first teammate joins
- [ ] Review Ruleset bypass actors after team roles are created
- [ ] Review Slack channel membership after teammates join

## Later AWS phase

- [ ] Decide staging and production topology
- [ ] Add GitHub OIDC; do not store long-lived AWS access keys
- [ ] Add ECR immutable image tags or digests
- [ ] Promote the same tested image digest to production
- [ ] Add deployment concurrency and rollback tests
- [ ] Add CloudWatch and budget alerts

