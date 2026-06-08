"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Autocarga Certificados Obras Page
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from src.components import button_add, button_delete, button_edit, dataframe
from src.constants import Endpoints
from src.services import (
    get_autocarga_certificados,
    get_obras,
    get_proveedores,
    process_certificados_obras,
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

REPORTE_OBRAS = "obras"

ayuda_uploader = """
### 📥 Guía de Importación
1. Ingrese al **SGF**, y seleccione el menú **Informes / Certificados de Obra / Informe para Contable [Certificados]** o **Informes / Certificados de Obra / Informe para Contable [Fondo Reparo]** 
2. Seleccione **Mes** y **Año**
3. Presione el botón **Exportar**
4. En la ventana emergente, mantenga la opción **Archivo...** antes de presionar aceptar
5. Elija el destino del archivo a descargar y preste atención a que el tipo sea **.csv**
6. **Importar** el archivo descargado previamente
"""


# --------------------------------------------------
def render() -> None:

    report_template(
        key=f"autocarga_{REPORTE_OBRAS}",
        title=REPORTE_OBRAS.capitalize(),
        description="",
        endpoint=Endpoints.ICARO_INFORME_CONTABLE.value,
        has_export=True,
        has_upload=True,
        uploader_func=process_certificados_obras,
        uploader_help=ayuda_uploader,
    )

    # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
    filtro_actual = st.session_state.get(
        f"autocarga_{REPORTE_OBRAS}_advanced_filter", ""
    )
    trigger = st.session_state.get(f"autocarga_{REPORTE_OBRAS}_uploader_iteration", 0)

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
            # 1. Creamos una fila de inputs usando columnas (podés elegir cuáles indexar)
            df_filtrado = df_certificados.copy()
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                f_beneficiario = st.text_input(
                    "Beneficiario",
                    placeholder="Ej: MECAR",
                    key=f"f_beneficiario_{REPORTE_OBRAS}",
                )
            with col2:
                f_desc_obra = st.text_input(
                    "Descripción Obra",
                    placeholder="Ej: Museo",
                    key=f"f_desc_obra_{REPORTE_OBRAS}",
                )
            with col3:
                nro_certificado = st.text_input(
                    "Nro Certificado",
                    placeholder="Ej: 11",
                    key=f"nro_certificado_{REPORTE_OBRAS}",
                )
            with col4:
                f_importe_min = st.number_input(
                    "Importe Bruto Mínimo",
                    min_value=0.0,
                    value=0.0,
                    step=10000.0,
                    key=f"f_importe_min_{REPORTE_OBRAS}",
                )

            # 2. Aplicamos los filtros en cascada sobre el DataFrame (Frontend Puro)
            if f_beneficiario:
                df_filtrado = df_filtrado[
                    df_filtrado["beneficiario"]
                    .astype(str)
                    .str.contains(f_beneficiario, case=False)
                ]
            if f_desc_obra:
                df_filtrado = df_filtrado[
                    df_filtrado["desc_obra"]
                    .astype(str)
                    .str.contains(f_desc_obra, case=False)
                ]
            if nro_certificado:
                df_filtrado = df_filtrado[
                    df_filtrado["nro_certificado"]
                    .astype(str)
                    .str.contains(nro_certificado, case=False)
                ]
            if f_importe_min:
                df_filtrado = df_filtrado[df_filtrado["importe_bruto"] >= f_importe_min]

            event = dataframe(
                df_filtrado,
                key=f"{REPORTE_OBRAS}_df_certificados",
                height=250,
                column_order=orden_dinamico,
                on_select="rerun",
                selection_mode="single-row",
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
                        "Agregar", key=f"btn_add_{REPORTE_OBRAS}", type="primary"
                    )
                    btn_edit = button_edit(
                        "Editar", key=f"btn_edit_{REPORTE_OBRAS}", disabled=True
                    )
                    btn_del = button_delete(
                        "Borrar", key=f"btn_delete_{REPORTE_OBRAS}", disabled=True
                    )

                # --- EL PLACEHOLDER VA AQUÍ (DEBAJO DE LOS BOTONES) ---
                error_placeholder = st.empty()

        if event is not None:
            if len(event.selection.rows) > 0:
                selected_row_index = event.selection.rows[0]
                datos_obras = df_filtrado.iloc[selected_row_index].to_dict()
                payload_retenciones = build_retenciones_payload(datos_obras)

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

                df_obras = get_obras(
                    update_trigger=st.session_state.get("obras_uploader_iteration", 0)
                )
                coincidencias = df_obras[
                    df_obras["desc_obra"] == datos_obras["desc_obra"]
                ]
                valor_imputacion = ""
                if not coincidencias.empty:
                    fila = coincidencias[["actividad", "partida"]].iloc[0]
                    valor_imputacion = f"{fila['actividad']}-{fila['partida']}"

                valor_importe_bruto = formato_moneda_ar(datos_obras["importe_bruto"])
                valor_retenciones = formato_moneda_ar(datos_obras["retenciones"])
                valor_importe_neto = formato_moneda_ar(datos_obras["importe_neto"])

                # 4. Armamos el DataFrame vertical
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
                        key=f"autocarga_{REPORTE_OBRAS}_imputacion",
                        height=150,
                    )
                    dataframe(
                        df_ret_tabla,
                        key=f"autocarga_{REPORTE_OBRAS}_retenciones",
                        height=150,
                    )

        if btn_add:
            if len(event.selection.rows) > 0:
                selected_row_index = event.selection.rows[0]
                datos_obras = df_filtrado.iloc[selected_row_index].to_dict()

                # --- VALIDACIÓN DE PROVEEDOR ---
                df_proveedores = get_proveedores(
                    update_trigger=st.session_state.proveedores_uploader_iteration
                )
                coincidencias_prov = df_proveedores[
                    df_proveedores["desc_proveedor"] == datos_obras["beneficiario"]
                ]
                proveedor_valido = not coincidencias_prov.empty
                if proveedor_valido:
                    datos_obras.update(coincidencias_prov[["cuit"]].iloc[0].to_dict())
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
                            f"El beneficiario '{datos_obras['beneficiario']}' no existe en la base de datos."
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
                coincidencias_obra = df_obras[
                    df_obras["desc_obra"] == datos_obras["desc_obra"]
                ]
                obra_valida = not coincidencias_obra.empty
                if obra_valida:
                    datos_obras.update(
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
                            f"La obra '{datos_obras['desc_obra']}' no existe en la base de datos."
                        )
                        modal_obras(
                            key_prefix=f"add_obra_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            datos_carga=datos_obras,
                            es_edicion=False,
                            es_autocarga=True,
                        )

                datos_obras["importe"] = float(datos_obras["importe_bruto"])
                datos_obras["origen"] = "Obras"
                # print(datos_obras)
                if obra_valida and proveedor_valido:
                    modal_comprobante_gasto(
                        key_prefix=f"edit_gasto_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        datos_carga=datos_obras,
                    )

        if btn_edit:
            pass
        if btn_del:
            pass


if __name__ == "__main__":
    render()
