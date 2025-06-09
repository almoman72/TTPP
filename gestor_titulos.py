import streamlit as st
import requests
import pandas as pd
import json
import os
import calendar

st.set_page_config(layout="wide")

URL = "https://www.cfp.upv.es/cfp-gow/titulaciones/web"
ARCHIVO_ESTADO = "estado_titulos.json"

# Función robusta para cargar el estado, incluso si el JSON está vacío/corrupto
def cargar_estado(archivo):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r") as f:
                return json.load(f)
        except Exception:
            return {}  # Si hay error, empieza con estado vacío
    return {}

def guardar_estado(archivo, estado):
    with open(archivo, "w") as f:
        json.dump(estado, f)

# -- Cargar estado desde un archivo subido --
uploaded_file = st.file_uploader("Subir estado (JSON) para restaurar", type=["json"])
if uploaded_file:
    try:
        estado_subido = json.load(uploaded_file)
        guardar_estado(ARCHIVO_ESTADO, estado_subido)
        st.success("Estado restaurado correctamente. Recarga la página para ver los cambios.")
    except Exception:
        st.error("El archivo subido no es un JSON válido.")

# --- CARGA EL ESTADO PARA EL BOTÓN DE DESCARGA, SIEMPRE ARRIBA ---
# (Lo cargamos ahora para que siempre puedas descargar el último)
estado_temp = cargar_estado(ARCHIVO_ESTADO)
st.download_button(
    label="Descargar estado (JSON)",
    data=json.dumps(estado_temp, indent=2),
    file_name="estado_titulos.json",
    mime="application/json"
)

# -- Resto de la aplicación --
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

# --- Buscador por denominación ---
busqueda = st.text_input("Buscar por denominación:")
if busqueda:
    df = df[df["Denominación"].str.contains(busqueda, case=False, na=False)]

df["Fecha inicio"] = pd.to_datetime(df["Fecha inicio"], errors="coerce")
df["Año"] = df["Fecha inicio"].apply(lambda x: x.year if pd.notnull(x) else "")

# ---- Añadir columna "Mes" (nombre) ----
df["Mes"] = df["Fecha inicio"].apply(
    lambda x: calendar.month_name[x.month].capitalize() if pd.notnull(x) else ""
)

# --- Filtro por año ---
anios_disponibles = sorted(df["Año"].unique())
opciones_filtro = ["Todos"] + [str(a) for a in anios_disponibles if str(a) != ""]
anio_filtro = st.selectbox("Filtrar por año", options=opciones_filtro)
if anio_filtro != "Todos":
    df = df[df["Año"] == int(anio_filtro)]

# --- Filtro múltiple por mes ---
meses_disponibles = [m for m in df["Mes"].unique() if m]
meses_seleccionados = st.multiselect(
    "Filtrar por mes de inicio",
    options=meses_disponibles,
    default=meses_disponibles
)
if meses_seleccionados:
    df = df[df["Mes"].isin(meses_seleccionados)]

if "ascendente" not in st.session_state:
    st.session_state.ascendente = True

if st.button("Ordenar por Fecha de Inicio"):
    st.session_state.ascendente = not st.session_state.ascendente

orden = st.session_state.ascendente
df = df.sort_values(by="Fecha inicio", ascending=orden)
df["Fecha inicio"] = df["Fecha inicio"].apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else "")

# ==== EDITOR DE ESTADO (checkboxes en una línea, con Mes y estilo stripe) ====
estado = cargar_estado(ARCHIVO_ESTADO)

st.markdown("### Edita el estado de los títulos:")
nuevo_estado = estado.copy()
stripe_color = "#f2f4f8"  # Gris claro para stripe

for idx, row in df.iterrows():
    background = stripe_color if idx % 2 == 0 else "#ffffff"
    with st.container():
        st.markdown(
            f"<div style='background-color: {background}; padding: 6px 0 3px 0; border-radius: 6px;'>",
            unsafe_allow_html=True
        )
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 3, 4, 2, 2])
        with col1:
            publicado = st.checkbox(
                "Publicado",
                value=estado.get(str(row["ID"]), {}).get("Publicado", False),
                key=str(row["ID"]) + "_publicado"
            )
        with col2:
            diseno = st.checkbox(
                "Diseño",
                value=estado.get(str(row["ID"]), {}).get("Diseño", False),
                key=str(row["ID"]) + "_diseno"
            )
        with col3:
            st.markdown(f"<span style='color:#003865'><b>{row['Denominación']}</b></span>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"ID Proyecto Docente: <b>{row['ID Proyecto']}</b>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<span style='color:#FF8200'>{row['Fecha inicio']}</span>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<span style='color:#003865'>{row['Mes']}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    nuevo_estado[str(row["ID"])] = {
        "Publicado": publicado,
        "Diseño": diseno
    }

guardar_estado(ARCHIVO_ESTADO, nuevo_estado)

# --- Actualiza el DataFrame con los checks tras la edición ---
df["Publicado"] = df["ID"].apply(lambda x: nuevo_estado.get(str(x), {}).get("Publicado", False))
df["Diseño"] = df["ID"].apply(lambda x: nuevo_estado.get(str(x), {}).get("Diseño", False))

# --- Filtros para "Diseño" y "Publicado" aplicados también a la lista ---
filtro_diseno = st.selectbox(
    "Filtrar por 'Diseño'",
    options=["Todos", "Sí", "No"],
    index=0
)
filtro_publicado = st.selectbox(
    "Filtrar por 'Publicado'",
    options=["Todos", "Sí", "No"],
    index=0
)

if filtro_diseno == "Sí":
    df = df[df["Diseño"] == True]
elif filtro_diseno == "No":
    df = df[df["Diseño"] == False]

if filtro_publicado == "Sí":
    df = df[df["Publicado"] == True]
elif filtro_publicado == "No":
    df = df[df["Publicado"] == False]

# ---- Tabla final, incluye la columna Mes ----
df = df[["ID", "ID Proyecto", "Denominación", "Fecha inicio", "Año", "Mes", "Publicado", "Diseño"]]

def stripe_rows(row):
    return ['background-color: #f2f4f8' if row.name % 2 == 0 else '' for _ in row]

st.dataframe(
    df.style.apply(stripe_rows, axis=1),
    use_container_width=True
)
