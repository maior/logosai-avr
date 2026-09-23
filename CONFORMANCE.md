# AVR 적합성 명세 (Conformance)

"AVR 을 구현했다"는 주장을 **증명 가능한 진술**로 만든다.

이 문서는 (1) 적합성 수준의 정의, (2) 각 수준의 필수 요건, (3) 골든 케이스의 형식과 실행 방법,
(4) 부동소수 비교 규칙을 규정한다. 구조와 계층은 [`ARCHITECTURE.md`](ARCHITECTURE.md) 참조.

---

## 1. 왜 적합성 수준을 나누는가

AVR 전체를 구현하려면 LLM 프로빙 파이프라인·통계 계층·사이트 수집기가 전부 필요하다.
그러나 실제 채택은 대개 부분부터 시작한다.

- 사내 대시보드에 ARS 만 붙이려는 팀
- 기존 SEO 감사 툴에 Plane B 항목 판정만 얹으려는 벤더
- 학술 목적으로 통계 처리만 재현하려는 연구자

수준을 나누지 않으면 이 셋이 전부 "AVR 미구현"이 되거나, 반대로 셋 다 "AVR 구현"이라고
주장하게 된다. 후자가 더 위험하다 — **같은 이름의 서로 다른 점수가 시장에 돌아다니는 것**이
프레임워크가 죽는 방식이다.

---

## 2. 적합성 수준

| 수준 | 이름 | 한 줄 정의 | 주장할 수 있는 것 |
|---|---|---|---|
| **Level 1** | Scoring Conformance | 채점 산식과 판정 규칙만 구현 | "AVR 산식으로 계산한 ARS/AVI" |
| **Level 2** | Assessment Conformance | Level 1 + `check: auto` 항목의 기계 판정 | "AVR Plane B 자동 진단" |
| **Level 3** | Measurement Conformance | Level 2 + Plane A 프로빙과 통계 | "AVR 전체 진단" |

수준은 누적이다. Level 3 을 주장하려면 Level 1·2 의 요건을 전부 만족해야 한다.

**그리고 어느 수준이든 `spec/reliability.md` 의 신뢰도 공시를 함께 만족해야 한다**
(2026-09-18 신설). 재현성을 모르는 점수는 해석할 수 없다 — 재측정에서 3점이 올랐을 때
그게 개선인지 잡음인지 가릴 근거가 없기 때문이다. **값이 나쁜 것은 적합성 문제가 아니지만,
재지 않은 것은 적합성 문제다.**

### 2.1 Level 1 — Scoring Conformance

**요구 사항**

1. `rubric/pillars.yaml` 과 `rubric/channels.yaml` 을 **파싱해서** 쓴다. 배점·가중치를
   코드에 복제하지 않는다. (검증: 두 파일을 수정하면 점수가 따라 바뀌어야 한다)
2. ARS 산식 — Pillar 정규화(`raw/max_raw`), 미판정 항목의 분모 제외, 커버리지 50% 미만
   Pillar 제외 및 재정규화, 게이팅 상한 `min()` 적용, `raw_ars` 와 `ars` 동시 산출.
3. blocking 항목의 입력 검증 — 사유 없는 누락·`null`·빈 사유·중복 지정을 **거부**한다.
   사유가 있는 `unavailable` 은 통과시키되 판정 불능 상태를 산출물에 남긴다.
4. AVI 산식 — 채널 가중치 재정규화, `CitShare = null` 채널의 `α'=0.625 / β'=0.375` 재정규화,
   `coverage` 산출.
5. Gap Matrix — 임계값 AVI ≥ 25 / ARS ≥ 60, 경계 포함, 게이팅 후 `ars` 로 판정.
6. 산출물이 `schema/report.schema.json` 을 통과한다.

**골든 케이스**: `level: 1` 인 케이스 전부 통과.

**주장할 수 없는 것**: 항목 점수를 어떻게 얻었는지에 대해서는 아무것도 주장할 수 없다.
Level 1 구현은 사람이 채점한 0/1/2 를 입력으로 받는 계산기다.

### 2.2 Level 2 — Assessment Conformance

**추가 요구 사항**

1. `check: auto` 항목을 `levels` 문구대로 기계 판정한다.
2. **근거 없는 점수를 내지 않는다.** 모든 채점 항목에 최소 1건의 근거를 남긴다
   (`plane-b-readiness.md` §2.1-3). 근거를 못 남기면 점수가 아니라 미판정이다.
3. **판정에 필요한 입력이 없으면 `unavailable` + 사유**를 낸다. 임의 대리 지표로 채우거나
   조용히 낮은 등급을 주는 것을 금지한다 (`ARCHITECTURE.md` §5.3).
4. 담당하지 않는 auto 항목을 **목록으로 공시**한다. "측정했는데 나빴다"와 "안 봤다"를
   구분할 수 있어야 한다.
5. 네트워크 실패를 0점으로 처리하지 않는다. 타임아웃을 0점으로 두면 감사 인프라의 장애가
   고객 사이트의 결함으로 기록된다.
6. 운영 정의를 **문서로 공시**한다 (`ARCHITECTURE.md` §6 의 등록부 항목 중 자기 구현이
   정한 값). 공시하지 않은 구현은 Level 2 를 주장할 수 없다 — 공시가 없으면 왜 다른 점수가
   나왔는지 아무도 추적할 수 없기 때문이다.

**골든 케이스**: `level: 1` 과 `level: 2` 전부 통과.

**부분 적합 표기**: auto 33개 전부를 구현하지 않아도 Level 2 를 주장할 수 있다.
단 **커버리지를 함께 표기**한다. 예: `AVR Level 2 conformant (auto coverage 22/33)`.

### 2.3 Level 3 — Measurement Conformance

**추가 요구 사항**

1. `channels.yaml` 의 채널에 대해 프로빙을 수행하고 MR·PosScore·CitShare 를 산출한다.
2. 모든 비율에 **Wilson score interval** 을 붙인다. 점추정만 보고하는 것을 금지한다.
3. **클러스터 보정.** 프로빙은 "질문 M개 × 반복 k회"라 관측이 독립이 아니다.
   raw `n` 으로 Wilson 을 내면 구간이 실제보다 좁다. `n` · `n_eff` · `ρ` 를 함께 보고한다.
4. 개선 주장에 **two-proportion z-test** 를 붙인다. 유의하지 않으면 "개선"이라고 쓰지 않는다.
   Matched Cohort(동일 질문 × 동일 채널 × 동일 검색 모드) 위에서만 비교한다.
5. **프록시 격차 δ 공시.** 트래킹 모델과 캘리브레이션 모델이 다르면 그 차이를 리포트에 남긴다.
   API 보유 채널 4개는 필수.
6. `not_shown`(채널 특성) · `off_topic`(질문 설계 결함) · `failed`(수집 장애)를 구분한다.
7. 미측정 채널을 0 으로 채우지 않는다. 제외하고 가중치를 재정규화하며 `coverage` 를 공시한다.

**골든 케이스**: `level: 1` · `2` · `3` 전부 통과.

**주의**: Level 3 은 *같은 숫자가 나오는 것*을 요구하지 않는다. LLM 응답은 비결정론적이고
모델은 조용히 갱신된다. Level 3 이 요구하는 것은 **같은 관측 데이터에 같은 통계 처리**다.
그래서 Level 3 골든 케이스의 입력은 응답이 아니라 집계된 `(k, n)` 이다.

### 2.4 적합성 표기 형식

```
AVR Level 2 conformant · rubric 1.2.0 · channels 1.0.0 · schema 1.0.0
  (auto coverage 22/33, known gaps: 4)
```

버전을 함께 적지 않은 적합성 주장은 무효다.

**참조 구현의 선언은 `DECLARATION.md` 에 있다** (2026-09-21 신설). 형식을 규정해 놓고
우리 것을 내지 않으면 이 문서는 표준이 아니라 마케팅이다. 그 선언은 Level 2 이고,
Level 3 을 주장하지 않는 이유(Plane A 재현성 미측정)와 **주장하지 않는 것 다섯 가지**를
함께 적는다. rubric 이 바뀌면 같은 사이트에 다른 점수가
나오므로, 어느 자로 쟀는지 밝히지 않은 점수는 검증할 수 없다.

---

## 3. 골든 케이스

### 3.1 위치와 형식

```
framework/conformance/cases/<id>.json     한 파일에 케이스 하나
```

파일명(확장자 제외)과 `id` 는 일치해야 한다. 러너는 디렉토리를 글롭으로 훑으므로
**케이스를 추가하면 자동으로 잡힌다.** 목록을 코드에 하드코딩하지 않는다.

### 3.2 케이스 스키마

| 필드 | 필수 | 의미 |
|---|---|---|
| `id` | ✅ | 파일명과 동일한 식별자 |
| `title` | ✅ | 한 줄 요약 |
| `level` | ✅ | 1 / 2 / 3 — 이 케이스가 속하는 적합성 수준 |
| `operation` | ✅ | 무엇을 호출하는가 (§3.4) |
| `rationale` | ✅ | **왜 이 케이스가 필요한가.** 이 필드가 없으면 기대값은 마법 상수다 |
| `spec_refs` | ✅ | 기대값을 유도한 명세 위치 |
| `input` | ✅ | 입력 |
| `expected` | ✅ | 기대 출력. 여기 있는 키만 비교한다 (부분 비교) |
| `tolerance` | ✅ | `{"absolute": ...}` — 부동소수 허용오차 (§4) |
| `reference_implementation` | | `{"status": "implemented" \| "known_gap", "note": "..."}` |
| `notes` | | 보조 설명 |

**`rationale` 은 장식이 아니다.** 케이스가 왜 존재하는지 모르면 6개월 뒤 그 케이스가
실패했을 때 "기대값을 고치자"는 결론이 나온다. 그 순간 스위트가 아무것도 재지 않게 된다.

### 3.3 케이스는 명세에서 유도한다 (강제)

> **케이스를 참조 구현에 돌려서 나온 값을 기대값으로 쓰지 않는다.**
> 구현에 맞추면 구현의 버그가 그대로 표준이 된다.

현재 케이스의 기대값은 `framework/spec/*.md` 의 수식을 **독립 구현**해 산출했고,
그중 6건은 명세 문서가 직접 제시한 값과 대조했다 —
`plane-b-readiness.md` §3.3 의 계산 예(64.6), §4.5 의 실측 표(40.0 / 97.5 / 100.0),
`plane-a-visibility.md` §3.3 의 표본수 표(97 / 196 / 385 / 1068 / 2401),
`scoring.md` §2-(1) 의 균일 부분충족선(50).

### 3.4 지원 operation

| operation | 대상 | Level |
|---|---|---|
| `compute_ars` | ARS 산식 · 게이팅 · 커버리지 · 입력 검증 | 1 |
| `compute_avi` | AVI 산식 · 가중치 재정규화 · CitShare null | 1 |
| `gap_quadrant` | 사분면 판정 · 임계값 경계 · borderline | 1 |
| `item_p1_01` | robots.txt 로부터 P1-01 판정 | 2 |
| `wilson_interval` | Wilson score interval | 3 |
| `wilson_interval_clustered` | 클러스터 보정 Wilson | 3 |
| `cluster_correction` | DEFF · n_eff | 3 |
| `required_sample_size` | 필요 표본수 | 3 |
| `two_proportion_z` | 개선 유의성 검정 | 3 |

새 operation 을 추가하려면 러너에 어댑터를 하나 추가한다.
**어댑터는 계산하지 않는다.** 입력을 구현의 호출 형태로 옮기고 출력을 딕셔너리로 펴는 것만 한다.
어댑터가 계산하기 시작하면 구현의 결손이 러너에 의해 가려진다.

### 3.5 `compute_ars` 입력 표기법

45항목을 매번 나열하지 않기 위해 다섯 필드를 조합한다.

```jsonc
"input": {
  "item_scores_default": 2,          // 전 항목의 기본 점수. null 이면 명시된 항목만 채점
  "item_scores": { "P1-01": 0 },     // 개별 덮어쓰기
  "unscored_item_ids": ["P3-08"],    // 키 자체를 제거해 '미판정'을 만든다
  "unavailable": { "P1-01": "사유" }, // 못 잰 항목과 사유 (사람이 읽는 문장)
  "unavailable_kinds": {             // rubric v1.4.0~ — 커버리지 분모를 가르는 필드
    "P5-04": "not_applicable"        // 6종(v1.5.0~): not_applicable · design_limit ·
  }                                  //   inconclusive · no_collector · input_missing ·
                                      //   awaiting_manual
}
```

**`unavailable_kinds` 가 없으면 `inconclusive` 로 간주한다** — 분모에 남기는 쪽이 안전한
기본값이다. 빼는 쪽으로 기울면 커버리지가 부풀려지고, 그건 이 프레임워크가 하지 말아야 할 일이다.

`not_applicable` 과 `design_limit` 만 `judgeable` 분모에서 빠진다. 규칙은 한 줄이다 —
**판정 대상이 사이트에 성립하지 않으면 뺀다. 우리가 모르면 남긴다.**

같은 입력에 `kind` 만 다르게 준 짝 케이스가 이 구분을 못박고 있다:
`ars-not-applicable-excludes-from-judgeable-crosses-threshold`(ARS 55.0) ↔
`ars-inconclusive-control-does-not-cross-threshold`(ARS 50.0).

### 3.6 거부(rejection) 케이스

입력이 규칙 위반이면 구현은 **거부해야 한다**. 조용히 해석하면 같은 입력에 두 점수가 생긴다.

```jsonc
"expected": { "rejected": true, "reason_contains": "P1-01" }
```

HTTP 계층을 가진 구현은 이를 **422** 로 번역한다. 거부의 수단(예외/에러 코드)은
구현 자유이나, 거부한다는 사실과 어느 항목 때문인지가 드러나야 한다.

### 3.7 `known_gap` — 참조 구현이 명세를 못 따라가는 지점

케이스가 옳고 참조 구현이 틀린 경우가 있다. 이때 **케이스를 고치지 않는다.**

```jsonc
"reference_implementation": {
  "status": "known_gap",
  "note": "왜 어긋나는지, 어느 파일 어느 줄인지"
}
```

러너는 이 케이스를 `xfail(strict=True)` 로 표시한다. strict 이므로 **구현이 고쳐지면
xpass 로 실패**해 케이스 상태를 갱신하라고 알린다. 조용히 초록이 되지 않는다.

이 장치가 없으면 선택지는 둘뿐이다 — 스위트를 빨간 채로 두거나(곧 아무도 안 본다),
케이스를 구현에 맞춰 고치거나(구현의 버그가 표준이 된다). 둘 다 나쁘다.

---

## 4. 부동소수 비교 규칙

| 대상 | 허용오차 (절대) | 근거 |
|---|---|---|
| ARS · Pillar 점수 · AVI | `1e-9` | 유한 자리 유리수 연산의 결과다. 이 이상 어긋나면 산식이 다른 것이다 |
| Wilson 구간 · 클러스터 보정 | `1e-9` | 케이스가 `z` 를 명시적으로 넘기므로 결정론적 |
| z 통계량 · p-value | `1e-6` | `erf` 구현 차이를 흡수. p-value 판정 경계(0.05)에서 안전한 여유 |
| 필요 표본수 · 항목 점수 | `0` | 정수다. 근사가 없다 |

**규칙**

1. **상대오차를 쓰지 않는다.** 이 프레임워크의 값은 전부 유계(0~100, 0~1)이므로
   절대오차로 충분하고, 절대오차가 더 읽기 쉽다.
2. **허용오차를 케이스마다 적는다.** 전역 기본값을 두면 어떤 케이스가 왜 느슨한지 추적할 수 없다.
3. **허용오차로 불일치를 덮지 않는다.** 참조 구현의 `z` 기본값이 명세와 다른 문제
   (1.96 vs 1.959964, 차이 약 6.4e-6)는 허용오차를 1e-4 로 늘려 통과시키는 대신
   `known_gap` 케이스로 고정했다. **허용오차를 늘려 통과시킨 항목은 더 이상 검증되지 않는다.**
4. `NaN` 은 언제나 실패다.
5. 리스트는 순서를 무시하고 비교한다(집합 비교). 순서에 의미가 있는 산출물은 현재 없다.

---

## 5. 실행

참조 구현에 대해:

```bash
cd backend && .venv/bin/python -m pytest tests/test_conformance_suite.py -q
```

러너: 참조 구현의 적합성 러너 (비공개). 어댑터 계약은 §3 에 정의돼 있으므로 각 구현이 자기 언어로 만들면 된다.
이 러너는 참조 구현 전용이 아니다 — §3.4 의 어댑터 9개만 자기 구현으로 갈아끼우면
어떤 구현이든 같은 케이스로 검증된다.

### 5.1 자체 검증 체크리스트

| | 확인 |
|---|---|
| ☐ | 케이스 디렉토리를 글롭으로 훑는가 (파일 하드코딩 없음) |
| ☐ | 주장하는 수준 이하의 모든 케이스가 통과하는가 |
| ☐ | `known_gap` 이 있다면 그 목록을 공시하는가 |
| ☐ | rubric YAML 의 배점을 바꾸면 점수가 따라 바뀌는가 (복제 여부 확인) |
| ☐ | 산출물이 `report.schema.json` 을 통과하는가 |
| ☐ | 자기 구현의 운영 정의(§2.2-6)를 문서로 공시했는가 |

---

## 6. 현재 케이스 인벤토리

> 이 절은 `backend/tests/test_conformance_inventory.py` 가 `cases/*.json` 에서
> 생성해 **글자 단위로** 대조한다. 손으로 고치면 시험이 빨개진다 — 사람이
> 세는 표는 반드시 낡기 때문이다. 케이스를 더하면 시험이 새 표를 출력한다.

108건. 수준별 L1 42 / L2 52 / L3 14.

| operation | 건수 | 수준 |
|---|---|---|
| `compute_ars` | 23 | L1×23 |
| `remedy_applies` | 15 | L2×15 |
| `remedy_demonstrates` | 14 | L2×14 |
| `gap_quadrant` | 8 | L1×8 |
| `item_p2_06` | 6 | L2×6 |
| `item_p1_07` | 5 | L2×5 |
| `item_p5_04` | 5 | L2×5 |
| `compute_avi` | 4 | L1×4 |
| `determinate_band` | 4 | L1×4 |
| `item_p1_01` | 4 | L2×4 |
| `weighted_cohen_kappa` | 4 | L3×4 |
| `item_p5_07` | 3 | L2×3 |
| `two_proportion_z` | 3 | L3×3 |
| `wilson_interval` | 3 | L3×3 |
| `cluster_correction` | 1 | L3×1 |
| `remedy_scope` | 1 | L1×1 |
| `required_sample_size` | 1 | L3×1 |
| `rubric_evidence` | 1 | L1×1 |
| `rubric_remediation` | 1 | L1×1 |
| `two_proportion_z_clustered` | 1 | L3×1 |
| `wilson_interval_clustered` | 1 | L3×1 |

**미커버 영역** (숨기지 않는다)

- `check: auto` 32개 중 **5개**(`P1-01` · `P1-07` · `P2-06` · `P5-04` · `P5-07`)에만
  항목 판정 케이스가 있다. Level 2 를 항목 단위로 전부 검증하려면 항목당
  level 0/1/2 각 1건 — 나머지 27개 항목에 최소 81건이 더 필요하다.
- `report.schema.json` 검증 케이스가 없다. 스키마를 만족하는 문서를 생성하는 구현이 아직 없다.
- 엔티티 baseline 보정(`MR_corrected = max(0, (MR_raw − f)/(1 − f))`) 케이스가 없다.
- Holm–Bonferroni 다중 비교 보정 케이스가 없다.
- FAI · Sentiment SoV 케이스가 없다 (참조 구현에 해당 계층이 없다).
