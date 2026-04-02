import itertools
from typing import Any, Optional

import pandas as pd
import streamlit as st

from src.components.buttons import button_export, button_update
from src.components.dataframes import dataframe
from src.components.multiselects import multiselect_filter
from src.components.text_inputs import text_input_advance_filter
from src.services.api_client import (
    APIConnectionError,
    APIResponseError,
    fetch_dataframe,
    fetch_excel_stream,
)


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
                    # REPETIMOS LÓGICA DE FILTROS:
                    listas_valores = [s[1] for s in selections]
                    nombres_params = [s[0] for s in selections]

                    # Para simplificar, si el usuario exporta, quizás quieras
                    # mandarle un solo Excel con la combinación actual o iterar.
                    # Aquí asumo que mandas el primer set de filtros o el consolidado:
                    for combinacion in itertools.product(*listas_valores):
                        params_peticion = dict(zip(nombres_params, combinacion))
                        params_peticion["queryFilter"] = filtro_avanzado

                        # Llamada a la API que devuelve StreamingResponse
                        excel_binario = fetch_excel_stream(
                            f"{endpoint}/export", params_peticion
                        )

                        if excel_binario:
                            # IMPORTANTE: Como st.download_button recarga la página,
                            # a veces es mejor usar un link o guardarlo en session_state
                            st.session_state[f"temp_file_{key}"] = excel_binario
                            st.success("✅ Archivo generado con éxito.")
                            st.rerun()
                        break  # Si solo quieres el primer set, o ajusta según tu necesidad

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
            df_final = pd.DataFrame()

            # Extraemos solo las listas de valores: [[2023, 2024], ["Salud", "Educación"]]
            listas_valores = [s[1] for s in selections]
            # Extraemos los nombres de los parámetros: ["ejercicio", "unidad_id"]
            nombres_params = [s[0] for s in selections]

            # Si permitimos que no haya filtros y todas las listas están vacías,
            # debemos forzar al menos una ejecución con params vacíos.
            if allow_no_filters and all(not lista for lista in listas_valores):
                params_peticion = {"limit": 0, "queryFilter": filtro_avanzado}
                df_final = fetch_dataframe(endpoint, params=params_peticion)
            else:
                # Si hay filtros, usamos la lógica de combinaciones
                # Pero ojo: product con una lista vacía devuelve nada.
                # Aseguramos que las listas vacías tengan al menos un [None]
                # si queremos que la combinación siga funcionando.
                listas_limpias = [l if l else [None] for l in listas_valores]
                # itertools.product genera todas las combinaciones posibles:
                # (2023, "Salud"), (2023, "Educación"), (2024, "Salud"), ...
                for combinacion in itertools.product(*listas_limpias):
                    # Creamos el diccionario de params para esta petición específica
                    params_peticion = dict(zip(nombres_params, combinacion))
                    params_peticion["limit"] = 0
                    params_peticion["queryFilter"] = filtro_avanzado

                    # DEBUG: Mostrar en la app (puedes borrarlo después)
                    # print(f"DEBUG API CALL [{endpoint}]: {params_peticion}")
                    # st.info(f"Enviando a API: {params_peticion}")

                    # Hacemos el fetch individual
                    df_parcial = fetch_dataframe(endpoint, params=params_peticion)
                    df_final = pd.concat([df_final, df_parcial], ignore_index=True)

            if df_final.empty:
                st.info("No se encontraron resultados.")
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
