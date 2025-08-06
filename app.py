import streamlit as st
import pandas as pd
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor

# Login simulado
usuarios = {
    "cliente1": "1234",
    "cliente2": "abcd",
}

st.set_page_config(page_title="Dashboard Cliente", layout="wide")
st.title("📊 Dashboard de Cliente")

usuario = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if st.button("Ingresar"):
    if usuario in usuarios and usuarios[usuario] == password:
        st.success(f"Bienvenido, {usuario} ✅")

        try:
            # Conexión con Athena
            conn = connect(
                s3_staging_dir='s3://datos-financieros-carlos/athena-results/',
                region_name='us-east-1',
                cursor_class=PandasCursor
            )

            # Consulta básica por defecto
            query = f"""
            SELECT * 
            FROM test.cuentas
            WHERE LOWER(cliente) = LOWER('{usuario}')
            """

            df = pd.read_sql(query, conn)

            if df.empty:
                st.warning("No se encontraron datos para este cliente.")
            else:
                st.subheader("Datos del Cliente")
                st.dataframe(df)

                col1, col2, col3 = st.columns(3)
                col1.metric("Ganancia", f"${int(df['ganancia'].sum()):,}")
                col2.metric("Gastado", f"${int(df['gastado'].sum()):,}")
                col3.metric("Valor Proyecto", f"${int(df['valor_proyecto'].sum()):,}")

                st.markdown("---")
                st.subheader("Consulta Personalizada 🛠️")

                user_sql = st.text_area(
                    "Escribe tu consulta personalizada sobre `test.cuentas`. Solo se mostrarán resultados de tu usuario.",
                    height=150,
                    placeholder="Ejemplo: SELECT proyecto, ganancia FROM test.cuentas WHERE LOWER(cliente) = LOWER('cliente1') AND ganancia > 10000"
                )

                if st.button("Ejecutar consulta personalizada"):
                    if f"LOWER(cliente) = LOWER('{usuario}')" in user_sql:
                        try:
                            df_custom = pd.read_sql(user_sql, conn)
                            st.success("Consulta ejecutada con éxito ✅")
                            st.dataframe(df_custom)
                        except Exception as e:
                            st.error(f"Error al ejecutar consulta: {e}")
                    else:
                        st.error("⚠️ La consulta debe filtrar por tu usuario.")

        except Exception as e:
            st.error(f"Error al conectar con Athena: {e}")

    else:
        st.error("Usuario o contraseña incorrectos ❌")
