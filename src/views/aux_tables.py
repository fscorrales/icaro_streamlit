__all__ = [
    "report_template",
    "report_template_without_filters",
    "params_preparation",
    "dataframe_with_buttons",
    "dataframe_home_carga",
]

import time
from typing import Any, Optional

import pandas as pd
import streamlit as st

from src.components import (
    button_add,
    button_delete,
    button_edit,
    button_export,
    button_selfadd,
    button_submit,
    button_update,
    dataframe,
    multiselect_filter,
    text_input_advance_filter,
)
from src.services import (
    fetch_dataframe,
    fetch_excel_stream,
    post_request,
)
from src.utils import APIConnectionError, APIResponseError, read_csv_file


# --------------------------------------------------
def params_preparation(
    selections: list = [], filtro_avanzado: str = ""
) -> dict[str, Any]:
    """
    Función auxiliar para preparar los parámetros de la API a partir de las selecciones y el filtro avanzado.
    Devuelve un diccionario listo para ser usado en la petición.
    """
    params_peticion = {"limit": 0, "queryFilter": filtro_avanzado}

    if len(selections) > 0:
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
                if button_export("Exportar a Excel", key=f"button_export_{key}"):
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


@st.fragment  # Permite que los filtros internos no recarguen TODA la página
# --------------------------------------------------
def report_template_without_filters(
    key: str,
    title: str,
    endpoint: str,
    description: str,
    has_export: bool = True,
    has_upload: bool = False,
    process_func=None,
):
    """
    Vista reutilizable.
    filters_config: Lista de dicts con ['label', 'options', 'key', 'default']
    """
    st.markdown(f"# {title}")
    st.write(description)

    # 0. Lógica de Exportación
    def download_file():
        # Validamos filtros antes de proceder
        try:
            # Limpiamos basura anterior antes de empezar el proceso pesado
            if f"temp_file_{key}" in st.session_state:
                del st.session_state[f"temp_file_{key}"]
            with st.spinner("Preparando archivos Excel..."):
                # Llamada a la API que devuelve StreamingResponse
                excel_binario = fetch_excel_stream(
                    f"{endpoint}/export",
                    params_preparation(filtro_avanzado=filtro_avanzado),
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
        filtro_avanzado = text_input_advance_filter(
            key="text_input_advance_filter-" + key
        )
        if f"{key}_uploader_iteration" not in st.session_state:
            st.session_state[f"{key}_uploader_iteration"] = 0

        uploaded_file = (
            st.file_uploader(
                f"Cargar CSV de {title}",
                type=["csv"],
                key=f"{key}_upload_file_{st.session_state[f'{key}_uploader_iteration']}",
                label_visibility="collapsed",
                disabled=not has_upload,  # Add this line to disable the uploader if has_upload is False
            )
            if has_upload
            else None
        )

        if has_export:
            # Aquí podrías integrar tu logic de exportación
            if f"temp_file_{key}" not in st.session_state:
                if button_export("Exportar a Excel", key=f"button_export_{key}"):
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

    if uploaded_file:
        df = read_csv_file(uploaded_file)
        if process_func:
            df = process_func(df)
        # Validación Visual (El "seguro" del usuario)
        col1, col2, col3 = st.columns(3)
        col1.metric("Filas a procesar", len(df))
        col2.metric("Columnas", len(df.columns))
        col3.info("Validación: OK" if not df.empty else "Error: CSV Vacío o Incorrecto")

        with st.expander("Ver vista previa de datos limpios"):
            st.dataframe(df.head(10), width="stretch")

        if not df.empty:
            with st.container(horizontal=True, horizontal_alignment="center"):
                if button_submit("Confirmar CARGA BD", key=f"btn_add_{key}"):
                    with st.spinner("Ejecutando script de carga..."):
                        # Transformación final para Mongo
                        registros = df.to_dict(orient="records")

                        res = post_request(endpoint, registros)

                        if res:
                            # 1. Extraer datos principales
                            titulo = res.get("title", "Sincronización")
                            agregados = res.get("added", 0)
                            eliminados = res.get("deleted", 0)
                            lista_errores = res.get("errors", [])
                            num_errores = len(lista_errores)

                            # 2. Toast Combinado (Resumen Ejecutivo)
                            # Ejemplo: 📊 Epam: +160 agregados, -160 eliminados.
                            mensaje_toast = f"📊 {titulo}: +{agregados} agregados, -{eliminados} eliminados."

                            if num_errores > 0:
                                mensaje_toast += f" ({num_errores} con errores)"
                                st.toast(mensaje_toast, icon="⚠️")
                            else:
                                st.toast(mensaje_toast, icon="✅")

                            # 3. Gestión de Errores Detallados (Si existen)
                            if num_errores > 0:
                                with st.expander(
                                    "❌ Detalle de Inconsistencias por Documento",
                                    expanded=True,
                                ):
                                    for error_doc in lista_errores:
                                        doc_id = error_doc.get(
                                            "doc_id", "ID Desconocido"
                                        )
                                        details = error_doc.get("details", [])

                                        st.markdown(f"**Documento ID:** `{doc_id}`")
                                        for det in details:
                                            # Estructura: loc, msg, error_type
                                            st.caption(
                                                f"📍 {det['loc']} | 🏷️ {det['error_type']}"
                                            )
                                            st.write(f"💬 {det['msg']}")
                                        st.divider()
                            else:
                                st.balloons()
                                st.session_state[f"{key}_uploader_iteration"] += 1
                                time.sleep(3)
                                st.rerun()

    # Sincronizamos con el session_state para que 'render' lo vea
    if st.session_state.get(f"{key}_advanced_filter") != filtro_avanzado:
        st.session_state[f"{key}_advanced_filter"] = filtro_avanzado
        st.rerun()  # Forzamos que toda la página (fuera del fragmento) reaccione


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
