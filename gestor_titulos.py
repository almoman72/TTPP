import streamlit as st
import requests
import pandas as pd
import os
import json

# ----------------- FUNCIONES AUXILIARES -----------------
def formatear_fecha(valor):
    try:
        fecha_obj = pd.to_datetime(valor)
        return fecha_obj.strftime('%d-%m-%Y')
    except:
        return valor

def cargar_tratados(nombre_archivo):
    if os.path.exists(nombre_archivo):
        with open(nombre_archivo, 'r') as f:
            return set(json.load(f))
    return set()

def guardar_tratados(nombre_archivo, tratados):
    with open(nombre_archivo, 'w') as f:
        json.dump(list(tratados), f)

# ----------------- DESCARGA Y PARSEO -----------------
@st.cache_data
def obtener_titulos():
    url = "https://www.cfp.upv.es/cfp-gow/titulaciones/web"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Error descargando datos de la URL principal: {e}")
        return pd.DataFrame()
    titulaciones = data.get("titulaciones", [])
    cursos_data = []
    for curso in titulaciones:
        idcurso = curso.get("idCurso")
        if idcurso is not None:
            url_curso = f"https://www.cfp.upv.es/cfp-gow/curso/ficha/{idcurso}/es"
            try:
                response_curso = requests.get(url_curso)
                response_curso.raise_for_status()
                json_data_curso = response_curso.json()
            except Exception as e:
                st.warning(f"Error descargando datos del curso {idcurso}: {e}")
                continue
            publicidad_data = json_data_curso.pop("publicidad", {})
            for key, value in publicidad_data.items():
                json_data_curso[f"publicidad_{key}"] = value
            # Asegura que idCurso esté como clave en cada curso
            json_data_curso["idCurso"] = idcurso
            cursos_data.append(json_data_curso)
    df = pd.DataFrame(cursos_data)
    # Formatear fechas
    columnas_fecha = ['fechaInicio', 'fechaFin', 'fechaMatriculaFin', 'fechaMatricula', 'fechaAnulado',
                      'fechaIniPreinscripcion', 'fechaFinPreinscripcion', 'fechaFinNoLectiva']
    for col in columnas_fecha:
        if col in df:
            df[col] = df[col].apply(formatear_fecha)
    return df

# ----------------- APP STREAMLIT -----------------
st.title("Gestor de Títulos Propios")

# Archivo donde guardar el estado de tratados
ESTADO_ARCHIVO = 'titulos_tratados.json'

# Carga y actualización de títulos
df = obtener_titulos()

if df.empty:
    st.error("No se han encontrado datos de cursos. Por favor, revisa la fuente o vuelve a intentarlo más tarde.")
    st.stop()

st.write("Columnas en los datos:", df.columns.tolist())

# Cargar estado de tratados
titulos_tratados = cargar_tratados(ESTADO_ARCHIVO)

# Verifica que la columna 'idCurso' existe
if 'idCurso' not in df.columns:
    st.error("La columna 'idCurso' no está en los datos recibidos. No se puede continuar.")
    st.write("Columnas disponibles:", df.columns.tolist())
    st.stop()

# Ordenar por fecha de inicio (si existe)
if "fechaInicio" in df.columns:
    df = df.sort_values(by="fechaInicio")

# Añadir columna al principio indicando si está tratado
df.insert(0, "Tratado", df['idCurso'].apply(lambda x: x in titulos_tratados))

# Mostrar tabla con checkboxes para marcar tratados
st.write("Marca los títulos ya tratados:")

tratados_nuevos = set(titulos_tratados)
for idx, row in df.iterrows():
    key = str(row['idCurso'])
    tratado = st.checkbox(
        f"[{row.get('fechaInicio', '')}] {row.get('nombreCurso', 'Sin nombre')}",
        value=row["Tratado"],
        key=key
    )
    if tratado:
        tratados_nuevos.add(row['idCurso'])
    else:
        tratados_nuevos.discard(row['idCurso'])

# Guardar el estado actualizado al cerrar
guardar_tratados(ESTADO_ARCHIVO, tratados_nuevos)

# Mostrar tabla para consulta
st.dataframe(df)
