# Debug: RSS Fetch Hang

Status: [OPEN]

## Symptom

User reports this command appears to hang:

```bash
python3 skills-zh/ai-news-briefing/scripts/fetch_news.py --opml /Users/bytedance/Desktop/fc/person-project/baoyu-skills/follow.opml --since 24h --fetch-full-text rss-only --timeout 5 --insecure-skip-verify --output /tmp/ai-news-briefing-smoke.json --pretty
```

## Hypotheses

1. Sequential fetch latency: the script fetches 70 RSS sources one by one, so a 5 second timeout can become several minutes in the worst case.
2. Dead or slow feeds: some RSS URLs no longer respond, redirect poorly, or time out.
3. Corporate network/TLS/proxy behavior: even with certificate verification disabled, some hosts may stall during TLS handshake or proxy negotiation.
4. XML parsing failure: some endpoints respond with HTML/error pages instead of RSS/Atom, causing parse failures after network fetch.
5. Missing progress output: the script may be working but provides no per-source progress, making long runs look like a dead hang.

## Evidence Log

## Evidence Log

### 2026-05-17 Probe

Ran a concurrent RSS health probe against all 70 OPML sources with:

- Timeout: 5s
- TLS verification: disabled, matching user's command
- Workers: 20
- Output: `/tmp/ai-news-briefing-probe.json`
- Markdown report: `/tmp/ai-news-briefing-source-health.md`

Summary:

- Total sources: 70
- OK within probe: 7
- Failed or abnormal: 63
- Failed by type: 52 `TimeoutError`, 10 `URLError`, 1 non-RSS `application/json`
- Most failures are concentrated on `api.xgo.ing`: 62 total, 61 timeout/URL error, 1 JSON system error.

Confirmed:

- Hypothesis 1 confirmed: current script fetches sources sequentially, so 70 sources * 5s timeout can look like a hang.
- Hypothesis 2 revised: the first high-concurrency probe produced many false positives. A gentler probe with 4 workers and 20s timeout shows 62/70 sources available. Only 8 are abnormal in that run.
- Hypothesis 3 confirmed: network/proxy/TLS behavior is a factor; disabling certificate verification fixed certificate errors but not xgo read/handshake timeouts.
- Hypothesis 4 confirmed for `宝玉(@dotey)`: endpoint returns JSON `{"success":false,"code":"xgo-9999","message":"System error, please try again later"}` rather than RSS.
- Hypothesis 5 confirmed: no per-source progress output makes sequential long-running fetch look stuck.

### 2026-05-17 Gentle Probe

After user showed that one `api.xgo.ing` feed opens in browser, ran a gentler check:

- Workers: 4
- Timeout: 20s
- TLS verification: disabled
- Output: `/tmp/ai-news-briefing-health-workers4.json`

Summary:

- Total sources: 70
- OK: 62
- Failed/abnormal: 8

Abnormal in this run:

1. 阮一峰的网络日志: `URLError timed out`
2. 李继刚(@lijigang_com): `TimeoutError`
3. 宝玉(@dotey): `200 application/json` xgo system error
4. Jina AI(@JinaAI_): `TimeoutError`
5. Anthropic(@AnthropicAI): `TimeoutError`
6. Google AI(@GoogleAI): `TimeoutError`
7. AI at Meta(@AIatMeta): `TimeoutError`
8. DeepLearning.AI(@DeepLearningAI): `TimeoutError`

### 2026-05-17 Anthropic Retest

User showed `Anthropic(@AnthropicAI)` opens in browser. Retested the exact URL three times in Python:

- URL: `https://api.xgo.ing/rss/user/fc28a211471b496682feff329ec616e5`
- Results: all 3 attempts returned `200 application/xml;charset=UTF-8`
- Timings: 3.68s, 18.55s, 5.39s

Conclusion: `Anthropic(@AnthropicAI)` is not a dead source. It is a slow/flaky source under current network conditions. Do not remove it from OPML based on a single timeout.

## Fix Applied

Updated `skills-zh/ai-news-briefing/scripts/fetch_news.py`:

- Added small-concurrency RSS fetching via `--workers` defaulting to 4.
- Added retry controls via `--retries` and `--retry-backoff`.
- Added progress output via `--progress`.
- Added full per-source health data in JSON output.
- Added `--source-health-output` for Markdown/JSON source health reports.
- Increased default timeout to 20s.
- Added browser-compatible default user agent.
- Added gzip/deflate support and `Connection: close`.
- Added `--max-feed-bytes` to avoid unbounded feed downloads.

Verification:

- `python3 -m py_compile` passed.
- Small OPML smoke test passed with 3/3 successful sources.
- Small OPML fetch time improved from about 83.8s to about 23.7s after gzip/UA/read optimizations.
