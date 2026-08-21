# 기여 가이드

PR 제목은 `<gitmoji> <type>(optional-scope): <description>` 형식을 사용합니다.

예시:

```text
⬆️ deps(frontend): 컴포넌트를 abc1234로 갱신
👷 ci: Docker Compose 검사 추가
🐛 fix(compose): backend health check 수정
```

`main`과 `development`의 모든 변경은 PR을 사용해야 합니다. 필수 검사를
통과하고 모든 review conversation을 해결한 후 squash merge합니다. 자동
브랜치 삭제는 사용하지 않으며 작업 브랜치는 sprint 정리 시 수동으로
삭제합니다.
