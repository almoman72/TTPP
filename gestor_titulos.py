import streamlit as st
import requests
import pandas as pd
import json
import os
import calendar

st.set_page_config(layout="wide")

# --- Cabecera con logo y colores corporativos ---
st.markdown(
    """
    <div style="display:flex;align-items:center;margin-bottom:10px;">
        <img src="https://www.cfp.upv.es/assets/images/logo_CFP_UPV.svg" alt="CFP UPV" width="120" style="margin-right:20px;" />
        <div>
            <h1 style="color:#003865; margin-bottom:0;">Listado de Títulos Propios UPV</h1>
            <span style="color:#FF8200; font-size:1.2em;">Centro de Formación Permanente</span>
        </div>
    </div>
    <hr style="border:1px solid #003865; margin-bottom:20px;"/>
    """,
    unsafe_allow_html=True
)

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
        "ID Proyecto Docente": t.get("idProyectoDocente"),
        "Denominación": t.get("denominacion"),
        "Fecha inicio": t.get("fechaInicio")
    })

df = pd.DataFrame(filas)
df = df[df["Fecha inicio"].notnull() & (df["Fecha inicio"] != "")]

if df.empty:
    st.error("No se han encontrado datos de títulos propios con fecha de inicio.")
    st.stop()

# --- Buscador por denominación ---
busqueda = st.text_input("Buscar por denominación:")
if busqueda:
    df = df[df["Denominación"].str.contains(busqueda, case=False, na=False)]

# --- Procesado de fechas, año y mes ---
df["Fecha inicio"] = pd.to_datetime(df["Fecha inicio"], errors="coerce")
df["Año"] = df["Fecha inicio"].apply(lambda x: x.year if pd.notnull(x) else "")

# Columna Mes y Mes nombre en español
df["Mes"] = df["Fecha inicio"].dt.month
meses_dict = {i: calendar.month_name[i].capitalize() for i in range(1, 13)}
df["Mes nombre"] = df["Mes"].apply(lambda x: meses_dict.get(x, ""))

# --- Filtro por año ---
anios_disponibles = sorted(df["Año"].unique())
opciones_filtro = ["Todos"] + [str(a) for a in anios_disponibles if str(a) != ""]
anio_filtro = st.selectbox("Filtrar por año", options=opciones_filtro)
if anio_filtro != "Todos":
    df = df[df["Año"] == int(anio_filtro)]

# --- Filtro multiselección de mes ---
meses_disponibles = [m for m in df["Mes nombre"].unique() if m]
meses_seleccionados = st.multiselect(
    "Filtrar por mes de inicio",
    options=meses_disponibles,
    default=meses_disponibles
)
if meses_seleccionados:
    df = df[df["Mes nombre"].isin(meses_seleccionados)]

# ------ ORDENACIÓN POR BOTÓN ------
if "ascendente" not in st.session_state:
    st.session_state.ascendente = True

if st.button("Ordenar por Fecha de Inicio"):
    st.session_state.ascendente = not st.session_state.ascendente

orden = st.session_state.ascendente
df = df.sort_values(by="Fecha inicio", ascending=orden)

# Formatear a dd/mm/yyyy
df["Fecha inicio"] = df["Fecha inicio"].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")

# === Editor de estado (checkboxes en una línea) ===
estado = cargar_estado(ARCHIVO_ESTADO)

st.markdown("### Edita el estado de los títulos:")
nuevo_estado = estado.copy()
for idx, row in df.iterrows():
    key_base = str(row["ID"])
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 3, 2, 5, 2])
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
        st.markdown(f"ID Proy.Doc.: <b>{row['ID Proyecto Docente']}</b>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<span style='color:#FF8200'>{row['Fecha inicio']}</span>", unsafe_allow_html=True)
    with col6:
        st.markdown(f"<span style='color:#003865'>{row['Mes nombre']}</span>", unsafe_allow_html=True)
    nuevo_estado[key_base] = {
        "Publicado": publicado,
        "Diseño": diseno
    }

guardar_estado(ARCHIVO_ESTADO, nuevo_estado)

df["Publicado"] = df["ID"].apply(lambda x: nuevo_estado.get(str(x), {}).get("Publicado", False))
df["Diseño"] = df["ID"].apply(lambda x: nuevo_estado.get(str(x), {}).get("Diseño", False))

# Orden final de columnas en la tabla
df = df[[
    "ID", "ID Proyecto Docente", "Denominación", "Fecha inicio", "Año", "Mes nombre", "Publicado", "Diseño"
]]

st.dataframe(df)
