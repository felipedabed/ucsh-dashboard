import streamlit as st 
import pandas as pd
import numpy as np

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
    rut_filter = st.selectbox("RUT Colaborador", options=["Todos"] + sorted(df["RUT Colaborador"].dropna().unique()))
    nombre_filter = st.selectbox("Nombre Colaborador", options=["Todos"] + sorted(df["Nombre Colaborador"].dropna().unique()))
    gerencia_filter = st.selectbox("Gerencia", options=["Todos"] + sorted(df["Gerencia"].dropna().unique()))
    centro_filter = st.selectbox("Centro de Costo", options=["Todos"] + sorted(df["Centro de Costo"].dropna().unique()))
    sucursal_filter = st.selectbox("Sucursal", options=["Todos"] + sorted(df["Sucursal"].dropna().unique()))

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

# Pivot notas por Rol Evaluador
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")

# Ponderaciones promedio por Rol
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean().to_dict()

# Función corregida para calcular Score Global Individual
def calcular_score(row):
    score, peso_total = 0, 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * peso
            peso_total += peso
    return (score / peso_total) if peso_total else np.nan

# Información del colaborador (ahora con Score individual corregido)
informacion = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates()
informacion["Nota Autoevaluación"] = informacion["RUT Colaborador"].map(pivot.get("Autoevaluacion"))
informacion["Nota Indirecto"] = informacion["RUT Colaborador"].map(pivot.get("Indirecto"))
informacion["Nota Jefatura"] = informacion["RUT Colaborador"].map(pivot.get("Jefatura"))

# Aplicando la función corregida
informacion["Score Global"] = pivot.apply(calcular_score, axis=1).round(3)

# Categoría desempeño por trabajador
def categoria(score):
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

informacion["Categoría desempeño"] = informacion["Score Global"].apply(categoria)

st.subheader("Información del colaborador")
st.dataframe(informacion)

# Puntaje promedio general por Dimensión (gráfico corregido)
st.subheader("Puntaje por Dimensión (Escala 1-4)")
dimensiones_promedio = pivot.mean().dropna()
st.bar_chart(dimensiones_promedio)

# Puntajes explícitos sobre gráfico
col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]
for i, (dimension, puntaje) in enumerate(dimensiones_promedio.items()):
    cols[i].metric(label=dimension, value=f"{puntaje:.2f}")

# Sección destacada Score Global promedio general corregido
st.subheader("Score Global Promedio")
score_global_promedio = informacion["Score Global"].mean().round(3)
categoria_promedio = categoria(score_global_promedio)

col1, col2 = st.columns([1, 2])

with col1:
    st.metric(label="Score Global", value=f"{score_global_promedio:.2f}")

with col2:
    st.markdown(f"### Categoría: {categoria_promedio}")

# Tabla resumen notas promedio por dimensión (corregido)
st.subheader("Resumen de Notas por Dimensión")
resumen = pd.DataFrame({
    "Dimensión": dimensiones_promedio.index,
    "Nota Obtenida": dimensiones_promedio.values,
    "Nota Obtenida %": [f"{((x-1)/3)*100:.0f}%" for x in dimensiones_promedio.values]
})
resumen.loc[len(resumen.index)] = ["Total ponderado", score_global_promedio, f"{((score_global_promedio-1)/3)*100:.0f}%"]
st.dataframe(resumen)

# Tabla fija informativa de ponderaciones
st.subheader("Ponderación por Dimensión")
info_ponderacion = pd.DataFrame({
    "Dimensión": ["Autoevaluación", "Indirecto", "Jefatura"],
    "% Ponderación": [f"{ponderaciones.get(r, np.nan):.0f}%" if not pd.isna(ponderaciones.get(r)) else "-" for r in ["Autoevaluacion", "Indirecto", "Jefatura"]]
})
st.dataframe(info_ponderacion)

# Evaluación por dimensión y atributos (sección funcional)
st.subheader("Evaluación por dimensión y atributos")
for rol in filtered_df["Rol Evaluador"].unique():
    sub_df = filtered_df[filtered_df["Rol Evaluador"] == rol].copy()
    sub_df["Nota"] = pd.to_numeric(sub_df["Nota"], errors="coerce")
    sub_df["Ponderación"] = pd.to_numeric(sub_df["Ponderación"], errors="coerce")
    sub_df["Nota Ponderada"] = sub_df["Nota"] * (sub_df["Ponderación"] / 100)
    tabla = sub_df.groupby("Nombre Atributo")[["Nota", "Ponderación", "Nota Ponderada"]].mean().reset_index()
    st.markdown(f"### {rol}")
    st.dataframe(tabla)

# Placeholder descarga PDF
st.subheader("Exportar a PDF")
if st.button("Descargar PDF del colaborador"):
    st.info("Funcionalidad en desarrollo. Requiere integración con librería de PDF como ReportLab o WeasyPrint.")
