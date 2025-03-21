import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# -------------------------
# Cargar los datos
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=",")
    df["Nota Final Evaluación"] = pd.to_numeric(df["Nota Final Evaluación"].replace("-", np.nan), errors="coerce")
    df["Ponderación Rol Evaluación"] = pd.to_numeric(df["Ponderación Rol Evaluación"].replace("-", np.nan), errors="coerce")
    return df

df = load_data()

st.set_page_config(layout="wide")
st.title("🔍 Dashboard Evaluación de Desempeño – UCSH")

# -------------------------
# Filtros
# -------------------------
st.sidebar.header("🎯 Filtros")

col1 = st.sidebar.multiselect("RUT Colaborador", df["RUT Colaborador"].unique())
col2 = st.sidebar.multiselect("Nombre Colaborador", df["Nombre Colaborador"].unique())
col3 = st.sidebar.multiselect("Cargo", df["Cargo"].unique())
col4 = st.sidebar.multiselect("Gerencia", df["Gerencia"].unique())
col5 = st.sidebar.multiselect("Sucursal", df["Sucursal"].unique())
col6 = st.sidebar.multiselect("Centro de Costo", df["Centro de Costo"].unique())

filtered_df = df.copy()
if col1: filtered_df = filtered_df[filtered_df["RUT Colaborador"].isin(col1)]
if col2: filtered_df = filtered_df[filtered_df["Nombre Colaborador"].isin(col2)]
if col3: filtered_df = filtered_df[filtered_df["Cargo"].isin(col3)]
if col4: filtered_df = filtered_df[filtered_df["Gerencia"].isin(col4)]
if col5: filtered_df = filtered_df[filtered_df["Sucursal"].isin(col5)]
if col6: filtered_df = filtered_df[filtered_df["Centro de Costo"].isin(col6)]

# -------------------------
# Mostrar datos filtrados
# -------------------------
if not filtered_df.empty:
    for (rut, nombre), df_persona in filtered_df.groupby(["RUT Colaborador", "Nombre Colaborador"]):
        st.subheader(f"👤 {nombre} – {rut}")
        
        df_persona = df_persona[["Rol Evaluador", "Nota Final Evaluación", "Ponderación Rol Evaluación"]].dropna()

        # Gráfico
        fig, ax = plt.subplots()
        evaluadores = df_persona["Rol Evaluador"]
        puntajes = df_persona["Nota Final Evaluación"]
        porcentajes = puntajes / 4 * 100
        ax.bar(evaluadores, porcentajes, color="skyblue")
        ax.set_ylabel("% de logro (1 = 0%, 4 = 100%)")
        ax.set_ylim(0, 100)
        ax.set_title("Score por Dimensión")
        st.pyplot(fig)

        # Cálculo Score Global
        df_persona["Peso"] = df_persona["Ponderación Rol Evaluación"] / 100
        df_persona["Peso Normalizado"] = df_persona["Peso"] / df_persona["Peso"].sum()
        df_persona["Score Ponderado"] = df_persona["Nota Final Evaluación"] * df_persona["Peso Normalizado"]
        score_global = df_persona["Score Ponderado"].sum()
        st.metric("🎯 Score Global Ponderado", f"{score_global:.2f} (de 4)")

        # Tabla resumen
        st.dataframe(df_persona[["Rol Evaluador", "Nota Final Evaluación", "Ponderación Rol Evaluación", "Score Ponderado"]])

else:
    st.warning("⚠️ No se encontraron resultados con los filtros seleccionados.")
