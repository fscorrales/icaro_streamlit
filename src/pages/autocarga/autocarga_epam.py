"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Autocarga Page
"""

import pandas as pd
import streamlit as st

from src.components import button_add, button_delete, button_edit, dataframe
from src.constants import Endpoints
from src.services import (
    get_autocarga_epam,
    process_resumen_rend_obras,
)
from src.utils import (
    APIConnectionError,
    APIResponseError,
    build_retenciones_payload,
    formato_moneda_ar,
)
from src.views import (
    report_template_without_filters,
)

REPORTE_EPAM = "epam"


# --------------------------------------------------
def render() -> None:

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
    trigger = st.session_state.get(f"autocarga_{REPORTE_EPAM}_uploader_iteration", 0)

    # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
    df_epam = pd.DataFrame()
    try:
        df_epam = get_autocarga_epam(filtro_actual_epam, trigger)

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

        with st.container(horizontal=False, border=True, width="stretch"):
            event = dataframe(
                df_epam,
                key=f"{REPORTE_EPAM}_df_epam",
                height=250,
                column_order=orden_dinamico,
                on_select="rerun",
                selection_mode="multi-row",
            )
            with st.container(
                horizontal=False,
                border=False,
                width="stretch",
                horizontal_alignment="center",
            ):
                with st.container(
                    horizontal=True,
                    border=False,
                    width="stretch",
                    horizontal_alignment="center",
                    gap="medium",
                ):
                    btn_add = button_add(
                        "Agregar", key=f"btn_add_{REPORTE_EPAM}", type="primary"
                    )
                    btn_edit = button_edit(
                        "Editar", key=f"btn_edit_{REPORTE_EPAM}", disabled=True
                    )
                    btn_del = button_delete(
                        "Borrar", key=f"btn_delete_{REPORTE_EPAM}", disabled=True
                    )

                # --- EL PLACEHOLDER VA AQUÍ (DEBAJO DE LOS BOTONES) ---
                error_placeholder = st.empty()

        if event is not None:
            if len(event.selection.rows) > 0:
                selected_indices = event.selection.rows
                df_suma = (
                    df_epam.iloc[selected_indices][
                        ["iibb", "gcias", "suss", "lp", "importe_bruto", "importe_neto"]
                    ]
                    .sum()
                    .to_dict()
                )
                payload_retenciones = build_retenciones_payload(df_suma)
                print(payload_retenciones)

                # Extraemos los datos crudos
                lista_ret = payload_retenciones.get("retenciones", [])

                # Ordenamos la lista de retenciones por el código (convertido a entero)
                lista_ordenada = sorted(lista_ret, key=lambda x: int(x["codigo"]))

                df_ret_tabla = pd.DataFrame(lista_ordenada)

                df_ret_tabla["importe"] = df_ret_tabla["importe"].apply(
                    formato_moneda_ar
                )

                #         df_obras = get_obras(
                #             update_trigger=st.session_state.get("obras_uploader_iteration", 0)
                #         )
                #         coincidencias = df_obras[
                #             df_obras["desc_obra"] == datos_obras["desc_obra"]
                #         ]
                #         valor_imputacion = ""
                #         if not coincidencias.empty:
                #             fila = coincidencias[["actividad", "partida"]].iloc[0]
                #             valor_imputacion = f"{fila['actividad']}-{fila['partida']}"

                valor_importe_bruto = formato_moneda_ar(df_suma["importe_bruto"])
                valor_retenciones = formato_moneda_ar(
                    df_suma["iibb"] + df_suma["gcias"] + df_suma["suss"] + df_suma["lp"]
                )
                valor_importe_neto = formato_moneda_ar(df_suma["importe_neto"])

                #         # 4. Armamos el DataFrame vertical
                df_imputacion = pd.DataFrame(
                    [
                        {"Concepto": "Imputación", "Valor": "valor_imputacion"},
                        {"Concepto": "Importe Bruto", "Valor": valor_importe_bruto},
                        {"Concepto": "Retenciones", "Valor": valor_retenciones},
                        {"Concepto": "Importe Neto", "Valor": valor_importe_neto},
                    ]
                )

                with st.container(horizontal=True, border=True, width="stretch"):
                    dataframe(
                        df_imputacion,
                        key=f"autocarga_{REPORTE_EPAM}_imputacion",
                        height=150,
                    )
                    dataframe(
                        df_ret_tabla,
                        key=f"autocarga_{REPORTE_EPAM}_retenciones",
                        height=150,
                    )

        # if btn_add:
        #     if len(event.selection.rows) > 0:
        #         selected_row_index = event.selection.rows[0]
        #         datos_obras = df_certificados.iloc[selected_row_index].to_dict()

        #         # --- VALIDACIÓN DE PROVEEDOR ---
        #         df_proveedores = get_proveedores()
        #         coincidencias_prov = df_proveedores[
        #             df_proveedores["desc_proveedor"] == datos_obras["beneficiario"]
        #         ]
        #         proveedor_valido = not coincidencias_prov.empty
        #         if proveedor_valido:
        #             datos_obras.update(coincidencias_prov[["cuit"]].iloc[0].to_dict())
        #         else:
        #             # 1. Alerta rápida en la esquina
        #             st.toast("⚠️ Proveedor no encontrado", icon="👤")

        #             # 2. Mensaje con acción en el cuerpo de la página
        #             with error_placeholder.container(
        #                 horizontal=False,
        #                 width="stretch",
        #                 horizontal_alignment="center",
        #             ):
        #                 st.error(
        #                     f"El beneficiario '{datos_obras['beneficiario']}' no existe en la base de datos."
        #                 )
        #                 if st.page_link(
        #                     "src/pages/proveedores.py",
        #                     label="Ir a Actualizar Proveedores",
        #                     icon="⚙️",
        #                 ):
        #                     pass
        #                 # st.stop()  # Detenemos la ejecución para que no abra el modal vacío

        #         # --- VALIDACIÓN DE OBRA ---
        #         df_obras = get_obras(
        #             update_trigger=st.session_state.get("obras_uploader_iteration", 0)
        #         )
        #         coincidencias_obra = df_obras[
        #             df_obras["desc_obra"] == datos_obras["desc_obra"]
        #         ]
        #         obra_valida = not coincidencias_obra.empty
        #         if obra_valida:
        #             datos_obras.update(
        #                 coincidencias_obra[
        #                     ["actividad", "partida", "fuente", "cta_cte"]
        #                 ]
        #                 .iloc[0]
        #                 .to_dict()
        #             )
        #         else:
        #             # 1. Alerta rápida en la esquina
        #             st.toast("⚠️ Obra no encontrada", icon="🏗️")

        #             # 2. Mensaje con acción en el cuerpo de la página
        #             with error_placeholder.container(
        #                 horizontal=False,
        #                 width="stretch",
        #                 horizontal_alignment="center",
        #             ):
        #                 st.error(
        #                     f"La obra '{datos_obras['desc_obra']}' no existe en la base de datos."
        #                 )
        #                 modal_obras(
        #                     key_prefix=f"add_obra_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        #                     datos_carga=datos_obras,
        #                     es_edicion=False,
        #                     es_autocarga=True,
        #                 )

        #         datos_obras["importe"] = float(datos_obras["importe_bruto"])
        #         datos_obras["origen"] = "Obras"
        #         # print(datos_obras)
        #         if obra_valida and proveedor_valido:
        #             modal_comprobante_gasto(
        #                 key_prefix=f"edit_gasto_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        #                 datos_carga=datos_obras,
        #             )

        # if btn_edit:
        #     pass
        # if btn_del:
        #     pass


if __name__ == "__main__":
    render()
