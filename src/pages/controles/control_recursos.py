"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: SIIF Recursos vs SSCC depósitos
Data required:
    - SIIF rci02
    - SSCC Consulta General de Movimiento
    - SSCC ctas_ctes (manual data)
Google Sheet:
    - https://docs.google.com/spreadsheets/d/1u_I5wN3w_rGX6rWIsItXkmwfIEuSox6ZsmKYbMZ2iUY
"""

import streamlit as st

from src.automation.analysis import control_recursos
from src.constants.endpoints import Endpoints
from src.constants.options import get_ejercicios_list
from src.views.aux_tables import report_template
from src.views.modals import request_siif_and_sscc_credentials_modal

ENDPONT = Endpoints.CONTROL_RECURSOS.value
REPORTE = "recursos"


# --------------------------------------------------
async def run_automation(
    siif_username: str, siif_password: str, sscc_username: str, sscc_password: str
) -> None:

    # 1. Obtenemos los ejercicios seleccionados en el estado de sesión
    ejercicios = st.session_state.get("ejercicios_" + REPORTE, [])
    if not ejercicios:
        st.error("No hay ejercicios seleccionados.")
        return

    # Ensure we have a list of integers
    if isinstance(ejercicios, int):
        ejercicios = [ejercicios]

    # 2. Iniciamos la descarga automática
    results = []
    # 2.a. Ejecutamos la automatización de SIIF
    results = await control_recursos.sync_control_recursos_from_siif(
        siif_username=siif_username,
        siif_password=siif_password,
        ejercicios=ejercicios,
    )

    # 2.b. Ejecutamos el módulo runner de SSCC en un proceso separado
    control_recursos.sync_control_recursos_from_sscc(
        sscc_username=sscc_username,
        sscc_password=sscc_password,
        ejercicios=ejercicios,
        token=st.session_state.get("token"),
    )
    results.append("SSCC ejecutado correctamente.")

    # 3. Combinamos las tablas y actualizamos el reporte
    control_recursos.compute_control_recursos(ejercicios=ejercicios)

    return results


# --------------------------------------------------
def render() -> None:

    mis_filtros = [
        {
            "label": "Elija los ejercicios a consultar",
            "options": get_ejercicios_list(),
            "query_param": "ejercicio",
            "key": "ejercicios_" + REPORTE,
            "default": get_ejercicios_list()[-1],
        },
    ]

    report_template(
        key=REPORTE,
        title="Control " + REPORTE.capitalize(),
        endpoint=ENDPONT,
        description="Cruce de recursos SIIF vs Depósitos Bancarios por tipo de recurso y cta. cte.",
        filters_config=mis_filtros,
        on_update=lambda: request_siif_and_sscc_credentials_modal(run_automation),
    )


if __name__ == "__main__":
    render()
