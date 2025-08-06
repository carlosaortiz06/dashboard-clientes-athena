import streamlit as st
import pandas as pd
from pyathena import connect

# Título
st.title("📊 Dashboard de Administración - Clientes")

# Conexión a Athena
conn = connect(
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    s3_staging_dir='s3://datos-financieros-carlos/athena-results/',
    region_name=st.secrets["AWS_REGION"]
)

# Consulta a la tabla completa
query = "SELECT * FROM test.cuentas"
df = pd.read_sql(query, conn)

# Mostrar tabla completa
st.subheader("🔎 Datos completos")
st.dataframe(df)

# Métricas generales
st.subheader("📈 Métricas Generales")
st.metric("💰 Ganancia total", f"${int(df['ganancia'].sum()):,}")
st.metric("💸 Total Gastado", f"${int(df['gastado'].sum()):,}")
st.metric("📦 Valor total de proyectos", f"${int(df['valor_proyecto'].sum()):,}")

# Gráfico: Ganancia por cliente
st.subheader("📊 Ganancia por cliente")
ganancia_por_cliente = df.groupby("cliente")["ganancia"].sum().reset_index()
st.bar_chart(ganancia_por_cliente.set_index("cliente"))

# Gráfico: Ganancia por mes (si tienes una columna "fecha")
if "fecha" in df.columns:
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['mes'] = df['fecha'].dt.to_period('M')
    ganancia_por_mes = df.groupby("mes")["ganancia"].sum().reset_index()
    st.subheader("📅 Ganancia mensual")
    st.line_chart(ganancia_por_mes.set_index("mes"))

# Consulta personalizada (opcional)
st.subheader("🛠 Consulta SQL personalizada (opcional)")
user_query = st.text_area("Escribe una consulta SQL (ej: SELECT * FROM test.cuentas WHERE cliente = 'cliente1')")
if st.button("Ejecutar consulta"):
    try:
        df_custom = pd.read_sql(user_query, conn)
        st.dataframe(df_custom)
    except Exception as e:
        st.error(f"Error en la consulta: {e}")
