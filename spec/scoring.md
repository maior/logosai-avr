# Scoring — Gap Matrix 사분면 판정 규칙

버전: 1.1.0 · 선행 문서: `plane-a-visibility.md`, `plane-b-readiness.md`

이 문서는 AVI(0~100)와 ARS(0~100)를 각각 이분해 사분면을 확정하는 규칙만 다룬다.
각 지수의 산출 자체는 선행 문서에 있다.

---

## 1. 임계값 (v1 고정)

```yaml
AVI_THRESHOLD: 25    # AVI ≥ 25  → high
ARS_THRESHOLD: 60    # ARS ≥ 60  → high
```

두 값 모두 **경계 포함(≥)이 high**다.

| | ARS < 60 | ARS ≥ 60 |
|---|---|---|
| **AVI ≥ 25** | **Q3** 브랜드 관성형 | **Q1** 리더 |
| **AVI < 25** | **Q4** 미개척 | **Q2** 준비만 된 상태 |

사분면 id와 라벨은 `report.schema.json`의 `gap_quadrant` enum과 일치한다.
각 사분면의 처방은 `avr-model.md` §4.1에 있다.

---

## 2. ARS 컷오프 60의 근거

ARS는 rubric 기반 결정론적 점수이므로 임계값을 구조에서 유도할 수 있다.

**(1) 균일 부분충족선이 50점이다.**
44개 항목이 전부 1점(부분 충족)이면 `raw_ARS = 0.5 × 100 = 50`이다.
따라서 50은 "전 항목을 어중간하게 했을 때"의 좌표다. 이 상태를 "준비됨"이라고 부를 수 없다.
임계값은 반드시 50을 넘어야 한다.

**(2) 60은 "다수 항목이 2점"을 요구하는 최소선이다.**
가중치를 무시하고 단순화하면, ARS 60은 전체 항목 정규화 평균 0.6 —
즉 **1점 항목보다 2점 항목이 더 많아야** 도달한다.
(예: 2점 44%·1점 32%·0점 24% → 0.60)
"부분적으로 했다"와 "했다"를 가르는 자연스러운 지점이다.

**(3) 게이팅 상한 40과 20점 마진을 둔다.**
`gating.max_score_when_blocked = 40`이므로, 게이팅 발동 브랜드가 ARS-high로
분류되는 일은 어떤 경우에도 발생하지 않는다. 임계값을 45~50까지 낮추면
게이팅 상한과 너무 가까워져 이 안전 여백이 사라진다.

**(4) P1·P2만 잘해도 넘을 수 있어서는 안 된다.**
P1(25) + P2(25) = 50. 두 Pillar를 만점 받아도 50점이므로 60을 넘지 못한다.
**P3·P4·P5에서 최소 10점 이상을 확보해야만 high로 분류된다.**
이것은 의도된 설계다 — "사이트 기술만 정리하면 준비 완료"라는 흔한 오해를 점수 구조로 차단한다.

---

## 3. AVI 컷오프 25의 근거

**AVI 임계값은 ARS와 달리 구조에서 유도되지 않는다. 시장 관측에 기반한 추정치다.**
이 사실을 리포트에 명시한다.

### 3.1 유도

AVI 25는 대략 다음 상태에 대응한다 (α=0.5, β=0.3, γ=0.2 적용):

```
MR = 0.33,  PosScore = 0.15,  CitShare = 0.10
→ 0.5(0.33) + 0.3(0.15) + 0.2(0.10) = 0.165 + 0.045 + 0.020 = 0.230 → AVI 23.0

MR = 0.35,  PosScore = 0.18,  CitShare = 0.12
→ 0.175 + 0.054 + 0.024 = 0.253 → AVI 25.3
```

즉 **"목표 질문 3개 중 1개에서 언급되고, 가끔 상위에 오르며, 인용은 드물게 발생하는 상태"**
가 대략 25다.

기준점으로 삼은 관측치는 GPTO가 자사 유료 고객 코호트에 대해 공개한 평균 SMR 35.4%
(내부 시장 분석 §2.3, 비공개)다. 이는 **이미 AEO에 투자 중인 브랜드들의 평균**이므로,
"양호"의 하한선으로 삼기에 적절한 참조점이다.
PosScore와 CitShare는 일반적으로 MR보다 상당히 낮게 관측되므로 위와 같이 보수적으로 잡았다.

### 3.2 한계와 재캘리브레이션 계획

이 컷오프의 약점을 숨기지 않는다:

1. **GPTO의 35.4%는 독립 검증되지 않은 자사 발표 수치**이고, 질문 세트 설계와 채널 구성이
   본 프레임워크와 다르다. 직접 비교 가능한 값이 아니다.
2. AVI 절대 수준은 **질문 세트 난이도에 강하게 의존한다.** 브랜드명을 포함한 질문을 넣으면
   MR이 인위적으로 올라간다. 따라서 질문 세트 설계 규약이 고정되기 전까지 컷오프는 잠정값이다.
3. **산업별 baseline이 다르다.** 카테고리 경쟁 밀도가 높을수록 개별 브랜드 MR은 구조적으로 낮다.

**재캘리브레이션 규칙**:
- 파일럿 10개 사이트(내부 파일럿 기록, 비공개) 완료 시 컷오프를 재검토한다.
- 동일 산업 코호트 표본이 **30 브랜드 이상** 확보되면 고정값 25를 폐기하고
  **산업별 코호트 중앙값**을 임계값으로 전환한다. 그때까지는 25를 사용하고
  리포트에 "절대 기준이 아닌 잠정 컷오프"임을 표기한다.
- 컷오프를 변경하면 과거 리포트의 사분면 판정이 바뀐다. `rubric_version`과 별도로
  `scoring` 규칙 버전을 리포트에 남기고, 소급 재판정 여부를 명시한다.

---

## 4. 경계 사례 규칙

### 4.1 AVI 신뢰구간이 임계선을 걸치는 경우

AVI에는 표본 오차가 있다(`plane-a-visibility.md` §3). 점추정만으로 사분면을 확정하면
**표본 잡음이 처방을 뒤바꾼다.** 다음 규칙을 강제한다.

```
if avi_ci.lower < AVI_THRESHOLD <= avi_ci.upper:
    gap_quadrant.borderline = true
```

`borderline = true`일 때:
1. 사분면 id는 점추정 기준으로 채우되, **리포트 UI에서 단일 사분면으로 단정하지 않는다.**
2. 상하 인접 두 사분면의 처방을 **함께** 제시한다.
   (예: AVI 점추정 26, CI 21~31, ARS 72 → Q1과 Q2 처방 병기)
3. 두 처방의 **공통 항목을 먼저 실행**하도록 우선순위를 재정렬한다.
4. 표본 수를 늘린 재측정을 1순위 권고로 넣는다.

ARS는 결정론적 점수이므로 신뢰구간이 없다. 다만 **커버리지가 낮으면** 불확실하다:

```
if plane_b.coverage.scored_items / plane_b.coverage.judgeable_count < 0.7:
    gap_quadrant.borderline = true
```

**분모는 `total_items`가 아니라 `judgeable_count`다 (v1.1.0~).** `judgeable_count`는
`total_items`에서 `unavailable_kind`가 `not_applicable`·`design_limit`인 항목 수를 뺀
값이다(`plane-b-readiness.md` §8.4). 이 두 kind는 "이 사이트에 애초에 해당하지 않는다"는
뜻이지 "확인하지 못했다"는 뜻이 아니므로, 그런 항목이 있다고 해서 ARS의 신뢰도가 낮아지는
것은 아니다. 반대로 `inconclusive`·`no_collector`·`input_missing`은 여전히 분모에 남으므로
"모르는 것"은 그대로 불확실성으로 반영된다. `not_applicable`·`design_limit`이 전혀 없는
진단은 `judgeable_count == total_items`이므로 이 재정의는 v1.0.0 시점의 결과를 바꾸지 않는다.

무료 티어(P4 미채점, 31/44 = 70.5%)는 이 경계를 아슬아슬하게 넘지만,
P4를 통째로 못 본 상태에서 Q2/Q4를 구분할 수 없으므로 무료 리포트는
**항상 `borderline = true`로 강제**하고 "권위 진단 없이는 Q2와 Q4를 구분할 수 없음"을 명시한다.

### 4.2 Plane B 변경 직후

Plane B의 주요 변경(게이팅 항목 해제, 스키마 전면 도입 등) 배포 후 **8주 미만**이면
AVI는 아직 변경을 반영하지 않았을 가능성이 높다(`avr-model.md` §2-(2)).
이 경우 ARS-high · AVI-low 조합(Q2)을 **"반영 대기 중"** 으로 별도 표기하고,
Q2 처방(외부 권위 투자)을 즉시 개시하지 않도록 경고한다.

```
if plane_b_major_change_days_ago < 56 and quadrant == "Q2":
    → label 유지, prescription.headline 을 "반영 대기 — 재측정 후 확정" 으로 치환
```

### 4.3 시계열 단절

`comparison.series_break = true`인 구간에서는 사분면 **이동**을 성과로 보고하지 않는다.
모델 버전 변경으로 인한 AVI 변동과 실제 개선을 구분할 수 없기 때문이다.

---

## 5. 판정 의사코드

```python
AVI_THRESHOLD = 25.0
ARS_THRESHOLD = 60.0

QUADRANT = {
    (True,  True):  ("Q1", "리더"),
    (False, True):  ("Q2", "준비만 된 상태"),
    (True,  False): ("Q3", "브랜드 관성형"),
    (False, False): ("Q4", "미개척"),
}

def classify(avi, ars, avi_ci=None, coverage_ratio=1.0, free_tier=False):
    avi_high = avi >= AVI_THRESHOLD
    ars_high = ars >= ARS_THRESHOLD
    qid, label = QUADRANT[(avi_high, ars_high)]

    borderline = free_tier or coverage_ratio < 0.7
    if avi_ci is not None:
        borderline |= (avi_ci["lower"] < AVI_THRESHOLD <= avi_ci["upper"])

    return {
        "id": qid,
        "label": label,
        "avi_band": "high" if avi_high else "low",
        "ars_band": "high" if ars_high else "low",
        "avi_threshold": AVI_THRESHOLD,
        "ars_threshold": ARS_THRESHOLD,
        "borderline": borderline,
    }
```

**주의**: `ars`는 게이팅 적용 **후** 값을 쓴다(`plane_b.ars`, `raw_ars` 아님).
게이팅 발동 브랜드는 상한 40 < 60이므로 반드시 ARS-low로 분류된다 — 의도된 동작이다.

---

## 6. 임계값 변경 절차

임계값은 코드 상수가 아니라 **버전 관리 대상**이다.

1. 변경 제안에는 근거 데이터(코호트 표본 수, 분포)를 첨부한다.
2. 변경 시 `scoring.md`의 버전을 올리고 변경 사유를 이 문서에 남긴다.
3. 과거 리포트 소급 재판정 여부를 결정하고 명시한다. 기본값은 **소급하지 않음**이다
   (고객이 이미 받은 진단 결론이 사후에 바뀌는 것은 신뢰 문제다).
4. 임계값을 **고객별로 조정하지 않는다.** 조정 가능한 임계값은 원하는 사분면을 만들어낸다.

---

## 7. 버전 이력

| scoring | 날짜 | 변경 | 과거 비교 |
|---|---|---|---|
| **1.1.0** | 2026-09-05 | §4.1 의 `min_item_coverage` 분모를 `total_items` 에서 `judgeable_count` 로 재정의 (`plane-b-readiness.md` §8). `unavailable_kind` 가 `not_applicable`·`design_limit` 인 항목만 분모에서 제외한다. 임계값(0.7) 자체는 불변 | `not_applicable`·`design_limit` 이 없는 진단은 `judgeable_count == total_items` 이므로 결과 불변. 이 kind 를 가진 항목이 있는 진단(2026-09-05 파일럿 2회차)만 재측정 필요 |
| 1.0.0 | 2026-09-05 | 최초 정의 — AVI 25 / ARS 60 임계값과 경계 사례 규칙 | 기준선 |
