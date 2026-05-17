#!/usr/bin/env python3
"""Fetch RSS items from an OPML file for ai-news-briefing.

The script intentionally works with Python standard library only. If
feedparser or BeautifulSoup are installed, it uses them for better parsing.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import email.utils
import gzip
import html
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import feedparser  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    feedparser = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    BeautifulSoup = None


AI_KEYWORDS = {
    "ai",
    "agent",
    "agents",
    "人工智能",
    "模型",
    "大模型",
    "llm",
    "gpt",
    "claude",
    "gemini",
    "qwen",
    "deepseek",
    "llama",
    "multimodal",
    "多模态",
    "rag",
    "benchmark",
    "eval",
    "inference",
    "推理",
    "训练",
    "open source",
    "开源",
    "github",
    "paper",
    "论文",
    "api",
    "tool calling",
    "cursor",
    "windsurf",
    "langchain",
    "llamaindex",
}


@dataclass
class Source:
    name: str
    title: str
    xml_url: str
    group: str


@dataclass
class Item:
    id: str
    title: str
    url: str
    canonical_url: str
    summary: str
    content_text: str | None
    published_at: str | None
    source_name: str
    source_title: str
    source_group: str
    feed_url: str
    ai_score: int


@dataclass
class SourceHealth:
    index: int
    name: str
    title: str
    group: str
    url: str
    ok: bool
    status: str
    attempts: int
    elapsed_seconds: float
    http_status: int | None
    content_type: str
    item_count: int
    error_type: str
    reason: str
    slow: bool


@dataclass
class FeedFetchResult:
    index: int
    source: Source
    entries: list[dict[str, Any]]
    health: SourceHealth


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch RSS news items from OPML and output normalized JSON."
    )
    parser.add_argument("--opml", required=True, help="Path to OPML file")
    parser.add_argument("--since", default="24h", help="24h, 7d, or YYYY-MM-DD..YYYY-MM-DD")
    parser.add_argument("--output", help="Output JSON path")
    parser.add_argument(
        "--fetch-full-text",
        choices=["rss-only", "important-only", "all"],
        default="important-only",
        help="Whether to fetch article pages",
    )
    parser.add_argument(
        "--top-full-text",
        type=int,
        default=20,
        help="Max article pages to fetch when using important-only",
    )
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds per attempt")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent RSS fetch workers")
    parser.add_argument("--retries", type=int, default=1, help="Retry count after the first failed attempt")
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=1.5,
        help="Seconds to wait between retries, multiplied by attempt number",
    )
    parser.add_argument("--progress", action="store_true", help="Print per-source progress to stderr")
    parser.add_argument("--source-health-output", help="Write source health report to .json or .md")
    parser.add_argument(
        "--max-feed-bytes",
        type=int,
        default=5_000_000,
        help="Maximum compressed bytes to read per RSS feed",
    )
    parser.add_argument(
        "--user-agent",
        default="Mozilla/5.0 (compatible; ai-news-briefing/0.1)",
    )
    parser.add_argument(
        "--insecure-skip-verify",
        action="store_true",
        help="Disable TLS certificate verification for corporate proxy environments",
    )
    parser.add_argument("--include-keyword", action="append", default=[])
    parser.add_argument("--exclude-keyword", action="append", default=[])
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser.parse_args()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time_window(value: str) -> tuple[datetime, datetime]:
    now = utc_now()
    value = value.strip()
    if ".." in value:
        start_raw, end_raw = value.split("..", 1)
        start = parse_date_like(start_raw, is_end=False)
        end = parse_date_like(end_raw, is_end=True)
        return start, end
    match = re.fullmatch(r"(\d+)([hd])", value)
    if not match:
        raise ValueError(f"Unsupported --since value: {value}")
    amount = int(match.group(1))
    unit = match.group(2)
    delta = timedelta(hours=amount) if unit == "h" else timedelta(days=amount)
    return now - delta, now


def parse_date_like(value: str, is_end: bool) -> datetime:
    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        dt = datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        if is_end:
            return dt + timedelta(days=1) - timedelta(microseconds=1)
        return dt
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def read_opml(path: Path) -> list[Source]:
    if not path.exists():
        raise FileNotFoundError(f"OPML file does not exist: {path}")
    root = ET.parse(path).getroot()
    body = root.find("body")
    if body is None:
        raise ValueError("Invalid OPML: missing <body>")
    sources: list[Source] = []

    def walk(node: ET.Element, groups: list[str]) -> None:
        text = node.attrib.get("text") or node.attrib.get("title") or ""
        xml_url = node.attrib.get("xmlUrl") or node.attrib.get("xmlurl")
        if xml_url:
            name = text or node.attrib.get("title") or xml_url
            title = node.attrib.get("title") or name
            sources.append(Source(name=name, title=title, xml_url=xml_url, group=" / ".join(groups)))
            return
        next_groups = groups + [text] if text else groups
        for child in node.findall("outline"):
            walk(child, next_groups)

    for outline in body.findall("outline"):
        walk(outline, [])
    return sources


def fetch_url_with_meta(
    url: str,
    timeout: int,
    user_agent: str,
    insecure_skip_verify: bool = False,
    max_bytes: int | None = None,
) -> tuple[bytes, int | None, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",
        },
    )
    context = ssl._create_unverified_context() if insecure_skip_verify else None
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        raw = read_response_body(response, max_bytes=max_bytes)
        encoding = response.headers.get("content-encoding", "").lower()
        return decode_response_body(raw, encoding), getattr(response, "status", None), response.headers.get("content-type", "")


def fetch_url(url: str, timeout: int, user_agent: str, insecure_skip_verify: bool = False) -> bytes:
    raw, _, _ = fetch_url_with_meta(url, timeout, user_agent, insecure_skip_verify)
    return raw


def read_response_body(response: Any, max_bytes: int | None) -> bytes:
    if max_bytes is None:
        return response.read()
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"Response exceeded --max-feed-bytes={max_bytes}")
        chunks.append(chunk)
    return b"".join(chunks)


def decode_response_body(raw: bytes, encoding: str) -> bytes:
    if "gzip" in encoding:
        return gzip.decompress(raw)
    if "deflate" in encoding:
        try:
            return zlib.decompress(raw)
        except zlib.error:
            return zlib.decompress(raw, -zlib.MAX_WBITS)
    return raw


def looks_like_feed(raw: bytes, content_type: str) -> bool:
    head = raw[:500].decode("utf-8", errors="ignore").lower()
    if any(marker in head for marker in ("<rss", "<feed", "<rdf", "<?xml")):
        return True
    lowered_type = content_type.lower()
    return "xml" in lowered_type or "rss" in lowered_type or "atom" in lowered_type


def parse_feed(raw: bytes, source: Source) -> list[dict[str, Any]]:
    if feedparser is not None:
        parsed = feedparser.parse(raw)
        entries: list[dict[str, Any]] = []
        for entry in parsed.entries:
            published = (
                getattr(entry, "published", None)
                or getattr(entry, "updated", None)
                or getattr(entry, "created", None)
            )
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            content = ""
            if getattr(entry, "content", None):
                content = " ".join(str(c.get("value", "")) for c in entry.content)
            entries.append(
                {
                    "title": getattr(entry, "title", ""),
                    "url": getattr(entry, "link", ""),
                    "summary": summary or content,
                    "published": published,
                }
            )
        return entries
    return parse_feed_stdlib(raw, source)


def parse_feed_stdlib(raw: bytes, source: Source) -> list[dict[str, Any]]:
    root = ET.fromstring(raw)
    entries: list[dict[str, Any]] = []
    channel_items = root.findall(".//item")
    if channel_items:
        for item in channel_items:
            entries.append(
                {
                    "title": find_text(item, ["title"]),
                    "url": find_text(item, ["link", "{http://purl.org/rss/1.0/modules/content/}encoded"]),
                    "summary": find_text(item, ["description", "summary"]),
                    "published": find_text(item, ["pubDate", "published", "updated"]),
                }
            )
        return entries

    ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f".//{ns}entry"):
        link = ""
        link_node = entry.find(f"{ns}link")
        if link_node is not None:
            link = link_node.attrib.get("href", "")
        entries.append(
            {
                "title": find_text(entry, [f"{ns}title", "title"]),
                "url": link,
                "summary": find_text(entry, [f"{ns}summary", f"{ns}content", "summary", "content"]),
                "published": find_text(entry, [f"{ns}published", f"{ns}updated", "published", "updated"]),
            }
        )
    return entries


def find_text(node: ET.Element, names: Iterable[str]) -> str:
    for name in names:
        child = node.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = html.unescape(value).strip()
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def clean_text(value: str, max_len: int = 2000) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:max_len]


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlsplit(url)
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered = [
        (k, v)
        for k, v in query_pairs
        if not k.lower().startswith("utm_")
        and k.lower() not in {"fbclid", "gclid", "igshid", "ref", "spm"}
    ]
    query = urllib.parse.urlencode(filtered)
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, query, "")
    )


def normalize_title(title: str) -> str:
    title = html.unescape(title or "").lower()
    title = re.sub(r"https?://\S+", "", title)
    title = re.sub(r"[^\w\u4e00-\u9fff]+", "", title)
    return title


def score_ai_relevance(text: str, include_keywords: list[str], exclude_keywords: list[str]) -> int:
    lowered = text.lower()
    score = 0
    for keyword in AI_KEYWORDS:
        if keyword.lower() in lowered:
            score += 1
    for keyword in include_keywords:
        if keyword.lower() in lowered:
            score += 3
    for keyword in exclude_keywords:
        if keyword.lower() in lowered:
            score -= 5
    return score


def should_keep(item: Item, start: datetime, end: datetime) -> bool:
    if item.published_at:
        published = datetime.fromisoformat(item.published_at.replace("Z", "+00:00"))
        if not (start <= published <= end):
            return False
    return item.ai_score > 0


def make_item(
    entry: dict[str, Any],
    source: Source,
    include_keywords: list[str],
    exclude_keywords: list[str],
) -> Item | None:
    title = clean_text(str(entry.get("title", "")), max_len=500)
    url = str(entry.get("url", "")).strip()
    if not title and not url:
        return None
    summary = clean_text(str(entry.get("summary", "")), max_len=2000)
    canonical_url = canonicalize_url(url)
    published_dt = parse_datetime(str(entry.get("published", "")))
    published_at = published_dt.isoformat() if published_dt else None
    text_for_score = " ".join([title, summary, source.name, source.group])
    ai_score = score_ai_relevance(text_for_score, include_keywords, exclude_keywords)
    item_id = canonical_url or f"{source.xml_url}#{normalize_title(title)}"
    return Item(
        id=item_id,
        title=title,
        url=url,
        canonical_url=canonical_url,
        summary=summary,
        content_text=None,
        published_at=published_at,
        source_name=source.name,
        source_title=source.title,
        source_group=source.group,
        feed_url=source.xml_url,
        ai_score=ai_score,
    )


def basic_dedupe(items: list[Item]) -> list[Item]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    deduped: list[Item] = []
    for item in items:
        title_key = normalize_title(item.title)
        url_key = item.canonical_url
        if url_key and url_key in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
        if url_key:
            seen_urls.add(url_key)
        if title_key:
            seen_titles.add(title_key)
        deduped.append(item)
    return deduped


def fetch_article_text(
    url: str,
    timeout: int,
    user_agent: str,
    insecure_skip_verify: bool,
) -> str | None:
    if not url:
        return None
    try:
        raw = fetch_url(
            url,
            timeout=timeout,
            user_agent=user_agent,
            insecure_skip_verify=insecure_skip_verify,
        )
    except Exception:
        return None
    text = raw.decode("utf-8", errors="ignore")
    if BeautifulSoup is not None:
        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        article = soup.find("article") or soup.find("main") or soup.body
        if article is not None:
            return clean_text(article.get_text(" "), max_len=6000)
    return clean_text(text, max_len=6000)


def enrich_full_text(
    items: list[Item],
    mode: str,
    top_n: int,
    timeout: int,
    user_agent: str,
    insecure_skip_verify: bool,
) -> int:
    if mode == "rss-only":
        return 0
    candidates = items if mode == "all" else sorted(items, key=lambda x: x.ai_score, reverse=True)[:top_n]
    count = 0
    for item in candidates:
        text = fetch_article_text(
            item.url,
            timeout=timeout,
            user_agent=user_agent,
            insecure_skip_verify=insecure_skip_verify,
        )
        if text:
            item.content_text = text
            count += 1
        time.sleep(0.1)
    return count


def classify_fetch_error(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, TimeoutError):
        return "timeout", str(exc)
    if isinstance(exc, urllib.error.HTTPError):
        return "http-error", f"HTTP {exc.code}: {exc.reason}"
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, "reason", exc)
        if "timed out" in str(reason).lower() or isinstance(reason, TimeoutError):
            return "timeout", str(exc)
        return "network-error", str(exc)
    if isinstance(exc, ET.ParseError):
        return "parse-error", str(exc)
    if isinstance(exc, ValueError):
        return "non-rss-response", str(exc)
    return type(exc).__name__, str(exc)


def make_source_health(
    index: int,
    source: Source,
    ok: bool,
    status: str,
    attempts: int,
    elapsed_seconds: float,
    http_status: int | None = None,
    content_type: str = "",
    item_count: int = 0,
    error_type: str = "",
    reason: str = "",
    timeout: int = 20,
) -> SourceHealth:
    return SourceHealth(
        index=index,
        name=source.name,
        title=source.title,
        group=source.group,
        url=source.xml_url,
        ok=ok,
        status=status,
        attempts=attempts,
        elapsed_seconds=round(elapsed_seconds, 3),
        http_status=http_status,
        content_type=content_type,
        item_count=item_count,
        error_type=error_type,
        reason=reason,
        slow=ok and elapsed_seconds >= timeout * 0.75,
    )


def fetch_source_with_retries(
    index: int,
    source: Source,
    timeout: int,
    user_agent: str,
    insecure_skip_verify: bool,
    retries: int,
    retry_backoff: float,
    max_feed_bytes: int,
) -> FeedFetchResult:
    started = time.monotonic()
    max_attempts = max(1, retries + 1)
    last_error_type = ""
    last_reason = ""
    last_http_status: int | None = None
    last_content_type = ""

    for attempt in range(1, max_attempts + 1):
        try:
            raw, http_status, content_type = fetch_url_with_meta(
                source.xml_url,
                timeout=timeout,
                user_agent=user_agent,
                insecure_skip_verify=insecure_skip_verify,
                max_bytes=max_feed_bytes,
            )
            last_http_status = http_status
            last_content_type = content_type
            if not looks_like_feed(raw, content_type):
                head = clean_text(raw[:300].decode("utf-8", errors="ignore"), max_len=180)
                raise ValueError(
                    f"Expected RSS/Atom XML but got content-type={content_type!r}, head={head!r}"
                )
            entries = parse_feed(raw, source)
            elapsed = time.monotonic() - started
            health = make_source_health(
                index=index,
                source=source,
                ok=True,
                status="ok",
                attempts=attempt,
                elapsed_seconds=elapsed,
                http_status=http_status,
                content_type=content_type,
                item_count=len(entries),
                timeout=timeout,
            )
            return FeedFetchResult(index=index, source=source, entries=entries, health=health)
        except Exception as exc:
            last_error_type, last_reason = classify_fetch_error(exc)
            if attempt < max_attempts:
                time.sleep(max(0.0, retry_backoff) * attempt)

    elapsed = time.monotonic() - started
    health = make_source_health(
        index=index,
        source=source,
        ok=False,
        status=last_error_type or "failed",
        attempts=max_attempts,
        elapsed_seconds=elapsed,
        http_status=last_http_status,
        content_type=last_content_type,
        error_type=last_error_type,
        reason=last_reason,
        timeout=timeout,
    )
    return FeedFetchResult(index=index, source=source, entries=[], health=health)


def fetch_sources_concurrently(args: argparse.Namespace, sources: list[Source]) -> list[FeedFetchResult]:
    worker_count = max(1, min(args.workers, len(sources) or 1))
    results: list[FeedFetchResult] = []
    completed = 0
    total = len(sources)

    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_source = {
            executor.submit(
                fetch_source_with_retries,
                index,
                source,
                args.timeout,
                args.user_agent,
                args.insecure_skip_verify,
                args.retries,
                args.retry_backoff,
                args.max_feed_bytes,
            ): source
            for index, source in enumerate(sources)
        }
        for future in concurrent.futures.as_completed(future_to_source):
            result = future.result()
            results.append(result)
            completed += 1
            if args.progress:
                health = result.health
                marker = "OK" if health.ok else health.status.upper()
                slow = " slow" if health.slow else ""
                print(
                    f"[{completed}/{total}] {marker}{slow} "
                    f"{health.name} ({health.elapsed_seconds:.2f}s, attempts={health.attempts})",
                    file=sys.stderr,
                    flush=True,
                )
    return sorted(results, key=lambda result: result.index)


def write_source_health_report(path: Path, healths: list[SourceHealth]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".md":
        lines = [
            "# RSS Source Health",
            "",
            "| Status | Source | Group | Attempts | Elapsed | Items | Reason | URL |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
        for health in healths:
            status = "ok"
            if not health.ok:
                status = health.status
            elif health.slow:
                status = "slow"
            reason = health.reason.replace("|", "\\|")
            lines.append(
                f"| {status} | {health.name} | {health.group} | {health.attempts} | "
                f"{health.elapsed_seconds:.2f}s | {health.item_count} | {reason} | {health.url} |"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    payload = [asdict(health) for health in healths]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    opml_path = Path(args.opml).expanduser()
    start, end = parse_time_window(args.since)
    started_at = utc_now()

    sources = read_opml(opml_path)
    raw_items: list[Item] = []
    fetch_started = time.monotonic()
    fetch_results = fetch_sources_concurrently(args, sources)
    fetch_elapsed = time.monotonic() - fetch_started
    source_health = [result.health for result in fetch_results]
    failed_sources = [
        {
            "name": health.name,
            "title": health.title,
            "group": health.group,
            "url": health.url,
            "status": health.status,
            "attempts": health.attempts,
            "elapsed_seconds": health.elapsed_seconds,
            "reason": health.reason,
        }
        for health in source_health
        if not health.ok
    ]

    for result in fetch_results:
        if not result.health.ok:
            continue
        for entry in result.entries:
            item = make_item(entry, result.source, args.include_keyword, args.exclude_keyword)
            if item is not None:
                raw_items.append(item)

    if args.source_health_output:
        write_source_health_report(Path(args.source_health_output).expanduser(), source_health)

    time_filtered = [item for item in raw_items if should_keep(item, start, end)]
    deduped = basic_dedupe(time_filtered)
    enriched_count = enrich_full_text(
        deduped,
        args.fetch_full_text,
        args.top_full_text,
        args.timeout,
        args.user_agent,
        args.insecure_skip_verify,
    )

    result = {
        "generated_at": utc_now().isoformat(),
        "started_at": started_at.isoformat(),
        "time_window": {
            "input": args.since,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "opml": str(opml_path),
        "dependencies": {
            "feedparser": feedparser is not None,
            "beautifulsoup4": BeautifulSoup is not None,
            "insecure_skip_verify": args.insecure_skip_verify,
        },
        "fetch_options": {
            "timeout": args.timeout,
            "workers": args.workers,
            "retries": args.retries,
            "retry_backoff": args.retry_backoff,
            "max_feed_bytes": args.max_feed_bytes,
            "fetch_full_text": args.fetch_full_text,
        },
        "sources": [asdict(source) for source in sources],
        "source_health": [asdict(health) for health in source_health],
        "failed_sources": failed_sources,
        "stats": {
            "source_count": len(sources),
            "successful_source_count": sum(1 for health in source_health if health.ok),
            "failed_source_count": len(failed_sources),
            "slow_source_count": sum(1 for health in source_health if health.slow),
            "rss_fetch_elapsed_seconds": round(fetch_elapsed, 3),
            "raw_item_count": len(raw_items),
            "time_filtered_count": len(time_filtered),
            "basic_deduped_count": len(deduped),
            "full_text_enriched_count": enriched_count,
        },
        "items": [asdict(item) for item in deduped],
    }

    json_text = json.dumps(
        result,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
        sort_keys=False,
    )
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_text + "\n", encoding="utf-8")
    else:
        print(json_text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
