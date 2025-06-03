import streamlit as st
import requests
import pandas as pd
import json
import os

st.title("Listado de Títulos Propios UPV")

URL = "https://www.cfp.upv.es/cfp-gow/titulaciones/web"
ARCHIVO_ESTADO = "estado_titulos.json"

# --- Funciones para guardar/cargar estado ---
def cargar_estado(archivo):
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            return json.load(f)
    return {}

def guardar_estado(archivo, estado):
    with open(archivo, "w") as f:
        json.dump(estado, f)

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

# ==== MARCADO DE PUBLICADO Y DISEÑO ====
# Cargar estado anterior
estado = cargar_estado(ARCHIVO_ESTADO)

# Inicializa los valores para cada curso
df["Publicado"] = df["ID"].apply(lambda x: estado.get(str(x), {}).get("Publicado", False))
df["Diseño"] = df["ID"].apply(lambda x: estado.get(str(x), {}).get("Diseño", False))

st.write("Marca los títulos según corresponda:")
nuevo_estado = estado.copy()
for idx, row in df.iterrows():
    key_base = str(row["ID"])
    publicado = st.checkbox(
        f"Publicado - {row['Denominación']} ({row['Fecha inicio']})",
        value=row["Publicado"],
        key=key_base + "_publicado"
    )
    diseno = st.checkbox(
        f"Diseño - {row['Denominación']} ({row['Fecha inicio']})",
        value=row["Diseño"],
        key=key_base + "_diseno"
    )
    nuevo_estado[key_base] = {
        "Publicado": publicado,
        "Diseño": diseno
    }

# Guardar estado actualizado
guardar_estado(ARCHIVO_ESTADO, nuevo_estado)

# Actualizar las columnas del DataFrame para la visualización
df["Publicado"] = df["ID"].apply(lambda x: nuevo_estado.get(str(x), {}).get("Publicado", False))
df["Diseño"] = df["ID"].apply(lambda x: nuevo_estado.get(str(x), {}).get("Diseño", False))

df = df[["ID", "Denominación", "Fecha inicio", "Año", "Publicado", "Diseño"]]

st.dataframe(df)
