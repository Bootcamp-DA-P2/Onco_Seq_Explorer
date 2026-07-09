import streamlit as st

st.set_page_config(

    page_title="OncoSeq Explorer",

    page_icon="",

    layout="wide",

)

st.title(" OncoSeq Explorer")

st.caption("Clasificación de tumores a partir de expresión génica (TCGA PANCAN)")

st.success("App funcionando correctamente dentro del contenedor Docker ")

st.markdown("---")

st.info(

    "Esqueleto inicial. Aquí irán: carga de datos, EDA, "

    "PCA/clustering, el clasificador multiclase y las predicciones."

)