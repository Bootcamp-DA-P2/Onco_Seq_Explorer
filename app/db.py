"""
OncoSeq — Conexión a Supabase para Streamlit
==============================================
Este módulo centraliza toda la comunicación con la base de datos. La app de
Streamlit importa las funciones de aquí en vez de escribir SQL directamente
en las páginas — así solo hay un sitio que tocar si el esquema cambia.

CONFIGURACIÓN (elige una de las dos):

  A) Streamlit Cloud / uso normal de la app -> archivo de secretos:
     Crea el archivo `.streamlit/secrets.toml` en la raíz del proyecto
     (ya está en el .gitignore, así que nunca se sube a GitHub) con:

         DATABASE_URL = "postgresql://postgres.vxigmcieuqtmiscszugt:TU_PASSWORD@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"

  B) Ejecutar scripts sueltos fuera de Streamlit (como load_data_to_supabase.py)
     -> variable de entorno DATABASE_URL, tal como ya veníamos haciendo.

Este módulo prueba primero A y si no existe, cae a B automáticamente.

USO en una página de Streamlit:

    from db import get_resumen, get_muestras, get_expresion_muestras

    resumen = get_resumen()
    st.metric("Muestras totales", resumen["total_muestras"])

    df_muestras = get_muestras(cohorte="BRCA", tipo="tumor")
    st.dataframe(df_muestras)
"""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text


# -----------------------------------------------------------------------------
# Conexión
# -----------------------------------------------------------------------------

def _get_database_url() -> str:
    """Busca la cadena de conexión primero en st.secrets, luego en el entorno."""
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError):
        pass

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "No se encontró DATABASE_URL. Defínela en .streamlit/secrets.toml "
            "(clave DATABASE_URL) o como variable de entorno."
        )
    return url


@st.cache_resource(show_spinner=False)
def get_engine():
    """Crea (una sola vez, reutilizada entre reruns) el motor de conexión."""
    return create_engine(_get_database_url(), pool_pre_ping=True)


# -----------------------------------------------------------------------------
# Consultas de metadatos (pacientes / muestras / genes)
# -----------------------------------------------------------------------------

@st.cache_data(ttl=600, show_spinner="Consultando muestras...")
def get_muestras(tipo: str | None = None, cohorte: str | None = None) -> pd.DataFrame:
    """Devuelve la tabla de muestras (opcionalmente filtrada por tipo/cohorte)."""
    query = "select sample_id, participante_id, tipo, cohorte, fecha_carga from muestras"
    filtros, params = [], {}
    if tipo:
        filtros.append("tipo = :tipo")
        params["tipo"] = tipo
    if cohorte:
        filtros.append("cohorte = :cohorte")
        params["cohorte"] = cohorte
    if filtros:
        query += " where " + " and ".join(filtros)

    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params=params)


@st.cache_data(ttl=600, show_spinner="Consultando pacientes...")
def get_pacientes() -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text("select * from pacientes"), conn)


@st.cache_data(ttl=3600, show_spinner="Consultando catálogo de genes...")
def get_genes() -> pd.DataFrame:
    """Catálogo completo de genes, ordenado por gene_id (importante: este
    orden es el mismo que usan las posiciones dentro de expresion.valores)."""
    with get_engine().connect() as conn:
        return pd.read_sql(text("select * from genes order by gene_id"), conn)


@st.cache_data(ttl=60, show_spinner=False)
def get_resumen() -> dict:
    """Cifras rápidas para una cabecera/dashboard: totales y desglose por cohorte."""
    with get_engine().connect() as conn:
        total_muestras = conn.execute(text("select count(*) from muestras")).scalar()
        total_pacientes = conn.execute(text("select count(*) from pacientes")).scalar()
        total_genes = conn.execute(text("select count(*) from genes")).scalar()
        por_cohorte = pd.read_sql(
            text("select cohorte, tipo, count(*) as n from muestras group by cohorte, tipo order by cohorte"),
            conn,
        )
    return {
        "total_muestras": total_muestras,
        "total_pacientes": total_pacientes,
        "total_genes": total_genes,
        "por_cohorte": por_cohorte,
    }


# -----------------------------------------------------------------------------
# Consultas de expresión génica
# -----------------------------------------------------------------------------

def _rows_to_wide_df(rows: list[tuple[str, list]], gene_labels: list[str]) -> pd.DataFrame:
    """Convierte filas (sample_id, valores[]) en una tabla ancha
    muestra x gen, lista para usar en pandas/scikit-learn. Es una función
    pura (sin tocar la base de datos) para poder probarla de forma aislada.
    """
    sample_ids = [r[0] for r in rows]
    data = [r[1] for r in rows]
    return pd.DataFrame(data, index=sample_ids, columns=gene_labels)


@st.cache_data(ttl=600, show_spinner="Cargando expresión génica (puede tardar)...")
def get_expresion_muestras(sample_ids: list[str]) -> pd.DataFrame:
    """Devuelve una tabla ancha (muestras x genes) con la expresión de las
    muestras indicadas. Útil para pasarle un subconjunto a un modelo o a un
    gráfico, sin tener que traer las 1680 muestras cada vez."""
    if not sample_ids:
        return pd.DataFrame()

    genes = get_genes()
    gene_labels = genes.sort_values("gene_id")["gene_label"].tolist()

    with get_engine().connect() as conn:
        result = conn.execute(
            text("select sample_id, valores from expresion where sample_id = any(:ids)"),
            {"ids": sample_ids},
        )
        rows = [(r[0], r[1]) for r in result]

    return _rows_to_wide_df(rows, gene_labels)


@st.cache_data(ttl=600, show_spinner="Cargando expresión génica de la cohorte...")
def get_expresion_por_filtro(tipo: str | None = None, cohorte: str | None = None,
                              limite: int = 200) -> pd.DataFrame:
    """Igual que get_expresion_muestras, pero partiendo de un filtro por
    tipo/cohorte en vez de una lista de sample_id. `limite` protege de traer
    sin querer las 1680 muestras enteras (34M numeros) de golpe a la app."""
    muestras = get_muestras(tipo=tipo, cohorte=cohorte)
    sample_ids = muestras["sample_id"].head(limite).tolist()
    return get_expresion_muestras(sample_ids)


# -----------------------------------------------------------------------------
# Comprobación rápida de conexión (útil para una página de "Estado" en la app)
# -----------------------------------------------------------------------------

def test_connection() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("select 1"))
        return True
    except Exception:
        return False
