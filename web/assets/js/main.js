const track = document.getElementById('tickerTrack');
  for (let i = 0; i < 2; i++) {
    for (let j = 0; j < 18; j++) {
      const geneId = Math.floor(Math.random() * 20531);
      const val = (Math.random() * 15).toFixed(2);
      const el = document.createElement('div');
      el.className = 'ticker-item';
      el.innerHTML = `<span class="gid">gene_${geneId}</span><span class="gval">${val}</span>`;
      track.appendChild(el);
    }
  }
