import streamlit as st
import pandas as pd
import numpy as np


# El resto de tu código sigue exactamente igual desde aquí

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

# Pivot por Rol Evaluador
pivot = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")
pivot = pivot.reindex(columns=["Autoevaluacion", "Indirecto", "Jefatura"])

# Ponderaciones globales por rol
ponderaciones = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()

# Función correcta para calcular score individual
def calcular_score(row):
    score, suma_ponderaciones = 0, 0
    for rol in ["Autoevaluacion", "Indirecto", "Jefatura"]:
        nota = row.get(rol)
        peso = ponderaciones.get(rol, np.nan)
        if not pd.isna(nota) and not pd.isna(peso):
            score += nota * peso
            suma_ponderaciones += peso
    return score / suma_ponderaciones if suma_ponderaciones else np.nan

# Información del colaborador con scores individuales corregidos
st.subheader("Información del colaborador")
informacion = filtered_df[["RUT Colaborador", "Nombre Colaborador", "Cargo", "Gerencia", "Sucursal", "Centro de Costo"]].drop_duplicates()

# Notas individuales por rol
informacion["Nota Autoevaluación"] = informacion["RUT Colaborador"].map(pivot["Autoevaluacion"])
informacion["Nota Indirecto"] = informacion["RUT Colaborador"].map(pivot["Indirecto"])
informacion["Nota Jefatura"] = informacion["RUT Colaborador"].map(pivot["Jefatura"])

# Score Global individual
informacion["Score Global"] = informacion.apply(lambda row: calcular_score({
    "Autoevaluacion": row["Nota Autoevaluación"],
    "Indirecto": row["Nota Indirecto"],
    "Jefatura": row["Nota Jefatura"]
}), axis=1).round(3)

# Categoría desempeño individual
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
st.dataframe(informacion, height=(len(informacion)+1)*35)

# Puntaje promedio por dimensión
st.subheader("Puntaje por Dimensión (Escala 1-4)")
dimensiones_promedio = pivot.mean(skipna=True)
st.bar_chart(dimensiones_promedio)

# Tabla resumen promedios correctos
st.subheader("Resumen de Notas por Dimensión")
resumen = pd.DataFrame({
    "Dimensión": dimensiones_promedio.index,
    "Nota Promedio": dimensiones_promedio.values.round(3),
    "Nota Promedio %": [f"{((x-1)/3)*100:.0f}%" for x in dimensiones_promedio.values]
})

# Total ponderado promedio correcto
resumen.loc[len(resumen)] = [
    "Total ponderado promedio",
    informacion["Score Global"].mean().round(3),
    f"{((informacion['Score Global'].mean()-1)/3)*100:.0f}%"
]
st.dataframe(resumen)

# Tabla fija informativa (bien desde antes)
st.subheader("Ponderación por Dimensión")
info_ponderacion = pd.DataFrame({
    "Dimensión": ["Autoevaluación", "Indirecto", "Jefatura"],
    "% Ponderación": [f"{ponderaciones.get(r, np.nan):.0f}%" if not pd.isna(ponderaciones.get(r)) else "-" for r in ["Autoevaluacion", "Indirecto", "Jefatura"]]
})
st.dataframe(info_ponderacion)


# UUUULTIMA SECCION


# Evaluación por dimensión y atributos (con puntaje final por dimensión)
st.subheader("Evaluación por dimensión y atributos")

atributos_por_dimension = {
    "Autoevaluacion": [col for col in filtered_df.columns if col.startswith("Nota A")],
    "Indirecto": [col for col in filtered_df.columns if col.startswith("Nota EI")],
    "Jefatura": [col for col in filtered_df.columns if col.startswith("Nota ED")]
}

for dimension, columnas_nota in atributos_por_dimension.items():
    columnas_ponderacion = [col.replace("Nota", "Ponderación") for col in columnas_nota]
    
    columnas_existentes = [col for col in columnas_nota + columnas_ponderacion if col in filtered_df.columns]
    if len(columnas_existentes) < len(columnas_nota + columnas_ponderacion):
        st.warning(f"Faltan columnas para la dimensión {dimension}.")
        continue
    
    notas_df = filtered_df[columnas_nota].copy()
    ponderaciones_df = filtered_df[columnas_ponderacion].copy()

    notas_melted = notas_df.melt(var_name="Atributo", value_name="Nota")
    ponderaciones_melted = ponderaciones_df.melt(var_name="Atributo", value_name="Ponderacion")

    ponderaciones_melted["Atributo"] = ponderaciones_melted["Atributo"].str.replace("Ponderación ", "Nota ")

    atributos_combinados = pd.merge(notas_melted, ponderaciones_melted, on=["Atributo"])

    atributos_combinados = atributos_combinados[
        atributos_combinados["Nota"].notna() &
        (atributos_combinados["Nota"] != "-") &
        atributos_combinados["Ponderacion"].notna()
    ]

    if not atributos_combinados.empty:
        atributos_combinados["Nota"] = pd.to_numeric(atributos_combinados["Nota"], errors="coerce")
        atributos_combinados["Ponderacion"] = pd.to_numeric(atributos_combinados["Ponderacion"], errors="coerce")

        tabla_atributos = atributos_combinados.groupby("Atributo", as_index=False).agg({
            "Nota": "mean",
            "Ponderacion": "mean"
        }).dropna()

        # Cálculo del puntaje final por dimensión
        tabla_atributos["Nota x Ponderación"] = tabla_atributos["Nota"] * tabla_atributos["Ponderacion"] / 100
        puntaje_final_dimension = tabla_atributos["Nota x Ponderación"].sum()

        # Preparar tabla para visualización
        tabla_visualizacion = tabla_atributos[["Atributo", "Nota", "Ponderacion"]].copy()
        tabla_visualizacion = tabla_visualizacion.rename(columns={
            "Nota": "Nota Promedio",
            "Ponderacion": "Ponderación (%)"
        }).round(2)

        # Agregar fila final con Puntaje Final de la Dimensión
        tabla_visualizacion.loc[len(tabla_visualizacion)] = ["**Puntaje Final Dimensión**", "", f"{puntaje_final_dimension:.2f}"]

        st.markdown(f"### {dimension}")
        st.dataframe(tabla_visualizacion)
    else:
        st.markdown(f"### {dimension}")
        st.info("No se encontraron atributos evaluados para esta dimensión.")

### DE AQUI PA ABAJO TIRAR ERRORES

from fpdf import FPDF
import streamlit as st
import pandas as pd
from io import BytesIO

def generar_pdf(informacion, resumen):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Informe Evaluación Colaborador", ln=True, align='C')

    # Información General
    pdf.cell(200, 10, txt="Información General", ln=True, align='L')
    for col in informacion.columns:
        pdf.cell(200, 10, txt=f"{col}: {informacion.iloc[0][col]}", ln=True)

    pdf.cell(200, 10, txt=" ", ln=True)

    # Notas por Dimensión
    pdf.cell(200, 10, txt="Notas por Dimensión", ln=True, align='L')
    for idx, row in resumen.iterrows():
        pdf.cell(200, 10, txt=f"{row['Dimensión']}: {row['Nota Promedio']:.2f}", ln=True)

    pdf_file = BytesIO()
    pdf.output(pdf_file)
    pdf_file.seek(0)

    return pdf_file

st.subheader("Exportar a PDF")

if st.button("Descargar PDF del colaborador seleccionado"):
    pdf_file = generar_pdf(informacion, resumen)

    st.download_button(
        label="Descargar PDF",
        data=pdf_file,
        file_name=f"{informacion.iloc[0]['RUT Colaborador']}.pdf",
        mime="application/pdf"
    )
