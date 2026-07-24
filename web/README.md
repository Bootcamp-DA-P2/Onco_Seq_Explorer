# web/

Sitio público de **OncoLens** (landing page + demo interactiva). Es la parte del proyecto pensada para ser vista por cualquiera, no solo para evaluación técnica.

## Estructura

```
web/
├── index.html              → Página principal (hero, secciones, enlace a la demo)
├── assets/
│   ├── css/
│   │   └── style.css       → Estilos globales (tokens de color, tipografía, layout)
│   ├── js/
│   │   └── main.js         → Interactividad (cinta de genes, futuras animaciones)
│   ├── img/                → Imágenes e ilustraciones del sitio
│   └── data/                → JSON pequeños derivados del dataset (para gráficos ligeros
│                              en la web; NUNCA el CSV completo — eso vive en /data del proyecto)
└── README.md                → Este archivo
```

## Cómo previsualizar en local

No hace falta servidor especial, es HTML/CSS/JS estático:

```bash
# Opción rápida: abrir directamente
open index.html          # macOS
start index.html         # Windows

# Opción con servidor local (recomendable, evita problemas de rutas relativas)
python3 -m http.server 8000
# luego visita http://localhost:8000
```

## Despliegue

Esta carpeta se publica en GitHub Pages. Como se llama `web/` y no `docs/`,
el despliegue se hace vía GitHub Actions (no por la configuración simple de 2 clics
de Settings → Pages, que solo reconoce `/docs` o la raíz del repo).

El Streamlit de la demo interactiva **no vive aquí** — se despliega por separado en
Streamlit Community Cloud, y esta web solo lo enlaza/incrusta vía `<iframe>` en la
sección `#demo`.

## Convenciones

- Un solo `style.css` global mientras el sitio sea pequeño. Si crece mucho,
  dividir por sección (`hero.css`, `demo.css`...) en vez de un archivo gigante.
- Los datos que alimenten visualizaciones en la web deben ser **resúmenes ligeros**
  (JSON de unos pocos KB), nunca el dataset completo — eso ralentizaría la carga
  de la página para cualquier visitante.
