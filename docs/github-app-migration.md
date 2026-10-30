# 이미지 빌드의 GitHub App 인증 전환

[PR #22](https://github.com/alphaprime-dev/alpha-actions/pull/22)에서 GAR·ECR 공용 이미지 빌드 인증을 `ACTIONS_TOKEN`에서 GitHub App 토큰으로 변경했습니다. 호출 방법은 [README](../README.md#이미지-빌드-시작하기)를 참고하세요.

## 기존 호출자 변경 사항

- `@main` 호출자는 GitHub App 인증을 사용합니다. 기존 `ACTIONS_TOKEN` 대신 `ALPHA_ACTIONS_APP_ID`, `ALPHA_ACTIONS_APP_PRIVATE_KEY`를 전달하세요. ECR은 기존 AWS secret 두 개도 계속 필요합니다.
- registry·image·target 입력과 BuildKit secret ID `github_token`은 유지됩니다.
- GitHub App 설치 범위에는 호출 저장소 자신과 private 직접·전이 의존성 및 서브모듈이 포함되어야 합니다. 호출 저장소에 두 App secret의 접근 권한도 있어야 합니다. `secrets: inherit`만으로 조직 secret의 허용 저장소가 늘어나지는 않습니다.
- 이전 SHA에 고정된 호출자는 ref와 인증 입력을 함께 변경해야 합니다.
- Dockerfile의 `.netrc` 인증을 대체하는 방법은 [Dockerfile 인증](../README.md#dockerfile-인증)을 참고하세요.

## 소비자와 필요한 저장소 권한

2026-10-30 GitHub 기본 브랜치의 배포 워크플로·Dockerfile·의존성 manifest/lock·`.gitmodules` 기준입니다. 모든 활성 호출자는 private이며, 호출 저장소와 표의 private 의존성에 `Contents: read`가 필요합니다. 이 조사는 의존성 기준 목록이며, 당시 App 설치·조직 secret 접근은 확인하지 못했습니다. 현재 설치 범위와 secret 접근은 호출 저장소별로 확인해야 합니다.

| 호출 저장소 | 공용 경로/ref | private 직접 의존성 | private 전이 의존성 | private 서브모듈 |
| --- | --- | --- | --- | --- |
| `alphasquare-base` | GAR `main` | `alphaverse`, `alphaship`, `alphabee` | `alphata` (`alphaship` 경유) | `alpha-contracts` |
| `alphacrawler` | GAR `main` | `alphabee` | 없음 | 없음 |
| `alphasquare-virtual-trading-server` | GAR `main` | `alphaverse`, `alphabee` | 없음 | 없음 |
| `alphasquare-socketio-server` | GAR `ecffc7ce6b868f4d7daa8b375e9ea57079d97516` | 없음 (현재 Rust 빌드) | 없음 | `alpha-contracts` |
| `alphasquare-data-server` | GAR `main` | `alphaverse`, `alphabee`, `alphata` | 없음 | 없음 |
| `alphaprime-bot` | GAR `main` | 없음 | 없음 | 없음 |
| `alphasquare-real-trading-server` | GAR `main` | `alphabee` | 없음 | 없음 |
| `alphasquare-cluster-ops` | GAR `main` | 없음 | 없음 | 없음 |
| `koscom-tcp-mediator` | GAR・ECR `main` | `alphabee` | 없음 | 없음 |

`ring`과 `alphastats`는 public이므로 설치 목록에 추가할 필요가 없습니다. `ring`은 crawler·virtual-trading·data에, `alphastats`는 virtual-trading 및 base의 `alphaship` 전이 의존성에 포함됩니다. `alpha-contracts`에는 추가 `.gitmodules`가 없음을 확인했습니다.

최소 설치 집합은 위 활성 호출 저장소 9개 + `alpha-contracts`, `alphaverse`, `alphaship`, `alphabee`, `alphata`입니다. 개별 토큰에는 표의 해당 행과 호출 저장소 자신만 지정합니다. `alpha-actions`·배포 manifest 대상 `alphasquare-infra`의 설치 필요 여부는 빌드 이외 작업의 별도 판단이며 이 빌드 의존성 목록에 포함하지 않습니다.

`alphasquare-main-server`에도 GAR/ECR `main` 호출이 남아 있으나 GitHub에서 archived 상태입니다. 재활성화하면 호출 저장소 자신과 `alphaverse`, `alphabee` 접근을 먼저 준비해야 합니다. `alphaprime-api-bot`는 `alphaprime-bot`로 리다이렉트되는 이전 이름이므로 중복 집계하지 않습니다.

## 호출자 검증

인증 설정이나 호출 ref를 변경한 서비스는 다음 항목을 확인하세요.

1. App 토큰 발급, private checkout·재귀 서브모듈 checkout, 명시적 저장소 범위.
2. Docker 빌드 중 private 의존성 설치와 GAR/ECR push.
3. 호출 Dockerfile별로 빌드 토큰이 이미지 레이어·환경변수에 남지 않는지 확인.

## 전환 준비 당시 검증 기록

다음은 2026-10-30 전환 준비 당시의 기록이며, merge 이후 운영 검증 결과를 나타내지는 않습니다.

- 통과: 전체 워크플로 `actionlint`, 실제 호출 17개를 GAR/ECR 로컬 정의에 연결한 `actionlint`, `git diff --check`.
- 미실행: 실제 App 토큰 발급, private checkout·재귀 서브모듈, Docker 의존성 설치, GAR/ECR push 및 Dockerfile별 토큰 잔존 검증.
- 확인 제한: 조직 App secret 허용 저장소 메타데이터 API는 당시 CLI 권한으로 HTTP 403.
- 승인 상태: 당시 `alphata`의 App 추가 승인은 대기 중이었습니다.

App 설정·조직 secret·서비스별 워크플로·운영 배포는 PR #22의 수정 범위에 포함되지 않았습니다.
