import streamlit as st
import pandas as pd
import numpy as np

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=",", encoding="ISO-8859-1")
    df = df.replace("-", np.nan)
    df["Nota Final Evaluación"] = pd.to_numeric(df["Nota Final Evaluación"], errors="coerce")
    df["Ponderación Rol Evaluación"] = pd.to_numeric(df["Ponderación Rol Evaluación"], errors="coerce")
    return df

df = load_data()

st.title("🔍 Dashboard Evaluaciones UCSH")

# --- Filtros dinámicos ---
st.sidebar.header("Filtrar colaborador")
rut = st.sidebar.selectbox("RUT Colaborador", options=["Todos"] + sorted(df["RUT Colaborador"].dropna().unique().tolist()))
nombre = st.sidebar.selectbox("Nombre Colaborador", options=["Todos"] + sorted(df["Nombre Colaborador"].dropna().unique().tolist()))
sucursal = st.sidebar.selectbox("Sucursal", options=["Todos"] + sorted(df["Sucursal"].dropna().unique().tolist()))

filtered_df = df.copy()

if rut != "Todos":
    filtered_df = filtered_df[filtered_df["RUT Colaborador"] == rut]
if nombre != "Todos":
    filtered_df = filtered_df[filtered_df["Nombre Colaborador"] == nombre]
if sucursal != "Todos":
    filtered_df = filtered_df[filtered_df["Sucursal"] == sucursal]

# --- Mostrar Info Colaborador ---
if filtered_df.empty:
    st.warning("No se encontraron datos con los filtros seleccionados.")
else:
    colaborador_info = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates()
    st.subheader("📄 Información del colaborador")
    st.dataframe(colaborador_info)

    st.subheader("📊 Scores por Rol Evaluador")
    roles = ["Autoevaluacion", "Indirecto", "Jefatura"]

    scores = {}
    for rol in roles:
        df_rol = filtered_df[filtered_df["Rol Evaluador"] == rol]
        if not df_rol.empty:
            nota = df_rol["Nota Final Evaluación"].values[0]
            if not np.isnan(nota):
                scores[rol] = nota
            else:
                scores[rol] = None
        else:
            scores[rol] = None

    # --- Mostrar gráfico de barras ---
    st.write("### Puntaje por dimensión")
    score_chart_data = pd.DataFrame({
        "Rol Evaluador": roles,
        "Score (1-4)": [scores[r] if scores[r] is not None else np.nan for r in roles],
        "Porcentaje (%)": [((scores[r]-1)/3)*100 if scores[r] is not None else np.nan for r in roles]
    })

    st.bar_chart(score_chart_data.set_index("Rol Evaluador")["Porcentaje (%)"])

    # --- Mostrar Score Global ponderado ---
    ponderaciones = {"Autoevaluacion": 0.2, "Indirecto": 0.35, "Jefatura": 0.45}
    ponderaciones_validas = {k: v for k, v in ponderaciones.items() if scores[k] is not None}
    total_ponderacion = sum(ponderaciones_validas.values())

    if total_ponderacion > 0:
        score_global = sum((scores[k] * v for k, v in ponderaciones_validas.items())) / total_ponderacion
        st.metric("⭐ Score Global", f"{score_global:.2f} / 4 ({((score_global - 1)/3 * 100):.1f}%)")
    else:
        st.warning("No hay suficientes datos para calcular el Score Global.")

    # --- Mostrar tablas por Rol Evaluador ---
    st.subheader("📑 Evaluación por dimensión y atributos")

    for rol in roles:
        df_rol = filtered_df[filtered_df["Rol Evaluador"] == rol]
        if df_rol.empty or df_rol["Nota Final Evaluación"].isna().all():
            continue

        # Filtrar columnas de atributos
        notas_cols = [col for col in df_rol.columns if "Nota" in col and "Final" not in col]
        pondera_cols = [col for col in df_rol.columns if "Ponderación" in col and "Rol" not in col]

        notas = df_rol[notas_cols].T
        ponderaciones = df_rol[pondera_cols].T

        notas.columns = ["Nota"]
        ponderaciones.columns = ["Ponderación"]

        tabla = notas.join(ponderaciones)
        tabla["Nota Ponderada"] = (tabla["Nota"].astype(float) * tabla["Ponderación"].astype(float)) / 100
        tabla = tabla.dropna(how="all")

        st.write(f"#### {rol}")
        st.dataframe(tabla.style.format({"Nota": "{:.2f}", "Ponderación": "{:.0f}%", "Nota Ponderada": "{:.2f}"}))

    # --- Exportar a PDF (opcional más adelante) ---
    # Aquí podríamos agregar lógica para exportar con pdfkit o similar
