"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Proveedores Page
"""

import streamlit as st

from src.constants import Endpoints
from src.services import (
    get_proveedores,
)
from src.views import (
    dataframe_with_buttons,
    report_template_without_filters,
)
from src.utils import APIConnectionError, APIResponseError

REPORTE = "proveedores"


# --------------------------------------------------
def render() -> None:
    report_template_without_filters(
        key=REPORTE,
        title=REPORTE.capitalize(),
        description="Proveedores del INVICO. Utiliza el filtro avanzado para realizar consultas específicas.",
        endpoint=Endpoints.ICARO_PROVEEDORES.value,
        has_export=True,
    )

    # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
    filtro_actual = st.session_state.get(f"{REPORTE}_advanced_filter", "")

    # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
    try:
        df_proveedores = get_proveedores(filtro_actual)

        if df_proveedores.empty:
            st.info("No se encontraron resultados.")
        # else:
        #     st.session_state[f"data_{key}_carga"] = df_final
        #     st.session_state[f"data_{key}_retenciones"] = df_final_ret

    except APIConnectionError as e:
        st.error(f"⚠️ Error de conexión: {e}")
    except APIResponseError as e:
        st.error(f"⚠️ Error de API: {e}")

    # 4. Mostrar resultados (usando session_state para que no desaparezcan)
    if not df_proveedores.empty:
        dataframe_with_buttons(
            df_proveedores,
            key=f"{REPORTE}_df_proveedores",
            height=300,
            column_order=[
                "cuit",
                "codigo",
                "desc_proveedor",
                "domicilio",
                "localidad",
                "condicion_iva",
            ],
        )


if __name__ == "__main__":
    render()
