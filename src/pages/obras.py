"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Obras Page
"""

import pandas as pd
import streamlit as st

from src.components import (
    button_export,
    text_input_advance_filter,
)
from src.constants import Endpoints
from src.services.api_client import (
    APIConnectionError,
    APIResponseError,
    fetch_dataframe,
    fetch_excel_stream,
)
from src.views import (
    dataframe_with_buttons,
    params_preparation,
    report_template_without_filters,
)

REPORTE = "obras"


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_data(filtro_avanzado: str = ""):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Obras
    df = fetch_dataframe(Endpoints.ICARO_OBRAS.value, params=params_peticion)
    if not df.empty:
        df = df.sort_values(
            ["actividad", "partida", "fuente", "desc_obra"], ascending=True
        )

    return df


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
        df_obras = get_data(filtro_actual)

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
        dataframe_with_buttons(df_obras, key=f"{REPORTE}_df_obras", height=300)


# # --------------------------------------------------
# def render() -> None:

#     icaro_obras_template(
#         key=REPORTE,
#         title=REPORTE.capitalize(),
#         description="Bienvenido a ICARO, el sistema de control de ejecución presupuestaria de obras del INVICO. Utiliza los filtros para seleccionar los ejercicios que deseas consultar.",
#     )


# @st.fragment  # Permite que los filtros internos no recarguen TODA la página
# # --------------------------------------------------
# def icaro_obras_template(
#     key: str,
#     title: str,
#     description: str,
# ):
#     st.markdown(f"# {title}")
#     st.write(description)

#     # 0. Lógica de Exportación
#     def download_file():
#         # Validamos filtros antes de proceder
#         try:
#             # Limpiamos basura anterior antes de empezar el proceso pesado
#             if f"temp_file_{key}" in st.session_state:
#                 del st.session_state[f"temp_file_{key}"]
#             with st.spinner("Preparando archivos Excel..."):
#                 # Llamada a la API que devuelve StreamingResponse
#                 excel_binario = fetch_excel_stream(
#                     f"{Endpoints.ICARO_OBRAS.value}/export",
#                     params_preparation(filtro_avanzado=filtro_avanzado),
#                 )

#                 if excel_binario:
#                     # IMPORTANTE: Como st.download_button recarga la página,
#                     # a veces es mejor usar un link o guardarlo en session_state
#                     st.session_state[f"temp_file_{key}"] = excel_binario
#                     st.success("✅ Archivo generado con éxito.")
#                     st.rerun()

#         except Exception as e:
#             st.error(f"Error al exportar: {e}")

#     # 1. Renderizar Filtros
#     # --- Filtros (Estado local del componente) ---
#     with st.container(horizontal=True, vertical_alignment="bottom"):
#         filtro_avanzado = text_input_advance_filter(
#             key="text_input_advance_filter-" + key
#         )

#         # Aquí podrías integrar tu logic de exportación
#         if f"temp_file_{key}" not in st.session_state:
#             if button_export("Exportar a Excel", key=f"button_export_{key}"):
#                 download_file()
#         else:
#             # Si hay archivo, el botón "Exportar" desaparece y aparece el de "Descargar"
#             st.download_button(
#                 label="📥 GUARDAR EXCEL",
#                 data=st.session_state[f"temp_file_{key}"],
#                 file_name=f"reporte_{key}.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 key=f"btn_dl_{key}",
#                 type="primary",  # Lo ponemos en color para que resalte
#                 on_click=lambda: st.session_state.pop(f"temp_file_{key}"),
#             )

#     # 3. Lógica de Fetch Iterativo (El equivalente al v-for de Vue + API calls)
#     try:
#         df_obras = get_data(filtro_avanzado)

#         if df_obras.empty:
#             st.info("No se encontraron resultados.")
#         # else:
#         #     st.session_state[f"data_{key}_carga"] = df_final
#         #     st.session_state[f"data_{key}_retenciones"] = df_final_ret

#     except APIConnectionError as e:
#         st.error(f"⚠️ Error de conexión: {e}")
#     except APIResponseError as e:
#         st.error(f"⚠️ Error de API: {e}")

#     # 4. Mostrar resultados (usando session_state para que no desaparezcan)
#     if not df_obras.empty:
#         dataframe_with_buttons(df_obras, key=f"{key}_df_obras", height=300)


if __name__ == "__main__":
    render()
