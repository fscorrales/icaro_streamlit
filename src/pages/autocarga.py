"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Autocarga Page
"""

import pandas as pd
import streamlit as st

from src.constants import Endpoints
from src.services import (
    fetch_dataframe,
    post_request,
    process_resumen_rend_obras,
)
from src.utils import APIConnectionError, APIResponseError, read_csv_file
from src.views import (
    dataframe_with_buttons,
    report_template_without_filters,
)

REPORTE_CERTIFICADOS = "certificados"
REPORTE_EPAM = "epam"


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_data_certificados(filtro_avanzado: str = ""):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Certificados
    df = fetch_dataframe(Endpoints.ICARO_CERTIFICADOS.value, params=params_peticion)
    if not df.empty:
        df = df.loc[df["id_carga"] == ""]
        df = df.sort_values(
            ["beneficiario", "desc_obra", "nro_certificado"],
            ascending=True,
        )

    return df


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_data_epam(filtro_avanzado: str = ""):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Certificados
    df = fetch_dataframe(
        Endpoints.ICARO_RESUMEN_REND_OBRAS.value, params=params_peticion
    )
    # if not df.empty:
    #     df = df.loc[df["id_carga"] == ""]
    #     df = df.sort_values(
    #         ["beneficiario", "desc_obra", "nro_certificado"],
    #         ascending=True,
    #     )

    return df


# --------------------------------------------------
def render() -> None:
    tab_certificados, tab_epam = st.tabs(["Certificados", "EPAM"])

    with tab_certificados:
        report_template_without_filters(
            key=REPORTE_CERTIFICADOS,
            title=REPORTE_CERTIFICADOS.capitalize(),
            description="Certificados del INVICO. Utiliza el filtro avanzado para realizar consultas específicas.",
            endpoint=Endpoints.ICARO_CERTIFICADOS.value,
            has_export=True,
        )

        # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
        filtro_actual = st.session_state.get(
            f"{REPORTE_CERTIFICADOS}_advanced_filter", ""
        )

        # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
        try:
            df_certificados = get_data_certificados(filtro_actual)

            if df_certificados.empty:
                st.info("No se encontraron resultados.")

        except APIConnectionError as e:
            st.error(f"⚠️ Error de conexión: {e}")
        except APIResponseError as e:
            st.error(f"⚠️ Error de API: {e}")

        # 4. Mostrar resultados (usando session_state para que no desaparezcan)
        if not df_certificados.empty:
            # Definimos las columnas que NO queremos mostrar
            columnas_a_excluir = ["id_carga", "updated_at", "id"]

            # Generamos el orden dinámico: todas las del DF que no estén en la lista negra
            orden_dinamico = [
                col for col in df_certificados.columns if col not in columnas_a_excluir
            ]

            dataframe_with_buttons(
                df_certificados,
                key=f"{REPORTE_CERTIFICADOS}_df_certificados",
                height=300,
                column_order=orden_dinamico,
            )

        uploaded_file = st.file_uploader(
            f"Cargar CSV de {REPORTE_CERTIFICADOS.capitalize()}",
            type=["csv"],
            key=f"{REPORTE_CERTIFICADOS}_upload_file",
        )
        if uploaded_file:
            pass
            # df = pd.read_csv(uploaded_file)
            # st.session_state[f"data_{key}"] = df

    with tab_epam:
        report_template_without_filters(
            key=REPORTE_EPAM,
            title=REPORTE_EPAM.capitalize(),
            description="Resumen de Rendiciones de Obras EPAM. Utiliza el filtro avanzado para realizar consultas específicas.",
            endpoint=Endpoints.ICARO_CERTIFICADOS.value,
            has_export=True,
        )

        # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
        filtro_actual = st.session_state.get(f"{REPORTE_EPAM}_advanced_filter", "")

        # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
        try:
            df_epam = get_data_epam(filtro_actual)

            if df_epam.empty:
                st.info("No se encontraron resultados.")

        except APIConnectionError as e:
            st.error(f"⚠️ Error de conexión: {e}")
        except APIResponseError as e:
            st.error(f"⚠️ Error de API: {e}")

        # 4. Mostrar resultados (usando session_state para que no desaparezcan)
        if not df_epam.empty:
            # Definimos las columnas que NO queremos mostrar
            columnas_a_excluir = ["id_carga", "updated_at", "id"]

            # Generamos el orden dinámico: todas las del DF que no estén en la lista negra
            orden_dinamico = [
                col for col in df_epam.columns if col not in columnas_a_excluir
            ]

            dataframe_with_buttons(
                df_epam,
                key=f"{REPORTE_EPAM}_df_epam",
                height=250,
                column_order=orden_dinamico,
            )

        uploaded_file = st.file_uploader(
            f"Cargar CSV de {REPORTE_EPAM.capitalize()}",
            type=["csv"],
            key=f"{REPORTE_EPAM}_upload_file",
        )
        if uploaded_file:
            df = read_csv_file(uploaded_file)
            df = process_resumen_rend_obras(df)
            # Validación Visual (El "seguro" del usuario)
            col1, col2, col3 = st.columns(3)
            col1.metric("Filas a procesar", len(df))
            col2.metric("Columnas", len(df.columns))
            col3.info("Validación: OK" if not df.empty else "Error: CSV Vacío")

            with st.expander("Ver vista previa de datos limpios"):
                st.dataframe(df.head(10), width="stretch")

            # Botón de Acción Definitiva
            # Usamos un botón con color 'primary' (rojo/naranja) para indicar acción
            if st.button(
                "🚀 Confirmar y Sincronizar con Base de Datos", type="primary"
            ):
                with st.spinner("Ejecutando script de carga..."):
                    # Transformación final para Mongo
                    registros = df.to_dict(orient="records")

                    res = post_request(
                        Endpoints.ICARO_RESUMEN_REND_OBRAS.value, registros
                    )

                    st.success(
                        f"✅ Sincronización exitosa: {len(registros)} documentos insertados."
                    )
                    st.balloons()  # Un poco de feedback visual nunca viene mal


if __name__ == "__main__":
    render()
