import streamlit as st
import pandas as pd
from pyathena import connect
import plotly.express as px
import boto3
import csv
from io import StringIO
from datetime import datetime  # Asegurarse de importar datetime

# Configuración de página
st.set_page_config(page_title="Dashboard Financiero", layout="wide")
st.title("📊 Dashboard JHK")

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

# ==============================
# SIDEBAR: FORMULARIO DE NUEVO CLIENTE
# ==============================

st.sidebar.markdown("---")
st.sidebar.header("➕ Añadir nuevo proyecto")

with st.sidebar.form("form_nuevo_proyecto"):
    nuevo_cliente = st.text_input("Cliente")
    nuevo_proyecto = st.text_input("Nombre del Proyecto")
    nuevo_valor = st.number_input("Valor del Proyecto", min_value=0.0)
    nuevo_gasto = st.number_input("Gastado", min_value=0.0)
    submitted = st.form_submit_button("Guardar")  # Botón de envío dentro del formulario

    if submitted:
        nueva_ganancia = nuevo_valor - nuevo_gasto
        nuevo_registro = {
            "cliente": nuevo_cliente,
            "nombre_proyecto": nuevo_proyecto,
            "valor_proyecto": nuevo_valor,
            "gastado": nuevo_gasto,
            "ganancia": nueva_ganancia,
        }
        
        # Guardar el registro en S3 en la ruta correcta
        s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
        bucket_name = "datos-financieros-carlos"
        file_name = "datos.csv"  # Cambiar la ruta

        # Leer el archivo CSV existente desde S3
        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
            csv_data = obj['Body'].read().decode('utf-8').splitlines()
            csv_reader = csv.reader(csv_data)
            existing_data = list(csv_reader)
            st.sidebar.write("Datos existentes leídos correctamente.")
        except s3_client.exceptions.NoSuchKey:
            existing_data = []
            st.sidebar.write("Archivo no encontrado. Creando uno nuevo.")

        # Agregar el nuevo registro
        new_row = [nuevo_cliente, nuevo_proyecto, nuevo_valor, nuevo_gasto, nueva_ganancia]
        existing_data.append(new_row)
        
        # Escribir el archivo actualizado en S3
        output = StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerows(existing_data)
        s3_client.put_object(Body=output.getvalue(), Bucket=bucket_name, Key=file_name)
        
        st.sidebar.success("✅ Proyecto añadido y guardado en S3.")

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
