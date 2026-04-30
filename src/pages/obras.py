"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Obras Page
"""

from datetime import datetime

import streamlit as st

from src.constants import Endpoints
from src.services import get_obras
from src.utils import APIConnectionError, APIResponseError
from src.views import (
    dataframe_with_buttons,
    modal_obras,
    report_template_without_filters,
)

REPORTE = "obras"


# --------------------------------------------------
def add_obra():
    modal_obras(key_prefix=f"add_obra_{datetime.now().strftime('%Y%m%d%H%M%S')}")


# --------------------------------------------------
def edit_obra(datos_edicion: dict):
    modal_obras(
        key_prefix=f"edit_obra_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        datos_carga=datos_edicion,
        es_edicion=True,
    )


# --------------------------------------------------
def render() -> None:
    report_template_without_filters(
        key=REPORTE,
        title=REPORTE.capitalize(),
        description="Obras del INVICO. Utiliza el filtro avanzado para realizar consultas específicas.",
        endpoint=Endpoints.ICARO_OBRAS.value,
        has_export=True,
    )

    # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
    filtro_actual = st.session_state.get(f"{REPORTE}_advanced_filter", "")

    # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
    try:
        df_obras = get_obras(filtro_actual)

        if df_obras.empty:
            st.info("No se encontraron resultados.")
        # else:
        #     st.session_state[f"data_{key}_carga"] = df_final
        #     st.session_state[f"data_{key}_retenciones"] = df_final_ret

    except APIConnectionError as e:
        st.error(f"⚠️ Error de conexión: {e}")
    except APIResponseError as e:
        st.error(f"⚠️ Error de API: {e}")

    # 4. Mostrar resultados (usando session_state para que no desaparezcan)
    if not df_obras.empty:
        dataframe_with_buttons(
            df_obras,
            key=f"{REPORTE}_df_obras",
            height=300,
            column_order=[
                "actividad",
                "partida",
                "fuente",
                "desc_obra",
                "cuit",
                "cta_cte",
                "norma_legal",
                "localidad",
                "info_adicional",
            ],
            add_func=add_obra,
            edit_func=edit_obra,
        )


if __name__ == "__main__":
    render()
