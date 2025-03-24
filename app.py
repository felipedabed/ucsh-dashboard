import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=",", encoding="ISO-8859-1")
    df["Nota Final Evaluación"] = pd.to_numeric(df["Nota Final Evaluación"].replace("-", np.nan), errors='coerce')
    df["Ponderación Rol Evaluación"] = pd.to_numeric(df["Ponderación Rol Evaluación"].replace("-", np.nan), errors='coerce')
    return df

df = load_data()

st.title("Panel de Evaluación UCSH")

# Filtros
with st.sidebar:
    st.header("Filtros")
    rut_filter = st.selectbox("RUT Colaborador", options=["Todos"] + sorted(df["RUT Colaborador"].dropna().unique().tolist()))
    nombre_filter = st.selectbox("Nombre Colaborador", options=["Todos"] + sorted(df["Nombre Colaborador"].dropna().unique().tolist()))
    gerencia_filter = st.selectbox("Gerencia", options=["Todos"] + sorted(df["Gerencia"].dropna().unique().tolist()))
    centro_filter = st.selectbox("Centro de Costo", options=["Todos"] + sorted(df["Centro de Costo"].dropna().unique().tolist()))
    sucursal_filter = st.selectbox("Sucursal", options=["Todos"] + sorted(df["Sucursal"].dropna().unique().tolist()))

# Aplicar filtros
filtered_df = df.copy()
if rut_filter != "Todos":
    filtered_df = filtered_df[filtered_df["RUT Colaborador"] == rut_filter]
if nombre_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Nombre Colaborador"] == nombre_filter]
if gerencia_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Gerencia"] == gerencia_filter]
if centro_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Centro de Costo"] == centro_filter]
if sucursal_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Sucursal"] == sucursal_filter]

if filtered_df.empty:
    st.warning("No se encontraron datos para los filtros seleccionados.")
    st.stop()

# Score por Rol Evaluador
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")

# Calcular ponderaciones
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()

# Información del colaborador
informacion = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates().copy()
informacion["Autoevaluación"] = informacion["RUT Colaborador"].map(pivot.get("Autoevaluacion"))
informacion["Indirecto"] = informacion["RUT Colaborador"].map(pivot.get("Indirecto"))
informacion["Jefatura"] = informacion["RUT Colaborador"].map(pivot.get("Jefatura"))

# Calcular Score Global individual
def calcular_score_global(row):
    score = 0
    suma_ponderaciones = 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * (peso / 100)
            suma_ponderaciones += peso
    return score if suma_ponderaciones > 0 else np.nan

informacion["Score Global"] = informacion.apply(calcular_score_global, axis=1)

# Categoría desempeño
def categoria_desempeno(score):
    if pd.isna(score):
        return "-"
    elif score >= 3.6:
        return "Desempeño destacado"
    elif score >= 2.8:
        return "Desempeño competente"
    elif score >= 2.2:
        return "Desempeño básico"
    else:
        return "Desempeño insuficiente"

informacion["Categoría desempeño"] = informacion["Score Global"].apply(categoria_desempeno)

st.subheader("Información del colaborador")
st.dataframe(informacion)

# Resumen de Notas por Dimensión
st.subheader("Resumen de Notas por Dimensión")
notas_dimensiones = {
    "Autoevaluación": pivot["Autoevaluacion"].mean(),
    "Indirecto": pivot["Indirecto"].mean(),
    "Jefatura": pivot["Jefatura"].mean()
}
score_global_promedio = informacion["Score Global"].mean()
resumen = pd.DataFrame({
    "Dimensión": ["Autoevaluación", "Indirecto", "Jefatura", "Total ponderado"],
    "Nota Obtenida": [notas_dimensiones["Autoevaluación"], notas_dimensiones["Indirecto"], notas_dimensiones["Jefatura"], score_global_promedio],
    "Nota Obtenida %": [
        f"{((notas_dimensiones['Autoevaluación']-1)/3)*100:.0f}%", 
        f"{((notas_dimensiones['Indirecto']-1)/3)*100:.0f}%", 
        f"{((notas_dimensiones['Jefatura']-1)/3)*100:.0f}%", 
        f"{((score_global_promedio-1)/3)*100:.0f}%"
    ]
})
st.dataframe(resumen)

# Descargar PDF (placeholder)
st.subheader("Exportar a PDF")
if st.button("Descargar PDF del colaborador"):
    st.info("Funcionalidad en desarrollo. Requiere integración con librería de PDF como ReportLab o WeasyPrint.")
