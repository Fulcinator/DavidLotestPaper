import json
import requests
import feedparser
from datetime import datetime
from pathlib import Path

AUTHOR_ID = "143960553"  # David Lo's Semantic Scholar Author ID

def get_semantic_scholar_papers():
    url = f"https://api.semanticscholar.org/graph/v1/author/{AUTHOR_ID}/papers"
    params = {
        "limit": 5,
        "sort": "-publicationDate",
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

def get_crossref_papers():
    url = "https://api.crossref.org/works"
    params = {
        "query.author": "David Lo",
        "rows": 5,
        "sort": "published",
        "order": "desc"
    }

    headers = {
        "User-Agent": "DavidLoPaperMonitor/1.0 (mailto:you@example.com)"
    }

    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()

    papers = []
    for item in r.json()["message"]["items"]:
        date_parts = item.get("published", {}).get("date-parts")
        if not date_parts:
            continue

        year, month, day = (date_parts[0] + [1, 1, 1])[:3]
        date = f"{year:04d}-{month:02d}-{day:02d}"

        papers.append({
            "source": "crossref",
            "id": item.get("DOI"),
            "title": item["title"][0],
            "date": date
        })

    p = papers.copy()
    for paper in papers:
        #discard papers if the date is > 
        if datetime.fromisoformat(paper["date"]) > datetime.now():
            p.remove(paper)
    return p



def get_arxiv_papers():
    base_url = "https://export.arxiv.org/api/query"

    params = {
        "search_query": 'au:"David Lo"',
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 5
    }

    headers = {
        "User-Agent": "DavidLoPaperMonitor/1.0 (contact: you@example.com)"
    }

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)

        # arXiv rate limit
        if response.status_code == 429:
            print("arXiv rate limited (429). Skipping arXiv.")
            return []

        response.raise_for_status()

    except requests.RequestException as e:
        print(f"arXiv request failed: {e}")
        return []

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
    if not papers:
        return None
    return max(papers, key=lambda p: datetime.fromisoformat(p["date"]))


def write_last_paper(paper, path="data/last_paper.json"):
    Path(path).write_text(json.dumps({
        "source": paper["source"],
        "paperId": paper["id"],
        "title": paper["title"],
        "publicationDate": paper["date"]
    }, indent=2))


if __name__ == "__main__":
    papers = get_crossref_papers() + get_arxiv_papers()
    
    latest = select_latest(papers)
    if latest and latest["date"] != json.loads(Path("data/last_paper.json").read_text())["publicationDate"]:
        write_last_paper(latest)

