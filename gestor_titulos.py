import streamlit as st
import requests
import pandas as pd

st.title("Listado de Títulos Propios UPV")

# URL con el JSON de titulaciones
URL = "https://www.cfp.upv.es/cfp-gow/titulaciones/web"

# Descarga los datos
try:
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    st.error(f"Error al descargar los datos: {e}")
    st.stop()

# Analiza estructura y crea tabla
titulaciones = data.get("titulaciones", [])

# Extrae solo las columnas necesarias
filas = []
for t in titulaciones:
    filas.append({
        "ID": t.get("idCurso"),
        "Denominación": t.get("nombreCurso"),
        "Fecha inicio": t.get("fechaInicio")
    })

df = pd.DataFrame(filas)

# Diagnóstico: muestra columnas y ejemplo de datos
st.write("Columnas del DataFrame:", df.columns.tolist())
st.write(df.head())

if df.empty:
    st.error("No se han encontrado datos de títulos propios.")
    st.stop()

# Muestra la tabla en Streamlit
st.dataframe(df)
