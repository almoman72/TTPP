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

# Muestra la tabla en Streamlit
st.dataframe(df)
