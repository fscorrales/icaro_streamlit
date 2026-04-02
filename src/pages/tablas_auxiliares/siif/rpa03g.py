import streamlit as st
from playwright.async_api import async_playwright

from src.automation.siif.rpa03g import Rpa03g
from src.constants.endpoints import Endpoints
from src.constants.options import (
    get_ejercicios_list,
    get_grupos_partidas_siif_list,
)
from src.services.api_client import post_request

# from src.services.models import TipoComprobanteSIIF
from src.views.aux_tables import report_template
from src.views.modals import request_siif_credentials_modal

ENDPONT = Endpoints.SIIF_RPA03G.value
REPORTE = "rpa03g"
GRUPOS = get_grupos_partidas_siif_list()


# --------------------------------------------------
async def run_automation(username: str, password: str) -> None:
    ejercicios = st.session_state.get("ejercicios_" + REPORTE, [])
    grupos = st.session_state.get("grupos_" + REPORTE, [])
    if not ejercicios:
        st.error("No hay ejercicios seleccionados.")
        return

    # Ensure we have a list of integers
    if isinstance(ejercicios, int):
        ejercicios = [ejercicios]

    if isinstance(grupos, int):
        grupos = [grupos]

    async with async_playwright() as p:
        siif = Rpa03g()
        # The Rfondos04 class handles login via SIIFReportManager.login
        await siif.login(
            username=username,
            password=password,
            playwright=p,
            headless=False,
        )
        await siif.go_to_reports()

        results = []
        for ej in ejercicios:
            for grupo in grupos:
                df_clean = await siif.download_and_process_report(
                    ejercicio=ej, grupo_partida=grupo
                )
                if df_clean is not None and not df_clean.empty:
                    # Send to backend
                    json_data = df_clean.to_dict(orient="records")
                    response = post_request(ENDPONT, json_body=json_data)
                    results.append(f"Ejercicio {ej}: {response}")

        await siif.logout()
        return results


# --------------------------------------------------
def render() -> None:

    mis_filtros = [
        {
            "label": "Elija los ejercicios",
            "options": get_ejercicios_list(),
            "query_param": "ejercicio",
            "key": "ejercicios_" + REPORTE,
            "default": get_ejercicios_list()[-1],
        },
        {
            "label": "Elija el Grupo de Partidas",
            "options": GRUPOS,
            "query_param": "grupo",
            "key": "grupos_" + REPORTE,
            "default": GRUPOS,
        },
    ]

    report_template(
        key=REPORTE,
        title="SIIF - Reporte " + REPORTE,
        endpoint=ENDPONT,
        description="Ejecución de Gastos del Ejercicio por Grupo de Partidas",
        filters_config=mis_filtros,
        on_update=lambda: request_siif_credentials_modal(run_automation),
    )
