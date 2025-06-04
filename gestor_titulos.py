import streamlit as st
import requests
import pandas as pd
import json
import os
import calendar

st.set_page_config(layout="wide")  # Página ancha

URL = "https://www.cfp.upv.es/cfp-gow/titulaciones/web"
ARCHIVO_ESTADO = "estado_titulos.json"

def cargar_estado(archivo):
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            return json.load(f)
    return {}

def guardar_estado(archivo, estado):
    with open(archivo, "w") as f:
        json.dump(estado, f)

try:
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    st.error(f"Error al descargar los datos: {e}")
    st.stop()

titulaciones = data.get("titulaciones", [])
filas = []
for t in titulaciones:
    filas.append({
        "ID": t.get("idCurso"),
        "ID Proyecto": t.get("idProyectoDocente"),
        "Denominación": t.get("denominacion"),
        "Fecha inicio": t.get("fechaInicio")
    })

df = pd.DataFrame(filas)
df = df[df["Fecha inicio"].notnull() & (df["Fecha inicio"] != "")]

if df.empty:
    st.error("No se han encontrado datos de títulos propios con fecha de inicio.")
    st.stop()

busqueda = st.text_input("Buscar por denominación:")
if busqueda:
    df = df[df["Denominación"].str.contains(busqueda, case=False, na=False)]

df["Fecha inicio"] = pd.to_datetime(df["Fecha inicio"], errors="coerce")
df["Año"] = df["Fecha inicio"].apply(lambda x: x.year if pd.notnull(x) else "")

# ---- Añadir columna "Mes" (nombre) ----
df["Mes"] = df["Fecha inicio"].apply(
    lambda x: calendar.month_name[x.month].capitalize() if pd.notnull(x) else ""
)

anios_disponibles = sorted(df["Año"].unique())
opciones_filtro = ["Todos"] + [str(a) for a in anios_disponibles if str(a) != ""]
anio_filtro = st.selectbox("Filtrar por año", options=opciones_filtro)

if anio_filtro != "Todos":
    df = df[df["Año"] == int(anio_filtro)]

if "ascendente" not in st.session_state:
    st.session_state.ascendente = True

if st.button("Ordenar por Fecha de Inicio"):
    st.session_state.ascendente = not st.session_state.ascendente

orden = st.session_state.ascendente
df = df.sort_values(by="Fecha inicio", ascending=orden)
df["Fecha inicio"] = df["Fecha inicio"].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")

# ==== EDITOR DE ESTADO (checkboxes en una línea, con Mes) ====
estado = cargar_estado(ARCHIVO_ESTADO)

st.markdown("### Edita el estado de los títulos:")
nuevo_estado = estado.copy()
for idx, row in df.iterrows():
    key_base = str(row["ID"])
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 3, 4, 2, 2])
    with col1:
        publicado = st.checkbox(
            "Publicado",
            value=estado.get(key_base, {}).get("Publicado", False),
            key=key_base + "_publicado"
        )
    with col2:
        diseno = st.checkbox(
            "Diseño",
            value=estado.get(key_base, {}).get("Diseño", False),
            key=key_base + "_diseno"
        )
    with col3:
        st.markdown(f"<span style='color:#003865'><b>{row['Denominación']}</b></span>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"ID Proyecto Docente: <b>{row['ID Proyecto']}</b>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<span style='color:#FF8200'>{row['Fecha inicio']}</span>", unsafe_allow_html=True)
    with col6:
        st.markdown(f"<span style='color:#003865'>{row['Mes']}</span>", unsafe_allow_html=True)
    nuevo_estado[key_base] = {
        "Publicado": publicado,
        "Diseño": diseno
    }

guardar_estado(ARCHIVO_ESTADO, nuevo_estado)

df["Publicado"] = df["ID"].apply(lambda x: nuevo_estado.get(str(x), {}).get("Publicado", False))
df["Diseño"] = df["ID"].apply(lambda x: nuevo_estado.get(str(x), {}).get("Diseño", False))

# ---- Tabla final, incluye la columna Mes ----
df = df[["ID", "ID Proyecto", "Denominación", "Fecha inicio", "Año", "Mes", "Publicado", "Diseño"]]

st.dataframe(df)
