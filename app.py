
import streamlit as st 
import pandas as pd
import numpy as np

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=",", encoding="ISO-8859-1")
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.replace("\u00a0", " ").str.replace("\ufeff", "")

    # Validar columna clave
    if "Nota Final Evaluación" not in df.columns:
        st.error("❌ No se encontró la columna 'Nota Final Evaluación' en el archivo. Verifica el nombre exacto en el CSV.")
        st.stop()

    # Limpiar datos
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
    solo_completos = st.checkbox("Mostrar solo evaluaciones completas", value=False)

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
if solo_completos:
    completos = filtered_df.groupby("RUT Colaborador")["Rol Evaluador"].nunique()
    filtered_df = filtered_df[filtered_df["RUT Colaborador"].isin(completos[completos == 3].index)]

if filtered_df.empty:
    st.warning("No se encontraron datos para los filtros seleccionados.")
    st.stop()

pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")
pivot = pivot.reindex(columns=["Autoevaluacion", "Indirecto", "Jefatura"])
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()

def calcular_score(row):
    score, suma_ponderaciones = 0, 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * peso
            suma_ponderaciones += peso
    return score / suma_ponderaciones if suma_ponderaciones else np.nan

st.subheader("Información del colaborador")
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

def evaluar_completitud(row):
    evaluaciones = [row["Nota Autoevaluación"], row["Nota Indirecto"], row["Nota Jefatura"]]
    if all(pd.notna(val) for val in evaluaciones):
        return "Completa"
    return "Incompleta"

informacion["Evaluación"] = informacion.apply(evaluar_completitud, axis=1)

def colorear_categoria(val):
    color = {
        "Desempeño destacado": "#27ae60",
        "Desempeño competente": "#2980b9",
        "Desempeño básico": "#f39c12",
        "Desempeño insuficiente": "#c0392b"
    }.get(val, "gray")
    return f"background-color: {color}; color: white;"

st.dataframe(informacion.style.applymap(colorear_categoria, subset=["Categoría desempeño"]))
