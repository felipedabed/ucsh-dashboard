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

# Score por Rol Evaluador
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")

# Calcular Score Global
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()
score_global = 0
suma_ponderaciones = 0
for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
    if rol in pivot.columns:
        nota = pivot[rol].mean()
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score_global += nota * (peso / 100)
            suma_ponderaciones += peso


# Categoría de desempeño
categoria = ""
if score_global >= 3.6:
    categoria = "Desempeño destacado"
elif score_global >= 2.8:
    categoria = "Desempeño competente"
elif score_global >= 2.2:
    categoria = "Desempeño básico"
else:
    categoria = "Desempeño insuficiente"

st.subheader("Información del colaborador")
informacion = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates()
informacion["Puntaje Autoevaluación"] = pivot.get("Autoevaluacion").mean()
informacion["Puntaje Indirecto"] = pivot.get("Indirecto").mean()
informacion["Puntaje Jefatura"] = pivot.get("Jefatura").mean()
informacion["Score Global"] = score_global
informacion["Categoría desempeño"] = categoria
st.dataframe(informacion)

# Gráfico de barras - Puntaje por Dimensión (ahora con gráfico nativo)
st.subheader("Puntaje por Dimensión (Escala 1-4)")
notas = pivot.loc[pivot.index[0]].dropna() if not pivot.empty else pd.Series()
st.bar_chart(notas)

# Tabla resumen
st.subheader("Resumen de Notas por Dimensión")
resumen = pd.DataFrame({
    "Dimensión": notas.index,
    "Nota Obtenida": notas.values,
    "Nota Obtenida %": [f"{((x-1)/3)*100:.0f}%" for x in notas.values]
})
resumen.loc[len(resumen.index)] = ["Total ponderado", score_global, f"{((score_global-1)/3)*100:.0f}%"]
st.dataframe(resumen)

# Tabla fija informativa
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

# Descarga PDF (Placeholder)
st.subheader("Exportar a PDF")
if st.button("Descargar PDF del colaborador"):
    st.info("Funcionalidad en desarrollo. Requiere integración con librería de PDF como ReportLab o WeasyPrint.")
