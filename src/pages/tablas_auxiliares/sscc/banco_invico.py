import os
import subprocess
import sys

import streamlit as st

from src.constants.endpoints import Endpoints
from src.constants.options import get_ejercicios_list
from src.views.aux_tables import report_template
from src.views.modals import request_sscc_credentials_modal

ENDPONT = Endpoints.SSCC_BANCO_INVICO.value
REPORTE = "banco_invico"


# --------------------------------------------------
def run_automation(username: str, password: str) -> None:
    ejercicios = st.session_state.get("ejercicios_" + REPORTE, [])
    if not ejercicios:
        st.error("No hay ejercicios seleccionados.")
        return

    # Ensure we have a list of integers
    if isinstance(ejercicios, int):
        ejercicios = [ejercicios]

    ejercicios_str = ",".join(map(str, ejercicios))

    # En lugar de la ruta al archivo, usamos el nombre del módulo
    # Esto equivale a hacer: python -m src.automation.sscc.banco_invico_runner
    modulo_runner = "src.automation.sscc.banco_invico_runner"

    # Aseguramos que el PYTHONPATH sea la raíz actual
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            modulo_runner,
            username,
            password,
            st.session_state.get("token"),
            ejercicios_str,
        ],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        env=env,
    )
    return process


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
        title="SSCC - Reporte " + REPORTE,
        endpoint=ENDPONT,
        description="",
        filters_config=mis_filtros,
        on_update=lambda: request_sscc_credentials_modal(run_automation),
    )
