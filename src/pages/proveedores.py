"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Proveedores Page
"""

import pandas as pd
import streamlit as st

from src.constants import Endpoints
from src.services.api_client import (
    APIConnectionError,
    APIResponseError,
    fetch_dataframe,
)
from src.views import (
    dataframe_with_buttons,
    report_template_without_filters,
)

REPORTE = "proveedores"


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_data(filtro_avanzado: str = ""):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Proveedores
    df = fetch_dataframe(Endpoints.ICARO_PROVEEDORES.value, params=params_peticion)
    if not df.empty:
        df = df.sort_values(["desc_proveedor"], ascending=True)

    return df


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
        df_proveedores = get_data(filtro_actual)

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
