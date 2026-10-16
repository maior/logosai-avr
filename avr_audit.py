#!/usr/bin/env python3
"""AVR 진단을 CI 에서 — 공개 진단 API(POST /v1/audits)를 부르고, 필수 항목이 깨졌을 때만 실패한다.

표준 라이브러리만 쓴다 (러너에 설치할 것이 없다).
판정은 하지 않는다 — 서버가 낸 gated·blocking_failures 를 읽기만 한다. 사본을 만들지 않는다.
미측정·미판정은 경고이지 실패가 아니다: 안 잰 것은 0 이 아니다.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


def verdict(job: dict, min_score: float | None) -> tuple[int, list[str]]:
    """(종료 코드, GitHub 워크플로 명령 줄들)."""
    if job.get("status") != "done":
        return 1, [f"::error::Audit failed — {job.get('error') or job.get('status')} (re-run the job to retry)"]
    r = job["result"]
    msgs: list[str] = []
    if not r.get("measurable", True) or r.get("score") is None:
        return 0, ["::warning::No score could be produced (not measurable) — not treated as a failure. "
                   f"{r.get('unmeasurable_reason') or ''}".rstrip()]
    msgs.append(f"ARS {r['score']:.1f} / 100 (adherence to recommended practices — not a prediction of AI citation)")
    code = 0
    if r.get("gated") or r.get("blocking_failures"):
        msgs.append("::error::Blocking item failed: " + ", ".join(r.get("blocking_failures") or ["(gated)"]))
        code = 1
    if r.get("gating_undetermined"):
        msgs.append("::warning::Blocking item could not be judged: " + ", ".join(r.get("blocking_unscored") or []))
    if min_score is not None and r["score"] < min_score:
        msgs.append(f"::error::ARS {r['score']:.1f} is below min-score {min_score:g}")
        code = 1
    return code, msgs


def _call(method: str, url: str, key: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"::error::AVR API returned {e.code} — {e.read().decode(errors='replace')[:300]}")


def main() -> int:
    base = os.environ["AVR_API_BASE"].rstrip("/")
    key, target = os.environ["AVR_API_KEY"], os.environ["AVR_URL"]
    min_score = float(os.environ["AVR_MIN_SCORE"]) if os.environ.get("AVR_MIN_SCORE") else None
    deadline = time.time() + int(os.environ.get("AVR_TIMEOUT_SECONDS") or 600)

    job = _call("POST", f"{base}/v1/audits", key, {"url": target})
    while job["status"] in ("queued", "running"):
        if time.time() > deadline:
            print(f"::error::Timed out — job {job['id']} did not finish (raise timeout-seconds or retry)")
            return 1
        time.sleep(5)
        job = _call("GET", f"{base}/v1/audits/{job['id']}", key)

    code, msgs = verdict(job, min_score)
    print("\n".join(msgs))
    if job.get("result") is not None and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"score={job['result'].get('score')}\njob_id={job['id']}\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
