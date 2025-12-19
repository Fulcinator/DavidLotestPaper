import json
import requests
from pathlib import Path

AUTHOR_ID = "1741107"  # David Lo - SMU

url = f"https://api.semanticscholar.org/graph/v1/author/{AUTHOR_ID}/papers"
params = {
    "limit": 1,
    "sort": "publicationDate",
    "fields": "paperId,title,publicationDate"
}

r = requests.get(url, params=params)
r.raise_for_status()

latest = r.json()["data"][0]

path = Path("data/last_paper.json")
old = json.loads(path.read_text()) if path.exists() else None

if old is None or old["paperId"] != latest["paperId"]:
    path.write_text(json.dumps(latest, indent=2))
