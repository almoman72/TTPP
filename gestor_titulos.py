import streamlit as st
import requests
import pandas as pd
import json
import os

st.title("Listado de Títulos Propios UPV")

URL = "https://www.cfp.upv.es/cfp-gow/titulaciones/web"
ARCHIVO_TRATADOS = "tratados.json"

# --- Función para cargar el estado ---
def cargar_tratados(archivo):
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            return set(json.load(f))
    return set()

def guardar_tratados(archivo, tratados):
    with open(archivo, "w") as f:
        json.dump(list(tratados), f)

# --- Descarga y limpieza de datos ---
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
        "Denominación": t.get("denominacion"),
        "Fecha inicio": t.get("fechaInicio")
    })

df = pd.DataFrame(filas)
df = df[df["Fecha inicio"].notnull() & (df["Fecha inicio"] != "")]

if df.empty:
    st.error("No se han encontrado datos de títulos propios con fecha de inicio.")
    st.stop()

# Búsqueda por denominación
busqueda = st.text_input("Buscar por denominación:")
if busqueda:
    df = df[df["Denominación"].str.contains(busqueda, case=False, na=False)]

# Convertir a fecha y añadir 'Año'
df["Fecha inicio"] = pd.to_datetime(df["Fecha inicio"], errors="coerce")
df["Año"] = df["Fecha inicio"].apply(lambda x: x.year if pd.notnull(x) else "")

# Filtro por año
anios_disponibles = sorted(df["Año"].unique())
opciones_filtro = ["Todos"] + [str(a) for a in anios_disponibles if str(a) != ""]
anio_filtro = st.selectbox("Filtrar por año", options=opciones_filtro)

if anio_filtro != "Todos":
    df = df[df["Año"] == int(anio_filtro)]

# ------ ORDENACIÓN POR BOTÓN ------
if "ascendente" not in st.session_state:
    st.session_state.ascendente = True

if st.button("Ordenar por Fecha de Inicio"):
    st.session_state.ascendente = not st.session_state.ascendente

orden = st.session_state.ascendente
df = df.sort_values(by="Fecha inicio", ascending=orden)

# Formatear a dd/mm/yyyy
df["Fecha inicio"] = df["Fecha inicio"].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")

# ==== MARCADO DE TRATADOS ====
# Cargar estado anterior
tratados = cargar_tratados(ARCHIVO_TRATADOS)

# Añadir columna Tratado (booleano)
df["Tratado"] = df["ID"].apply(lambda x: x in tratados)

# Mostrar y permitir marcar checkboxes
st.write("Marca los títulos que ya has tratado:")
nuevos_tratados = set(tratados)
for idx, row in df.iterrows():
    checked = st.checkbox(
        f"{row['Denominación']} ({row['Fecha inicio']})",
        value=row["Tratado"],
        key=str(row["ID"])
    )
    if checked:
        nuevos_tratados.add(row["ID"])
    else:
        nuevos_tratados.discard(row["ID"])

# Guardar al archivo el nuevo estado
guardar_tratados(ARCHIVO_TRATADOS, nuevos_tratados)

# Mostrar la tabla con el estado actual de "Tratado"
df["Tratado"] = df["ID"].apply(lambda x: x in nuevos_tratados)
df = df[["ID", "Denominación", "Fecha inicio", "Año", "Tratado"]]

st.dataframe(df)
