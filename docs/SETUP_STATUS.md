# 초기 설정 상태와 추후 검토 사항

최종 검토일: 2026-08-24

## GitHub 초기 설정

- [x] 네 저장소에 초기 commit 반영
- [x] 모든 저장소에 `development` branch 생성
- [x] squash merge 활성화, merge commit과 rebase merge 비활성화
- [x] merge 후 source branch 자동 삭제 비활성화
- [x] `main`, `development` Ruleset 활성화
- [x] Organization 관리자 우회를 `Always allow`로 설정
- [x] Organization 기본 멤버 권한 `Read`, 일반 Issue 삭제 비활성화 확인
- [x] Gitmoji PR 제목 검사를 필수 검사로 등록
- [x] 저장소별 quality 검사를 필수 검사로 등록
- [x] Integration Bot을 정확히 네 저장소에 설치
- [x] 컴포넌트 `main` merge 시 integration PR 생성 또는 갱신

### 적용 식별자

| 항목 | 값 |
| --- | --- |
| GitHub App | `DodamDodam Integration Bot` |
| GitHub App slug | `dodamdodam-integration-bot` |
| GitHub App ID | `4673621` |
| Frontend Ruleset | `21153783` |
| Backend Ruleset | `21153778` |
| AI Ruleset | `21153782` |
| Integration Ruleset | `21153781` |

GitHub App에는 저장소 metadata read, Contents read/write, Pull Requests
read/write 권한이 있습니다. App webhook은 비활성화되어 있습니다. 공개 Client
ID는 workflow에 기록하고 private key만 저장소 Actions secret으로 보관하며
private key를 commit하지 않았습니다. 생성되는 installation token은 integration
한 저장소와 현재 단계에 필요한 contents/pull request 권한으로 제한합니다.

## Slack 설정

- [x] `#frontend-actions` 생성 및 연결
- [x] `#backend-actions` 생성 및 연결
- [x] `#ai-actions` 생성 및 연결
- [x] `#integration-actions` 생성 및 연결
- [x] 네 채널에서 성공 알림 검증
- [x] `#frontend-actions`에서 실패 알림 검증
- [x] 네 채널에서 `development` → `main`, source, target, PR, commit, actor,
      attempt, duration 표시 검증
- [x] 네 저장소에서 merge된 PR 재실행 시 fallback 검증
- [x] Webhook URL을 GitHub Actions secret에만 저장

Slack App은 `DodamDodam GitHub Actions` (`A0BRVD5EF0S`)입니다. 각 공개
채널은 별도의 Incoming Webhook을 사용하고, 각 저장소에는 자신의 채널과
일치하는 URL만 저장합니다.

## 검증 결과

- 애플리케이션 source가 없는 상태에서 `workflow_dispatch`로 네 readiness CI를
  실행하고 성공을 확인했습니다.
- Frontend test PR
  [#4](https://github.com/DodamDodam-Capstone/frontend/pull/4)는 잘못된 제목
  `docs: validate automation`으로 실패했고, 실패 알림이
  `#frontend-actions`에 도착했습니다.
- PR 제목을 `📝 docs: validate automation`으로 변경한 후
  `gitmoji-conventional-title`과 `frontend-quality`가 통과했습니다.
- 검사가 성공했지만 승인이 없을 때 GitHub가 `REVIEW_REQUIRED`로 일반 merge를
  차단했습니다. 이후 Organization 관리자가 설정된 긴급 우회를 사용해 설정
  문서를 squash merge했습니다.
- 해당 merge가 GitHub App을 실행하여 integration PR
  [#3](https://github.com/DodamDodam-Capstone/integration/pull/3)을 생성했습니다.
  squash auto-merge를 활성화하고 `docker-compose-build` readiness 검사와
  Gitmoji 검사를 통과한 후 사람의 승인을 기다렸다가 자동으로 merge했습니다.
- 이미 lock된 컴포넌트 SHA를 다시 dispatch해도 빈 commit이나 중복 PR을
  생성하지 않고 성공하는 멱등성을 확인했습니다.
- merge된 source branch가 유지되어 자동 branch 삭제가 꺼져 있음을
  확인했습니다.

### Development 승격 및 integration 검증

- 첫 승격 검사에서 가장 최근 push를 수행한 사용자의 승인이
  `require_last_push_approval` 규칙으로 거부되는 것을 확인했습니다. 해당 test
  PR을 닫고 pusher와 reviewer가 다른 PR로 다시 생성했습니다.
- 초기 `development` → `main` 승격은 필수 CI와 별도 Integration Bot 승인을
  통과한 후 squash merge했습니다.
  [frontend #6](https://github.com/DodamDodam-Capstone/frontend/pull/6),
  [backend #5](https://github.com/DodamDodam-Capstone/backend/pull/5),
  [ai #5](https://github.com/DodamDodam-Capstone/ai/pull/5),
  [integration #5](https://github.com/DodamDodam-Capstone/integration/pull/5).
- Slack metadata 보완도 같은 보호 흐름으로 승격했습니다.
  [frontend #7](https://github.com/DodamDodam-Capstone/frontend/pull/7),
  [backend #6](https://github.com/DodamDodam-Capstone/backend/pull/6),
  [ai #6](https://github.com/DodamDodam-Capstone/ai/pull/6),
  [integration #9](https://github.com/DodamDodam-Capstone/integration/pull/9).
- 세 컴포넌트 승격이 정상적으로 dispatch되어 다음 Bot PR을 생성했습니다.
  [integration #10](https://github.com/DodamDodam-Capstone/integration/pull/10),
  [#11](https://github.com/DodamDodam-Capstone/integration/pull/11), and
  [#12](https://github.com/DodamDodam-Capstone/integration/pull/12). 각 PR을 최신
  integration `main`에 맞춘 후 build, 승인, merge를 완료했습니다.
- `components.lock.json`에는 컴포넌트의 정확한 merge commit을 기록합니다.
  현재 frontend `a7891d2d4ee2049e6c123f1049aa2e04fd635428`, backend
  `91a11b309940b4efaafef11508e0fe0b86789b13`, AI
  `a8fb5fd878953a62859df27c3205f3d920cd4ce0`입니다.
- 컴포넌트 승격은 integration PR을 생성하지만, integration 저장소의 승격은
  자기 자신을 대상으로 하는 PR을 생성하지 않습니다.

### 한국어 문서 및 Jira 연동 반영

- 네 저장소의 README, 기여 지침, 보안 정책, PR 템플릿을 한국어 중심으로
  정리했습니다. 명령어, 파일명, GitHub UI 명칭처럼 번역하면 오히려 모호한
  기술 식별자는 원문을 유지했습니다.
- 문서 승격 PR
  [frontend #8](https://github.com/DodamDodam-Capstone/frontend/pull/8),
  [backend #7](https://github.com/DodamDodam-Capstone/backend/pull/7),
  [ai #7](https://github.com/DodamDodam-Capstone/ai/pull/7),
  [integration #13](https://github.com/DodamDodam-Capstone/integration/pull/13)을
  필수 CI와 별도 승인 후 squash merge했습니다.
- 세 컴포넌트의 최종 merge SHA가 integration PR
  [#14](https://github.com/DodamDodam-Capstone/integration/pull/14),
  [#15](https://github.com/DodamDodam-Capstone/integration/pull/15),
  [#16](https://github.com/DodamDodam-Capstone/integration/pull/16)으로 순차
  반영되었고, 각 PR의 Docker Compose build와 Gitmoji 검사가 통과했습니다.
- Jira Epic → GitHub 상위 이슈 → 저장소별 하위 이슈 구조와 완료 자동화 규칙은
  [`JIRA_GITHUB_INTEGRATION.md`](JIRA_GITHUB_INTEGRATION.md)에 기록했습니다.

### Jira·GitHub 실제 연결 및 검증

- [x] Jira `SCRUM` 프로젝트에 공식 `GitHub for Atlassian` App 설치
- [x] `DodamDodam-Capstone`의 네 저장소만 선택하여 연결
- [x] repository backfill `FINISHED`, permissions `FULL ACCESS` 확인
- [x] `SCRUM-1` Epic과 저장소별 `SCRUM-2`~`SCRUM-5` Task 생성 및 상위 관계 연결
- [x] GitHub `integration#18` 상위 이슈와 네 저장소 하위 이슈 연결
- [x] Team Board Gantt에서 Epic 아래 네 Task가 `1.1`~`1.4`로 표시되는 것 확인
- [x] 기능 branch, commit, PR, CI build가 Jira Development panel에 연결되는 것 확인
- [x] 네 저장소에 Jira 키와 저장소 접두어를 검사하는 `jira-issue-key` 추가
- [x] 네 Ruleset의 필수 status check에 `jira-issue-key` 등록
- [x] `development` merge 시 PR 본문의 같은 저장소 이슈를 닫는 workflow 추가
- [x] 컴포넌트 `main` merge의 Jira 키를 integration Bot PR까지 전달하도록 확장
- [x] Jira Automation `PR 병합 시 Task 완료` 활성화
- [x] PR 승인·병합, GitHub Issue 종료, Jira Task 완료, Team Board 반영 검증
- [x] scoped `read:jira-work`, `write:jira-work` 토큰으로 조직 Actions Secret 교체
- [x] 네 저장소 Task·Bug Issue Form과 integration Epic Form 추가
- [x] GitHub Issue → Jira 생성 → GitHub 링크 기록 → Slack 알림 자동화 추가
- [x] 실제 테스트 Issue로 네 저장소 종단간 자동 생성 검증

GitHub Issue 자동 생성 구축은 Jira `SCRUM-6` Epic 아래 저장소별 `SCRUM-7`
(Frontend), `SCRUM-8`(Backend), `SCRUM-9`(AI), `SCRUM-10`(Integration) Task로
추적합니다. 중앙 스크립트는 integration에서 관리하며 네 workflow가 같은
보호된 `integration/main` 코드를 사용합니다. API 토큰은 2027-08-21 만료 전에
교체해야 합니다.

2026-08-22 종단간 재검증에서 frontend#15 → `SCRUM-11`, backend#14 →
`SCRUM-12`, ai#14 → `SCRUM-13`, integration#37 → `SCRUM-14`가 생성되었습니다.
네 업무 모두 `SCRUM-6` Epic 아래 Task로 연결됐고 GitHub 제목, 자동 링크 댓글,
`jira-linked`, `jira-notified`, 저장소별 Slack Source/Target 알림을 확인했습니다.
frontend#15를 반복 실행해 Jira와 댓글이 중복되지 않는 것도 확인했습니다.
새 토큰 저장 후 기존 토큰을 철회하고 다시 실행해 새 토큰 단독 동작도
확인했습니다.
`integration#48`에서는 `jira-skip`을 수동 재실행해 Jira 업무, 링크 댓글,
연결 레이블을 만들지 않고 성공 종료하는 것을 확인한 뒤 테스트 Issue를
닫았습니다.

검증에 사용한 기능 PR은
[frontend #10](https://github.com/DodamDodam-Capstone/frontend/pull/10),
[backend #9](https://github.com/DodamDodam-Capstone/backend/pull/9),
[ai #9](https://github.com/DodamDodam-Capstone/ai/pull/9),
[integration #20](https://github.com/DodamDodam-Capstone/integration/pull/20)입니다.
Jira에서는 branch, commit, 열린 PR 및 성공한 build가 연결되었습니다. PR 검토
승인은 GitHub의 보호 규칙에서 판정하며, Jira 개발 상세에도 승인된 사용자와
`MERGED` 상태가 표시되는 것을 확인했습니다.

완료 자동화 검증은
[integration #24](https://github.com/DodamDodam-Capstone/integration/pull/24)로
수행했습니다. `development` 병합 후 `integration#19`가 자동으로 종료되고 Jira
`SCRUM-5`가 `완료`로 전환되었습니다. 이어
[frontend #12](https://github.com/DodamDodam-Capstone/frontend/pull/12),
[backend #11](https://github.com/DodamDodam-Capstone/backend/pull/11),
[ai #11](https://github.com/DodamDodam-Capstone/ai/pull/11)로 저장소별 workflow도
검증했습니다. 각 GitHub Task가 자동 종료되고 Jira `SCRUM-2`~`SCRUM-4`가
`완료`로 전환되었으며 저장소별 Slack 알림도 성공했습니다.

네 sub-issue가 모두 닫힌 후 GitHub `integration#18`과 Jira `SCRUM-1` Epic을
수동 완료했습니다. Epic은 `issuetype != Epic` JQL 조건으로 자동 완료 대상에서
제외됩니다. Team Board의 기본 View는 완료 업무를 숨겨 최종
`0/0 work item`처럼 보였지만 데이터가 삭제된 것은 아니었습니다.
`Show completed tickets`를 켠 뒤 새로 고침해 `SCRUM-1`~`SCRUM-10`이 모두
남아 있고 완료 업무가 `완료` 상태로 표시되는 것을 확인했습니다.
`SCRUM-11`~`SCRUM-14`를 추가한 뒤에도 `14/14 work items`가 표시되어 완료된
9개 업무와 진행 전 5개 업무가 같은 Gantt에 함께 남는 것을 재확인했습니다.

컴포넌트 승격의 Jira key와 source metadata는 integration Bot PR
[#22](https://github.com/DodamDodam-Capstone/integration/pull/22),
[#23](https://github.com/DodamDodam-Capstone/integration/pull/23),
[#26](https://github.com/DodamDodam-Capstone/integration/pull/26)에서 확인했습니다.
각 본문에는 컴포넌트, 저장소, 정확한 main SHA, `SCRUM-1`, source workflow URL이
표시되며 Docker Compose, Gitmoji, Jira key 검사를 통과한 뒤 사람 승인으로
순차 자동 병합되었습니다.

### 인수인계 기준 상태

- [ ] 초기 독립 squash로 끊긴 main/development 계보를 force push 없이
      보호된 PR로 보존·정렬. 현재 네 저장소의 `development` → `main` 승격 PR은
      충돌 상태이며, 장기 브랜치의 병합 방식을 분리한 뒤 처리해야 합니다.

- [x] 초기 Dependabot major Action 갱신 PR을 merge하지 않고 종료
- [x] 더 이상 필요하지 않은 설정 및 승격 test PR 종료
- [ ] Component Bot PR merge 후 임시 branch 수동 삭제
- [x] source branch 자동 삭제 비활성화 유지
- [ ] 모든 저장소에 `main`, `development`만 유지
- [ ] 모든 저장소의 열린 PR 0개 확인

## 각 프로젝트 초기화 시 확인할 항목

### Frontend

- [ ] `.nvmrc` 또는 `.node-version` 추가
- [ ] 지원하는 package manager lockfile 하나만 commit
- [ ] 필요한 `lint`, `typecheck`, `test`, `build` script 정의
- [ ] integration build를 시작할 때 운영용 Dockerfile 추가

### Backend

- [ ] `.java-version` 추가
- [ ] Gradle 또는 Maven wrapper commit
- [ ] unit test와 integration test 추가
- [ ] health 및 readiness endpoint 추가
- [ ] 운영용 Dockerfile 추가

### AI

- [ ] `.python-version` 추가
- [ ] `uv.lock`, `requirements.txt`, `pyproject.toml` 중 사용할 방식 결정 및 commit
- [ ] Ruff와 pytest 설정
- [ ] model 및 dataset 출처 문서화
- [ ] 큰 model file과 dataset을 Git에서 제외
- [ ] 운영용 Dockerfile 추가

### Integration

- [ ] `.components/frontend`, `.components/backend`, `.components/ai` build
      context를 사용하는 Compose 설정 추가
- [ ] 서비스 health check 추가
- [ ] `docker compose up --wait` smoke test 추가
- [ ] backend와 AI 사이 contract test 추가
- [ ] frontend와 backend 사이 end-to-end test 추가

## 보안 및 유지보수 검토

- [x] 외부 Action을 검토한 전체 commit SHA로 고정
- [ ] Dependabot Action 갱신을 매주 검토
- [ ] source language가 추가된 후 CodeQL 활성화
- [x] secret scanning과 push protection 활성화
- [ ] 노출이 의심되면 GitHub App private key와 Slack webhook 회전
- [ ] 첫 팀원 참가 후 일반 사용자의 direct push 거부 검사
- [ ] 역할을 지정한 후 Ruleset bypass actor 재검토
- [ ] 팀원 초대 전 멤버의 저장소 생성, App 설치, 저장소 삭제·이전·공개 범위
      변경, 보호 branch 이름 변경, Team 생성 권한을 Owner 전용으로 제한할지
      결정합니다.
- [ ] 팀원 참가 후 Slack 채널 멤버 검토
- [ ] 팀원 초대 후 실제 담당 명단으로 GitHub visible Team 구성
- [ ] Jira parent/subteam 구성 후 SCRUM `Team` field와 저장소별 Team ID 연결
- [ ] 기존 Jira 업무의 Team 값을 보정한 뒤 Team별 Board·Gantt filter 검증

### 2026-08-22 추가 보안 감사

- [x] Dependabot vulnerability alert 활성화 확인
- [x] 네 저장소의 secret scanning 및 push protection 활성화
- [x] 각 저장소 정책에서 Action의 전체 commit SHA 고정 강제
- [x] `Allow all actions`를 GitHub 공식 Action과 명시한
      `astral-sh/setup-uv`만 허용하도록 축소
- [x] Node.js 20 Action을 Node.js 24 기반 최신 major와 전체 SHA로 갱신
- [x] Dependabot security updates와 vulnerability alerts 활성화
- [ ] Secret scanning validity checks와 non-provider patterns는 현재 공개 저장소
      요금제/API에서 활성화되지 않아 기본 provider 패턴과 push protection을
      사용합니다. Organization 요금제 변경 시 다시 검토합니다.
- [ ] Slack 권한 감사 중 표시된 사용하지 않는 Bot OAuth token을 회전하고,
      필요하면 네 Incoming Webhook을 재발급해 GitHub secret을 교체합니다.
      현재 앱 권한은 `incoming-webhook` 하나이고 사용자 token 범위는 없습니다.
- [ ] 팀원 초대 후 개인 계정 기반 `CODEOWNERS` 적용 여부 결정

## 즉시 검토할 항목

- [ ] 새 Dependabot PR이 생성되면 검토합니다. Dependabot은 `development`를
      대상으로 하며 Jira 키만 예외이고 CI와 사람 승인은 그대로 필요합니다.
- [ ] 설정 인수인계 승인 후 휴지통에 남아 있는 복구 가능한 GitHub App
      private key 사본을 영구 삭제합니다. GitHub에는 active key 하나가 남아
      있고 Actions secret에는 정상 credential이 저장되어 있습니다.
- [ ] merge된 feature branch를 sprint 주기로 수동 삭제할지 결정합니다.
      GitHub의 자동 branch 삭제 기능은 의도적으로 사용하지 않습니다.
- [ ] 팀원 초대 후 일반 Organization 멤버로 잘못된 제목과 direct push 거부
      검사를 다시 실행합니다.

## 추후 AWS 단계

- [ ] staging과 production topology 결정
- [ ] GitHub OIDC 추가, 장기 AWS access key 저장 금지
- [ ] 변경 불가능한 ECR image tag 또는 digest 적용
- [ ] 검증한 동일 image digest를 production으로 승격
- [ ] deployment concurrency 및 rollback test 추가
- [ ] CloudWatch 및 budget alert 추가
