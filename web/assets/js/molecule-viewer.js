/*
 * Visor 3D de estructuras proteicas reales — panel del hero.
 *
 * NOTA PARA EL EQUIPO: estos genes (ESR1, VHL, EGFR, receptor de andrógenos,
 * KRAS) son genes EMBLEMÁTICOS y de dominio público asociados a cada tipo de
 * tumor — no son necesariamente los genes con mayor peso en VUESTRO modelo
 * entrenado. Son un placeholder ilustrativo, real y con fundamento biológico,
 * mientras no tengáis el feature importance del clasificador. Cuando lo
 * tengáis, si los genes top resultan tener estructura conocida en PDB,
 * podéis sustituir los pdbId de aquí abajo por los reales.
 *
 * Las estructuras se descargan en directo desde el RCSB Protein Data Bank
 * (files.rcsb.org) a través de 3Dmol.js — no alojamos ningún archivo molecular.
 */

(function () {
  const stage = document.getElementById('molStage');
  const activeLabel = document.getElementById('visualActive');
  const legendEl = document.getElementById('visualLegend');
  if (!stage || typeof $3Dmol === 'undefined') return;

  const TUMOR_TYPES = [
    { code: 'BRCA', gene: 'ESR1', pdbId: '1A52', color: 0x1652f0 },
    { code: 'KIRC', gene: 'VHL',  pdbId: '1VCB', color: 0x2c7be5 },
    { code: 'LUAD', gene: 'EGFR', pdbId: '1M17', color: 0x14a6b8 },
    { code: 'PRAD', gene: 'AR',   pdbId: '1E3G', color: 0x0e8f8a },
    { code: 'COAD', gene: 'KRAS', pdbId: '5P21', color: 0x6b5ce0 },
  ];

  const CYCLE_MS = 4200;

  // ---------- Legend (HTML overlay) ----------
  TUMOR_TYPES.forEach((t, i) => {
    const item = document.createElement('div');
    item.className = 'legend-item' + (i === 0 ? ' active' : '');
    item.dataset.index = i;
    const dot = document.createElement('span');
    dot.className = 'legend-dot';
    dot.style.background = '#' + t.color.toString(16).padStart(6, '0');
    item.appendChild(dot);
    item.appendChild(document.createTextNode(t.code));
    legendEl.appendChild(item);
  });
  const legendItems = legendEl.querySelectorAll('.legend-item');

  // ---------- 3Dmol viewer ----------
  // El fondo del visor toma el mismo color que el fondo de la página
  // (variable --bg en style.css), para que se vea continuo, sin marco.
  const pageBg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#FBFDFF';

  const viewer = $3Dmol.createViewer(stage, {
    backgroundColor: pageBg,
  });

  let activeIndex = 0;
  let loading = false;

  function hexColor(c) {
    return '#' + c.toString(16).padStart(6, '0');
  }

  function loadStructure(index) {
    if (loading) return;
    loading = true;
    const type = TUMOR_TYPES[index];

    viewer.clear();
    $3Dmol.download('pdb:' + type.pdbId, viewer, {}, function () {
      viewer.setStyle({}, { cartoon: { color: hexColor(type.color) } });
      viewer.zoomTo();
      viewer.render();
      viewer.spin('y', 0.35);
      loading = false;
    });

    activeLabel.textContent = type.code + ' · ' + type.gene;
    legendItems.forEach((el, i) => el.classList.toggle('active', i === index));
  }

  loadStructure(0);
  setInterval(() => {
    activeIndex = (activeIndex + 1) % TUMOR_TYPES.length;
    loadStructure(activeIndex);
  }, CYCLE_MS);

  window.addEventListener('resize', () => {
    viewer.resize();
  });
})();
