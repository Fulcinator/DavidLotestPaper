fetch("data/last_paper.json")
  .then(r => r.json())
  .then(paper => {
    const answer = document.getElementById("answer");
    const latest = document.getElementById("latest");

    const pubDate = new Date(paper.publicationDate);
    const now = new Date();
    const diffDays = (now - pubDate) / (1000 * 60 * 60 * 24);

    if (diffDays <= 7) {
      answer.textContent = "YES";
      answer.className = "yes";
    } else {
      answer.textContent = "NOT YET";
      answer.className = "no";
    }

    latest.textContent = `the latest paper is: ${paper.title}`;
  })
  .catch(() => {
    const answer = document.getElementById("answer");
    answer.textContent = "NOT YET";
    answer.className = "no";
  });