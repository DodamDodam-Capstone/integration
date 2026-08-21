# DodamDodam Integration

Integration control repository for the DodamDodam frontend, backend, and AI
services.

This repository will track exact component commit SHAs and validate the Docker
Compose build. It does not copy component source code.

The initial GitHub Rulesets, repository CI, Integration Bot, and per-repository
Slack notifications are applied and end-to-end verified. Application runtime
versions and Docker build definitions remain intentionally deferred until each
service is initialized.

Integration changes are also promoted from `development` to `main` through a
protected, human-approved squash pull request. This repository is the promotion
target for component SHAs, so its own merge does not create a self-referential
integration PR.

Documentation:

- [GitHub collaboration and CI workflow](docs/GITHUB_WORKFLOW.md)
- [Setup status and future review](docs/SETUP_STATUS.md)
