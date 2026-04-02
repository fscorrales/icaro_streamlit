from src.constants.endpoints import Endpoints
from src.constants.options import get_ctas_ctes_list
from src.views.aux_tables import report_template

ENDPONT = Endpoints.CTAS_CTES.value
REPORTE = "ctas_ctes"


# --------------------------------------------------
def render() -> None:

    mis_filtros = [
        {
            "label": "Elija la Cta. Cte. a consultar",
            "options": get_ctas_ctes_list(),
            "query_param": "cta_cte",
            "key": "ctas_ctes_" + REPORTE,
            "default": None,
        },
    ]

    report_template(
        key=REPORTE,
        title="SSCC - Reporte " + REPORTE,
        endpoint=ENDPONT,
        description="Unificador de Cuentas Corrientes",
        filters_config=mis_filtros,
        on_update=None,
        has_export=False,  # Asumo que este reporte no tiene exportación por ahora
        has_update=False,  # Asumo que este reporte no necesita actualización manual por ahora
        allow_no_filters=True,  # Permitimos que el usuario deje este filtro vacío
    )
