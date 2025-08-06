import streamlit as st
import pandas as pd
import boto3
import os
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard de Clientes", layout="wide")

# Conexión a AWS Athena
def cargar_datos_athena():
    session = boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name="us-east-1"
    )

    athena_client = session.client("athena")
    query = """
        SELECT * FROM bd_dashboard.dashboard_clientes
    """
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": "bd_dashboard"},
        ResultConfiguration={"OutputLocation": "s3://resultados-athena-carlos/"}
    )

    execution_id = response["QueryExecutionId"]

    # Esperar que termine la consulta
    state = "RUNNING"
    while state in ["RUNNING", "QUEUED"]:
        response = athena_client.get_query_execution(QueryExecutionId=execution_id)
        state = response["QueryExecution"]["Status"]["State"]

    if state == "SUCCEEDED":
        result = athena_client.get_query_results(QueryExecutionId=execution_id)
        columnas = [col["VarCharValue"] for col in result["ResultSet"]["Rows"][0]["Data"]]
        filas = result["ResultSet"]["Rows"][1:]
        datos = []
        for fila in filas:
            valores = [col.get("VarCharValue", "") for col in fila["Data"]]
            datos.append(valores)
        df = pd.DataFrame(datos, columns=columnas)
        return df
    else:
        st.error("Error al ejecutar la consulta.")
        return pd.DataFrame()

# Cargar datos
df = cargar_datos_athena()

# Asegurar tipos numéricos
for col in ["valor_proyecto", "gastado", "ganancia"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

st.title("📊 Dashboard de Clientes y Proyectos")

# Filtros en la barra lateral
with st.sidebar:
    st.header("🔍 Filtros")
    clientes = df["cliente"].unique().tolist()
    cliente_sel = st.multiselect("Cliente", clientes, default=clientes)

    proyectos = df["nombre_proyecto"].unique().tolist()
    proyecto_sel = st.multiselect("Proyecto", proyectos, default=proyectos)

# Aplicar filtros
filtered_df = df[
    df["cliente"].isin(cliente_sel) &
    df["nombre_proyecto"].isin(proyecto_sel)
]

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("💰 Valor Total", f"${filtered_df['valor_proyecto'].sum():,.2f}")
col2.metric("💸 Total Gastado", f"${filtered_df['gastado'].sum():,.2f}")
col3.metric("📈 Ganancia Total", f"${filtered_df['ganancia'].sum():,.2f}")

st.markdown("---")

# Gráfica de ganancias por cliente
fig = px.bar(
    filtered_df,
    x="cliente",
    y="ganancia",
    color="nombre_proyecto",
    title="Ganancia por Cliente y Proyecto",
    barmode="group"
)
st.plotly_chart(fig, use_container_width=True)

# Tabla de datos filtrados
st.subheader("📄 Detalle de Datos")
st.dataframe(filtered_df, use_container_width=True)

# Añadir nuevo cliente
st.sidebar.markdown("---")
st.sidebar.header("➕ Añadir Nuevo Cliente")

with st.sidebar.form("nuevo_cliente"):
    nuevo_cliente = st.text_input("Cliente")
    nuevo_proyecto = st.text_input("Nombre del Proyecto")
    nuevo_valor = st.number_input("Valor del Proyecto", min_value=0.0, step=100.0)
    nuevo_gasto = st.number_input("Gastado", min_value=0.0, step=100.0)
    submitted = st.form_submit_button("Añadir")

    if submitted and nuevo_cliente and nuevo_proyecto:
        nueva_ganancia = nuevo_valor - nuevo_gasto
        nuevo_registro = pd.DataFrame([{
            "cliente": nuevo_cliente,
            "nombre_proyecto": nuevo_proyecto,
            "valor_proyecto": nuevo_valor,
            "gastado": nuevo_gasto,
            "ganancia": nueva_ganancia
        }])
        df = pd.concat([df, nuevo_registro], ignore_index=True)
        filtered_df = pd.concat([filtered_df, nuevo_registro], ignore_index=True)
        st.sidebar.success("✅ Proyecto añadido (solo en la sesión actual).")

