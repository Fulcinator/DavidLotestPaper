import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

AUTHOR_NAME = "David Lo"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "last_paper.json"

ARXIV_URL = "https://export.arxiv.org/api/query"
HEADERS = {
    "User-Agent": "DavidLoPaperMonitor/1.0 (+https://github.com/Fulcinator/DavidLotestPaper)"
}


class SourceError(Exception):
    pass


def get_arxiv_papers(max_results=25, retries=3, timeout=30):
    params = {
        "search_query": f'au:"{AUTHOR_NAME}"',
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }

    last_error = None
    for attempt in range(retries):
        if attempt:
            time.sleep(5 * 2 ** attempt)  # 10s, 20s - arXiv asks for >= 3s between calls
        try:
            response = requests.get(ARXIV_URL, params=params, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            last_error = e
            print(f"arXiv attempt {attempt + 1}/{retries} failed: {e}")
            continue

        feed = feedparser.parse(response.text)
        # arXiv sometimes answers 200 with an empty feed: treat it as a transient failure
        if not feed.entries:
            last_error = "empty feed"
            print(f"arXiv attempt {attempt + 1}/{retries} returned no entries")
            continue

        papers = []
        for e in feed.entries:
            authors = [a.name.strip() for a in e.get("authors", [])]
            if AUTHOR_NAME in authors:
                papers.append({
                    "source": "arxiv",
                    "id": e.id.split("/")[-1],
                    "title": " ".join(e.title.split()),
                    "published": e.published,  # full ISO timestamp, e.g. 2026-09-30T13:09:24Z
                })
        return papers

    raise SourceError(f"arXiv unavailable after {retries} attempts: {last_error}")


def parse_ts(value):
    """Parse 'YYYY-MM-DD' or a full ISO timestamp into an aware UTC datetime."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def select_latest(papers):
    if not papers:
        return None
    return max(papers, key=lambda p: parse_ts(p["published"]))


def read_last_paper(path=DATA_PATH):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def is_newer(candidate, stored):
    if stored is None:
        return True
    if candidate["id"] == stored.get("paperId"):
        return False
    # Older files only have "publicationDate"; never move backwards in time
    stored_ts = parse_ts(stored.get("publishedAt") or stored["publicationDate"])
    return parse_ts(candidate["published"]) >= stored_ts


def write_last_paper(paper, path=DATA_PATH, now=None):
    now = now or datetime.now(timezone.utc)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({
        "source": paper["source"],
        "paperId": paper["id"],
        "title": paper["title"],
        "publicationDate": paper["published"][:10],
        "publishedAt": paper["published"],
        "detectedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, indent=2) + "\n", encoding="utf-8")


def main(path=DATA_PATH):
    try:
        papers = get_arxiv_papers()
    except SourceError as e:
        # Fail the job so GitHub notifies us instead of silently keeping stale data
        print(e)
        return 1

    for p in papers:
        print(f'Considering {p["id"]} ({p["published"]}): {p["title"]}')

    latest = select_latest(papers)
    stored = read_last_paper(path)
    if latest and is_newer(latest, stored):
        print(f'New latest paper: {latest["title"]}')
        write_last_paper(latest, path)
    else:
        print("No new paper")
    return 0


if __name__ == "__main__":
    sys.exit(main())
