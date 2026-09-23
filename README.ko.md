# AVR 프레임워크 — AI Visibility & Readiness

AEO(Answer Engine Optimization) 진단 프레임워크의 **명세 정본**.
백엔드 스코어러·리포트 렌더러는 이 디렉토리의 파일을 파싱해 동작한다.

정본 버전: rubric **1.10.0** · scoring **1.1.0** · channels **1.2.0** · schema **1.5.0**
상태: 명세 확정 · 참조 구현 가동 중 · 파일럿 3회차 완료
라이선스: **[CC BY 4.0](LICENSE)** · English: **[README.md](README.md)** — 자유롭게 쓰고 고치고 상업적으로 이용할 수 있습니다. 출처만 밝혀 주십시오.

> **왜 명세를 공개하는가.** 진단 제품이 자기 자를 감추면 그 점수는 검증할 수 없는 주장이 됩니다.
> 자를 공개해야 남이 우리 점수를 재현하거나 반박할 수 있고, 그게 이 제품이 파는 것입니다.
> 경쟁사가 이 기준으로 점수를 내면 그건 우리에게 손해가 아닙니다.

---

## 1. 한 줄 요약

브랜드의 AI 답변 노출을 **결과(Visibility, Plane A)** 와 **원인(Readiness, Plane B)** 두 평면으로
분리 측정하고, 그 교차점(Gap Matrix)에서 처방을 도출한다.

```
Plane A → AVI (0~100) + 신뢰구간     6채널 LLM 프로빙
                    ×
Plane B → ARS (0~100) + 항목별 근거   5 Pillar · 45항목 rubric
                    ↓
              Gap Matrix 4사분면 → 사분면별 처방
```

---

## 1.5 무엇이 들어 있고, 무엇은 없는가

| | |
|---|---|
| ✅ 들어 있음 | 명세 문서 9편 · 채점 정본 `rubric/*.yaml` · 리포트 `schema/` · 적합성 케이스 |
| ❌ 없음 | 참조 구현(수집기·채점 엔진·프로빙 파이프라인) · 코호트 데이터 · 보정된 임계값 |

**적합성은 자기 선언입니다.** `conformance/cases/` 의 케이스를 자기 구현으로 돌려
통과 여부를 스스로 밝히면 됩니다. MKII 가 발급하는 인증이 아닙니다.

케이스의 기대값은 **명세의 수식에서 독립 유도**했습니다 — 참조 구현에 돌려 나온 값을
기대값으로 쓰면 구현의 버그가 그대로 표준이 되기 때문입니다. 그래서 참조 구현이
케이스를 통과하지 못하는 항목이 있으면 케이스가 아니라 구현을 고칩니다.

**실측 사례의 대상은 익명입니다.** 명세에 나오는 「사이트 A/B/C」는 만들어낸 예시가 아니라
파일럿에서 실제로 관측한 사이트이고, 사전 고지 없이 감사한 대상이므로 이름을 적지 않습니다.

---

## 2. 파일 구성

```
framework/
├── README.md                     ← 지금 이 파일. 진입점
├── rubric/
│   ├── pillars.yaml              ★ Plane B 채점 정본 (5 Pillar · 45항목)
│   └── channels.yaml             ★ Plane A 채널 가중치 정본 (6채널)
├── schema/
│   └── report.schema.json        ★ 리포트 산출물 JSON Schema (draft 2020-12)
└── spec/
    ├── avr-model.md              모델 총론 · 두 평면 분리 근거 · Gap Matrix 처방
    ├── plane-a-visibility.md     Visibility 지표 정의 · 수식 · 통계 규칙
    ├── plane-b-readiness.md      Readiness 채점 규칙 · ARS 산식 · 게이팅
    └── scoring.md                사분면 판정 임계값과 근거
```

★ 표시 = 코드가 직접 파싱하는 **정본(Single Source of Truth)**.
정본 3개는 서로 id가 일치해야 하며, 변경 시 **같은 커밋에서 함께** 갱신한다.

---

## 3. 읽는 순서

| 목적 | 순서 |
|---|---|
| 모델을 처음 이해 | `spec/avr-model.md` → `README.md` §4 |
| 스코어러 구현 | `rubric/pillars.yaml` → `spec/plane-b-readiness.md` → `spec/scoring.md` |
| 프로빙 파이프라인 구현 | `rubric/channels.yaml` → `spec/plane-a-visibility.md` |
| 리포트 렌더러 구현 | `schema/report.schema.json` → `spec/avr-model.md` §4.1 (처방 문안) |
| rubric 항목 수정 | `spec/plane-b-readiness.md` §2 → `rubric/pillars.yaml` → `schema/report.schema.json` |

---

## 4. 핵심 수치 (한눈에)

### Plane B — Pillar 배점

| id | 이름 | name_en | weight | 항목 수 | auto | manual |
|---|---|---|---|---|---|---|
| P1 | 접근성 | Retrievability | 25 | 10 | 9 | 1 |
| P2 | 추출성 | Extractability | 25 | 10 | 10 | 0 |
| P3 | 기계가독성 | MachineReadability | 20 | 9 | 8 | 1 |
| P4 | 권위 | Trust | 20 | 9 | 2 | 7 |
| P5 | 신선도·운영 | Freshness | 10 | 6 | 4 | 2 |
| | | **합계** | **100** | **44** | **33** | **11** |

**게이팅**: `P1-01`(AI 크롤러 전면 차단) 또는 `P1-03`(JS 없이 렌더 불가)이 0점이면 **총점 상한 40**.

### Plane A — 채널 가중치

| id | 채널 | weight | search toggle | API |
|---|---|---|---|---|
| `chatgpt` | ChatGPT | 0.28 | ✅ | ✅ |
| `gemini` | Gemini | 0.22 | ✅ | ✅ |
| `naver_ai_briefing` | 네이버 AI 브리핑 | 0.18 | ❌ | ❌ 스크래핑 |
| `claude` | Claude | 0.14 | ✅ | ✅ |
| `perplexity` | Perplexity | 0.10 | ❌ 상시 ON | ✅ |
| `google_ai_overviews` | Google AI Overviews | 0.08 | ❌ | ❌ 스크래핑 |
| | **합계** | **1.00** | | |

### 핵심 산식

```
AVI = 100 × Σ_c w_c ( 0.5·MR_c + 0.3·PosScore_c + 0.2·CitShare_c )
ARS = Σ_p (raw_p / max_raw_p) × weight_p      (게이팅 시 min(·, 40))
```

### 사분면 임계값

```
AVI ≥ 25 → high     ARS ≥ 60 → high
```

| | ARS < 60 | ARS ≥ 60 |
|---|---|---|
| **AVI ≥ 25** | Q3 브랜드 관성형 | Q1 리더 |
| **AVI < 25** | Q4 미개척 | **Q2 준비만 된 상태** ← 가장 흔하고 시장이 못 짚는 사분면 |

---

## 5. 이 프레임워크가 시장과 다른 지점

1. **통계적 신뢰구간** — MR을 Wilson score interval로 구간 추정한다.
   `"33%"`가 아니라 `"33.0% (95% CI 28.5%–37.8%, n=400)"`로 보고한다.
   개선 주장은 two-proportion z-test로 검정하며, 유의하지 않으면 "개선"이라고 쓰지 않는다.
2. **프록시 격차 공시** — 주간 트래킹에 저가 모델을 쓴다는 사실과, 플래그십 대비 MR 차이 `δ`를
   리포트에 의무 공시한다.
3. **원인·결과 분리** — 사이트는 멀쩡한데 안 뜨는 케이스(Q2)를 식별하고,
   "사이트를 더 고치자"가 아니라 "외부 권위가 병목"이라고 진단한다.
4. **한국 특수 항목** — 네이버 서치어드바이저/Yeti(`P1-10`), 한국어 어절 기준 문장 길이(`P2-05`),
   네이버 플레이스 NAP(`P3-08`), 네이버 생태계 신뢰 신호(`P4-09`).
5. **게이팅** — 도달 불가 상태를 가산 점수로 얼버무리지 않고 상한으로 강제한다.

---

## 6. 명세의 한계 (숨기지 않는다)

- Pillar weight(25/25/20/20/10), AVI 계수(α=0.5, β=0.3, γ=0.2), 임계값(AVI 25 / ARS 60)은
  모두 **v1 고정값이며 실증으로 유도된 값이 아니다.** 근거는 각 spec 문서에 서술되어 있고,
  파일럿 10개 사이트와 코호트 30 브랜드 확보 시점에 재캘리브레이션한다.
- 네이버의 출처 선정 로직은 비공개다. 관련 항목은 **관측 기반 추정**이며 인과가 검증되지 않았다.
- 네이버 AI 브리핑·Google AI Overviews는 공식 API가 없어 스크래핑에 의존한다.
  약관 리스크·파서 파손·시계열 단절 가능성을 계약서와 리포트에 명시해야 한다.
- "AI 언급 → 매출"의 인과는 이 프레임워크가 검증하지 않는다. AVI는 성과 측정 지표이지
  결과 보장이 아니다.

---

## 7. 정합성 검증

정본 3개 파일의 파싱과 id 일치를 확인한다.

```bash
python3 - <<'PY'
import json, yaml
p = yaml.safe_load(open('framework/rubric/pillars.yaml'))
c = yaml.safe_load(open('framework/rubric/channels.yaml'))
s = json.load(open('framework/schema/report.schema.json'))

assert sum(x['weight'] for x in p['pillars']) == 100
assert abs(sum(x['weight'] for x in c['channels']) - 1.0) < 1e-9
assert {i['id'] for pl in p['pillars'] for i in pl['items']} == set(s['$defs']['item_id']['enum'])
assert {pl['id'] for pl in p['pillars']} == set(s['$defs']['pillar_id']['enum'])
assert {ch['id'] for ch in c['channels']} == set(s['$defs']['channel_id']['enum'])
print("OK")
PY
```

---

## 8. 다음 단계

1. 원가 검증 스파이크 — 6채널 프로빙 1회 실측, 계정당 월 원가 산출
2. `check: auto` 33개 항목의 판정 로직 구현 (크롤러 + 파서)
3. 파일럿 10개 사이트 — Plane A + Plane B 동시 측정, Gap Matrix 분포 확인
4. 임계값·계수 재캘리브레이션 → `scoring.md` v1.1

> 코드 작성 착수 전 `/dev-cycle` 필수.
