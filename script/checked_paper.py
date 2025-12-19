import json
import requests
import feesdparser
from datetime import datetime
from pathlib import Path

AUTHOR_ID = "1741107"  # David Lo (SMU)

# ---------- Semantic Scholar ----------
ss_url = f"https://api.semanticscholar.org/graph/v1/author/{AUTHOR_ID}/papers"
ss_params = {
    "limit": 5,
    "sort": "publicationDate",
    "fields": "paperId,title,publicationDate"
}

ss_resp = requests.get(ss_url, params=ss_params)
ss_resp.raise_for_status()

ss_papers = []
for p in ss_resp.json()["data"]:
    if p.get("publicationDate"):
        ss_papers.append({
            "source": "semantic_scholar",
            "id": p["paperId"],
            "title": p["title"],
            "date": p["publicationDate"]
        })

# ---------- arXiv ----------
arxiv_url = (
    "http://export.arxiv.org/api/query?"
    "search_query=au:\"David Lo\"&"
    "sortBy=submittedDate&"
    "sortOrder=descending&"
    "max_results=5"
)

feed = feedparser.parse(arxiv_url)

arxiv_papers = []
for e in feed.entries:
    authors = [a.name for a in e.authors]
    if "David Lo" in authors:
        arxiv_papers.append({
            "source": "arxiv",
            "id": e.id.split("/")[-1],
            "title": e.title.strip(),
            "date": e.published[:10]
        })

# ---------- Merge & select latest ----------
all_papers = ss_papers + arxiv_papers

def parse_date(p):
    return datetime.fromisoformat(p["date"])

latest = max(all_papers, key=parse_date)

out = {
    "source": latest["source"],
    "paperId": latest["id"],
    "title": latest["title"],
    "publicationDate": latest["date"]
}

Path("data/last_paper.json").write_text(
    json.dumps(out, indent=2)
)
