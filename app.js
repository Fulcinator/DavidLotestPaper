fetch("data/last_paper.json")
  .then(r => r.json())
  .then(paper => {
    const today = new Date().toISOString().slice(0, 10);
    const answer = document.getElementById("answer");
    const latest = document.getElementById("latest");

    if (paper.publicationDate === today) {
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

  latest.textContent = `the latest paper is: ${paper.title}`;
