"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Home Page
"""

import pandas as pd
import streamlit as st

from src.components import (
    button_export,
    dataframe,
    multiselect_filter,
    text_input_advance_filter,
)

# from src.components.buttons import button_export
# from src.components.dataframes import dataframe
# from src.components.multiselects import multiselect_filter
# from src.components.text_inputs import text_input_advance_filter
from src.constants.endpoints import Endpoints
from src.constants.options import get_ejercicios_list
from src.services.api_client import (
    APIConnectionError,
    APIResponseError,
    fetch_dataframe,
    fetch_excel_stream,
)
from src.views.aux_tables import params_preparation

REPORTE = "home"


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_data_carga(selections: list, filtro_avanzado: str = ""):
    df_carga = pd.DataFrame()
    df_ret = pd.DataFrame()

    params_peticion = params_preparation(
        selections, filtro_avanzado
    )  # Preparamos los parámetros para la API

    # Hacemos el fetch individual
    # Tabla CARGA
    df_carga = fetch_dataframe(Endpoints.ICARO_CARGA.value, params=params_peticion)

    # Tabla Retenciones
    df_ret = fetch_dataframe(Endpoints.ICARO_RETENCIONES.value, params=params_peticion)

    return df_carga, df_ret


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

    icaro_carga_template(
        key=REPORTE,
        title=REPORTE.capitalize(),
        description="Bienvenido a ICARO, el sistema de control de ejecución presupuestaria de obras del INVICO. Utiliza los filtros para seleccionar los ejercicios que deseas consultar.",
        filters_config=mis_filtros,
    )


@st.fragment  # Permite que los filtros internos no recarguen TODA la página
# --------------------------------------------------
def icaro_carga_template(
    key: str,
    title: str,
    description: str,
    filters_config: list,
):
    """
    Vista reutilizable.
    filters_config: Lista de dicts con ['label', 'options', 'key', 'default']
    """
    st.markdown(f"# {title}")
    st.write(description)

    selections = []

    # 0. Lógica de Exportación
    def download_file():
        # Validamos filtros antes de proceder
        if all(s[1] is not None for s in selections):
            try:
                # Limpiamos basura anterior antes de empezar el proceso pesado
                if f"temp_file_{key}" in st.session_state:
                    del st.session_state[f"temp_file_{key}"]
                with st.spinner("Preparando archivos Excel..."):
                    # Llamada a la API que devuelve StreamingResponse
                    excel_binario = fetch_excel_stream(
                        f"{Endpoints.ICARO_CARGA.value}/export",
                        params_preparation(selections, filtro_avanzado),
                    )

                    if excel_binario:
                        # IMPORTANTE: Como st.download_button recarga la página,
                        # a veces es mejor usar un link o guardarlo en session_state
                        st.session_state[f"temp_file_{key}"] = excel_binario
                        st.success("✅ Archivo generado con éxito.")
                        st.rerun()

            except Exception as e:
                st.error(f"Error al exportar: {e}")

    # 1. Renderizar Filtros
    # --- Filtros (Estado local del componente) ---
    with st.container(horizontal=True, vertical_alignment="bottom"):
        for i, f_conf in enumerate(filters_config):
            # Guardamos la selección en un diccionario para la API
            val = multiselect_filter(
                label=f_conf["label"],
                options=f_conf["options"],
                default=f_conf.get("default", []),
                key=f_conf["key"],  # Key única para evitar conflictos en Streamlit
            )
            # El nombre de la clave aquí debe coincidir con lo que espera tu API
            selections.append((f_conf["query_param"], val))

        filtro_avanzado = text_input_advance_filter(
            key="text_input_advance_filter-" + key
        )

        # Aquí podrías integrar tu logic de exportación
        if f"temp_file_{key}" not in st.session_state:
            if button_export("Exportar a Excel y GS", key=f"button_export_{key}"):
                download_file()
        else:
            # Si hay archivo, el botón "Exportar" desaparece y aparece el de "Descargar"
            st.download_button(
                label="📥 GUARDAR EXCEL",
                data=st.session_state[f"temp_file_{key}"],
                file_name=f"reporte_{key}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"btn_dl_{key}",
                type="primary",  # Lo ponemos en color para que resalte
                on_click=lambda: st.session_state.pop(f"temp_file_{key}"),
            )

    # 2. Validar que no haya filtros vacíos
    if any(not s[1] for s in selections):
        st.warning(
            "Seleccione al menos un valor en cada filtro obligatorio. El filtro avanzado es opcional"
        )
        return

    # 3. Lógica de Fetch Iterativo (El equivalente al v-for de Vue + API calls)
    try:
        df_carga, df_ret = get_data_carga(selections, filtro_avanzado)

        if df_carga.empty:
            st.info("No se encontraron resultados.")
        # else:
        #     st.session_state[f"data_{key}_carga"] = df_final
        #     st.session_state[f"data_{key}_retenciones"] = df_final_ret

    except APIConnectionError as e:
        st.error(f"⚠️ Error de conexión: {e}")
    except APIResponseError as e:
        st.error(f"⚠️ Error de API: {e}")

    # 4. Mostrar resultados (usando session_state para que no desaparezcan)
    if not df_carga.empty:
        with st.container(horizontal=False, border=True, width="stretch"):
            event = dataframe(
                df_carga,
                key=f"df_carga_{key}",
                height=200,
                on_select="rerun",
                selection_mode="single-row",
                column_order=[
                    "mes",
                    "fecha",
                    "id_carga",
                    # "nro_comprobante",
                    "tipo",
                    "fuente",
                    "cta_cte",
                    "importe",
                    "desc_obra",
                    # "fondo_reparo",
                    "avance",
                    "nro_certificado",
                    "cuit",
                    "origen",
                ],
                column_config={
                    "fecha": st.column_config.DateColumn(
                        "fecha",
                        format="DD/MM/YYYY",  # O el formato que prefieras
                    ),
                    "nro_certificado": st.column_config.TextColumn("cert"),
                },
            )
            with st.container(horizontal=True, border=False, width="stretch"):
                if st.button("Autocarga", key=f"btn_autocarga_df_carga_{key}"):
                    pass
                if st.button("Carga Manual", key=f"btn_carga_manual_df_carga_{key}"):
                    pass
                if st.button("Editar", key=f"btn_editar_carga_df_carga_{key}"):
                    pass
                if st.button("Borrar", key=f"btn_borrar_df_carga_{key}"):
                    pass

        # 2. Lógica de filtrado dinámico
        # Verificamos si hay alguna fila seleccionada
        if len(event.selection.rows) > 0:
            selected_row_index = event.selection.rows[0]
            # Extraemos el id_carga de esa fila
            selected_id = df_carga.iloc[selected_row_index]["id_carga"]

            # st.info(f"Mostrando detalles para ID Carga: **{selected_id}**")
            df_ret_filtrado = df_ret[df_ret["id_carga"] == selected_id]
            df_carga_filtrado = df_carga[df_carga["id_carga"] == selected_id]
            with st.container(horizontal=True, border=False, width="stretch"):
                with st.container(horizontal=False, border=True, width="stretch"):
                    dataframe(
                        df_carga_filtrado,
                        key=f"df_imp_{key}",
                        height=150,
                        column_order=[
                            "actividad",
                            "partida",
                            "importe",
                        ],
                    )
                    with st.container(horizontal=True, border=False, width="stretch"):
                        if st.button("Agregar", key=f"btn_agregar_df_imp_{key}"):
                            pass
                        if st.button("Editar", key=f"btn_editar_df_imp_{key}"):
                            pass
                        if st.button("Borrar", key=f"btn_borrar_df_imp_{key}"):
                            pass
                with st.container(horizontal=False, border=True, width="stretch"):
                    dataframe(
                        df_ret_filtrado,
                        key=f"df_ret_{key}",
                        height=150,
                        column_order=[
                            "codigo",
                            "importe",
                        ],
                    )
                    with st.container(horizontal=True, border=False, width="stretch"):
                        if st.button("Agregar", key=f"btn_agregar_df_ret_{key}"):
                            pass
                        if st.button("Editar", key=f"btn_editar_df_ret_{key}"):
                            pass
                        if st.button("Borrar", key=f"btn_borrar_df_ret_{key}"):
                            pass


if __name__ == "__main__":
    render()
