import streamlit as st
import pandas as pd
from pyathena import connect
import plotly.express as px
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Dashboard Financiero", layout="wide")
st.title("📊 Dashboard Financiero de Clientes")

# Conectar a Athena con variables secretas
aws_access_key = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]

conn = connect(
    s3_staging_dir="s3://datos-financieros-carlos/athena-results/",
    region_name="us-east-1",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

# Cargar datos
query = "SELECT * FROM test.cuentas"
df = pd.read_sql(query, conn)

# Procesamiento de datos
if 'fecha' in df.columns:
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

for col in ['valor_proyecto', 'gastado', 'ganancia']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Validar si hay datos
if df.empty:
    st.warning("⚠️ No hay datos disponibles para mostrar.")
    st.stop()

# Sidebar - Filtros
st.sidebar.header("🔍 Filtros")

# Cliente
if 'cliente' in df.columns:
    clientes = df['cliente'].dropna().unique()
    cliente = st.sidebar.selectbox("Cliente", ["Todos"] + list(clientes))
    if cliente != "Todos":
        df = df[df['cliente'] == cliente]

# Nombre proyecto
if 'nombre_proyecto' in df.columns:
    proyectos = df['nombre_proyecto'].dropna().unique()
    proyecto = st.sidebar.selectbox("Proyecto", ["Todos"] + list(proyectos))
    if proyecto != "Todos":
        df = df[df['nombre_proyecto'] == proyecto]

# Fecha
if 'fecha' in df.columns:
    min_date = df['fecha'].min()
    max_date = df['fecha'].max()
    fecha_inicio = st.sidebar.date_input("Desde", min_value=min_date, value=min_date)
    fecha_fin = st.sidebar.date_input("Hasta", max_value=max_date, value=max_date)
    df = df[(df['fecha'] >= pd.to_datetime(fecha_inicio)) & (df['fecha'] <= pd.to_datetime(fecha_fin))]

# Rango de ganancia
if 'ganancia' in df.columns:
    min_g = int(df['ganancia'].min())
    max_g = int(df['ganancia'].max())
    rango_ganancia = st.sidebar.slider("Rango de Ganancia", min_value=min_g, max_value=max_g, value=(min_g, max_g))
    df = df[df['ganancia'].between(rango_ganancia[0], rango_ganancia[1])]

# Mostrar aviso si no hay resultados
if df.empty:
    st.warning("⚠️ No hay resultados para los filtros seleccionados.")
    st.stop()

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("💼 Total Valor Proyectos", f"${df['valor_proyecto'].sum():,.0f}" if 'valor_proyecto' in df.columns else "N/A")
col2.metric("💸 Total Gastado", f"${df['gastado'].sum():,.0f}" if 'gastado' in df.columns else "N/A")
col3.metric("💰 Ganancia Total", f"${df['ganancia'].sum():,.0f}" if 'ganancia' in df.columns else "N/A")

# Gráfico
if 'cliente' in df.columns and 'ganancia' in df.columns:
    st.subheader("📈 Ganancia por Cliente")
    fig = px.bar(
        df,
        x="cliente",
        y="ganancia",
        color="cliente",
        text="ganancia",
        title="Ganancias por Cliente"
    )
    fig.update_traces(texttemplate='%{text:$,.0f}', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig, use_container_width=True)

# Tabla
st.subheader("📋 Detalles por Proyecto")
st.dataframe(df, use_container_width=True)
