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

# ---- Crear columna auxiliar para filtrar y ordenar ----
df["fecha_aux"] = pd.to_datetime(df["Fecha inicio"], errors="coerce")

# ---- FILTRO POR AÑO ----
anios_disponibles = sorted(df["fecha_aux"].dropna().dt.year.unique())
opciones_anio = ["Todos"] + [str(a) for a in anios_disponibles]

anio_seleccionado = st.selectbox("Filtrar por año de inicio", options=opciones_anio)

if anio_seleccionado != "Todos":
    df = df[df["fecha_aux"].dt.year == int(anio_seleccionado)]

# ------ ORDENACIÓN POR BOTÓN ------
if "ascendente" not in st.session_state:
    st.session_state.ascendente = True

if st.button("Ordenar por Fecha de Inicio"):
    st.session_state.ascendente = not st.session_state.ascendente

orden = st.session_state.ascendente
df = df.sort_values(by="fecha_aux", ascending=orden)

# Paso 2: Mostrar la fecha en formato dd/mm/yyyy
df["Fecha inicio"] = df["fecha_aux"].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")

# ---- Mostrar la tabla solo con las columnas deseadas ----
st.dataframe(df[["ID", "Denominación", "Fecha inicio"]])

