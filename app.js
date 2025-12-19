fetch("data/last_paper.json")
  .then(r => r.json())
  .then(paper => {
    const today = new Date().toISOString().slice(0, 10);

    let msg = `
      <p><strong>Titolo:</strong> ${paper.title}</p>
      <p><strong>Data:</strong> ${paper.publicationDate}</p>
    `;

    if (paper.publicationDate === today) {
      msg += "<p><strong>Nuovo paper pubblicato oggi!</strong></p>";
    }

    document.getElementById("status").innerHTML = msg;
  });
