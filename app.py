import streamlit as st
import pandas as pd
import numpy as np


# El resto de tu código sigue exactamente igual desde aquí

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("data/Resultados_ROL.csv", delimiter=",", encoding="utf-8")
    df.columns = df.columns.str.strip().str.replace("\u00a0", " ").str.replace("\ufeff", "")
    
    # Validaciones
    columnas_requeridas = ["Nota Final Evaluación", "Ponderación Rol Evaluación"]
    for col in columnas_requeridas:
        if col not in df.columns:
            st.error(f"❌ No se encontró la columna '{col}' en el archivo.")
            st.stop()

    df["Nota Final Evaluación"] = pd.to_numeric(df["Nota Final Evaluación"].replace("-", np.nan), errors='coerce')
    df["Ponderación Rol Evaluación"] = pd.to_numeric(df["Ponderación Rol Evaluación"].replace("-", np.nan), errors='coerce')

    return df

# Cargar el DataFrame
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

# Tabla resumen con pesos reales por dimensión
st.subheader("Resumen de Notas por Dimensión")

# Obtener pesos reales en base al dataframe filtrado
ponderaciones_reales = filtered_df.groupby("Rol Evaluador")["Ponderación Rol Evaluación"].mean()
ponderaciones_reales = ponderaciones_reales.reindex(["Autoevaluacion", "Indirecto", "Jefatura"])

# Normalizar para que sumen 100%
ponderaciones_normalizadas = (ponderaciones_reales / ponderaciones_reales.sum()) * 100

resumen = pd.DataFrame({
    "Dimensión": dimensiones_promedio.index,
    "Nota Promedio": dimensiones_promedio.values.round(3),
    "Peso % Dimensión": ponderaciones_normalizadas.values.round(1).astype(str) + "%"
})

# Agregar fila con promedio global
resumen.loc[len(resumen)] = [
    "Total ponderado promedio",
    informacion["Score Global"].mean().round(3),
    "100%"
]

st.dataframe(resumen)



if len(informacion) == 1:
    st.subheader("Resumen por Dimensión")

    autoeval = dimensiones_promedio.get("Autoevaluacion", np.nan)
    indirecto = dimensiones_promedio.get("Indirecto", np.nan)
    jefatura = dimensiones_promedio.get("Jefatura", np.nan)

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; gap: 20px; margin-top: 10px; margin-bottom: 20px;">
        <div style="flex: 1; background-color: #f1f8e9; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 26px;">🧠</div>
            <div style="font-size: 16px; font-weight: bold; margin-top: 5px;">Autoevaluación</div>
            <div style="font-size: 22px; color: #2e7d32; font-weight: bold;">{autoeval:.2f}</div>
        </div>
        <div style="flex: 1; background-color: #e3f2fd; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 26px;">👥</div>
            <div style="font-size: 16px; font-weight: bold; margin-top: 5px;">Evaluación Indirecta</div>
            <div style="font-size: 22px; color: #1565c0; font-weight: bold;">{indirecto:.2f}</div>
        </div>
        <div style="flex: 1; background-color: #fce4ec; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 26px;">👔</div>
            <div style="font-size: 16px; font-weight: bold; margin-top: 5px;">Evaluación Jefatura</div>
            <div style="font-size: 22px; color: #ad1457; font-weight: bold;">{jefatura:.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Categoría de Desempeño con estilo visual y emoji
if len(informacion) == 1:
    st.subheader("Categoría de Desempeño Obtenida")

    categoria_colaborador = informacion["Categoría desempeño"].values[0]
    puntaje_colaborador = informacion["Score Global"].values[0]

    # Colores y emojis según categoría
    color = {
        "Desempeño destacado": "#27ae60",   # verde
        "Desempeño competente": "#2980b9",  # azul
        "Desempeño básico": "#f39c12",      # naranjo
        "Desempeño insuficiente": "#c0392b" # rojo
    }.get(categoria_colaborador, "#7f8c8d")  # gris por defecto

    emoji = {
        "Desempeño destacado": "🟢",
        "Desempeño competente": "🔵",
        "Desempeño básico": "🟠",
        "Desempeño insuficiente": "🔴"
    }.get(categoria_colaborador, "⚪")

    st.markdown(
        f"""
        <div style="padding:20px;border-radius:10px;background-color:{color};color:white;text-align:center;font-size:24px;">
            <b>{emoji} {categoria_colaborador}</b><br>
            <span style="font-size:18px;">Puntaje obtenido: <b>{puntaje_colaborador:.2f}</b></span>
        </div>
        """,
        unsafe_allow_html=True
    )


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


st.markdown("""
    <style>
        @media print {
            header, footer, .stSidebar, .stButton, .stDownloadButton, .stTextInput {
                display: none !important;
            }

            div[data-testid="stAppViewContainer"] {
                padding: 0 !important;
            }

            div.block-container {
                padding: 0 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)




