# Jira와 GitHub Issue 연동 운영 규칙

최종 검토일: 2026-08-22

## 적용 상태

- Jira 사이트: `https://dodamdodam.atlassian.net`
- Jira 프로젝트: `DodamDodam` (`SCRUM`)
- GitHub Organization: `DodamDodam-Capstone`
- `GitHub for Atlassian` 설치 완료
- `frontend`, `backend`, `ai`, `integration` 네 저장소만 연결
- GitHub 백필 상태 `FINISHED`, 권한 상태 `FULL ACCESS` 확인
- Team Board Gantt에서 Epic과 네 Task의 계층 표시 확인

실제 검증 업무:

```text
SCRUM-1 [EPIC] GitHub·Jira 협업 흐름 검증
├─ SCRUM-2 [FE]  GitHub·Jira 연동 및 문서 검증
├─ SCRUM-3 [BE]  GitHub·Jira 연동 및 문서 검증
├─ SCRUM-4 [AI]  GitHub·Jira 연동 및 문서 검증
└─ SCRUM-5 [INT] GitHub·Jira 연동 및 문서 검증
```

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

## 필요한 GitHub 설정

현재 Organization Issue Type은 `Task`, `Bug`, `Feature`입니다. 다음 설정을
추가합니다.

1. Organization Issue Type에 `Epic` 추가
2. `integration` 저장소에 Epic Issue Form 추가
3. 네 저장소에 Task 및 Bug Issue Form 추가
4. Issue Form에 Jira key와 Jira URL 필드 추가
5. PR template에 Jira key와 관련 GitHub Issue 항목 유지
6. Organization GitHub Project에 `Parent issue`, `Sub-issue progress`,
   `Repository`, `Status` field 추가

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

현재 Gitmoji 제목 검사는 위 형식을 허용합니다. Jira 연결 후에는 기능 PR에
정확히 하나의 Jira key가 있는지 검사하는 workflow를 추가합니다. Dependabot,
Integration Bot, 문서만 수정하는 초기 설정 PR은 명시적인 예외 규칙을
사용합니다.

## 업무 상태 자동화

권장 Jira 상태는 다음과 같습니다.

```text
To Do -> In Progress -> In Review -> Done
```

Jira Automation 규칙:

1. `Branch created`
   - branch에 Jira key가 있으면 Task를 `In Progress`로 전환합니다.
2. `Pull request created`
   - 연결된 Task를 `In Review`로 전환하고 PR URL을 기록합니다.
3. `Pull request declined`
   - 다른 열린 PR이 없으면 Task를 `In Progress`로 되돌립니다.
4. `Pull request merged`
   - target이 `development`이면 일반 Task를 `Done`으로 전환합니다.
   - hotfix PR의 target이 `main`이면 해당 Task를 `Done`으로 전환합니다.
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
현재 저장소는 squash merge를 사용하며, Atlassian은 commit history가
재작성되면 Smart Commit 명령이 중복 실행될 수 있다고 안내합니다.

따라서 commit의 Jira key는 개발 정보 연결에만 사용하고, 상태 변경은 PR
event 기반 Jira Automation으로 처리합니다.

- [Jira Smart Commits](https://support.atlassian.com/jira-software-cloud/docs/process-issues-with-smart-commits/)

## 적용 순서

1. Jira project key와 workflow 상태 확정
2. `GitHub for Atlassian` 설치 및 네 저장소 연결
3. GitHub `Epic` Issue Type과 Issue Form 추가
4. Organization GitHub Project에 sub-issue 관련 field 추가
5. PR template과 Jira key 검사 workflow 반영
6. `development` merge 시 GitHub Issue 종료 workflow 반영
7. Jira Branch/PR Automation 규칙 구성
8. Epic 하나와 frontend/backend Task로 전체 흐름 검증
9. 검증 후 AI 및 integration Task로 확대

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
