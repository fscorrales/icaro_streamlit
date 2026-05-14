"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Programas Page
"""

from datetime import datetime

import streamlit as st

from src.constants import Endpoints
from src.services.data_fetcher import get_estructuras
from src.utils import APIConnectionError, APIResponseError
from src.views import (
    dataframe_with_buttons,
    modal_delete_registro_gral,
    modal_estructura,
    report_template_without_filters,
)

REPORTE = "proyectos"


# --------------------------------------------------
def add_estructura():
    modal_estructura(
        key_prefix=f"add_estructura_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        len_estructura=8,
    )


# --------------------------------------------------
def edit_estructura(datos_edicion: dict):
    modal_estructura(
        key_prefix=f"edit_estructura_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        datos_carga=datos_edicion,
        len_estructura=8,
        es_edicion=True,
    )


# --------------------------------------------------
def delete_estructura(datos_eliminar: dict):
    modal_delete_registro_gral(
        endpoint=f"{Endpoints.ICARO_ESTRUCTURAS.value}/delete_one/{datos_eliminar['id']}",
        desc_registro=f"con la estructura {datos_eliminar['estructura']} denominado {datos_eliminar['desc_estructura']}",
        session_state_update_key="estructuras_uploader_iteration",
        key_prefix=f"delete_estructura_{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )


# --------------------------------------------------
def render() -> None:
    report_template_without_filters(
        key=REPORTE,
        title=REPORTE.capitalize(),
        description="Proyectos Presupuestarios del INVICO. Utiliza el filtro avanzado para realizar consultas específicas.",
        endpoint=Endpoints.ICARO_ESTRUCTURAS.value,
        has_export=True,
    )

    # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
    filtro_actual = st.session_state.get(f"{REPORTE}_advanced_filter", "")

    # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
    try:
        df = get_estructuras(
            filtro_actual,
            update_trigger=st.session_state.estructuras_uploader_iteration,
        )
        df = df[df["estructura"].str.len() == 8]

        if df.empty:
            st.info("No se encontraron resultados.")
        # else:
        #     st.session_state[f"data_{key}_carga"] = df_final
        #     st.session_state[f"data_{key}_retenciones"] = df_final_ret

    except APIConnectionError as e:
        st.error(f"⚠️ Error de conexión: {e}")
    except APIResponseError as e:
        st.error(f"⚠️ Error de API: {e}")

    # 4. Mostrar resultados (usando session_state para que no desaparezcan)
    if not df.empty:
        dataframe_with_buttons(
            df,
            key=f"{REPORTE}_df_subprogramas",
            height=300,
            column_order=["estructura", "desc_estructura"],
            selection_mode="single-row",
            add_func=add_estructura,
            edit_func=edit_estructura,
            delete_func=delete_estructura,
        )


if __name__ == "__main__":
    render()
