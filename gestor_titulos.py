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

# Eliminar filas sin fecha de inicio
df = df[df["Fecha inicio"].notnull() & (df["Fecha inicio"] != "")]

if df.empty:
    st.error("No se han encontrado datos de títulos propios con fecha de inicio.")
    st.stop()

# ---> Convierte a datetime lo antes posible <---
df["Fecha inicio"] = pd.to_datetime(df["Fecha inicio"], errors="coerce")

# ---- FILTRO POR AÑO ----
if not df["Fecha inicio"].isnull().all():
    anios = df["Fecha inicio"].dropna().dt.year.astype(int).unique()
    anios = sorted(anios)
    opciones = ["Todos"] + [str(a) for a in anios]
else:
    opciones = ["Todos"]

anio_seleccionado = st.selectbox("Filtrar por año de inicio", options=opciones)

if anio_seleccionado != "Todos":
    df = df[df["Fecha inicio"].dt.year == int(anio_seleccionado)]

# ------ ORDENACIÓN POR BOTÓN ------
if "ascendente" not in st.session_state:
    st.session_state.ascendente = True

if st.button("Ordenar por Fecha de Inicio"):
    st.session_state.ascendente = not st.session_state.ascendente

orden = st.session_state.ascendente
df = df.sort_values(by="Fecha inicio", ascending=orden)

# Paso 2: Formatear a dd/mm/yyyy (solo fechas válidas)
df["Fecha inicio"] = df["Fecha inicio"].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")

st.dataframe(df)
