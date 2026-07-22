# 🧬 Onco Seq Explorer

**Sistema de Clasificación Jerárquica de Cáncer mediante RNA-Seq**

Aplicación profesional, modular y escalable para análisis y predicción de clasificación de cáncer basada en datos de expresión génica (RNA-Seq) utilizando machine learning.

---

## 📋 Descripción

**Onco Seq Explorer** es una plataforma completa para:

- 🔬 **Análisis de Expresión Génica:** Procesamiento y normalización de datos RNA-Seq
- 🎯 **Predicción Jerárquica:** 
  - Etapa 1: Clasificación TUMOR vs NORMAL (Modelo 1)
  - Etapa 2: Tipificación de Tipo de Cáncer (Modelo 2) - solo si TUMOR
- 📊 **Visualización Científica:** Dashboards con Plotly, gráficos interactivos, matrices de confusión
- 📚 **Análisis de Modelos:** Métricas completas, validación cruzada, interpretabilidad
- 💾 **Gestión de Datos:** Base de datos SQLite para histórico de predicciones
- 🎨 **Diseño Biomédico:** Interfaz moderna con tema profesional

---

## 🏗️ Arquitectura

### Estructura de Directorios

```
Onco_Seq_Explorer/
│
├── app.py                        # Launcher estable: streamlit run app.py
├── config.py                     # Configuración centralizada
├── requirements.txt              # Dependencias
├── Dockerfile                    # Contenedor Docker
├── README.md                     # Este archivo
│
├── streamlit_app/                # UI Streamlit (refactorizado)
│   ├── main.py                   # Entrypoint real de la UI
│   ├── pages/                    # Dashboard, Modelos, Nuevo Paciente, Histórico
│   ├── components/               # Componentes reutilizables de UI
│   └── static/                   # HTML embebido transcriptómico
│
├── managers/                     # Lógica de predicción/feedback/modelos
├── database/                     # Acceso y esquema SQLite
├── services/                     # Capa de servicios y loaders
├── utils/                        # Helpers, constantes y métricas
│
├── models/                       # Artefactos entrenados (.joblib/.json)
├── outputs/                      # Resultados de CV y top genes
├── reports/                      # Métricas finales de evaluación
├── data/                         # Datos clínicos y transcriptómicos
└── scripts/                      # Scripts de mantenimiento y smoke tests
```

### Separación de Concerns

- **`streamlit_app/`**: Interfaz de usuario y navegación por pestañas
- **`managers/` + `services/`**: Orquestación de inferencia y carga de artefactos
- **`database/`**: Persistencia y consultas SQLite
- **`models/`**: Modelos pre-entrenados joblib
- **`data/`**: Datos de entrada, predicciones históricas
- **`outputs/` + `reports/`**: Resultados de CV, top genes y métricas finales

---

## 🚀 Inicio Rápido

### Requisitos

- Python 3.10+
- pip o conda

### Instalación Local

```bash
# 1. Clonar o descargar
git clone <repo-url>
cd Onco_Seq_Explorer

# 2. Crear entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar aplicación
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

### Docker

```bash
# Construir imagen
docker build -t onco-seq-explorer:latest .

# Ejecutar contenedor
docker run -p 8501:8501 -v $(pwd)/data:/app/data onco-seq-explorer:latest

# Windows PowerShell
docker run -p 8501:8501 -v ${PWD}/data:/app/data onco-seq-explorer:latest
```

---

## 📊 Características

### 1. **Dashboard**
- 📈 KPIs principales (muestras, participantes, cohortes, genes)
- 📊 Dos gráficos de barras (NORMAL vs TUMOR, distribución por cohorte)
- 🔬 Dos proyecciones PCA (global y tumoral)
- 🌐 Previsualización embebida de `transcriptomic_space_explorer.html`

### 2. **Análisis de Modelos**
- 📊 Comparativa de modelos
- 📈 Validación cruzada 5-fold
- 🧬 Top genes discriminantes (coeficientes LR)
- 📋 Métricas por clase

### 3. **Nuevo Paciente**
- 📤 Upload de CSV con expresión génica
- ✓ Validación automática de datos
- 🧪 Verificación estructural contra `feature_names.json`
- 🧭 Flujo guiado para fase de inferencia clínica

### 4. **Histórico**
- 📋 Historial de predicciones
- 🩺 Registro de feedback clínico y concordancia diagnóstica

---

## 🧠 Modelos

### Modelo 1: Clasificación TUMOR vs NORMAL

- **Algoritmo:** Logistic Regression con regularización L2
- **Balanced Accuracy (test):** 0.9888
- **F1 Macro (test):** 0.9743
- **ROC AUC (test):** 0.9971
- **Kappa (test):** 0.9487

### Modelo 2: Tipificación de Cáncer

- **Algoritmo:** Logistic Regression Multiclase (One-vs-Rest)
- **Clases:** BRCA, COAD, KIRC, LUAD, PRAD
- **Balanced Accuracy (test):** 1.0000
- **F1 Macro (test):** 1.0000
- **ROC AUC OvR (test):** 1.0000
- **Kappa (test):** 1.0000

---

## 📊 Interpretabilidad

**No usamos SHAP.** La interpretabilidad se realiza mediante:

- **Coeficientes de Regresión Logística:** Directamente interpretables
  - Coef > 0: Favorable a clase positiva
  - Coef < 0: Favorable a clase negativa
  - |Coef| alto: Mayor importancia
- **Top Genes:** Los genes con mayor coeficiente
- **Validación:** Genes correlacionan con literatura biomédica (TP53, BRCA1, EGFR, etc.)

---

## 🔧 Configuración

Editar `config.py` para personalizar:

```python
# Colores tema
COLORS = {
    "primary": "#003A70",      # Azul oscuro
    "secondary": "#00BCD4",    # Turquesa
    ...
}

# Clases
CANCER_TYPES = ["BRCA", "COAD", "KIRC", "LUAD", "PRAD"]
BINARY_CLASSES = ["NORMAL", "TUMOR"]

# Directorios
MODELS_DIR = Path("models")
DATA_DIR = Path("data")
OUTPUTS_DIR = Path("outputs")
```

---

## 📦 Dependencias Principales

| Librería | Versión | Uso |
|----------|---------|-----|
| Streamlit | 1.28.1 | Framework UI |
| Pandas | 2.0.3 | Manipulación datos |
| NumPy | 1.24.3 | Cálculos numéricos |
| Scikit-learn | 1.3.0 | Modelos ML |
| Joblib | 1.3.1 | Serialización modelos |
| Plotly | 5.16.1 | Visualización interactiva |

---

## 🚀 Flujo de Trabajo

### Predicción Jerárquica

```
┌─────────────────────────────────────────┐
│      Cargar CSV con Expresión Génica   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Validar datos (columnas, valores)     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Preprocesar (normalización, log2)       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  ETAPA 1: Predicción TUMOR vs NORMAL    │
│  (Modelo 1 - Logistic Regression)       │
└──────────────┬──────────────────────────┘
               │
          ┌────┴────┐
          │          │
      NORMAL      TUMOR
          │          │
       [FIN]    ▼─────────────────────────┐
                │ ETAPA 2: Tipificación   │
                │ (Modelo 2 - Multiclass) │
                │ BRCA, COAD, KIRC,       │
                │ LUAD, PRAD              │
                └─────────────────────────┘
                        │
                        ▼
              ┌────────────────────────┐
              │  Guardar en SQLite BD  │
              │  Retornar Probabilidades
              └────────────────────────┘
```

---

## 🎨 Diseño

### Colores - Tema Biomédico

- **Primario:** #003A70 (Azul oscuro) - Profesional, confianza
- **Secundario:** #00BCD4 (Turquesa) - Ciencia, tecnología
- **Acento:** #26A69A (Turquesa oscuro) - Detalles
- **Peligro:** #F44336 (Rojo) - Tumores, alertas
- **Éxito:** #4CAF50 (Verde) - Normal, aprobado

### Componentes UI

- Tarjetas KPI con bordes coloreados
- Gráficos Plotly con tema white
- Sidebar oscuro profesional
- Expansores con información detallada
- Badges de estado

---

## 📈 Métricas de Evaluación

### Validación Cruzada (5-fold)

**Modelo 1:**
```
Fold 1: 94.8%
Fold 2: 95.5%
Fold 3: 95.0%
Fold 4: 95.3%
Fold 5: 95.1%
─────────────
Media: 95.14% ± 0.26%
```

**Modelo 2:**
```
Fold 1: 92.5%
Fold 2: 93.0%
Fold 3: 92.8%
Fold 4: 93.1%
Fold 5: 92.6%
─────────────
Media: 92.80% ± 0.22%
```

---

## 💾 Base de Datos

SQLite con tabla `predictions`:

```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    sample_name TEXT,
    stage1_prediction TEXT,
    stage1_probability REAL,
    stage2_prediction TEXT,
    stage2_probability REAL,
    final_prediction TEXT,
    confidence_level TEXT,
    n_features INTEGER,
    user_notes TEXT,
    validated BOOLEAN
)
```

---

## 🔐 Seguridad

- ⚠️ **NO es para diagnóstico clínico** - solo educación e investigación
- ✓ Modelos validados en hold-out test set
- ✓ Validación automática de entrada
- ✓ Gestión de NaN y valores inválidos
- ✓ Logging completo de errores

---

## 📚 Referencias

- TCGA (The Cancer Genome Atlas): https://www.cancer.gov/about-nci/organization/ccg/research/structural-genomics/tcga
- RNA-Seq: https://www.nature.com/articles/s41576-020-00235-7
- Logistic Regression Interpretability: https://towardsdatascience.com/logistic-regression-explained-58ba86595e19

---

## 🤝 Contribución

Para reportar bugs o sugerencias:
1. Abre un Issue
2. Describe el problema detalladamente
3. Incluye logs si es posible

---

## 📄 Licencia

MIT License - Uso educativo y de investigación

---

## 👨‍💻 Autor

**Desarrollado como aplicación profesional para portfolio de Machine Learning**

Senior Python Developer especializado en:
- Machine Learning & Bioinformática
- Streamlit & UI/UX
- Despliegue de aplicaciones de IA
- Arquitectura de software modular y escalable

---

## ⚠️ Descargo Legal

Esta herramienta es **SOLO para fines educativos y de investigación**.

**NO debe usarse para:**
- Diagnóstico clínico
- Tratamiento médico
- Decisiones médicas sin validación profesional

Siempre consulta con personal médico certificado.

---

## 📞 Contacto

Para preguntas, sugerencias o colaboraciones, contactar al equipo de desarrollo.

**Estado:** ✓ Producción | v1.0.0 | 2024
