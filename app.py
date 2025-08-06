import streamlit as st
import pandas as pd
from pyathena import connect
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard Financiero", layout="wide")
st.title("📊 Dashboard Financiero de Clientes")

# Conectar a Athena con credenciales ocultas
aws_access_key = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]

conn = connect(
    s3_staging_dir="s3://datos-financieros-carlos/athena-results/",
    region_name="us-east-1",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

# Consulta automática (tú no escribes nada)
query = "SELECT * FROM test.cuentas"
df = pd.read_sql(query, conn)

# Convertir fechas si hay columna de fecha (opcional)
if 'fecha' in df.columns:
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

# Convertir valores numéricos
for col in ['valor_proyecto', 'gastado', 'ganancia']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Filtros visuales (tú solo eliges del menú)
st.sidebar.header("🔍 Filtros")

clientes = df['cliente'].dropna().unique()
cliente = st.sidebar.selectbox("Cliente", options=["Todos"] + list(clientes))

if 'fecha' in df.columns:
    min_date = df['fecha'].min()
    max_date = df['fecha'].max()
    fecha_inicio = st.sidebar.date_input("Desde", min_value=min_date, value=min_date)
    fecha_fin = st.sidebar.date_input("Hasta", max_value=max_date, value=max_date)

    df = df[(df['fecha'] >= pd.to_datetime(fecha_inicio)) & (df['fecha'] <= pd.to_datetime(fecha_fin))]

if cliente != "Todos":
    df = df[df['cliente'] == cliente]

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("💼 Total Valor Proyectos", f"${df['valor_proyecto'].sum():,.0f}")
col2.metric("💸 Total Gastado", f"${df['gastado'].sum():,.0f}")
col3.metric("💰 Ganancia Total", f"${df['ganancia'].sum():,.0f}")

# Gráfico por cliente
st.subheader("📈 Ganancia por Cliente")
grafico = px.bar(df, x="cliente", y="ganancia", color="cliente", text="ganancia", title="Ganancias")
grafico.update_traces(texttemplate='%{text:$,.0f}', textposition='outside')
grafico.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(grafico, use_container_width=True)

# Mostrar tabla completa
st.subheader("📋 Detalles por Proyecto")
st.dataframe(df, use_container_width=True)
