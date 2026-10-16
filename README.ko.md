# AVR audit — GitHub Action

배포한 사이트를 [AVR](https://github.com/maior/logosai-avr) 공개 진단 API 로 검사하고,
**필수 항목(AI 크롤러 접근 · JS 없이 본문 렌더링)이 깨졌을 때만** 워크플로를 실패시킵니다.

> **English:** [README.md](README.md)

```yaml
# .github/workflows/avr.yml — 배포 뒤 단계
- uses: maior/logosai-avr@action
  with:
    url: https://example.com
    api-key: ${{ secrets.AVR_API_KEY }}
    api-base: https://<AVR 배포 주소>/api
    # min-score: 60   # 선택. 비우면 필수 항목만 본다
```

| 입력 | 필수 | 뜻 |
|---|---|---|
| `url` | ✓ | 진단할 주소 |
| `api-key` | ✓ | AVR API 키 (`aeo_…`). 저장소 secret 으로 넘깁니다 |
| `api-base` | ✓ | AVR API 주소 |
| `min-score` | | 이 ARS 미만이면 실패. 비우면 필수 항목만 봅니다 |
| `timeout-seconds` | | 결과를 기다릴 최대 시간 (기본 600) |

출력: `score` (측정 불가면 `None`), `job_id` (`GET /v1/audits/{id}` 로 전체 결과).

## 판정 규칙

- **실패:** 필수 항목이 0점(`gated` · `blocking_failures`)이거나, 지정한 `min-score` 미만.
- **경고만:** 점수를 내지 못했거나(측정 불가) 필수 항목을 판정하지 못한 경우. 안 잰 것은 0 이 아닙니다.
- 판정은 서버가 합니다. 이 액션은 결과를 읽기만 하고 점수를 다시 계산하지 않습니다.

ARS 는 **권장 관행 이행도**이지 AI 인용 예측이 아닙니다. 채점 기준은
[공개 명세](https://github.com/maior/logosai-avr)(CC BY 4.0)에 있습니다.

표준 라이브러리만 쓰므로 러너에 설치할 것이 없습니다 (`python3` 필요).

---

이 브랜치는 비공개 저장소의 `integrations/github-action/` 에서 내보낸 것입니다. 이슈는 받지만
변경은 원본에서 합니다. 라이선스는 [MIT](LICENSE).
