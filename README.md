# AVR audit — GitHub Action

Audits a deployed site with the public [AVR](https://github.com/maior/logosai-avr) diagnostic
API and fails the workflow **only when a blocking item breaks** — AI-crawler access, or body
text that renders without JavaScript.

> **한국어:** [README.ko.md](README.ko.md)

```yaml
# .github/workflows/avr.yml — a step after deploy
- uses: maior/logosai-avr@action
  with:
    url: https://example.com
    api-key: ${{ secrets.AVR_API_KEY }}
    api-base: https://<your AVR host>/api
    # min-score: 60   # optional. Leave empty to check blocking items only
```

| Input | Required | Meaning |
|---|---|---|
| `url` | ✓ | URL to audit |
| `api-key` | ✓ | AVR API key (`aeo_…`). Pass it as a repository secret |
| `api-base` | ✓ | AVR API base URL |
| `min-score` | | Fail if ARS is below this. Empty = blocking items only |
| `timeout-seconds` | | Maximum time to wait for the result (default 600) |

Outputs: `score` (`None` when the site could not be scored) and `job_id`
(full result at `GET /v1/audits/{id}`).

## Verdict rules

- **Fail:** a blocking item scored 0 (`gated` · `blocking_failures`), or the score is below the
  `min-score` you set.
- **Warn only:** no score could be produced, or a blocking item could not be judged.
  Not measured is not zero.
- The server decides. This action only reads the result and never recomputes a score.

ARS measures **adherence to recommended practices**. It is not a prediction of AI citation.
The scoring rules are in the [public specification](https://github.com/maior/logosai-avr)
(CC BY 4.0).

Standard library only — nothing to install on the runner (`python3` required).

---

This branch is exported from `integrations/github-action/` in a private repository.
Issues are welcome; changes are made at the source. Licensed under [MIT](LICENSE).
