__all__ = [
    "report_template",
    "params_preparation",
    "dataframe_with_buttons",
    "dataframe_home_carga",
]

from typing import Any, Optional

import pandas as pd
import streamlit as st

from src.components import (
    button_add,
    button_delete,
    button_edit,
    button_export,
    button_selfadd,
    button_update,
    dataframe,
    multiselect_filter,
    text_input_advance_filter,
)
from src.services.api_client import (
    APIConnectionError,
    APIResponseError,
    fetch_dataframe,
    fetch_excel_stream,
)


# --------------------------------------------------
def params_preparation(selections: list, filtro_avanzado: str):
    """
    Función auxiliar para preparar los parámetros de la API a partir de las selecciones y el filtro avanzado.
    Devuelve un diccionario listo para ser usado en la petición.
    """
    params_peticion = {"limit": 0, "queryFilter": filtro_avanzado}

    for nombre_param, valores in selections:
        if valores:
            params_peticion[nombre_param] = ",".join(map(str, valores))

    return params_peticion


@st.fragment  # Permite que los filtros internos no recarguen TODA la página
# --------------------------------------------------
def report_template(
    key: str,
    title: str,
    endpoint: str,
    description: str,
    filters_config: list,
    on_update: Optional[Any] = None,
    allow_no_filters: bool = False,
    has_update: bool = True,
    has_export: bool = True,
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
                        f"{endpoint}/export",
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

        if has_update:
            if button_update("Actualizador automático", key=f"button_update_{key}"):
                if on_update:
                    on_update()

        if has_export:
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
    if not allow_no_filters:
        if any(not s[1] for s in selections):
            st.warning(
                "Seleccione al menos un valor en cada filtro obligatorio. El filtro avanzado es opcional"
            )
            return

    # 3. Lógica de Fetch Iterativo (El equivalente al v-for de Vue + API calls)
    try:
        with st.spinner("Consultando datos..."):
            df_final = fetch_dataframe(
                endpoint, params=params_preparation(selections, filtro_avanzado)
            )

            if df_final is None or df_final.empty:
                st.info("No se encontraron resultados.")
                st.session_state[f"data_{key}"] = (
                    pd.DataFrame()
                )  # Evita errores de 'None' después
            else:
                st.session_state[f"data_{key}"] = df_final

    except APIConnectionError as e:
        st.error(f"⚠️ Error de conexión: {e}")
    except APIResponseError as e:
        st.error(f"⚠️ Error de API: {e}")

    # 4. Mostrar resultados (usando session_state para que no desaparezcan)
    data_key = f"data_{key}"
    if data_key in st.session_state:
        dataframe(st.session_state[data_key], key=f"df_{key}")
        # st.dataframe(st.session_state[data_key], width="stretch")


# --------------------------------------------------
def dataframe_with_buttons(
    df: pd.DataFrame,
    key: str = "df_with_btns",
    height: int = 150,
    column_order: list = [],
    **kwargs,
):

    with st.container(horizontal=False, border=True, width="stretch"):
        dataframe(df, key=f"{key}", height=height, column_order=column_order, **kwargs)
        with st.container(
            horizontal=True,
            border=False,
            width="stretch",
            horizontal_alignment="center",
            gap="medium",
        ):
            if button_add("Agregar", key=f"btn_add_{key}", type="primary"):
                pass
            if button_edit("Editar", key=f"btn_edit_{key}"):
                pass
            if button_delete("Borrar", key=f"btn_delete_{key}"):
                pass


# --------------------------------------------------
def dataframe_home_carga(
    df_carga: pd.DataFrame, key: str = "df_home_carga", height: int = 200, **kwargs
):
    with st.container(
        horizontal=False,
        border=True,
        width="stretch",
    ):
        event = dataframe(
            df_carga,
            key=f"df_carga_{key}",
            height=height,
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
            **kwargs,
        )
        with st.container(
            horizontal=True,
            border=False,
            width="stretch",
            horizontal_alignment="center",
            gap="medium",
        ):
            if button_selfadd("Autocarga", key=f"btn_selfadd_{key}", type="primary"):
                pass
            if button_add("Agregar", key=f"btn_add_{key}"):
                pass
            if button_edit("Editar", key=f"btn_edit_{key}"):
                pass
            if button_delete("Borrar", key=f"btn_delete_{key}"):
                pass

    return event
