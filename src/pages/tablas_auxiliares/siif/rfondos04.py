import streamlit as st
from playwright.async_api import async_playwright

from src.automation.siif.rfondos04 import Rfondos04
from src.constants.endpoints import Endpoints
from src.constants.options import get_ejercicios_list, get_tipos_comprobantes_siif_list
from src.services.api_client import post_request

# from src.services.models import TipoComprobanteSIIF
from src.views.aux_tables import report_template
from src.views.modals import request_siif_credentials_modal

ENDPONT = Endpoints.SIIF_RFONDOS04.value
REPORTE = "rfondos04"
TIPOS_COMPROBANTES = get_tipos_comprobantes_siif_list()


# --------------------------------------------------
async def run_automation(username: str, password: str) -> None:
    ejercicios = st.session_state.get("ejercicios_" + REPORTE, [])
    if not ejercicios:
        st.error("No hay ejercicios seleccionados.")
        return

    # Ensure we have a list of integers
    if isinstance(ejercicios, int):
        ejercicios = [ejercicios]

    async with async_playwright() as p:
        siif = Rfondos04()
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
            df_clean = await siif.download_and_process_report(ejercicio=ej)
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
            "label": "Elija el tipo de comprobante",
            "options": TIPOS_COMPROBANTES,
            "query_param": "tipoComprobante",
            "key": "tipos_comprobante_" + REPORTE,
            "default": "REV",
        },
    ]

    report_template(
        key=REPORTE,
        title="SIIF - Reporte " + REPORTE,
        endpoint=ENDPONT,
        description="Listado de Fondos del Ejercicio por Tipo de Comprobante",
        filters_config=mis_filtros,
        on_update=lambda: request_siif_credentials_modal(run_automation),
    )
