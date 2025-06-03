import streamlit as st
import requests
import pandas as pd

st.title("Listado de Títulos Propios UPV")

URL = "https://www.cfp.upv.es/cfp-gow/titulaciones/web"

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

# === Eliminar filas sin fecha de inicio ===
df = df[df["Fecha inicio"].notnull() & (df["Fecha inicio"] != "")]

if df.empty:
    st.error("No se han encontrado datos de títulos propios con fecha de inicio.")
    st.stop()

st.dataframe(df)


