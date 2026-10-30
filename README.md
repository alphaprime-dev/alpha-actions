# alpha-actions

AlphaPrime 서비스에서 공통으로 사용하는 GitHub Actions 워크플로입니다. GAR·ECR 이미지 빌드와 push, 이미지 태그 생성, 릴리스, 배포 manifest 갱신을 각 서비스 저장소에서 재사용할 수 있습니다.

## 이미지 빌드 시작하기

호출 저장소의 Dockerfile로 이미지를 빌드해 GAR 또는 ECR에 push합니다. private 소스·서브모듈 checkout과 Docker 빌드 중 의존성 접근에는 `Contents: read`로 발급한 단기 GitHub App 토큰을 사용합니다.

GAR·ECR 빌드는 GitHub App 인증을 사용합니다. 기존 `ACTIONS_TOKEN` 대신 아래 두 App secret을 전달하세요.

### 준비

- 호출 저장소에 Dockerfile이 있어야 합니다. `target`을 지정한다면 해당 빌드 stage가 있어야 합니다.
- GitHub App이 **호출 저장소 자신과 필요한 private 직접·전이 의존성 및 서브모듈**에 설치되어 있어야 합니다.
- 호출 저장소에서 `ALPHA_ACTIONS_APP_ID`, `ALPHA_ACTIONS_APP_PRIVATE_KEY` secret에 접근할 수 있어야 합니다. `secrets: inherit`도 지원하지만 조직 secret의 허용 저장소가 늘어나지는 않습니다.
- GAR은 대상 repository와 Workload Identity Provider·서비스 계정의 인증 및 push 권한을 준비해야 합니다. ECR은 대상 repository와 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` secret 및 push 권한이 필요합니다.
- Docker 빌드 중 private 의존성을 설치한다면 [Dockerfile 인증](#dockerfile-인증)도 설정하세요.

### GAR에 빌드하고 push하기

호출 저장소의 `.github/workflows/build-image.yaml`에 다음 파일을 추가합니다. GAR 설정과 `service-name`, `github-repositories`를 해당 서비스에 맞게 바꾸세요. 아래 저장소 목록은 `alphasquare-base`용입니다.

```yaml
name: Build image

on:
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

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

파일을 기본 브랜치에 추가한 뒤 GitHub Actions의 **Build image → Run workflow**에서 실행합니다. `image-tag: example`은 서비스의 태그 정책에 맞게 변경하세요.

성공하면 `Build and push` 단계가 완료되고, 위 예제에서는 `asia-northeast3-docker.pkg.dev/alphasquare/alphasquare/alphasquare-base:example`에 이미지가 push됩니다. GAR에서 태그를 확인하세요. 서비스 배포는 별도입니다.

### ECR을 사용하는 경우

같은 파일에서 `permissions`는 `contents: read`만 남기고, `build` job을 아래 내용으로 교체합니다. registry·repository와 private 의존성 목록을 서비스에 맞게 바꾸세요.

```yaml
  build:
    uses: alphaprime-dev/alpha-actions/.github/workflows/build-push.yaml@main
    with:
      ecr-registry: ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com
      ecr-repository: YOUR_REPOSITORY
      image-tag: example
      github-repositories: |
        YOUR_CALLER_REPOSITORY
        YOUR_PRIVATE_DEPENDENCY
    secrets:
      ALPHA_ACTIONS_APP_ID: ${{ secrets.ALPHA_ACTIONS_APP_ID }}
      ALPHA_ACTIONS_APP_PRIVATE_KEY: ${{ secrets.ALPHA_ACTIONS_APP_PRIVATE_KEY }}
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

성공하면 `<ecr-registry>/<ecr-repository>:example`에 push됩니다. AWS region은 `ap-northeast-2`로 고정되어 있습니다.

### 공통 입력과 인증 범위

| 공통 입력 | 의미 |
| --- | --- |
| `github-repositories` | **호출 저장소 자신**과 필요한 private 직접·전이 의존성, 서브모듈의 **저장소 이름**을 쉼표 또는 줄바꿈으로 지정합니다. `owner/repo`나 URL은 사용하지 않습니다. |
| 생략 또는 빈 `github-repositories` | 호출 조직의 App 설치 대상 전체를 사용합니다. 저장소별 최소 목록을 명시하는 방식을 권장합니다. |
| `submodules` | 기본값은 `recursive`. 서브모듈 checkout이 필요 없으면 문자열 `"false"`를 지정합니다. |
| `target` | 선택할 Dockerfile 빌드 stage. 생략하면 Dockerfile의 기본 빌드 대상을 사용합니다. |

다른 조직의 private 저장소는 이 조직 설치 토큰으로 접근할 수 없습니다. App 자체의 code 쓰기 권한과 이 빌드가 발급하는 읽기 전용 토큰 권한은 별개이므로, App 설치 범위를 늘리는 결정은 별도 승인이 필요합니다.

GAR의 `gar-region` 기본값은 `asia-northeast3`입니다. 전체 입력과 필수 secret은 [GAR 정의](.github/workflows/build-push-gar.yaml), [ECR 정의](.github/workflows/build-push.yaml)에서 확인할 수 있습니다. checkout 자격증명은 저장하지 않으며, 작업 종료 시 토큰 발급 Action이 토큰을 폐기합니다.

## Dockerfile 인증

BuildKit secret ID는 기존과 동일한 `github_token`입니다. 토큰을 `ARG`·`ENV`·이미지 URL에 넣지 않고, secret을 마운트한 단일 명령에만 전달합니다. [base PR #2781](https://github.com/alphaprime-dev/alphasquare-base/pull/2781)의 `scripts/with-github-auth.sh`는 `gh` 설치 없이 Git credential helper를 해당 명령에만 적용합니다.

```dockerfile
COPY scripts/with-github-auth.sh scripts/with-github-auth.sh
RUN --mount=type=secret,id=github_token,required \
    GH_TOKEN="$(cat /run/secrets/github_token)" \
    sh scripts/with-github-auth.sh uv sync --locked --no-install-project --no-editable --no-dev
```

이 예제를 쓰려면 호출 저장소에 위 스크립트를 추가하고 기존 Dockerfile의 `.netrc` 인증을 대체합니다. 빌드에서 secret을 사용하지 않는 서비스도 private 소스 checkout을 위해 App 접근이 필요합니다.

## 다른 공용 워크플로

각 파일의 `workflow_call`에 입력·secret·출력이 정의되어 있습니다.

| 용도 | 워크플로 |
| --- | --- |
| 이미지 태그 생성 | [staging: commit SHA](.github/workflows/staging-image-tag.yaml), [prod: ref 이름](.github/workflows/prod-image-tag.yaml) |
| pyproject 버전에 따른 릴리스 생성 | [uv](.github/workflows/auto-release-on-uv-pyproject-version-update.yaml), [Poetry](.github/workflows/auto-release-on-pyproject-version-update.yaml) |
| 릴리스 초안·PR 버전 라벨 | [릴리스 초안](.github/workflows/draft-release.yaml), [PR 라벨](.github/workflows/pr-version-labeler.yaml) |
| 배포 manifest 갱신·push | [update-k8s-mainifest.yaml](.github/workflows/update-k8s-mainifest.yaml) |
| Discord 알림 | [notify-discord.yaml](.github/workflows/notify-discord.yaml) |
