const DAY_MS = 1000 * 60 * 60 * 24;

fetch(`data/last_paper.json?t=${Date.now()}`, { cache: "no-store" })
  .then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then(paper => {
    const answer = document.getElementById("answer");
    const latest = document.getElementById("latest");

    // arXiv exposes a paper only after its announcement (often the day after submission),
    // so "today" means: published or first seen by the checker in the last 24 hours.
    const published = new Date(paper.publishedAt || paper.publicationDate);
    const detected = paper.detectedAt ? new Date(paper.detectedAt) : published;
    const newest = Math.max(published, detected);

    if (Date.now() - newest <= DAY_MS) {
      answer.textContent = "YES";
      answer.className = "yes";
    } else {
      answer.textContent = "NOT YET";
      answer.className = "no";
    }

    latest.textContent = `the latest paper is: ${paper.title}`;
  })
  .catch(err => {
    console.error(err);
    const answer = document.getElementById("answer");
    answer.textContent = "?";
    answer.className = "no";
    document.getElementById("latest").textContent = "could not load the latest paper, try reloading";
  });
