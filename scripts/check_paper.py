import json
import requests
import feedparser
from datetime import datetime
from pathlib import Path

AUTHOR_ID = "1741107"

def get_semantic_scholar_papers():
    url = f"https://api.semanticscholar.org/graph/v1/author/{AUTHOR_ID}/papers"
    params = {
        "limit": 5,
        "sort": "publicationDate",
        "fields": "paperId,title,publicationDate"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()

    papers = []
    for p in r.json()["data"]:
        if p.get("publicationDate"):
            papers.append({
                "source": "semantic_scholar",
                "id": p["paperId"],
                "title": p["title"],
                "date": p["publicationDate"]
            })
    return papers


def get_arxiv_papers():
    base_url = "http://export.arxiv.org/api/query"

    params = {
        "search_query": 'au:"David Lo"',
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 5
    }

    # arXiv richiede User-Agent valido
    headers = {
        "User-Agent": "DavidLoPaperMonitor/1.0 (contact: you@example.com)"
    }

    response = requests.get(base_url, params=params, headers=headers)
    response.raise_for_status()

    feed = feedparser.parse(response.text)

    papers = []
    for e in feed.entries:
        authors = [a.name for a in e.authors]
        if "David Lo" in authors:
            papers.append({
                "source": "arxiv",
                "id": e.id.split("/")[-1],
                "title": e.title.strip(),
                "date": e.published[:10]
            })

    return papers


def select_latest(papers):
    return max(papers, key=lambda p: datetime.fromisoformat(p["date"]))


def write_last_paper(paper, path="data/last_paper.json"):
    Path(path).write_text(json.dumps({
        "source": paper["source"],
        "paperId": paper["id"],
        "title": paper["title"],
        "publicationDate": paper["date"]
    }, indent=2))


if __name__ == "__main__":
    papers = get_semantic_scholar_papers() + get_arxiv_papers()
    latest = select_latest(papers)
    write_last_paper(latest)
