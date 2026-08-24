# Jira와 GitHub Issue 연동 운영 규칙

최종 검토일: 2026-08-24

## 적용 상태

- Jira 사이트: `https://dodamdodam.atlassian.net`
- Jira 프로젝트: `DodamDodam` (`SCRUM`)
- GitHub Organization: `DodamDodam-Capstone`
- `GitHub for Atlassian` 설치 완료
- `frontend`, `backend`, `ai`, `integration` 네 저장소만 연결
- GitHub 백필 상태 `FINISHED`, 권한 상태 `FULL ACCESS` 확인
- Team Board Gantt에서 Epic과 Task 계층 및 완료 업무 보존 표시 확인
- 네 저장소에 `jira-issue-key` 및 `close-linked-issues` workflow 추가
- 컴포넌트의 Jira key를 integration Bot PR까지 전달하도록 적용
- Jira Automation `PR 병합 시 Task 완료` 활성화 및 실제 완료 흐름 검증
- GitHub Issue Form에서 Jira Epic·Task·Bug 자동 생성 workflow 추가
- 조직 Actions Secret `JIRA_API_TOKEN`을 최소 Jira scope 토큰으로 교체하고
  기존 토큰 철회 및 종단간 재검증 완료

실제 검증 업무:

```text
SCRUM-1 [EPIC] GitHub·Jira 협업 흐름 검증
├─ SCRUM-2 [FE]  GitHub·Jira 연동 및 문서 검증
├─ SCRUM-3 [BE]  GitHub·Jira 연동 및 문서 검증
├─ SCRUM-4 [AI]  GitHub·Jira 연동 및 문서 검증
└─ SCRUM-5 [INT] GitHub·Jira 연동 및 문서 검증
```

Issue Form 자동 생성 재검증:

```text
SCRUM-6 [EPIC] GitHub Issue 자동 동기화 구축
├─ SCRUM-11 [FE]  frontend#15
├─ SCRUM-12 [BE]  backend#14
├─ SCRUM-13 [AI]  ai#14
└─ SCRUM-14 [INT] integration#37
```

각 업무에서 Task 유형, `SCRUM-6` 상위 관계, `github-sync` 고유 레이블,
GitHub 자동 링크 댓글과 상태 레이블, 저장소별 Slack Source/Target을
확인했습니다. 같은 Issue를 다시 실행해도 Jira 업무와 댓글을 중복 생성하지
않습니다.

## 목표

- Jira는 Epic, Task, sprint, 일정, 담당자, 업무 상태의 기준으로 사용합니다.
- GitHub Issue는 저장소별 개발 작업과 PR의 기준으로 사용합니다.
- Jira Task 하나와 GitHub Task Issue 하나를 1:1로 연결합니다.
- PR merge를 기준으로 GitHub Issue와 Jira Task를 완료 처리합니다.
- 동일 정보를 양쪽에서 독립적으로 수정하지 않아 상태 충돌을 방지합니다.

## 권장 계층

Jira Epic 하나에 대응하는 GitHub Epic Issue는 `integration` 저장소에
생성합니다. 실제 개발 Task는 담당 컴포넌트 저장소에 생성하고 GitHub
sub-issue로 연결합니다.

```text
Jira SCRUM-1: [EPIC] GitHub·Jira 협업 흐름 검증
└─ integration#18: SCRUM-1 [EPIC] GitHub·Jira 협업 흐름 검증
   ├─ frontend#9: SCRUM-2 [FE] GitHub·Jira 연동 및 문서 검증
   ├─ backend#8: SCRUM-3 [BE] GitHub·Jira 연동 및 문서 검증
   ├─ ai#8: SCRUM-4 [AI] GitHub·Jira 연동 및 문서 검증
   └─ integration#19: SCRUM-5 [INT] GitHub·Jira 연동 및 문서 검증
```

한 Jira Task가 여러 저장소의 PR을 직접 소유하지 않도록 합니다. 여러
저장소가 필요하면 Epic 아래에 저장소별 Task를 분리합니다. 그래야 첫 PR이
merge되었을 때 Jira Task가 너무 일찍 완료되는 문제를 방지할 수 있습니다.

GitHub sub-issue는 같은 Organization 소유자의 다른 저장소 Issue를 연결할 수
있습니다.

- [GitHub Sub-issues REST API](https://docs.github.com/en/rest/issues/sub-issues)
- [Parent issue와 Sub-issue progress](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-parent-issue-and-sub-issue-progress-fields)

## GitHub Issue에서 Jira 자동 생성

네 저장소의 `New issue` 화면에 Task·Bug Issue Form을 제공합니다. Epic은 여러
저장소가 참여하는 목표이므로 `integration`의 `Project Epic` Form에서만
생성합니다.

```text
GitHub Issue opened
-> 저장소/레이블로 [FE]·[BE]·[AI]·[INT]·[EPIC]과 업무 유형 결정
-> Jira SCRUM 업무 생성
-> GitHub Issue 제목에 Jira 키 추가
-> Jira 링크 댓글과 jira-linked 레이블 추가
-> 저장소별 Slack Actions 채널에 Source/Target/Actor/Result 전송
```

Task·Bug를 기존 Epic 아래에 둘 때 Form의 `상위 Jira 키`에 `SCRUM-6`처럼
입력합니다. 비워 두면 상위 항목 없는 Jira 업무로 생성됩니다. 한 GitHub Issue의
고유 레이블(`github-<repo>-<number>`)을 Jira에도 저장하므로 workflow 재실행 시
중복 Jira 업무를 만들지 않습니다.

저장소가 public이므로 외부 사용자가 Issue만 열어 내부 Jira 업무를 무제한
생성하지 못하도록 `OWNER`, `MEMBER`, `COLLABORATOR`가 만든 Issue만 자동
동기화합니다. 외부 Issue는 팀원이 검토한 뒤 `Run workflow`에 번호를 입력해
수동 승인합니다. Jira 연결 완료는 `jira-linked`, Slack 성공 알림 완료는
`jira-notified` 레이블로 구분합니다.

자동 동기화에서 GitHub가 원본이며, Jira가 sprint·일정·담당자·상태의 원본입니다.
생성 이후 Jira 제목/설명의 양방향 자동 덮어쓰기는 하지 않습니다. 이는 사람이
Jira에서 보완한 계획 정보가 GitHub 수정으로 사라지는 것을 방지합니다.

### 실패와 재시도

- 의도적으로 Jira를 만들지 않을 Issue에는 생성 즉시 `jira-skip`을 붙입니다.
- 이미 같은 GitHub Issue 고유 레이블로 만든 Jira 업무가 있으면 그 업무를
  재사용합니다. 제목에 Jira 키가 있더라도 해당 고유 레이블과 프로젝트가
  일치하지 않으면 임의의 기존 업무에 연결하지 않습니다.
- 실패 알림은 저장소별 Slack Actions 채널에 전송됩니다.
- Actions의 `GitHub Issue to Jira`에서 `Run workflow`를 선택하고 Issue 번호를
  입력하면 수동 재시도할 수 있습니다.
- 중앙 실행 코드는 `integration/.github/scripts/sync_github_issue_to_jira.py`이며
  컴포넌트 저장소 workflow는 검증한 integration commit SHA를 사용합니다.
  따라서 이후 `integration/main`이 바뀌어도 secret을 사용하는 실행 코드가
  예고 없이 바뀌지 않습니다. 중앙 helper를 수정하면 단위 테스트와 integration
  CI를 통과시킨 뒤 세 컴포넌트의 고정 SHA를 함께 갱신합니다.
- 수동 재시도는 `main`에서만 허용하고 Issue 번호는 양의 정수만 받습니다.
- `epic`, `task`, `bug` 레이블이 충돌하면 임의로 유형을 선택하지 않고 실패
  알림을 보냅니다.
- Jira 생성, GitHub 제목 변경, 링크 댓글, Slack 알림 중간에 실패해도 고유 Jira
  레이블, 댓글 marker, `jira-linked`, `jira-notified`를 기준으로 다음 실행이
  완료되지 않은 단계만 복구합니다.

### 권한과 토큰 운영

- 조직 Secret: `JIRA_API_TOKEN`(네 저장소만 선택 허용)
- 토큰 이름: `DodamDodam GitHub Issue Sync v2`
- Jira API 권한: scoped token의 classic `read:jira-work`,
  `write:jira-work`만 허용
- 만료일: `2027-08-21`
- 만료 전 새 토큰을 만든 뒤 동일 Secret 값을 교체하고 테스트 Issue로 확인합니다.
- Secret 값은 로그·문서·로컬 파일에 기록하지 않습니다.
- 새 토큰으로 네 저장소 생성과 재시도를 확인한 뒤 기존 토큰은 철회했습니다.

Jira 업무 유형 ID는 프로젝트 설정에서 확인한 Epic `10001`, Task `10003`, Bug
`10006`으로 고정합니다. Jira 표시 언어가 바뀌어도 API 생성이 깨지지 않도록
번역된 업무 유형 이름을 사용하지 않습니다.

추후 검토할 GitHub 설정은 Organization Project에 `Parent issue`,
`Sub-issue progress`, `Repository`, `Status` field를 추가하는 것입니다.

## 팀과 권한 구조

팀원 초대 전에는 빈 팀을 저장소 개수에 맞춰 미리 만들지 않습니다. 실제 담당과
중복 역할을 확인한 뒤 팀원을 먼저 Organization 및 Jira에 초대하고 다음 최소
구조를 적용합니다.

### GitHub Teams

| 팀 | 기본 저장소 권한 | 용도 |
| --- | --- | --- |
| `frontend` | frontend `Write` | Frontend 개발과 리뷰 |
| `backend` | backend `Write` | Backend 개발과 리뷰 |
| `ai` | ai `Write` | AI 개발과 리뷰 |
| `integration-maintainers` | integration `Write` | 통합 설정과 Docker 검증 |
| `maintainers` | 네 저장소 `Maintain` | 신뢰할 수 있는 2명 이상이 생길 때만 생성 |

저장소가 public이어도 공개되는 것은 읽기 권한뿐입니다. 쓰기 권한, 팀 mention,
CODEOWNERS와 팀 리뷰 배정에는 GitHub Teams가 유용합니다. 팀은 visible로 만들고,
각 도메인 팀에 대응 저장소만 직접 부여합니다. 현재 규모에서는 parent/child
GitHub Team을 만들지 않습니다. child team이 parent의 저장소 권한을 상속하므로
소규모 조직에서는 의도하지 않은 권한 확대가 발생하기 쉽습니다.

팀원이 한 명뿐인 팀에는 자동 리뷰 배정을 켜지 않습니다. 두 명 이상일 때
CODEOWNERS를 추가하고 load-balance 방식으로 한 명을 자동 요청합니다. Owner와
Admin은 비상 설정을 담당할 1~2명으로 제한하고 일반 개발자는 `Write`, 릴리스
관리자는 필요한 경우에만 `Maintain`을 사용합니다. 브랜치 Ruleset이
`main`·`development` 직접 push를 별도로 차단하므로 `Write` 부여가 보호 브랜치
우회를 의미하지 않습니다.

### Jira/Atlassian Teams

권장 구조는 parent `DodamDodam Capstone` 아래 `Frontend`, `Backend`, `AI`
subteam입니다. `Integration/Platform`은 전담 인원이 2명 이상 생겼을 때만
추가합니다. Jira Team은 업무의 책임 그룹을 표현하는 용도이며 보안 권한 경계가
아닙니다. Jira 접근 권한은 Atlassian Group과 Jira project role로 별도
관리하고, 일반 팀은 invite-only 또는 closed로 운영합니다.

Jira Team을 만들기만 해서는 업무가 자동 배정되지 않습니다. 실제 적용할 때는
다음 순서를 지킵니다.

1. SCRUM 화면에 `Team` field를 추가합니다.
2. 저장소와 Jira Team ID의 매핑을 GitHub Issue 동기화 workflow에 추가합니다.
3. 기존 SCRUM 업무의 Team 값을 모두 보정합니다.
4. 그 뒤에 Team별 Board·Gantt filter를 적용합니다.

`Assignee`는 실제 담당 개인, `Team`은 책임 그룹으로 사용합니다. 기존
`[FE]`·`[BE]`·`[AI]`·`[INT]` 제목 접두사는 Slack과 검색 식별을 위해 그대로
유지합니다. 기존 업무를 보정하기 전에 Team filter를 켜면 Team 값이 빈 업무가
Gantt에서 사라진 것처럼 보일 수 있습니다. 팀 구조와 완료 업무 보존은 별개이며,
완료 업무는 `Done` 상태와 `Show completed tickets` 설정으로 계속 표시합니다.

## GitHub for Atlassian 연결

Jira Cloud에 `GitHub for Atlassian` App을 설치하고
`DodamDodam-Capstone` Organization의 다음 저장소만 선택합니다.

- `frontend`
- `backend`
- `ai`
- `integration`

설치에는 Jira Site Admin과 GitHub Organization Owner 권한이 필요합니다.

- [GitHub Cloud와 Jira 연결](https://support.atlassian.com/jira-cloud-administration/docs/integrate-with-github-cloud/)

연결 후 Jira key를 branch, commit, PR 제목 또는 본문에 포함하면 Jira의
Development panel에 관련 개발 정보가 표시됩니다.

## 이름 규칙

### Jira Epic과 Task

| 종류 | 제목 형식 | 저장소 |
| --- | --- | --- |
| Epic | `[EPIC] <사용자 가치 또는 목표>` | GitHub 대응 이슈는 `integration` |
| Frontend Task | `[FE] <구현할 결과>` | `frontend` |
| Backend Task | `[BE] <구현할 결과>` | `backend` |
| AI Task | `[AI] <구현할 결과>` | `ai` |
| Integration Task | `[INT] <검증 또는 통합 결과>` | `integration` |

GitHub Issue 제목은 Jira 키를 앞에 추가합니다.

```text
SCRUM-2 [FE] 로그인 화면 구현
SCRUM-3 [BE] 인증 API 구현
SCRUM-4 [AI] 이상 로그인 판별 구현
SCRUM-5 [INT] 인증 흐름 통합 검증
```

### Branch

```text
feature/SCRUM-2-login-page
fix/SCRUM-3-refresh-token
hotfix/SCRUM-4-auth-failure
```

### Commit

```text
✨ feat(auth): SCRUM-2 [FE] 로그인 화면 추가
🐛 fix(auth): SCRUM-3 [BE] 만료된 refresh token 거부
```

### PR 제목

```text
✨ feat(auth): SCRUM-2 [FE] 로그인 화면 추가
🐛 fix(auth): SCRUM-3 [BE] refresh token 검증 수정
```

현재 Gitmoji 제목 검사는 위 형식을 허용합니다. `jira-issue-key` workflow는
기능 PR의 branch와 제목에 정확히 하나의 같은 Jira key가 있는지 검사하며,
`development` 대상 PR에는 저장소별 `[FE]`, `[BE]`, `[AI]`, `[INT]` 접두어도
요구합니다. Dependabot과 Integration Bot branch는 명시적으로 예외 처리합니다.

## 업무 상태 자동화

권장 Jira 상태는 다음과 같습니다.

```text
To Do -> In Progress -> In Review -> Done
```

적용한 Jira Automation 규칙 `PR 병합 시 Task 완료`:

```text
Pull request merged
-> JQL: issuetype != Epic
-> 연결된 Jira 업무 항목을 완료로 전환
```

실제 [integration #24](https://github.com/DodamDodam-Capstone/integration/pull/24)
병합으로 GitHub `integration#19`가 닫히고 Jira `SCRUM-5`가 `완료`로 전환되는
것을 확인했습니다. 같은 검증을 frontend #12, backend #11, AI #11에서 반복해
네 저장소의 GitHub Issue 종료와 Jira Task 완료가 모두 동작함을 확인했습니다.
Epic은 자동 완료하지 않으며, 네 GitHub sub-issue와 Jira Task가 모두 완료된 뒤
sprint review 절차로 GitHub `integration#18`과 Jira `SCRUM-1`을 수동
완료했습니다.

추가할 수 있는 Jira Automation 규칙:

1. `Branch created`
   - branch에 Jira key가 있으면 Task를 `In Progress`로 전환합니다.
2. `Pull request created`
   - 연결된 Task를 `In Review`로 전환하고 PR URL을 기록합니다.
3. `Pull request declined`
   - 다른 열린 PR이 없으면 Task를 `In Progress`로 되돌립니다.
4. `Pull request merged`는 현재 적용된 규칙으로 처리합니다.
5. Child Task 완료
   - Epic의 모든 child Task가 완료되었고 integration 검증이 끝났을 때만 Epic을
     `Done`으로 전환합니다.

- [Jira Automation trigger](https://support.atlassian.com/cloud-automation/docs/jira-automation-triggers/)
- [Development smart value](https://support.atlassian.com/cloud-automation/docs/jira-smart-values-development/)

## GitHub Issue 완료 처리

GitHub의 `Closes #123` 같은 keyword는 변경이 기본 branch에 들어갈 때 Issue를
자동으로 닫습니다. 일반 기능 PR은 `development`로 merge하므로 별도의
workflow가 필요합니다.

권장 흐름:

```text
PR merge to development
-> PR 본문의 Resolves/Closes #번호 확인
-> 같은 저장소의 GitHub Task Issue 종료
-> GitHub sub-issue progress 갱신
-> Jira Pull request merged automation 실행
-> 연결된 Jira Task를 Done으로 전환
```

완료 workflow 보안 조건:

- `pull_request_target`의 `closed` event 사용
- `merged == true` 확인
- target이 `development` 또는 허용된 hotfix의 `main`인지 확인
- 최소 권한인 `issues: write`, `pull-requests: read`만 사용
- PR code checkout 및 실행 금지
- PR 템플릿의 HTML 주석과 code block 안에 있는 `Resolves #123` 예시는 무시
- 연결 번호가 GitHub Pull Request이면 닫지 않고, 열린 같은 저장소 Issue만 완료
- 검증한 중앙 helper를 변경 불가능한 commit SHA로 checkout
- Dependabot, Integration Bot, release PR 제외

## Release Epic 연결

`development` → `main` 승격 PR에는 sprint 또는 release Epic key를 사용합니다.

```text
🚀 chore(release): SCRUM-1 development를 main으로 승격
```

컴포넌트 sync event와 Integration Bot PR에도 같은 Epic key를 전달하도록
확장합니다.

```text
⬆️ deps(frontend): SCRUM-1 컴포넌트를 8e973e2로 갱신
```

이 구조를 적용하면 Jira Epic에서 컴포넌트 승격 PR, integration PR,
integration build 결과를 함께 추적할 수 있습니다.

## Smart Commit 사용 원칙

Jira Smart Commit은 `SCRUM-2 #done` 같은 상태 변경 명령을 지원합니다. 하지만
기능 변경은 `development`로 squash merge하며, Atlassian은 commit history가
재작성되면 Smart Commit 명령이 중복 실행될 수 있다고 안내합니다.

따라서 commit의 Jira key는 개발 정보 연결에만 사용하고, 상태 변경은 PR
event 기반 Jira Automation으로 처리합니다.

- [Jira Smart Commits](https://support.atlassian.com/jira-software-cloud/docs/process-issues-with-smart-commits/)

## 적용 및 검증 순서

1. [완료] Jira project key와 Epic/Task 이름 규칙 확정
2. [완료] `GitHub for Atlassian` 설치 및 네 저장소 연결
3. [완료] Jira Epic/Task와 GitHub 상위/하위 Issue 생성
4. [완료] PR template과 Jira key 검사 workflow 반영
5. [완료] `development` merge 시 GitHub Issue 종료 workflow 반영
6. [완료] frontend/backend/ai/integration 기능 PR과 CI 연결 검증
7. [완료] Jira PR merge Automation으로 Task 상태를 `완료`로 전환
8. [검토] GitHub Organization Project에 sub-issue 관련 field 추가
9. [검토] 필요할 때 Organization Issue Type에 `Epic` 추가

## 실제 적용에 필요한 정보

- Jira Cloud site URL
- Jira project key
- Jira Site Admin 권한
- Jira Task workflow의 상태 이름과 transition
- 팀원의 Jira 계정 email과 Git commit email 일치 여부

## Team Board Gantt 운영

Team Board Gantt는 Jira의 상위 항목 관계를 읽어 Epic과 Task를 자동으로
계층화합니다. 실제 검증에서 `SCRUM-1` 아래 `SCRUM-2`~`SCRUM-5`가
`1.1`~`1.4`로 표시되었습니다.

업무가 완료될 때 Jira Automation은 삭제 작업을 실행하지 않고 상태만 `완료`로
전환합니다. 2026-08-22 감사에서 흐름 구성이 `Pull request merged` →
`issuetype != Epic` → `업무 항목을 완료로 전환`뿐임을 확인했고, 최근 감사 로그도
성공 또는 적용 대상 없음으로 기록되어 있었습니다.

완료 업무가 사라져 보였던 원인은 Team Board Gantt의 `View Settings`에서
`Show completed tickets`가 꺼져 있었기 때문입니다. 이 옵션을 활성화하고 새로
고침한 뒤 최초 `SCRUM-1`~`SCRUM-10` 총 10개 업무가 유지되며 완료된 9개 업무가
`완료` 상태로 표시되는 것을 재검증했습니다. Issue Form 종단간 테스트로
`SCRUM-11`~`SCRUM-14`를 추가한 뒤에도 Gantt가 `14/14 work items`를 표시해
완료 9개와 진행 전 5개를 함께 보존하는 것을 확인했습니다. 이 옵션을 끄면
데이터가 삭제되는 것이 아니라 현재 Gantt View에서만 숨겨집니다.

일정 막대를 사용하려면 다음 항목을 입력합니다.

- Jira `시작 날짜`와 `기한`
- Team Board Gantt의 `Start Date (Teamboard)`와 `End Date (Teamboard)`
- 담당자가 확정된 뒤 Team Board `Resource`에 해당 멤버 추가

현재 Team Board는 전용 날짜 필드를 표시하므로 Jira 날짜만 입력했다고 일정
막대가 자동 생성되지는 않습니다. Sprint 계획 시 Gantt에서 전용 시작·종료
날짜를 함께 입력합니다.

## 팀원 이용 조건

팀원은 `GitHub for Atlassian`을 다시 설치하지 않습니다. 다음 권한만 있으면
동일한 연동 정보를 사용할 수 있습니다.

1. Jira `SCRUM` 프로젝트 접근 권한
2. 담당 GitHub 저장소 접근 권한
3. branch, commit, PR에 `SCRUM-번호` 포함
4. 자신의 GitHub 계정과 Jira 계정으로 로그인

Organization Owner만 앱의 저장소 접근 범위를 변경합니다. 새 저장소를 만들면
자동 연결되지 않으며 GitHub App 설정에서 명시적으로 추가해야 합니다.

## PR 승인·병합 정보의 반영 범위

- GitHub Ruleset이 승인 수, 마지막 push와 다른 승인자, 필수 CI를 강제합니다.
- Jira Development panel은 branch, commit, PR, build와 PR 상태를 표시합니다.
- PR 상세에는 승인된 사용자 표시가 나타나며, 병합 후 `MERGED`로 변경됩니다.
- GitHub Issue 완료는 `close-linked-issues` workflow가 담당합니다.
- Jira Task 완료는 `PR 병합 시 Task 완료` Automation이 담당합니다.
- Slack은 저장소별 Actions 채널에 source/target branch, PR, commit, actor,
  결과와 실행 링크를 보냅니다.
