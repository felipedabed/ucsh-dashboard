import streamlit as st
import pandas as pd
import numpy as np
import os

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=";", encoding="latin1")
    df["Nota Final Evaluación"] = pd.to_numeric(df["Nota Final Evaluación"].replace("-", np.nan), errors='coerce')
    df["% Evaluación"] = df["Nota Final Evaluación"] / 4 * 100
    return df

df = load_data()

st.title("Panel de Evaluaciones - UCSH")

# Filtros
with st.sidebar:
    st.header("Filtros")
    rut = st.selectbox("RUT Colaborador", options=["Todos"] + sorted(df["RUT Colaborador"].dropna().unique().tolist()))
    sucursal = st.multiselect("Sucursal", options=sorted(df["Sucursal"].dropna().unique()), default=None)
    gerencia = st.multiselect("Gerencia", options=sorted(df["Gerencia"].dropna().unique()), default=None)

# Aplicar filtros
filtered_df = df.copy()
if rut != "Todos":
    filtered_df = filtered_df[filtered_df["RUT Colaborador"] == rut]
if sucursal:
    filtered_df = filtered_df[filtered_df["Sucursal"].isin(sucursal)]
if gerencia:
    filtered_df = filtered_df[filtered_df["Gerencia"].isin(gerencia)]

# Mostrar gráfica de barras
st.subheader("Resumen por Dimensión (Rol Evaluador)")
dimensiones = filtered_df.groupby("Rol Evaluador")["Nota Final Evaluación"].mean().dropna()

if not dimensiones.empty:
    st.bar_chart(dimensiones)
else:
    st.info("No hay datos disponibles para los filtros seleccionados.")

# Mostrar tablas por dimensión
for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
    df_rol = filtered_df[filtered_df["Rol Evaluador"] == rol].copy()
    if not df_rol.empty:
        st.subheader(f"Detalle de Atributos - {rol}")
        atributos = []
        for col in df_rol.columns:
            if col.startswith("Nota ") and "Final" not in col:
                base = col.replace("Nota ", "")
                try:
                    nota = pd.to_numeric(df_rol[col].values[0], errors='coerce')
                    ponderacion = pd.to_numeric(df_rol.get(f"Ponderación {base}", np.nan).values[0], errors='coerce')
                    ponderada = nota * ponderacion / 100 if not np.isnan(nota) and not np.isnan(ponderacion) else np.nan
                    atributos.append({
                        "Atributo": base,
                        "Nota": nota,
                        "Ponderación": ponderacion,
                        "Nota Ponderada": ponderada
                    })
                except:
                    continue
        if atributos:
            df_tabla = pd.DataFrame(atributos).dropna()
            st.dataframe(df_tabla)
        else:
            st.write("Sin atributos evaluados.")
    else:
        st.info(f"No hay evaluación para el rol {rol} en los filtros aplicados.")

