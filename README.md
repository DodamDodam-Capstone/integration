# DodamDodam Integration

DodamDodam frontend, backend, AI 서비스의 통합 상태를 관리하는 저장소입니다.

각 컴포넌트의 정확한 commit SHA를 기록하고 Docker Compose build를
검증합니다. 컴포넌트 source code를 이 저장소에 복사하지 않습니다.

GitHub Ruleset, 저장소별 CI, Integration Bot, 저장소별 Slack 알림을 적용하고
전체 흐름을 검증했습니다. 애플리케이션 runtime 버전과 Docker build 정의는
각 서비스가 초기화될 때 결정합니다.

Integration 변경도 보호된 `development` → `main` PR에서 사람의 승인을 받은
후 squash merge합니다. 이 저장소는 컴포넌트 SHA 반영 대상이므로 자체
merge는 다시 integration PR을 생성하지 않습니다.

문서:

- [GitHub 협업 및 CI 흐름](docs/GITHUB_WORKFLOW.md)
- [초기 설정 상태와 추후 검토 사항](docs/SETUP_STATUS.md)
- [Jira와 GitHub Issue 연동 운영 규칙](docs/JIRA_GITHUB_INTEGRATION.md)
