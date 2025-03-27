import streamlit as st
import pandas as pd
import numpy as np

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=",", encoding="ISO-8859-1")
    df.columns = df.columns.str.strip().str.replace("\u00a0", " ").str.replace("\ufeff", "")
    columnas_requeridas = ["Nota Final Evaluación", "Ponderación Rol Evaluación"]
    for col in columnas_requeridas:
        if col not in df.columns:
            st.error(f"❌ No se encontró la columna '{col}' en el archivo.")
            st.stop()
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
    if "Familia del Cargo" in df.columns:
        familia_cargo_filter = st.selectbox("Familia del Cargo", options=["Todos"] + sorted(df["Familia del Cargo"].dropna().unique().tolist()))
    else:
        familia_cargo_filter = "Todos"

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
if familia_cargo_filter != "Todos" and "Familia del Cargo" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Familia del Cargo"] == familia_cargo_filter]

if filtered_df.empty:
    st.warning("No se encontraron datos para los filtros seleccionados.")
    st.stop()

# Pivot y Ponderaciones
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")
pivot = pivot.reindex(columns=["Autoevaluacion", "Indirecto", "Jefatura"])
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()

# Función Score Global
def calcular_score(row):
    score, suma_ponderaciones = 0, 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * peso
            suma_ponderaciones += peso
    return score / suma_ponderaciones if suma_ponderaciones else np.nan

# Info colaborador
st.subheader("Información del colaborador")
informacion = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates()
informacion["Nota Autoevaluación"] = informacion["RUT Colaborador"].map(pivot["Autoevaluacion"]) if "Autoevaluacion" in pivot else np.nan
informacion["Nota Indirecto"] = informacion["RUT Colaborador"].map(pivot["Indirecto"]) if "Indirecto" in pivot else np.nan
informacion["Nota Jefatura"] = informacion["RUT Colaborador"].map(pivot["Jefatura"]) if "Jefatura" in pivot else np.nan

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

st.dataframe(informacion)

# Gráfico
st.subheader("Puntaje por Dimensión (Escala 1-4)")
dimensiones_promedio = pivot.mean(skipna=True)
st.bar_chart(dimensiones_promedio)

# Tabla resumen
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

# Categoría visual destacada
if len(informacion) == 1:
    st.subheader("Categoría de Desempeño Obtenida")

    autoeval = informacion["Nota Autoevaluación"].values[0]
    indirecto = informacion["Nota Indirecto"].values[0]
    jefatura = informacion["Nota Jefatura"].values[0]
    score = informacion["Score Global"].values[0]
    categoria = informacion["Categoría desempeño"].values[0]

    color = {
        "Desempeño destacado": "#27ae60",
        "Desempeño competente": "#2980b9",
        "Desempeño básico": "#f39c12",
        "Desempeño insuficiente": "#c0392b"
    }.get(categoria, "#7f8c8d")

    emoji = {
        "Desempeño destacado": "🟢",
        "Desempeño competente": "🔵",
        "Desempeño básico": "🟠",
        "Desempeño insuficiente": "🔴"
    }.get(categoria, "⚪")

    col1, col2, col3 = st.columns(3)
    col1.metric("Autoevaluación", f"{autoeval:.2f}" if pd.notna(autoeval) else "N/A")
    col2.metric("Indirecto", f"{indirecto:.2f}" if pd.notna(indirecto) else "N/A")
    col3.metric("Jefatura", f"{jefatura:.2f}" if pd.notna(jefatura) else "N/A")

    st.markdown(
        f"""
        <div style="padding:20px;margin-top:10px;border-radius:10px;background-color:{color};color:white;text-align:center;font-size:24px;">
            <b>{emoji} {categoria} — {score:.2f}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Botón de imprimir con nombre personalizado
    rut_colaborador = informacion["RUT Colaborador"].values[0]
    st.markdown(f"""
        <script>
            function printPDF() {{
                const filename = "{rut_colaborador}.pdf";
                document.title = filename;
                window.print();
                setTimeout(() => {{
                    document.title = "Panel de Evaluación UCSH";
                }}, 3000);
            }}
        </script>
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="printPDF()" style="
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                cursor: pointer;">
                🖨️ Imprimir Evaluación / Guardar como PDF
            </button>
        </div>
    """, unsafe_allow_html=True)
