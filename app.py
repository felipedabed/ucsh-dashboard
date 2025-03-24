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
st.dataframe(informacion)

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



# Descarga PDF (Placeholder)
import io
from fpdf import FPDF
import zipfile

def crear_pdf(rut, info_df, dimensiones_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Título
    pdf.cell(200, 10, f"Evaluación UCSH - RUT {rut}", ln=True, align='C')

    # Información del colaborador
    pdf.cell(200, 10, "Información del Colaborador:", ln=True)
    for col in info_df.columns:
        pdf.cell(200, 10, f"{col}: {info_df.iloc[0][col]}", ln=True)

    pdf.ln(10)

    # Puntajes por dimensión
    pdf.cell(200, 10, "Puntajes por Dimensión:", ln=True)
    for idx, row in dimensiones_df.iterrows():
        pdf.cell(200, 10, f"{row['Dimensión']}: {row['Nota Promedio']:.2f}", ln=True)

    return pdf.output(dest='S').encode('latin1')

def crear_zip_pdfs(df_filtrado, informacion):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for rut in informacion["RUT Colaborador"].unique():
            info_colab = informacion[informacion["RUT Colaborador"] == rut]
            pivot_colab = df_filtrado[df_filtrado["RUT Colaborador"] == rut].pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")
            
            dimensiones_colab = pivot_colab.mean().reset_index().rename(columns={0: "Nota Promedio", "Rol Evaluador": "Dimensión"})
            pdf_bytes = crear_pdf(rut, info_colab, dimensiones_colab)

            zf.writestr(f"{rut}.pdf", pdf_bytes)
    return zip_buffer.getvalue()

# Botones en Streamlit
st.subheader("Exportar a PDF")

# PDF Individual
if st.button("Descargar PDF del colaborador seleccionado"):
    if len(informacion) == 1:
        rut_seleccionado = informacion.iloc[0]["RUT Colaborador"]
        pivot_colab = filtered_df.pivot_table(index="RUT Colaborador", columns="Rol Evaluador", values="Nota Final Evaluación", aggfunc="mean")
        dimensiones_colab = pivot_colab.mean().reset_index().rename(columns={0: "Nota Promedio", "Rol Evaluador": "Dimensión"})

        pdf_bytes = crear_pdf(rut_seleccionado, informacion, dimensiones_colab)
        
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name=f"{rut_seleccionado}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Por favor, selecciona exactamente un colaborador para descargar su PDF individual.")

# PDF Bulk
if st.button("Descargar PDFs de TODOS los colaboradores (ZIP)"):
    zip_bytes = crear_zip_pdfs(filtered_df, informacion)

    st.download_button(
        label="Descargar ZIP con PDFs",
        data=zip_bytes,
        file_name="Evaluaciones_Colaboradores.zip",
        mime="application/zip"
    )
