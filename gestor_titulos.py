{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import requests\
import pandas as pd\
import os\
import json\
\
# ----------------- FUNCIONES AUXILIARES -----------------\
def formatear_fecha(valor):\
    try:\
        fecha_obj = pd.to_datetime(valor)\
        return fecha_obj.strftime('%d-%m-%Y')\
    except:\
        return valor\
\
def cargar_tratados(nombre_archivo):\
    if os.path.exists(nombre_archivo):\
        with open(nombre_archivo, 'r') as f:\
            return set(json.load(f))\
    return set()\
\
def guardar_tratados(nombre_archivo, tratados):\
    with open(nombre_archivo, 'w') as f:\
        json.dump(list(tratados), f)\
\
# ----------------- DESCARGA Y PARSEO -----------------\
@st.cache_data\
def obtener_titulos():\
    url = "https://www.cfp.upv.es/cfp-gow/titulaciones/web"\
    response = requests.get(url)\
    data = response.json()\
    titulaciones = data.get("titulaciones", [])\
    cursos_data = []\
    for curso in titulaciones:\
        idcurso = curso.get("idCurso")\
        if idcurso is not None:\
            url_curso = f"https://www.cfp.upv.es/cfp-gow/curso/ficha/\{idcurso\}/es"\
            response_curso = requests.get(url_curso)\
            json_data_curso = response_curso.json()\
            publicidad_data = json_data_curso.pop("publicidad", \{\})\
            for key, value in publicidad_data.items():\
                json_data_curso[f"publicidad_\{key\}"] = value\
            cursos_data.append(json_data_curso)\
    df = pd.DataFrame(cursos_data)\
    # Formatear fechas\
    columnas_fecha = ['fechaInicio', 'fechaFin', 'fechaMatriculaFin', 'fechaMatricula', 'fechaAnulado',\
                      'fechaIniPreinscripcion', 'fechaFinPreinscripcion', 'fechaFinNoLectiva']\
    for col in columnas_fecha:\
        if col in df:\
            df[col] = df[col].apply(formatear_fecha)\
    return df\
\
# ----------------- APP STREAMLIT -----------------\
st.title("Gestor de T\'edtulos Propios")\
\
# Archivo donde guardar el estado de tratados\
ESTADO_ARCHIVO = 'titulos_tratados.json'\
\
# Carga y actualizaci\'f3n de t\'edtulos\
df = obtener_titulos()\
\
# Cargar estado de tratados\
titulos_tratados = cargar_tratados(ESTADO_ARCHIVO)\
\
# Ordenar por fecha de inicio\
df = df.sort_values(by="fechaInicio")\
\
# A\'f1adir columna al principio indicando si est\'e1 tratado\
df.insert(0, "Tratado", df['idCurso'].apply(lambda x: x in titulos_tratados))\
\
# Mostrar tabla con checkboxes para marcar tratados\
st.write("Marca los t\'edtulos ya tratados:")\
\
tratados_nuevos = set(titulos_tratados)\
for idx, row in df.iterrows():\
    key = str(row['idCurso'])\
    tratado = st.checkbox(\
        f"[\{row['fechaInicio']\}] \{row['nombreCurso']\}",\
        value=row["Tratado"],\
        key=key\
    )\
    if tratado:\
        tratados_nuevos.add(row['idCurso'])\
    else:\
        tratados_nuevos.discard(row['idCurso'])\
\
# Guardar el estado actualizado al cerrar\
guardar_tratados(ESTADO_ARCHIVO, tratados_nuevos)\
\
# Mostrar tabla para consulta\
st.dataframe(df)\
\
}