from src.constants.endpoints import Endpoints
from src.constants.options import get_ejercicios_list
from src.views.aux_tables import report_template

ENDPONT = Endpoints.ICARO_CARGA.value
REPORTE = "icaro_carga"


# --------------------------------------------------
def render() -> None:

    mis_filtros = [
        {
            "label": "Elija el Ejercicio a consultar",
            "options": get_ejercicios_list(),
            "query_param": "ejercicio",
            "key": "ejercicios_" + REPORTE,
            "default": get_ejercicios_list()[-1],
        },
    ]

    report_template(
        key=REPORTE,
        title="ICARO - Reporte " + REPORTE,
        endpoint=ENDPONT,
        description="Tabla de Carga de Datos en ICARO",
        filters_config=mis_filtros,
        on_update=None,
        has_update=False,  # Asumo que este reporte no necesita actualización manual por ahora
    )
