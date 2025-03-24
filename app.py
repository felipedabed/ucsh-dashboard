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

# Pivot notas por rol
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")

# Ponderaciones promedio por rol
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()

# Calcular Score Global por trabajador
def calcular_score_global(row):
    score = 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol, np.nan)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * (peso / 100)
    return score

# Información del colaborador con scores
st.subheader("Información del colaborador")
informacion = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates()

informacion["Nota Autoevaluación"] = informacion["RUT Colaborador"].map(pivot["Autoevaluacion"]) if "Autoevaluacion" in pivot else np.nan
informacion["Nota Indirecto"] = informacion["RUT Colaborador"].map(pivot["Indirecto"]) if "Indirecto" in pivot else np.nan
informacion["Nota Jefatura"] = informacion["RUT Colaborador"].map(pivot["Jefatura"]) if "Jefatura" in pivot else np.nan

informacion["Score Global"] = pivot.apply(calcular_score_global, axis=1)

def categoria_desempeno(score):
    if score >= 3.6:
        return "Desempeño destacado"
    elif score >= 2.8:
        return "Desempeño competente"
    elif score >= 2.2:
        return "Desempeño básico"
    else:
        return "Desempeño insuficiente"

informacion["Categoría desempeño"] = informacion["Score Global"].apply(categoria_desempeno)

st.dataframe(informacion)

# Gráfico original de Streamlit con puntajes
st.subheader("Puntaje por Dimensión (Escala 1-4)")

dimensiones_promedio = pivot.mean().dropna()
st.bar_chart(dimensiones_promedio)

# Mostrar puntajes explícitos sobre gráfico
for dimension, puntaje in dimensiones_promedio.items():
    st.markdown(f"**{dimension}**: {puntaje:.2f}")

# Sección destacada Score Global
st.subheader("Score Global Promedio")
score_global_promedio = informacion["Score Global"].mean()
categoria_promedio = categoria_desempeno(score_global_promedio)

col1, col2 = st.columns([1, 2])

with col1:
    st.metric(label="Score Global", value=f"{score_global_promedio:.2f}")

with col2:
    st.markdown(f"### Categoría: {categoria_promedio}")

# Tabla resumen notas por dimensión
st.subheader("Resumen de Notas por Dimensión")
resumen = pd.DataFrame({
    "Dimensión": dimensiones_promedio.index,
    "Nota Obtenida": dimensiones_promedio.values,
    "Nota Obtenida %": [f"{((x-1)/3)*100:.0f}%" for x in dimensiones_promedio.values]
})
resumen.loc[len(resumen.index)] = ["Total ponderado", score_global_promedio, f"{((score_global_promedio-1)/3)*100:.0f}%"]
st.dataframe(resumen)

# Tabla ponderaciones
st.subheader("Ponderación por Dimensión")
info_ponderacion = pd.DataFrame({
    "Dimensión": ["Autoevaluación", "Indirecto", "Jefatura"],
    "% Ponderación": [f"{ponderaciones.get(r, np.nan):.0f}%" if not pd.isna(ponderaciones.get(r)) else "-" for r in ["Autoevaluacion", "Indirecto", "Jefatura"]]
})
st.dataframe(info_ponderacion)

# Evaluación por dimensión y atributos
st.subheader("Evaluación por dimensión y atributos")
roles = filtered_df["Rol Evaluador"].unique()
for rol in roles:
    sub_df = filtered_df[filtered_df["Rol Evaluador"] == rol].copy()
    if not sub_df.empty:
        sub_df["Nota"] = pd.to_numeric(sub_df["Nota"], errors="coerce")
        sub_df["Ponderación"] = pd.to_numeric(sub_df["Ponderación"], errors="coerce")
        sub_df["Nota Ponderada"] = sub_df["Nota"] * (sub_df["Ponderación"] / 100)
        tabla = sub_df.groupby("Nombre Atributo")[["Nota", "Ponderación", "Nota Ponderada"]].mean().reset_index()
        st.markdown(f"### {rol}")
        st.dataframe(tabla)

# Placeholder para descarga PDF
st.subheader("Exportar a PDF")
if st.button("Descargar PDF del colaborador"):
    st.info("Funcionalidad en desarrollo. Requiere integración con librería de PDF como ReportLab o WeasyPrint.")
