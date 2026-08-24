# 팀 업무 시작과 완료 가이드

이 문서는 팀원이 업무를 받은 뒤 어느 저장소에서 무엇을 만들고, PR이 병합되면
GitHub와 Jira에서 무엇이 완료되는지를 한 번에 확인하기 위한 실행 가이드입니다.

상세한 자동화 구조와 관리자 운영 방법은
[`JIRA_GITHUB_INTEGRATION.md`](JIRA_GITHUB_INTEGRATION.md)를 참고합니다.

## 1. 먼저 시작 경로를 하나만 선택합니다

| 현재 상태 | 선택할 경로 | GitHub Issue Form |
| --- | --- | --- |
| Jira Task가 이미 있음 | Jira-first | 사용하지 않음 |
| Jira Task가 아직 없음 | GitHub-first | 담당 저장소에서 사용 |
| Jira Epic도 아직 없음 | GitHub-first Epic | integration의 `Project Epic` Form 사용 |

같은 업무에 두 경로를 동시에 사용하지 않습니다. 이미 Jira Task가 있는데 GitHub
Task Form을 다시 열면 새로운 Jira Task가 생성될 수 있습니다.

## 2. 저장소와 접두어를 선택합니다

| 업무 | Jira/GitHub 접두어 | 저장소 | Slack | 필수 CI |
| --- | --- | --- | --- | --- |
| 화면·클라이언트 | `[FE]` | `frontend` | `#frontend-actions` | `frontend-quality` |
| API·DB·서버 | `[BE]` | `backend` | `#backend-actions` | `backend-quality` |
| 모델·추론·데이터 처리 | `[AI]` | `ai` | `#ai-actions` | `ai-quality` |
| Compose·컴포넌트 버전·통합 검증 | `[INT]` | `integration` | `#integration-actions` | `docker-compose-build` |

여러 저장소가 참여하면 하나의 Task를 공유하지 말고 Epic 아래에 저장소별 Task를
만듭니다. 첫 번째 저장소의 PR만 병합되어 전체 업무가 너무 일찍 완료되는 것을
막기 위해서입니다.

```text
SCRUM-200 [EPIC] 회원 인증 흐름 제공
├─ SCRUM-201 [FE] 로그인 화면과 인증 상태 처리
├─ SCRUM-202 [BE] 로그인 및 토큰 재발급 API
├─ SCRUM-203 [AI] 이상 로그인 위험 점수 제공
└─ SCRUM-204 [INT] 인증 흐름 Compose 통합 검증
```

위 번호는 문서 예시입니다. 실제로 생성된 Jira 키를 사용해야 합니다.

## 3. 흐름 A: Jira Epic과 Task를 먼저 만든 경우

### 3.1 Jira에서 계획합니다

1. Epic 제목을 `[EPIC] 회원 인증 흐름 제공`처럼 작성합니다.
2. Epic의 child Task를 저장소별로 나눕니다.
3. Task에 담당자, sprint, 시작 날짜와 기한을 설정합니다.
4. Team Board Gantt를 사용하면 `Start Date (Teamboard)`와
   `End Date (Teamboard)`도 입력합니다.

### 3.2 GitHub에서는 Jira 키로 바로 작업합니다

이 경로에서는 GitHub Task Issue를 새로 만들지 않습니다. Jira Task 키가 이미
업무 식별자이므로 branch, commit, PR에 같은 키를 사용합니다.

Frontend `SCRUM-201`의 예시:

```text
branch: feature/SCRUM-201-login-page
commit: ✨ feat(auth): SCRUM-201 [FE] 로그인 화면 추가
PR:     ✨ feat(auth): SCRUM-201 [FE] 로그인 화면 추가
base:   development
```

PR 본문:

```text
Jira: https://dodamdodam.atlassian.net/browse/SCRUM-201

관련 GitHub Issue: 없음 (Jira-first 업무)
```

PR이 `development`에 병합되면 GitHub for Atlassian이 같은 Jira 키를 가진 PR을
연결하고, Jira Automation `PR 병합 시 Task 완료`가 Task를 `완료`로 전환합니다.
GitHub Issue가 없으므로 닫을 Issue도 없습니다.

## 4. 흐름 B: GitHub Issue에서 Jira Task를 자동 생성하는 경우

### 4.1 담당 저장소에서 Issue Form을 엽니다

예를 들어 기존 Epic `SCRUM-200` 아래 Frontend Task가 필요하면:

```text
Repository: frontend
Form:       Frontend Task
Title:      [FE] 로그인 오류 메시지 개선
상위 Jira 키: SCRUM-200
```

Issue가 열리면 자동화가 다음을 처리합니다.

```text
frontend GitHub Issue 생성
-> Jira에 [FE] Task 생성, parent=SCRUM-200
-> GitHub Issue 제목을 SCRUM-205 [FE] ... 형식으로 변경
-> Jira 링크 댓글 추가
-> jira-linked 레이블 추가
-> #frontend-actions에 연결 결과 전송
```

`SCRUM-205`와 GitHub Issue 번호는 예시이며 실제 자동 생성 결과를 확인합니다.

### 4.2 자동 생성된 키로 작업합니다

```text
GitHub Issue: frontend#123 SCRUM-205 [FE] 로그인 오류 메시지 개선
branch:       fix/SCRUM-205-login-error-message
commit:       🐛 fix(auth): SCRUM-205 [FE] 로그인 오류 메시지 수정
PR:           🐛 fix(auth): SCRUM-205 [FE] 로그인 오류 메시지 수정
base:         development
```

PR 본문에는 Jira 링크와 같은 저장소의 Issue 번호를 모두 적습니다.

```text
Jira: https://dodamdodam.atlassian.net/browse/SCRUM-205
Resolves #123
```

PR이 `development`에 병합되면 두 자동화가 병렬로 결과를 정리합니다.

```text
GitHub close-linked-issues workflow -> frontend#123 Closed
Jira Pull request merged Automation -> SCRUM-205 완료
Team Board Gantt -> 업무를 삭제하지 않고 완료 상태로 유지
Slack -> CI/PR 결과를 #frontend-actions에 전송
```

## 5. 저장소별 정확한 예시

### Frontend

```text
Jira:   SCRUM-201 [FE] 로그인 화면과 인증 상태 처리
branch: feature/SCRUM-201-login-page
commit: ✨ feat(auth): SCRUM-201 [FE] 로그인 화면 추가
PR:     ✨ feat(auth): SCRUM-201 [FE] 로그인 화면 추가
```

### Backend

```text
Jira:   SCRUM-202 [BE] 로그인 및 토큰 재발급 API
branch: feature/SCRUM-202-auth-api
commit: ✨ feat(auth): SCRUM-202 [BE] 토큰 재발급 API 추가
PR:     ✨ feat(auth): SCRUM-202 [BE] 토큰 재발급 API 추가
```

### AI

```text
Jira:   SCRUM-203 [AI] 이상 로그인 위험 점수 제공
branch: feature/SCRUM-203-login-risk-score
commit: ✨ feat(model): SCRUM-203 [AI] 로그인 위험 점수 계산 추가
PR:     ✨ feat(model): SCRUM-203 [AI] 로그인 위험 점수 계산 추가
```

### Integration

```text
Jira:   SCRUM-204 [INT] 인증 흐름 Compose 통합 검증
branch: feature/SCRUM-204-auth-integration
commit: 👷 ci(compose): SCRUM-204 [INT] 인증 서비스 통합 검사 추가
PR:     👷 ci(compose): SCRUM-204 [INT] 인증 서비스 통합 검사 추가
```

## 6. PR 작성과 병합 규칙

1. 작업 브랜치는 최신 `development`에서 만듭니다.
2. branch와 PR 제목에는 Jira 키를 정확히 하나씩 넣고 서로 일치시킵니다.
3. `development` 대상 PR 제목에는 담당 저장소 접두어를 정확히 하나 넣습니다.
4. Gitmoji는 변경 의미에 맞게 선택하고 Conventional Commit type을 사용합니다.
5. GitHub Issue가 있을 때만 `Resolves #번호`를 적습니다.
6. 필수 CI, 리뷰 승인, conversation 해결 후 squash merge합니다.
7. `development`에서 `main`으로 올리는 sprint/release PR은 Epic 키를 사용하고
   merge commit으로 병합합니다.

```text
🚀 chore(release): SCRUM-200 development를 main으로 승격
```

## 7. 완료 상태의 기준

| 대상 | 완료 시점 | 자동/수동 |
| --- | --- | --- |
| GitHub Task Issue | 연결된 PR이 `development`에 merge | 자동 |
| Jira Task/Bug | Jira 키가 연결된 PR이 merge | 자동 |
| Jira Epic | 모든 child Task와 integration 검증 완료 | sprint review에서 수동 |
| GitHub Epic Issue | 모든 sub-issue 완료 확인 | sprint review에서 수동 |

Jira Task가 완료되면 삭제하지 않습니다. Team Board에서 보이지 않으면 Gantt의
`Show completed tickets`가 켜져 있는지 확인합니다.

## 8. 자주 하는 실수

- Jira Task가 이미 있는데 GitHub Task Form을 다시 열지 않습니다.
- 하나의 Jira Task로 여러 저장소 PR을 처리하지 않습니다.
- 다른 저장소 Issue 번호를 `Resolves #번호`로 적지 않습니다.
- branch와 PR에 서로 다른 Jira 키를 넣지 않습니다.
- PR merge 전에 Jira Task를 수동으로 완료하지 않습니다.
- commit에 `#done` Smart Commit을 사용하지 않습니다.
- `main`과 `development`에 직접 push하지 않습니다.
- Epic은 첫 번째 child Task가 끝났다고 완료하지 않습니다.

## 9. 팀원 완료 체크리스트

- [ ] Jira Task와 저장소 접두어가 담당 영역에 맞습니다.
- [ ] 작업 브랜치를 최신 `development`에서 만들었습니다.
- [ ] branch, commit, PR에 같은 Jira 키를 사용했습니다.
- [ ] PR target이 `development`입니다.
- [ ] GitHub Issue가 있으면 Jira 링크와 `Resolves #번호`를 적었습니다.
- [ ] 필수 CI가 모두 성공했습니다.
- [ ] 다른 팀원의 승인을 받았습니다.
- [ ] 모든 conversation을 해결했습니다.
- [ ] merge 후 GitHub Issue와 Jira Task 상태를 확인했습니다.
- [ ] 저장소별 Slack 채널에서 결과를 확인했습니다.
- [ ] Gantt에서 완료 업무가 삭제되지 않고 `완료`로 남는지 확인했습니다.
