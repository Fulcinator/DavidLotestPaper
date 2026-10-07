import json
from datetime import datetime, timezone

import pytest
import requests

from scripts import check_paper
from scripts.check_paper import is_newer, main, select_latest, write_last_paper

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2609.39678v1</id>
    <published>2026-09-30T13:09:24Z</published>
    <title>Aletheia:
      Permission-Minimality Testing</title>
    <author><name>Someone Else</name></author>
    <author><name>David Lo</name></author>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2609.00001v1</id>
    <published>2026-10-02T10:00:00Z</published>
    <title>Not by David Lo</title>
    <author><name>David Lopez</name></author>
  </entry>
</feed>"""


class FakeResponse:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(check_paper.time, "sleep", lambda s: None)


def paper(pid, published):
    return {"source": "arxiv", "id": pid, "title": pid, "published": published}


def test_select_latest_uses_full_timestamp():
    papers = [
        paper("a", "2026-09-30T06:26:07Z"),
        paper("b", "2026-09-30T13:09:24Z"),
        paper("c", "2026-09-27T10:44:38Z"),
    ]
    assert select_latest(papers)["id"] == "b"


def test_is_newer_same_day_different_paper():
    stored = {"paperId": "a", "publicationDate": "2026-09-30", "publishedAt": "2026-09-30T06:26:07Z"}
    assert is_newer(paper("b", "2026-09-30T13:09:24Z"), stored)


def test_is_newer_never_goes_backwards():
    stored = {"paperId": "b", "publicationDate": "2026-09-30"}  # old format, date only
    assert not is_newer(paper("c", "2026-09-27T10:44:38Z"), stored)
    assert not is_newer(paper("b", "2026-09-30T13:09:24Z"), stored)


def test_arxiv_filters_author_and_normalises_title(monkeypatch):
    monkeypatch.setattr(check_paper.requests, "get", lambda *a, **k: FakeResponse(FEED))
    papers = check_paper.get_arxiv_papers()
    assert [p["id"] for p in papers] == ["2609.39678v1"]
    assert papers[0]["title"] == "Aletheia: Permission-Minimality Testing"


def test_arxiv_retries_then_succeeds(monkeypatch):
    responses = iter([FakeResponse("", 503), FakeResponse("<feed/>"), FakeResponse(FEED)])
    monkeypatch.setattr(check_paper.requests, "get", lambda *a, **k: next(responses))
    assert len(check_paper.get_arxiv_papers()) == 1


def test_main_fails_when_arxiv_down(monkeypatch, tmp_path):
    monkeypatch.setattr(check_paper.requests, "get", lambda *a, **k: FakeResponse("", 429))
    assert main(tmp_path / "last_paper.json") == 1


def test_main_writes_new_paper(monkeypatch, tmp_path):
    out = tmp_path / "data" / "last_paper.json"
    monkeypatch.setattr(check_paper.requests, "get", lambda *a, **k: FakeResponse(FEED))
    assert main(out) == 0
    content = json.loads(out.read_text())
    assert content["paperId"] == "2609.39678v1"
    assert content["publicationDate"] == "2026-09-30"
    assert content["publishedAt"] == "2026-09-30T13:09:24Z"
    assert "detectedAt" in content


def test_main_keeps_file_when_nothing_new(monkeypatch, tmp_path):
    out = tmp_path / "last_paper.json"
    write_last_paper(paper("2609.39678v1", "2026-09-30T13:09:24Z"), out,
                     now=datetime(2026, 10, 1, tzinfo=timezone.utc))
    before = out.read_text()
    monkeypatch.setattr(check_paper.requests, "get", lambda *a, **k: FakeResponse(FEED))
    assert main(out) == 0
    assert out.read_text() == before
