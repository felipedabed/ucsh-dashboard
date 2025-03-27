import streamlit as st
import pandas as pd
import numpy as np

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados2024.csv", delimiter=",", encoding="ISO-8859-1")
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
    centro_filter = st.selectbox("Centro de Costo", options=["Todos"] + sorted(df["Centro de Costo"].dropna().unique().tolist()))
    sucursal_filter = st.selectbox("Sucursal", options=["Todos"] + sorted(df["Sucursal"].dropna().unique().tolist()))
    familia_cargo_filter = st.selectbox("Familia del Cargo", options=["Todos"] + sorted(df["Familia del Cargo"].dropna().unique().tolist()))

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
if familia_cargo_filter != "Todos":
    filtered_df = filtered_df[filtered_df["Familia del Cargo"] == familia_cargo_filter]

if filtered_df.empty:
    st.warning("No se encontraron datos para los filtros seleccionados.")
    st.stop()

# Pivot por Rol Evaluador
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")
pivot = pivot.reindex(columns=["Autoevaluacion", "Indirecto", "Jefatura"])

# Ponderaciones globales
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()

# Función de Score Global
def calcular_score(row):
    score, suma_ponderaciones = 0, 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * peso
            suma_ponderaciones += peso
    return score / suma_ponderaciones if suma_ponderaciones else np.nan

# Información del colaborador
informacion = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates()
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

# Mostrar información del colaborador
st.subheader("Información del colaborador")
st.dataframe(informacion)

# Puntaje promedio por dimensión
dimensiones_promedio = pivot.mean(skipna=True)

# Visualización por dimensión (barras)
st.subheader("Puntaje por Dimensión (Escala 1-4)")
st.bar_chart(dimensiones_promedio)

# Tabla resumen por dimensión
st.subheader("Resumen de Notas por Dimensión")
resumen = pd.DataFrame({
    "Dimensión": dimensiones_promedio.index,
    "Nota Promedio": dimensiones_promedio.values.round(3),
    "Nota Promedio %": [f"{((x-1)/3)*100:.0f}%" for x in dimensiones_promedio.values]
})
resumen.loc[len(resumen)] = [
    "Total ponderado promedio",
    informacion["Score Global"].mean().round(3),
    f"{((informacion['Score Global'].mean()-1)/3)*100:.0f}%"
]
st.dataframe(resumen)

# NUEVA SECCIÓN: Categoría + Breakdown
if len(informacion) == 1:
    st.subheader("Resumen por Dimensión")

    autoeval = dimensiones_promedio.get("Autoevaluacion", np.nan)
    indirecto = dimensiones_promedio.get("Indirecto", np.nan)
    jefatura = dimensiones_promedio.get("Jefatura", np.nan)

    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-around; text-align: center; margin-top: 20px;'>
            <div>
                <h5>Autoevaluación</h5>
                <p style='font-size:24px; font-weight:bold;'>{autoeval:.2f}</p>
            </div>
            <div>
                <h5>Evaluación Indirecta</h5>
                <p style='font-size:24px; font-weight:bold;'>{indirecto:.2f}</p>
            </div>
            <div>
                <h5>Jefatura</h5>
                <p style='font-size:24px; font-weight:bold;'>{jefatura:.2f}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("Categoría de Desempeño Obtenida")

    categoria_colaborador = informacion["Categoría desempeño"].values[0]
    score_colaborador = informacion["Score Global"].values[0]

    color = {
        "Desempeño destacado": "#27ae60",
        "Desempeño competente": "#2980b9",
        "Desempeño básico": "#f39c12",
        "Desempeño insuficiente": "#c0392b"
    }.get(categoria_colaborador, "#7f8c8d")

    emoji = {
        "Desempeño destacado": "🟢",
        "Desempeño competente": "🔵",
        "Desempeño básico": "🟠",
        "Desempeño insuficiente": "🔴"
    }.get(categoria_colaborador, "⚪")

    st.markdown(
        f"""
        <div style="padding:20px;border-radius:10px;background-color:{color};color:white;text-align:center;font-size:24px;">
            <b>{emoji} {categoria_colaborador} (Score: {score_colaborador:.2f})</b>
        </div>
        """,
        unsafe_allow_html=True
    )
