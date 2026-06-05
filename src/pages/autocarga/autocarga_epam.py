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
    get_autocarga_epam,
    get_obras,
    get_proveedores,
    process_resumen_rend_obras,
)
from src.utils import (
    APIConnectionError,
    APIResponseError,
    build_retenciones_payload,
    formato_moneda_ar,
)
from src.views import (
    modal_comprobante_gasto,
    modal_obras,
    report_template,
)

REPORTE_EPAM = "epam"

ayuda_uploader = """
### 📥 Guía de Importación
1. Ingrese al **SGF**, y seleccione el menú **Informes / Resumen de Rendiciones**
2. Seleccione **Agrupamiento = Por Obra**, **Origen = EPAM** y el **rango de fechas** que desee
3. Presione el botón **Exportar**
4. En la ventana emergente, mantenga la opción **Archivo...** antes de presionar aceptar
5. Elija el destino del archivo a descargar y preste atención a que el tipo sea **.csv**
6. **Importar** el archivo descargado previamente
"""


# --------------------------------------------------
def render() -> None:

    report_template(
        key=f"autocarga_{REPORTE_EPAM}",
        title=REPORTE_EPAM.capitalize(),
        description="",
        endpoint=Endpoints.ICARO_RESUMEN_REND_OBRAS.value,
        has_export=True,
        has_upload=True,
        uploader_func=process_resumen_rend_obras,
        uploader_help=ayuda_uploader,
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

                # Extraemos los datos crudos
                lista_ret = payload_retenciones.get("retenciones", [])

                # Ordenamos la lista de retenciones por el código (convertido a entero)
                lista_ordenada = sorted(lista_ret, key=lambda x: int(x["codigo"]))

                df_ret_tabla = pd.DataFrame(lista_ordenada)

                if not df_ret_tabla.empty:
                    # Si tiene datos, formateamos la columna importe
                    df_ret_tabla["importe"] = df_ret_tabla["importe"].apply(
                        formato_moneda_ar
                    )
                else:
                    # Si está vacío, creamos un DataFrame con las columnas correctas
                    # pero vacío para que Streamlit no rompa al renderizar
                    df_ret_tabla = pd.DataFrame(columns=["codigo", "importe"])

                # Creamos la tabla resumen de imputacion y totales
                df_obras = get_obras(
                    update_trigger=st.session_state.get("obras_uploader_iteration", 0)
                )

                coincidencias = df_obras[
                    df_obras["desc_obra"].isin(
                        df_epam.iloc[selected_indices]["desc_obra"].unique().tolist()
                    )
                ]

                valor_imputacion = "Sin coincidencia"

                if not coincidencias.empty:
                    # Verificamos si todas las filas seleccionadas pertenecen a la misma imputación
                    # Agrupamos por actividad y partida para ver si hay una sola combinación
                    imputaciones_unicas = coincidencias.drop_duplicates(
                        subset=["actividad", "partida"]
                    )

                    if len(imputaciones_unicas) == 1:
                        # Caso ideal: Una sola combinación Actividad-Partida para todo lo seleccionado
                        fila = imputaciones_unicas.iloc[0]
                        valor_imputacion = f"{fila['actividad']} - {fila['partida']}"
                    else:
                        # Caso mixto: Se seleccionaron filas de distintas partidas/actividades
                        valor_imputacion = "Múltiples Imputaciones"

                valor_importe_bruto = formato_moneda_ar(df_suma["importe_bruto"])
                valor_retenciones = formato_moneda_ar(
                    df_suma["iibb"] + df_suma["gcias"] + df_suma["suss"] + df_suma["lp"]
                )
                valor_importe_neto = formato_moneda_ar(df_suma["importe_neto"])

                #         # 4. Armamos el DataFrame vertical
                df_imputacion = pd.DataFrame(
                    [
                        {"Concepto": "Imputación", "Valor": valor_imputacion},
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

        if btn_add:
            if len(event.selection.rows) > 0:
                selected_indices = event.selection.rows
                datos_epam = {}

                # --- VALIDACIÓN DE PROVEEDOR ---
                df_proveedores = get_proveedores(
                    update_trigger=st.session_state.get(
                        "proveedores_uploader_iteration", 0
                    )
                )

                unique_beneficiarios = (
                    df_epam.iloc[selected_indices]["beneficiario"].unique().tolist()
                )
                if len(unique_beneficiarios) > 1:
                    proveedor_valido = (
                        True  # Suponemos que el proveedor a cargar en SIIF es INVICO
                    )
                    datos_epam["cuit"] = "30632351514"
                else:
                    coincidencias_prov = df_proveedores[
                        df_proveedores["desc_proveedor"].isin(unique_beneficiarios)
                    ]
                    proveedor_valido = not coincidencias_prov.empty
                    if proveedor_valido:
                        datos_epam.update(
                            coincidencias_prov[["cuit"]].iloc[0].to_dict()
                        )
                    else:
                        # 1. Alerta rápida en la esquina
                        st.toast("⚠️ Proveedor no encontrado", icon="👤")

                        # 2. Mensaje con acción en el cuerpo de la página
                        with error_placeholder.container(
                            horizontal=False,
                            width="stretch",
                            horizontal_alignment="center",
                        ):
                            st.error(
                                f"El beneficiario '{unique_beneficiarios[0]}' no existe en la base de datos."
                            )
                            if st.page_link(
                                "src/pages/proveedores.py",
                                label="Ir a Actualizar Proveedores",
                                icon="⚙️",
                            ):
                                pass

                # --- VALIDACIÓN DE OBRA ---
                df_obras = get_obras(
                    update_trigger=st.session_state.get("obras_uploader_iteration", 0)
                )
                unique_obras = (
                    df_epam.iloc[selected_indices]["desc_obra"].unique().tolist()
                )
                if len(unique_obras) > 1:
                    obra_valida = False  # No podemos cargar si hay más de una obra diferente seleccionada
                    st.toast("⚠️ Multiples imputaciones seleccionadas", icon="🏗️")
                    with error_placeholder.container(
                        horizontal=False,
                        width="stretch",
                        horizontal_alignment="center",
                    ):
                        st.error(
                            f"No es posible agregar las obras '{unique_obras}' en el mismo comprobante."
                        )
                else:
                    datos_epam["desc_obra"] = unique_obras[0]
                    coincidencias_obra = df_obras[
                        df_obras["desc_obra"].isin(unique_obras)
                    ]
                    obra_valida = not coincidencias_obra.empty
                    if obra_valida:
                        datos_epam.update(
                            coincidencias_obra[
                                ["actividad", "partida", "fuente", "cta_cte"]
                            ]
                            .iloc[0]
                            .to_dict()
                        )
                    else:
                        # 1. Alerta rápida en la esquina
                        st.toast("⚠️ Obra no encontrada", icon="🏗️")

                        # 2. Mensaje con acción en el cuerpo de la página
                        with error_placeholder.container(
                            horizontal=False,
                            width="stretch",
                            horizontal_alignment="center",
                        ):
                            st.error(
                                f"La obra '{unique_obras[0]}' no existe en la base de datos."
                            )
                            modal_obras(
                                key_prefix=f"add_obra_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                datos_carga=datos_epam,
                                es_edicion=False,
                                es_autocarga=True,
                            )

                datos_epam.update(
                    df_epam.iloc[selected_indices][
                        ["iibb", "gcias", "suss", "lp", "importe_bruto", "importe_neto"]
                    ]
                    .sum()
                    .to_dict()
                )
                datos_epam["importe"] = float(datos_epam["importe_bruto"])
                datos_epam["origen"] = "EPAM"
                datos_epam["id"] = df_epam.iloc[selected_indices]["id"].tolist()

                # print(datos_epam)
                if obra_valida and proveedor_valido:
                    modal_comprobante_gasto(
                        key_prefix=f"edit_gasto_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        datos_carga=datos_epam,
                    )

        if btn_edit:
            pass
        if btn_del:
            pass


if __name__ == "__main__":
    render()
