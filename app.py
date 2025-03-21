import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=",")
    df["Nota Final Evaluación"] = pd.to_numeric(df["Nota Final Evaluación"].replace("-", np.nan), errors='coerce')
    df["Ponderación Rol Evaluación"] = pd.to_numeric(df["Ponderación Rol Evaluación"], errors='coerce')
    return df

df = load_data()

st.title("Dashboard Evaluación UCSH")

# Filtros
with st.sidebar:
    rut = st.selectbox("RUT Colaborador", options=["Todos"] + sorted(df["RUT Colaborador"].dropna().unique().tolist()))
    sucursal = st.selectbox("Sucursal", options=["Todos"] + sorted(df["Sucursal"].dropna().unique().tolist()))
    gerencia = st.selectbox("Gerencia", options=["Todos"] + sorted(df["Gerencia"].dropna().unique().tolist()))

filtered_df = df.copy()
if rut != "Todos":
    filtered_df = filtered_df[filtered_df["RUT Colaborador"] == rut]
if sucursal != "Todos":
    filtered_df = filtered_df[filtered_df["Sucursal"] == sucursal]
if gerencia != "Todos":
    filtered_df = filtered_df[filtered_df["Gerencia"] == gerencia]

# Consolidado por Rol Evaluador
st.subheader("Resumen por Rol Evaluador")

roles = ["Autoevaluacion", "Indirecto", "Jefatura"]
resumen = {}
for rol in roles:
    notas = filtered_df[filtered_df["Rol Evaluador"] == rol]["Nota Final Evaluación"]
    if not notas.empty:
        promedio = notas.mean()
        porcentaje = (promedio - 1) / 3 * 100  # escala 1 a 4 => 0% a 100%
        resumen[rol] = porcentaje
    else:
        resumen[rol] = None

# Mostrar gráfico de barras nativo
st.bar_chart(pd.Series({k: v for k, v in resumen.items() if v is not None}))

# Mostrar tablas por Rol Evaluador
st.subheader("Detalle por Atributo")
for rol in roles:
    subset = filtered_df[filtered_df["Rol Evaluador"] == rol]
    if not subset.empty:
        cols = [col for col in subset.columns if "Nota" in col or "Ponderación" in col]
        tabla = subset[cols].copy()
        for col in tabla.columns:
            if "Nota" in col:
                tabla[col] = pd.to_numeric(tabla[col].replace("-", np.nan), errors="coerce")
        ponderadas = []
        for i in range(0, len(cols), 2):
            try:
                nota = tabla.iloc[:, i]
                ponderacion = tabla.iloc[:, i+1] / 100
                ponderadas.append(nota * ponderacion)
            except:
                continue
        if ponderadas:
            tabla["Nota Ponderada Total"] = sum(ponderadas)
        st.markdown(f"**{rol}**")
        st.dataframe(tabla)
