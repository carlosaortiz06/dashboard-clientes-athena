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

# Consulta y carga de datos
query = "SELECT * FROM test.cuentas"
df = pd.read_sql(query, conn)

# Procesamiento
if 'fecha' in df.columns:
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

for col in ['valor_proyecto', 'gastado', 'ganancia']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Validar si hay datos
if df.empty:
    st.warning("⚠️ No hay datos disponibles para mostrar.")
    st.stop()

# ==============================
# SIDEBAR: FILTROS
# ==============================

st.sidebar.header("🔍 Filtros")
filtered_df = df.copy()

# Filtro por Cliente
if 'cliente' in df.columns:
    clientes = sorted(df['cliente'].dropna().unique())
    cliente = st.sidebar.selectbox("Cliente", ["Todos"] + clientes)
    if cliente != "Todos":
        filtered_df = filtered_df[filtered_df['cliente'] == cliente]

# Filtro por Proyecto
if 'nombre_proyecto' in df.columns:
    proyectos = sorted(filtered_df['nombre_proyecto'].dropna().unique())
    proyecto = st.sidebar.selectbox("Proyecto", ["Todos"] + list(proyectos))
    if proyecto != "Todos":
        filtered_df = filtered_df[filtered_df['nombre_proyecto'] == proyecto]

# Filtro por Fecha
if 'fecha' in filtered_df.columns:
    min_date = filtered_df['fecha'].min()
    max_date = filtered_df['fecha'].max()
    fecha_inicio = st.sidebar.date_input("Desde", min_value=min_date, value=min_date)
    fecha_fin = st.sidebar.date_input("Hasta", min_value=min_date, value=max_date)
    filtered_df = filtered_df[
        (filtered_df['fecha'] >= pd.to_datetime(fecha_inicio)) & 
        (filtered_df['fecha'] <= pd.to_datetime(fecha_fin))
    ]

# Mostrar aviso si no hay resultados
if filtered_df.empty:
    st.warning("⚠️ No hay resultados para los filtros seleccionados.")
    st.stop()

# ==============================
# KPIs
# ==============================

st.markdown("### 📌 Indicadores Generales")

col1, col2, col3 = st.columns(3)
col1.metric("💼 Total Valor Proyectos", f"${filtered_df['valor_proyecto'].sum():,.0f}")
col2.metric("💸 Total Gastado", f"${filtered_df['gastado'].sum():,.0f}")
col3.metric("💰 Ganancia Total", f"${filtered_df['ganancia'].sum():,.0f}")

# ==============================
# GRÁFICO DE GANANCIA POR CLIENTE
# ==============================

if 'cliente' in filtered_df.columns and 'ganancia' in filtered_df.columns:
    st.subheader("📈 Ganancia por Cliente")
    fig = px.bar(
        filtered_df.groupby("cliente", as_index=False)["ganancia"].sum(),
        x="cliente",
        y="ganancia",
        color="cliente",
        text="ganancia",
        title="Ganancias por Cliente"
    )
    fig.update_traces(texttemplate='%{text:$,.0f}', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig, use_container_width=True)

# ==============================
# TABLA DE DETALLES
# ==============================

st.subheader("📋 Detalles por Proyecto")
st.dataframe(filtered_df, use_container_width=True)
