"""Página: SGF Resumen Rendiciones Proveedores.

Muestra el DataFrame del resumen de rendiciones obtenido vía
GET /sgf/resumenRendProv/ con filtros por ejercicio y origen.
"""

import streamlit as st

from src.constants.endpoints import Endpoints
from src.services.api_client import (
    APIConnectionError,
    APIResponseError,
    fetch_dataframe,
)

ENDPOINT = Endpoints.SGF_RESUMEN_REND_PROV.value

ORIGENES = [None, "EPAM", "OBRAS", "FUNCIONAMIENTO"]


def render() -> None:
    st.markdown("# SGF - Resumen Rendiciones Proveedores")
    st.write(
        "Resumen de rendiciones a proveedores con detalle de "
        "retenciones. Datos del Sistema de Gestión Financiera (SGF)."
    )

    # --- Filtros y Actualización ---
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        ejercicio = st.number_input(
            "Ejercicio",
            min_value=2010,
            max_value=2030,
            value=2025,
            step=1,
        )
    with col2:
        origen = st.selectbox(
            "Origen",
            options=ORIGENES,
            format_func=lambda x: "Todos" if x is None else x,
        )
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Actualizar desde SGF"):
            st.info(
                "Automatización no implementada aún. "
                "Se lanzará el script correspondiente del SGF."
            )

    # --- Carga y visualización de datos ---
    try:
        with st.spinner("Cargando datos de Rendiciones..."):
            df = fetch_dataframe(
                ENDPOINT,
                params={
                    "ejercicio": ejercicio,
                    "origen": origen,
                    "limit": None,
                },
            )

        if df.empty:
            st.info(f"No se encontraron rendiciones para el ejercicio {ejercicio}.")
        else:
            st.write(f"### Registros encontrados: {len(df)}")
            st.dataframe(df, width="stretch")

    except APIConnectionError as e:
        st.error(f"⚠️ Error de conexión: {e}")
    except APIResponseError as e:
        st.error(f"⚠️ Error de API: {e}")
