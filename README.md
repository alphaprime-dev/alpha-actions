# alpha-actions

공용 이미지 빌드는 GAR(`build-push-gar.yaml`)와 ECR(`build-push.yaml`) 모두 GitHub App 토큰을 사용합니다. 호출 저장소의 checkout, 재귀 서브모듈 checkout, BuildKit `github_token` secret에 같은 단기 토큰을 전달합니다. 토큰은 `Contents: read`로 요청하며 checkout 자격증명을 저장하지 않고, 작업 종료 시 Action이 폐기합니다.

## 호출 계약

기존 registry·image·target 입력은 유지합니다. `ACTIONS_TOKEN`을 전달하던 호출자는 아래 App secret 두 개에 접근할 수 있어야 합니다. ECR은 기존 AWS secret 두 개도 계속 필요합니다.

```yaml
jobs:
  build:
    uses: alphaprime-dev/alpha-actions/.github/workflows/build-push-gar.yaml@main
    with:
      gar-project-id: alphasquare
      gar-repository: alphasquare
      service-name: alphasquare-base
      image-tag: example
      workload-identity-provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER
      service-account: github-actions-sa@alphasquare.iam.gserviceaccount.com
      target: prod
      github-repositories: |
        alphasquare-base
        alpha-contracts
        alphaverse
        alphaship
        alphabee
        alphata
    secrets:
      ALPHA_ACTIONS_APP_ID: ${{ secrets.ALPHA_ACTIONS_APP_ID }}
      ALPHA_ACTIONS_APP_PRIVATE_KEY: ${{ secrets.ALPHA_ACTIONS_APP_PRIVATE_KEY }}
```

`secrets: inherit`도 지원합니다. ECR 호출은 `uses`를 `build-push.yaml`로 바꾸고 기존 `ecr-registry`, `ecr-repository`, `image-tag`, `target`을 사용합니다. 명시적으로 secret을 전달한다면 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`도 포함해야 합니다.

| 공통 입력 | 의미 |
| --- | --- |
| `github-repositories` | **호출 저장소 자신**과 필요한 private 직접·전이 의존성, 서브모듈의 **저장소 이름**을 쉼표 또는 줄바꿈으로 지정합니다. `owner/repo`나 URL은 사용하지 않습니다. |
| 생략 또는 빈 `github-repositories` | 호출 조직의 App 설치 대상 전체를 사용합니다. 저장소별 최소 목록을 명시하는 방식을 권장합니다. |
| `submodules` | 기본 `recursive`. 서브모듈이 없다면 `"false"`로 생략할 수 있습니다. |

다른 조직의 private 저장소는 이 조직 설치 토큰으로 접근할 수 없습니다. App 자체의 code 쓰기 권한과 이 빌드가 발급하는 읽기 전용 토큰 권한은 별개이므로, App 설치 범위를 늘리는 결정은 별도 승인이 필요합니다.

## Dockerfile 인증

BuildKit secret ID는 기존과 동일한 `github_token`입니다. 토큰을 `ARG`·`ENV`·이미지 URL에 넣지 않고, secret을 마운트한 단일 명령에만 전달합니다. [base PR #2781](https://github.com/alphaprime-dev/alphasquare-base/pull/2781)의 `scripts/with-github-auth.sh`는 `gh` 설치 없이 Git credential helper를 해당 명령에만 적용합니다.

```dockerfile
COPY scripts/with-github-auth.sh scripts/with-github-auth.sh
RUN --mount=type=secret,id=github_token,required \
    GH_TOKEN="$(cat /run/secrets/github_token)" \
    sh scripts/with-github-auth.sh uv sync --locked --no-install-project --no-editable --no-dev
```

이 예제를 쓰려면 호출 저장소에 위 스크립트를 추가하고 기존 Dockerfile의 `.netrc` 인증을 대체합니다. 빌드에서 secret을 사용하지 않는 서비스도 private 소스 checkout을 위해 App 접근이 필요합니다.

## 소비자와 필요한 저장소 권한

2026-10-30 GitHub 기본 브랜치의 배포 워크플로·Dockerfile·의존성 manifest/lock·`.gitmodules` 기준입니다. 모든 활성 호출자는 private이며, 호출 저장소와 표의 private 의존성에 `Contents: read`가 필요합니다. App 설치·조직 secret 접근은 미확인입니다.

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

## 전환 조건과 검증 한계

[PR #22](https://github.com/alphaprime-dev/alpha-actions/pull/22)는 다음 조건을 충족하기 전까지 draft로 유지합니다.

1. 활성 호출자와 표의 private 직접·전이 의존성·서브모듈 전체의 App 설치 범위를 승인받습니다. **`alphata`는 private이며 App 추가 승인 대기**입니다.
2. 각 호출자가 두 App secret에 접근할 수 있어야 합니다. `secrets: inherit`만으로 조직 secret의 허용 저장소가 늘어나지 않습니다. ECR의 기존 AWS 접근도 유지해야 합니다.
3. `@main` 호출자는 이 PR merge 즉시 새 계약을 사용하므로 기존 호출자 App 미설치·secret 미공유 상태에서 merge하면 checkout 전에 실패합니다. socketio처럼 SHA에 고정된 호출자는 별도 PR에서 새 ref와 인증 입력을 함께 전환해야 합니다.
4. 실제 App 토큰 발급, private checkout·재귀 서브모듈, 명시적 저장소 범위, Docker 의존성 설치, GAR/ECR push를 승인된 검증 환경에서 확인합니다. 빌드 토큰이 이미지 레이어·환경변수에 남지 않는 검증은 호출 Dockerfile별로 수행해야 합니다.

검증 현황:

- 통과: 전체 워크플로 `actionlint`, 실제 호출 17개를 GAR/ECR 로컬 정의에 연결한 `actionlint`, `git diff --check`.
- 미실행: 위 4번의 실제 App·빌드·registry 검증.
- 확인 제한: 조직 App secret 허용 저장소 메타데이터 API는 현재 CLI 권한으로 HTTP 403.

App 설정·조직 secret·서비스별 워크플로·운영 배포는 이 PR에서 수정하지 않습니다.
