# AVR audit — GitHub Action

배포할 때마다 AI 답변 엔진(ChatGPT · Claude · Perplexity · Gemini …)이 내 사이트에 **닿고 읽을 수
있는지** 확인합니다. [AVR](https://github.com/maior/logosai-avr) 진단 API 를 부르고,
**필수 항목이 깨졌을 때만** 워크플로를 실패시킵니다.

| 필수 항목 | 실패 조건 |
|---|---|
| **P1-01** AI 크롤러 접근 | `robots.txt` 가 AI 봇을 전부 막음 (예: `User-agent: *` + `Disallow: /` 에 AI 봇 예외 없음), 또는 5xx 가 계속됨 |
| **P1-03** JS 없이 본문 렌더링 | 서버가 보내는 HTML 이 빈 CSR 셸 — H1 도 실질 문단도 없고, 렌더링 후 대비 30% 미만 |

나머지 항목은 로그에 보여 줄 뿐, `min-score` 를 직접 지정하지 않는 한 배포를 막지 않습니다.

> **English:** [README.md](README.md)

---

## 빠른 시작 (3단계)

**1. API 키 받기.** AVR 에 로그인해 **대시보드** 아래 **API 키** 칸에서 **새 키 발급** 을 누릅니다.
키는 `aeo_` 로 시작하고 **한 번만 보입니다** — 바로 복사하세요. 같은 목록에서 폐기할 수 있습니다.

**2. secret 으로 저장.** 저장소 *Settings → Secrets and variables → Actions →
New repository secret* 에서 이름 `AVR_API_KEY` 로 저장합니다. AVR API 주소는 변수
`AVR_API_BASE` 로 두면 편합니다 (예: `https://avr.example.com/api`).

**3. 배포 뒤에 한 단계 추가.**

```yaml
# .github/workflows/avr.yml
name: AVR audit
on:
  push:
    branches: [main]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      # … 배포 단계 …
      - uses: maior/logosai-avr@action
        with:
          url: https://example.com
          api-key: ${{ secrets.AVR_API_KEY }}
          api-base: ${{ vars.AVR_API_BASE }}
```

끝입니다. checkout 도 설치도 필요 없습니다 — 파이썬 표준 라이브러리만 씁니다
(GitHub 호스트 러너에는 `python3` 가 이미 있습니다).

---

## 입력

| 입력 | 필수 | 기본값 | 뜻 |
|---|---|---|---|
| `url` | ✓ | | 진단할 주소. 스킴을 빼면 `https://` 를 붙입니다 |
| `api-key` | ✓ | | AVR API 키 (`aeo_…`). 반드시 secret 으로 넘깁니다 |
| `api-base` | ✓ | | AVR API 주소. 예: `https://avr.example.com/api` |
| `min-score` | | *(비움)* | 이 ARS 미만이어도 실패. 비우면 필수 항목만 봅니다 |
| `timeout-seconds` | | `600` | 결과를 기다릴 최대 시간. 진단은 보통 30~60초 |

## 출력

| 출력 | 뜻 |
|---|---|
| `score` | ARS 0~100. 점수를 내지 못했으면 `None` |
| `job_id` | 작업 id. 같은 키로 `GET {api-base}/v1/audits/{job_id}` 하면 전체 결과 |

```yaml
      - id: avr
        uses: maior/logosai-avr@action
        with: { url: https://example.com, api-key: "${{ secrets.AVR_API_KEY }}", api-base: "${{ vars.AVR_API_BASE }}" }
      - run: echo "ARS = ${{ steps.avr.outputs.score }} (job ${{ steps.avr.outputs.job_id }})"
```

## 판정 규칙

| 상황 | 결과 |
|---|---|
| 필수 항목 0점 (`gated` / `blocking_failures`) | ❌ 실패 |
| `min-score` 를 지정했고 ARS 가 그 미만 | ❌ 실패 |
| 진단 작업 자체가 실패 (대상 불통, 서버 재시작) | ❌ 실패 — 다시 실행하세요 |
| 점수를 내지 못함 (측정 불가) | ⚠️ 경고만 |
| 필수 항목을 판정하지 못함 | ⚠️ 경고만 |
| 그 밖 | ✅ 통과, 점수 출력 |

**안 잰 것은 0 이 아닙니다.** 우리 크롤러가 잠깐 막혔거나 속도 제한에 걸렸다면 "확인하지
못했다" 이지 "사이트가 망가졌다" 가 아니므로, 배포를 멈추지 않고 경고만 냅니다.
판정은 모두 서버가 하고, 이 액션은 결과를 읽기만 하며 점수를 다시 계산하지 않습니다.

---

## 더 많은 예

**미리보기 배포 진단** (배포 단계가 내놓는 주소 사용):

```yaml
      - uses: maior/logosai-avr@action
        with:
          url: ${{ steps.deploy.outputs.preview-url }}
          api-key: ${{ secrets.AVR_API_KEY }}
          api-base: ${{ vars.AVR_API_BASE }}
```

**매주 점검, 아무것도 막지 않음** (보고만):

```yaml
on:
  schedule: [{ cron: "0 0 * * 1" }]   # 매주 월요일 00:00 UTC
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: maior/logosai-avr@action
        continue-on-error: true
        with: { url: https://example.com, api-key: "${{ secrets.AVR_API_KEY }}", api-base: "${{ vars.AVR_API_BASE }}" }
```

**여러 페이지** — matrix 를 씁니다. 아래 도메인별 한도에 주의하세요.

```yaml
    strategy:
      matrix:
        url: [https://example.com, https://example.com/pricing]
    steps:
      - uses: maior/logosai-avr@action
        with: { url: "${{ matrix.url }}", api-key: "${{ secrets.AVR_API_KEY }}", api-base: "${{ vars.AVR_API_BASE }}" }
```

**버전 고정.** `@action` 은 최신 내보내기를 따라갑니다. 고정하려면
[`action` 브랜치](https://github.com/maior/logosai-avr/commits/action)의 커밋 SHA 를 씁니다:
`uses: maior/logosai-avr@<sha>`.

---

## 한도

| 상한 | 값 | 넘으면 |
|---|---|---|
| 월 진단 수 | 플랜 한도 (웹 진단과 합산) | HTTP 429 |
| 같은 대상 도메인 | 키 하나가 24시간에 10회 — 진단 대상 서버 부담 방지 | HTTP 429 |
| 사설·내부 주소 | 받지 않음 | HTTP 422 |

## 문제 해결

| 로그 메시지 | 원인 | 해결 |
|---|---|---|
| `AVR API returned 401` | 키 없음·오타·폐기 | `AVR_API_KEY` secret 확인, 새 키 발급 |
| `AVR API returned 422` | 잘못된 주소 또는 사설·내부 주소 | 공개 `https://` 주소 사용 |
| `AVR API returned 429` | 월 한도 또는 도메인별 한도 도달 | 기다리거나 matrix 를 줄이거나 플랜 상향 |
| `Audit failed — …` | 대상 불통 또는 서버 재시작 | 다시 실행 |
| `Timed out — job … did not finish` | `timeout-seconds` 안에 끝나지 않음 | `timeout-seconds` 를 늘리거나 다시 실행 |
| `Blocking item failed: P1-01` | `robots.txt` 가 AI 봇을 막음 | 최소한 `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot` 허용 |
| `Blocking item failed: P1-03` | 서버가 빈 JS 셸을 반환 | H1 과 첫 문단을 서버 렌더링 또는 사전 렌더링 |
| `Blocking item could not be judged` | 이번에 확인하지 못함 | 대개 일시적 — 고칠 것 없음, 나중에 다시 실행 |

로그 메시지는 영어입니다. API 오류 안의 `detail` 문구는 서버가 보낸 것이라 한국어일 수 있습니다.

## 자주 묻는 질문

**점수는 무엇을 뜻하나요?** ARS 는 **AEO 권장 관행의 이행도**입니다 (45항목 rubric 중 자동
판정 가능한 항목). AI 답변이 나를 인용할지에 대한 **예측이 아닙니다** — 그 관계는 검증되지
않았고, 우리는 그렇게 주장하지 않습니다.

**왜 낮은 점수로 기본 실패시키지 않나요?** 점수는 관행 체크리스트이지 검증된 결과 지표가
아니기 때문입니다. 우리 숫자로 남의 배포를 막을 근거가 없다고 봅니다. 팀이 원하면
`min-score` 로 켜세요.

**API 에 무엇이 전송되나요?** `url` 과 키뿐입니다. 진단은 정직한 User-Agent 로 그 주소의
공개 페이지를 가져오고 `robots.txt` 를 따릅니다.

**채점 규칙은 어디에 있나요?** [공개 명세](https://github.com/maior/logosai-avr)(CC BY 4.0)의
`rubric/pillars.yaml` 과 `spec/plane-b-readiness.md` 에 있습니다.

---

이 브랜치는 비공개 저장소의 `integrations/github-action/` 에서 내보낸 것입니다. 이슈는 받지만
변경은 원본에서 합니다. 라이선스는 [MIT](LICENSE).
