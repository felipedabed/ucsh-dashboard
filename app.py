
import streamlit as st
import pandas as pd
import numpy as np

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=",", encoding="utf-8")
    df.columns = df.columns.str.strip().str.replace("\u00a0", " ").str.replace("\ufeff", "")
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
    centro_filter = st.multiselect("Centro de Costo", options=sorted(df["Centro de Costo"].dropna().unique().tolist()), default=sorted(df["Centro de Costo"].dropna().unique().tolist()))
    sucursal_filter = st.selectbox("Sucursal", options=["Todos"] + sorted(df["Sucursal"].dropna().unique().tolist()))
    familia_cargo_filter = st.selectbox("Familia del Cargo", options=["Todos"] + sorted(df["Familia del Cargo"].dropna().unique().tolist()))
    mostrar_completas = st.checkbox("Mostrar solo evaluaciones completas", value=False)

# Aplicar filtros
filtered_df = df.copy()
if rut_filter != "Todos":
    filtered_df = filtered_df[filtered_df["RUT Colaborador"] == rut_filter]
if nombre_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Nombre Colaborador"] == nombre_filter]
if gerencia_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Gerencia"] == gerencia_filter]
if centro_filter:
    filtered_df = filtered_df[filtered_df["Centro de Costo"].isin(centro_filter)]
if sucursal_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Sucursal"] == sucursal_filter]
if familia_cargo_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Familia del Cargo"] == familia_cargo_filter]

if filtered_df.empty:
    st.warning("No se encontraron datos para los filtros seleccionados.")
    st.stop()

# Pivot por Rol Evaluador
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")
pivot = pivot.reindex(columns=["Autoevaluacion", "Indirecto", "Jefatura"])

# Ponderaciones
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()

# Calcular score global
def calcular_score(row):
    score, suma_ponderaciones = 0, 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * peso
            suma_ponderaciones += peso
    return score / suma_ponderaciones if suma_ponderaciones else np.nan

# Tabla principal
informacion = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo", "Familia del Cargo"]].drop_duplicates()
informacion["Nota Autoevaluación"] = informacion["RUT Colaborador"].map(pivot["Autoevaluacion"])
informacion["Nota Indirecto"] = informacion["RUT Colaborador"].map(pivot["Indirecto"])
informacion["Nota Jefatura"] = informacion["RUT Colaborador"].map(pivot["Jefatura"])

informacion["Score Global"] = informacion.apply(lambda row: calcular_score({
    "Autoevaluacion": row["Nota Autoevaluación"],
    "Indirecto": row["Nota Indirecto"],
    "Jefatura": row["Nota Jefatura"]
}), axis=1).round(3)

def categoria_desempeno(score):
    if pd.isna(score):
        return "Sin evaluación"
    if score >= 3.6:
        return "Desempeño destacado"
    elif score >= 2.8:
        return "Desempeño competente"
    elif score >= 2.2:
        return "Desempeño básico"
    else:
        return "Desempeño insuficiente"

informacion["Categoría desempeño"] = informacion["Score Global"].apply(categoria_desempeno)

informacion["Evaluación completa"] = informacion.apply(
    lambda row: "Completa" if not pd.isna(row["Nota Autoevaluación"]) and not pd.isna(row["Nota Indirecto"]) and not pd.isna(row["Nota Jefatura"]) else "Incompleta", axis=1
)

if mostrar_completas:
    informacion = informacion[informacion["Evaluación completa"] == "Completa"]

def color_categoria(val):
    if val == "Desempeño destacado":
        return "background-color: #27ae60; color: white"
    elif val == "Desempeño competente":
        return "background-color: #2980b9; color: white"
    elif val == "Desempeño básico":
        return "background-color: #f39c12; color: black"
    elif val == "Desempeño insuficiente":
        return "background-color: #c0392b; color: white"
    return ""

styled_info = informacion.style.applymap(color_categoria, subset=["Categoría desempeño"])
st.dataframe(styled_info, use_container_width=True)

# Aquí van las demás secciones que el usuario ya tiene
