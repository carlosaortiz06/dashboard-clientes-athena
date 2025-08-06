import streamlit as st
import pandas as pd
from pyathena import connect
import plotly.express as px
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Dashboard Financiero", layout="wide")
st.title("📊 Dashboard Financiero de Clientes")

# Conectar a Athena
aws_access_key = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]

conn = connect(
    s3_staging_dir="s3://datos-financieros-carlos/athena-results/",
    region_name="us-east-1",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

# Consulta de datos
query = "SELECT * FROM test.cuentas"
df = pd.read_sql(query, conn)

# Procesamiento de datos
if 'fecha' in df.columns:
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

for col in ['valor_proyecto', 'gastado', 'ganancia']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Validación de datos
if df.empty:
    st.warning("⚠️ No hay datos disponibles.")
    st.stop()

# ==============================
# SIDEBAR: FILTROS
# ==============================

st.sidebar.header("🔍 Filtros")
filtered_df = df.copy()

# Filtro Cliente
clientes = sorted(df['cliente'].dropna().unique().tolist())
cliente_seleccionado = st.sidebar.selectbox("Cliente", ["Todos"] + clientes)

if cliente_seleccionado != "Todos":
    filtered_df = filtered_df[filtered_df['cliente'] == cliente_seleccionado]

# Filtro Proyecto
proyectos = sorted(filtered_df['nombre_proyecto'].dropna().unique().tolist())
proyecto_seleccionado = st.sidebar.selectbox("Proyecto", ["Todos"] + proyectos)

if proyecto_seleccionado != "Todos":
    filtered_df = filtered_df[filtered_df['nombre_proyecto'] == proyecto_seleccionado]

# Filtro Fecha
if 'fecha' in filtered_df.columns and not filtered_df['fecha'].isnull().all():
    min_fecha = filtered_df['fecha'].min()
    max_fecha = filtered_df['fecha'].max()
    fecha_inicio = st.sidebar.date_input("Desde", min_value=min_fecha, value=min_fecha)
    fecha_fin = st.sidebar.date_input("Hasta", min_value=min_fecha, value=max_fecha)
    filtered_df = filtered_df[
        (filtered_df['fecha'] >= pd.to_datetime(fecha_inicio)) &
        (filtered_df['fecha'] <= pd.to_datetime(fecha_fin))
    ]

# Filtro Ganancia
if 'ganancia' in filtered_df.columns and not filtered_df['ganancia'].isnull().all():
    ganancia_min = int(filtered_df['ganancia'].min())
    ganancia_max = int(filtered_df['ganancia'].max())
    rango = st.sidebar.slider("Rango de Ganancia", ganancia_min, ganancia_max, (ganancia_min, ganancia_max))
    filtered_df = filtered_df[filtered_df['ganancia'].between(rango[0], rango[1])]

# Validar después de aplicar filtros
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
