import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", encoding="utf-8")
    df.columns = df.columns.str.strip().str.replace("\u00a0", " ").str.replace("\ufeff", "")
    df["Nota Final Evaluación"] = pd.to_numeric(df["Nota Final Evaluación"].replace("-", np.nan), errors='coerce')
    df["Ponderación Rol Evaluación"] = pd.to_numeric(df["Ponderación Rol Evaluación"].replace("-", np.nan), errors='coerce')
    return df

df = load_data()
st.title("Panel de Evaluación UCSH")

# Sidebar
with st.sidebar:
    st.header("Filtros")
    rut_filter = st.selectbox("RUT Colaborador", options=["Todos"] + sorted(df["RUT Colaborador"].dropna().unique()))
    nombre_filter = st.selectbox("Nombre Colaborador", options=["Todos"] + sorted(df["Nombre Colaborador"].dropna().unique()))
    gerencia_filter = st.selectbox("Gerencia", options=["Todos"] + sorted(df["Gerencia"].dropna().unique()))
    centro_filter = st.multiselect("Centro de Costo", options=sorted(df["Centro de Costo"].dropna().unique()))
    sucursal_filter = st.selectbox("Sucursal", options=["Todos"] + sorted(df["Sucursal"].dropna().unique()))
    ver_completos = st.checkbox("Mostrar solo evaluaciones completas")

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

if filtered_df.empty:
    st.warning("No se encontraron datos para los filtros seleccionados.")
    st.stop()

# Pivot y Ponderaciones
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()

# Función para calcular Score Global
def calcular_score(row):
    score = 0
    suma = 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * peso
            suma += peso
    return score / suma if suma else np.nan

# Info colaborador
st.subheader("Identificación del colaborador")
info = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates()
info["Nota Autoevaluación"] = info["RUT Colaborador"].map(pivot["Autoevaluacion"]) if "Autoevaluacion" in pivot else np.nan
info["Nota Indirecto"] = info["RUT Colaborador"].map(pivot["Indirecto"]) if "Indirecto" in pivot else np.nan
info["Nota Jefatura"] = info["RUT Colaborador"].map(pivot["Jefatura"]) if "Jefatura" in pivot else np.nan
info["Score Global"] = info.apply(lambda row: calcular_score({
    "Autoevaluacion": row["Nota Autoevaluación"],
    "Indirecto": row["Nota Indirecto"],
    "Jefatura": row["Nota Jefatura"]
}), axis=1).round(3)

# Categoría desempeño
def categoria(score):
    if pd.isna(score): return "Sin evaluación"
    if score >= 3.6: return "Desempeño destacado"
    elif score >= 2.8: return "Desempeño competente"
    elif score >= 2.2: return "Desempeño básico"
    else: return "Desempeño insuficiente"
info["Categoría de desempeño"] = info["Score Global"].apply(categoria)

# Estado evaluación completa
def estado_eval(row):
    roles = [row["Nota Autoevaluación"], row["Nota Indirecto"], row["Nota Jefatura"]]
    return "Completa" if all(not pd.isna(r) for r in roles) else "Incompleta"
info["Estado Evaluación"] = info.apply(estado_eval, axis=1)

# Filtrar por evaluación completa si se marcó checkbox
if ver_completos:
    info = info[info["Estado Evaluación"] == "Completa"]

# Color para categoría
def colorear_categoria(val):
    colores = {
        "Desempeño destacado": "background-color: #27ae60; color: white",
        "Desempeño competente": "background-color: #2980b9; color: white",
        "Desempeño básico": "background-color: #f39c12; color: black",
        "Desempeño insuficiente": "background-color: #c0392b; color: white",
    }
    return colores.get(val, "")

st.dataframe(info.style.applymap(colorear_categoria, subset=["Categoría de desempeño"]))
