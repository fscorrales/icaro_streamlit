"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Home Page
"""

from src.constants.endpoints import Endpoints
from src.constants.options import get_ejercicios_list
from src.views.aux_tables import report_template

ENDPONT = Endpoints.ICARO_CARGA.value
REPORTE = "home"


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
        on_update=None,
        has_update=False,
    )


if __name__ == "__main__":
    render()
