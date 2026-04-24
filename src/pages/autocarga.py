"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Autocarga Page
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from src.components import button_add, button_delete, button_edit, dataframe
from src.constants import Endpoints
from src.services import (
    get_autocarga_certificados,
    get_autocarga_epam,
    get_obras,
    get_proveedores,
    process_certificados_obras,
    process_resumen_rend_obras,
)
from src.utils import APIConnectionError, APIResponseError
from src.views import (
    dataframe_with_buttons,
    modal_comprobante_gasto,
    report_template_without_filters,
)

REPORTE_CERTIFICADOS = "certificados"
REPORTE_EPAM = "epam"


# --------------------------------------------------
def render() -> None:
    tab_certificados, tab_epam = st.tabs(["Certificados", "EPAM"])

    with tab_certificados:
        report_template_without_filters(
            key=f"autocarga_{REPORTE_CERTIFICADOS}",
            title=REPORTE_CERTIFICADOS.capitalize(),
            description="Certificados del INVICO. Utiliza el filtro avanzado para realizar consultas específicas.",
            endpoint=Endpoints.ICARO_INFORME_CONTABLE.value,
            has_export=True,
            has_upload=True,
            process_func=process_certificados_obras,
        )

        # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
        filtro_actual = st.session_state.get(
            f"autocarga_{REPORTE_CERTIFICADOS}_advanced_filter", ""
        )
        trigger = st.session_state.get(
            f"autocarga_{REPORTE_CERTIFICADOS}_uploader_iteration", 0
        )

        # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
        df_certificados = pd.DataFrame()
        try:
            df_certificados = get_autocarga_certificados(filtro_actual, trigger)

            if df_certificados.empty:
                st.info("No se encontraron resultados.")

        except APIConnectionError as e:
            st.error(f"⚠️ Error de conexión: {e}")
        except APIResponseError as e:
            st.error(f"⚠️ Error de API: {e}")

        # 4. Mostrar resultados (usando session_state para que no desaparezcan)
        if not df_certificados.empty:
            # Definimos las columnas que NO queremos mostrar
            columnas_a_excluir = ["id_carga", "updated_at", "id"]

            # Generamos el orden dinámico: todas las del DF que no estén en la lista negra
            orden_dinamico = [
                col for col in df_certificados.columns if col not in columnas_a_excluir
            ]

            with st.container(horizontal=False, border=True, width="stretch"):
                event = dataframe(
                    df_certificados,
                    key=f"{REPORTE_CERTIFICADOS}_df_certificados",
                    height=300,
                    column_order=orden_dinamico,
                    on_select="rerun",
                    selection_mode="single-row",
                )
                with st.container(
                    horizontal=True,
                    border=False,
                    width="stretch",
                    horizontal_alignment="center",
                    gap="medium",
                ):
                    if button_add(
                        "Agregar", key=f"btn_add_{REPORTE_CERTIFICADOS}", type="primary"
                    ):
                        if len(event.selection.rows) > 0:
                            selected_row_index = event.selection.rows[0]
                            datos_obras = df_certificados.iloc[
                                selected_row_index
                            ].to_dict()

                            # Traemos el cuit desde el DF de proveedores para completar los datos que le pasamos al modal
                            df_proveedores = get_proveedores()
                            coincidencias = df_proveedores[
                                df_proveedores["desc_proveedor"]
                                == datos_obras["beneficiario"]
                            ]
                            if not coincidencias.empty:
                                fila = coincidencias[["cuit"]].iloc[0]
                                datos_obras.update(fila.to_dict())
                            else:
                                print("No se encontró el proveedor.")

                            # Traemos la fuente y cta_cte desde el DF de obras para completar los datos que le pasamos al modal
                            df_obras = get_obras()
                            coincidencias = df_obras[
                                df_obras["desc_obra"] == datos_obras["desc_obra"]
                            ]

                            if not coincidencias.empty:
                                fila = coincidencias[
                                    ["actividad", "partida", "fuente", "cta_cte"]
                                ].iloc[0]
                                datos_obras.update(fila.to_dict())
                            else:
                                print("No se encontró la obra.")

                            datos_obras["importe"] = float(datos_obras["importe_bruto"])
                            datos_obras["origen"] = "Obras"
                            print(datos_obras)
                            modal_comprobante_gasto(
                                key_prefix=f"edit_gasto_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                datos_carga=datos_obras,
                            )
                    if button_edit("Editar", key=f"btn_edit_{REPORTE_CERTIFICADOS}"):
                        pass
                    if button_delete(
                        "Borrar", key=f"btn_delete_{REPORTE_CERTIFICADOS}"
                    ):
                        pass

    with tab_epam:
        report_template_without_filters(
            key=f"autocarga_{REPORTE_EPAM}",
            title=REPORTE_EPAM.capitalize(),
            description="Resumen de Rendiciones de Obras EPAM. Utiliza el filtro avanzado para realizar consultas específicas.",
            endpoint=Endpoints.ICARO_RESUMEN_REND_OBRAS.value,
            has_export=True,
            has_upload=True,
            process_func=process_resumen_rend_obras,
        )

        # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
        filtro_actual_epam = st.session_state.get(
            f"autocarga_{REPORTE_EPAM}_advanced_filter", ""
        )
        trigger_epam = st.session_state.get(
            f"autocarga_{REPORTE_EPAM}_uploader_iteration", 0
        )

        # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
        df_epam = pd.DataFrame()
        try:
            df_epam = get_autocarga_epam(filtro_actual_epam, trigger_epam)

            if df_epam.empty:
                st.info("No se encontraron resultados.")

        except APIConnectionError as e:
            st.error(f"⚠️ Error de conexión: {e}")
        except APIResponseError as e:
            st.error(f"⚠️ Error de API: {e}")

        # 4. Mostrar resultados (usando session_state para que no desaparezcan)
        if not df_epam.empty:
            # Definimos las columnas que NO queremos mostrar
            columnas_a_excluir = ["id_carga", "updated_at", "id"]

            # Generamos el orden dinámico: todas las del DF que no estén en la lista negra
            orden_dinamico = [
                col for col in df_epam.columns if col not in columnas_a_excluir
            ]

            dataframe_with_buttons(
                df_epam,
                key=f"{REPORTE_EPAM}_df_epam",
                height=300,
                column_order=orden_dinamico,
            )


if __name__ == "__main__":
    render()
