# AVR audit — GitHub Action

Check, on every deploy, that AI answer engines (ChatGPT, Claude, Perplexity, Gemini …) can
still **reach and read** your site. The action calls the [AVR](https://github.com/maior/logosai-avr)
diagnostic API and fails the workflow **only when a blocking item breaks**:

| Blocking item | Fails when |
|---|---|
| **P1-01** AI crawler access | `robots.txt` blocks every AI bot (e.g. `User-agent: *` + `Disallow: /` with no AI-bot exception), or keeps returning 5xx |
| **P1-03** Body renders without JavaScript | The HTML your server sends is an empty client-side shell — no H1 and no real paragraph, under 30% of the rendered text |

Everything else is reported in the log but never blocks your deploy unless you opt in with
`min-score`.

> **한국어:** [README.ko.md](README.ko.md)

---

## Quick start (3 steps)

**1. Get an API key.** Sign in to AVR, open the **dashboard**, scroll to **API 키** (API keys)
and press **새 키 발급** (issue new key). The key starts with `aeo_` and is **shown once** —
copy it immediately. You can revoke keys from the same list.

**2. Store it as a secret.** In your repository: *Settings → Secrets and variables →
Actions → New repository secret*, name `AVR_API_KEY`. Optionally add a variable
`AVR_API_BASE` with your AVR API address (for example `https://avr.example.com/api`).

**3. Add a step after your deploy.**

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
      # … your deploy steps …
      - uses: maior/logosai-avr@action
        with:
          url: https://example.com
          api-key: ${{ secrets.AVR_API_KEY }}
          api-base: ${{ vars.AVR_API_BASE }}
```

That's it. No checkout, no install — the action uses only the Python standard library
(`python3` is preinstalled on GitHub-hosted runners).

---

## Inputs

| Input | Required | Default | Meaning |
|---|---|---|---|
| `url` | ✓ | | Page to audit. `https://` is added if you omit the scheme |
| `api-key` | ✓ | | AVR API key (`aeo_…`). Always pass it from a secret |
| `api-base` | ✓ | | AVR API base URL, e.g. `https://avr.example.com/api` |
| `min-score` | | *(empty)* | Also fail if ARS is below this number. Empty = blocking items only |
| `timeout-seconds` | | `600` | How long to wait for the result. An audit usually takes 30–60 s |

## Outputs

| Output | Meaning |
|---|---|
| `score` | ARS 0–100, or `None` when the site could not be scored |
| `job_id` | Job id. Full result: `GET {api-base}/v1/audits/{job_id}` with the same key |

```yaml
      - id: avr
        uses: maior/logosai-avr@action
        with: { url: https://example.com, api-key: "${{ secrets.AVR_API_KEY }}", api-base: "${{ vars.AVR_API_BASE }}" }
      - run: echo "ARS = ${{ steps.avr.outputs.score }} (job ${{ steps.avr.outputs.job_id }})"
```

## Verdict rules

| Situation | Result |
|---|---|
| A blocking item scored 0 (`gated` / `blocking_failures`) | ❌ fail |
| `min-score` set and ARS below it | ❌ fail |
| The audit job itself failed (target unreachable, server restart) | ❌ fail — re-run the job |
| No score could be produced (not measurable) | ⚠️ warning only |
| A blocking item could not be judged | ⚠️ warning only |
| Everything else | ✅ pass, score printed |

**Not measured is not zero.** If our crawler was briefly blocked or rate-limited, that is
"we could not check", not "your site is broken" — so it warns instead of stopping your deploy.
The server makes every judgment; the action only reads the result and never recomputes a score.

---

## More examples

**Audit a preview deployment** (use the URL your deploy step outputs):

```yaml
      - uses: maior/logosai-avr@action
        with:
          url: ${{ steps.deploy.outputs.preview-url }}
          api-key: ${{ secrets.AVR_API_KEY }}
          api-base: ${{ vars.AVR_API_BASE }}
```

**Weekly check without blocking anything** (report only):

```yaml
on:
  schedule: [{ cron: "0 0 * * 1" }]   # Mondays 00:00 UTC
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: maior/logosai-avr@action
        continue-on-error: true
        with: { url: https://example.com, api-key: "${{ secrets.AVR_API_KEY }}", api-base: "${{ vars.AVR_API_BASE }}" }
```

**Several pages** — use a matrix. Mind the per-domain limit below.

```yaml
    strategy:
      matrix:
        url: [https://example.com, https://example.com/pricing]
    steps:
      - uses: maior/logosai-avr@action
        with: { url: "${{ matrix.url }}", api-key: "${{ secrets.AVR_API_KEY }}", api-base: "${{ vars.AVR_API_BASE }}" }
```

**Pin a version.** `@action` follows the latest export. To pin, use a commit SHA from the
[`action` branch](https://github.com/maior/logosai-avr/commits/action):
`uses: maior/logosai-avr@<sha>`.

---

## Limits

| Limit | Value | When exceeded |
|---|---|---|
| Audits per month | Your plan's allowance (shared with web audits) | HTTP 429 |
| Same target domain | 10 audits per key per 24 h — protects the audited server | HTTP 429 |
| Private / internal addresses | Not accepted | HTTP 422 |

## Troubleshooting

| Log message | Cause | Fix |
|---|---|---|
| `AVR API returned 401` | Key missing, mistyped or revoked | Check the `AVR_API_KEY` secret; create a new key |
| `AVR API returned 422` | Invalid URL, or a private/internal address | Use a public `https://` URL |
| `AVR API returned 429` | Monthly or per-domain limit reached | Wait, reduce matrix size, or raise your plan |
| `Audit failed — …` | Target was unreachable, or the server restarted | Re-run the job |
| `Timed out — job … did not finish` | Audit took longer than `timeout-seconds` | Raise `timeout-seconds` or re-run |
| `Blocking item failed: P1-01` | `robots.txt` blocks AI bots | Allow at least `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot` |
| `Blocking item failed: P1-03` | Server returns an empty JS shell | Server-side render or pre-render the H1 and first paragraph |
| `Blocking item could not be judged` | Could not check this time | Usually transient — nothing to fix; re-run later |

The `detail` text inside an API error comes from the server and may be in Korean; the status
code in the table is what matters.

## FAQ

**What does the score mean?** ARS measures **adherence to recommended AEO practices** (the
automatically checkable items of a 45-item rubric). It is **not** a prediction that AI answers
will cite you — that link has not been validated, and we do not claim it.

**Why doesn't a low score fail my build by default?** Because the score is a practice
checklist, not a proven outcome measure. We don't think our number should stop your deploy.
Opt in with `min-score` if your team decides otherwise.

**What is sent to the API?** Only the `url` and your key. The audit fetches public pages from
that URL with an honest User-Agent and respects `robots.txt`.

**Where are the scoring rules?** In the [public specification](https://github.com/maior/logosai-avr)
(CC BY 4.0) — `rubric/pillars.yaml` and `spec/plane-b-readiness.md`.

---

This branch is exported from `integrations/github-action/` in a private repository.
Issues are welcome; changes are made at the source. Licensed under [MIT](LICENSE).
