# GitHub 협업 및 CI 흐름

최종 검토일: 2026-08-22

## 저장소 역할

- `frontend`: React client source와 frontend CI
- `backend`: Spring Boot source와 backend CI
- `ai`: Python AI 서비스 source와 AI CI
- `integration`: 변경할 수 없는 컴포넌트 버전, Docker Compose, integration CI

integration 저장소는 애플리케이션 source를 복사하지 않습니다.
`components.lock.json`에 전체 commit SHA를 기록하고, 검증할 때 해당
revision을 정확히 checkout합니다.

## 브랜치 흐름

일반 작업 흐름:

```text
feature/* 또는 fix/* -> development -> main
```

긴급 수정은 `main`에서 hotfix branch를 생성하고 `main`에 merge한 다음
`development`에도 반영합니다.

모든 저장소에서 `main`과 `development`를 보호합니다. 관리자가 아닌 사용자는
반드시 PR을 사용해야 하며, 저장소 관리자는 긴급 상황을 위한 우회 권한을
가집니다. 두 보호 브랜치는 force push와 삭제를 차단합니다. 다른 브랜치는
수동으로 삭제할 수 있지만 merge 후 자동 삭제하지 않습니다.

`development`는 장기간 유지하지만 `main` 승격은 squash merge하므로 두
브랜치의 commit 계보가 달라질 수 있습니다. 승격이 완료되면 release 관리자는
PR head 이후 `development`에 새 commit이 없는지, 승격할 파일 변경이 모두
`main`에 있는지 확인한 후 `development`를 결과 `main` commit과 일치시켜야
합니다. 이 절차는 linear history를 유지하면서 다음 승격의 반복 충돌을
방지합니다. 다른 변경이 `development`에 반영 중일 때는 정렬 작업을 하면 안
됩니다.

Dependabot의 GitHub Actions 갱신 PR도 `main`이 아니라 `development`를 대상으로
생성합니다. Bot PR은 Jira 키만 예외이며 Gitmoji, 저장소별 CI, 사람 승인 규칙은
동일하게 적용합니다.

2026-08-22 초기 승격에서 두 보호 branch에 동일 변경을 각각 squash하여 공통
계보가 끊긴 상태를 발견했습니다. 현재 네 저장소의 `development` → `main`
승격 PR은 이 계보 문제로 충돌 상태입니다. 기존 commit을 삭제하는 force push나
보호 branch 직접 push는 사용하지 않습니다. 장기 해법은 `feature/*` →
`development`를 squash로 유지하고 `development` → `main`은 merge commit으로
승격하도록 ruleset을 분리한 뒤, 보호된 PR로 `main` 계보를 `development`에 한 번
합치는 것입니다. 저장소 병합 정책 변경 승인을 받은 뒤 적용하고 이 문서를
완료 상태로 갱신합니다.

## PR 제목

형식:

```text
<Gitmoji> <type>(optional-scope): <description>
```

예시:

```text
🚀 feat: 로그인 흐름 추가
🐛 feat: 사용자 profile 조회 추가
:sparkles: fix(auth): 만료된 token 갱신
```

Gitmoji와 type을 의미상 고정해 연결하지 않습니다. 허용하는 type은 `feat`,
`fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`, `security`,
`revert`, `style`, `build`, `deps`입니다.

## PR 필수 조건

- 한 명 이상의 승인
- 새 commit이 추가되면 기존 승인 무효화
- 가장 최근 push를 수행하지 않은 사용자의 승인
- 모든 review conversation 해결
- target branch의 최신 변경 반영
- 저장소별 quality CI 통과
- `gitmoji-conventional-title` 통과
- squash merge만 허용

## 컴포넌트 승격

`frontend`, `backend`, `ai`의 변경이 `main`에 merge되면 integration 저장소에
`component-main-updated` event를 전송합니다. Integration Bot은
`components.lock.json`의 해당 항목을 갱신합니다. 같은 컴포넌트의 PR이 이미
열려 있으면 기존 Bot branch를 재사용하고 squash auto-merge를 활성화합니다.
단, 필수 검사와 사람의 승인을 통과하기 전에는 merge되지 않습니다.

수신 workflow는 component, repository, 전체 SHA, source workflow URL 형식을
검증하며, 이벤트 SHA가 해당 저장소의 현재 `main`과 다르면 오래된 이벤트로
판단해 PR을 만들지 않습니다. Integration Bot secret이 없으면 성공으로
건너뛰지 않고 workflow를 실패시켜 설정 손상을 Slack에 드러냅니다.

## 개발 환경 버전

Runtime 버전은 각 프로젝트가 직접 관리합니다.

- Frontend: `.nvmrc` or `.node-version`
- Backend: `.java-version`
- AI: `.python-version`

현재 저장소에는 애플리케이션 source가 없습니다. 따라서 workflow는 준비 상태를
확인하고 성공합니다. 프로젝트 source가 추가되었는데 버전 파일, lockfile,
build wrapper가 없으면 CI가 필요한 조치를 포함한 오류 메시지와 함께
실패합니다.

## Slack 알림

| 저장소 | 채널 |
| --- | --- |
| frontend | `#frontend-actions` |
| backend | `#backend-actions` |
| ai | `#ai-actions` |
| integration | `#integration-actions` |

각 저장소는 자신의 채널에 해당하는 Incoming Webhook만
`SLACK_WEBHOOK_URL` Actions secret에 저장합니다. 알림은 별도의
`workflow_run` workflow에서 실행하며 PR code를 checkout하지 않습니다.
알림 helper는 보호된 integration 코드의 검증한 commit SHA로 고정하고
checkout credential을 남기지 않습니다.

모든 메시지는 저장소, workflow, 결과, source branch, target branch, trigger,
PR, commit, actor, 실행 시도 횟수, 소요 시간, Actions 및 PR 링크를
표시합니다. 일반 승격은 `development` → `main`으로 명확하게 표시됩니다.
이미 merge된 PR의 workflow를 다시 실행해 GitHub event에서 PR 정보가 빠지는
경우에는 GitHub API로 commit에 연결된 PR을 조회하여 target branch와 PR
링크를 복구합니다.

Slack webhook은 `hooks.slack.com` HTTPS 주소만 허용하고 일시 오류에는 제한된
재시도를 수행합니다. 사용자 입력이 될 수 있는 branch·actor 텍스트는 Slack
markup을 escape하며, 응답이 HTTP 200과 plain text `ok`일 때만 성공으로
처리합니다. CI, PR 제목, Jira 키, Issue 완료, Component/Integration Sync를
알리고 GitHub Issue→Jira는 생성 결과를 별도 상세 메시지로 알립니다.

외부 GitHub Action은 변경 불가능한 전체 commit SHA로 고정하며 현재
`actions/checkout` v7, `setup-node` v7, `setup-java` v5,
`setup-python` v7, `create-github-app-token` v3처럼 Node.js 24 기반 버전을
사용합니다. Integration Bot은 공개 Client ID와 private key만 사용하고 토큰
권한을 해당 작업의 contents/pull request 범위로 제한합니다.

## 초기 설정 범위에서 제외한 항목

- AWS, ECR, ECS 및 운영 배포
- 운영 secret과 environment
- database provisioning 및 migration 실행
- GPU 및 model 실행 인프라
- Dockerfile과 Compose를 추가하기 전의 실제 Docker integration build

검토 checklist는 [SETUP_STATUS.md](SETUP_STATUS.md)를 참고하세요.
Jira와 GitHub Issue의 권장 연결 방식은
[JIRA_GITHUB_INTEGRATION.md](JIRA_GITHUB_INTEGRATION.md)를 참고하세요.
