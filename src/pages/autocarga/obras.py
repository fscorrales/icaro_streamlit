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
from src.utils import APIConnectionError, APIResponseError, build_retenciones_payload
from src.views import (
    modal_comprobante_gasto,
    report_template_without_filters,
)

REPORTE_OBRAS = "obras"


# --------------------------------------------------
def render() -> None:

    report_template_without_filters(
        key=f"autocarga_{REPORTE_OBRAS}",
        title=REPORTE_OBRAS.capitalize(),
        description="Obras del INVICO. Utiliza el filtro avanzado para realizar consultas específicas.",
        endpoint=Endpoints.ICARO_INFORME_CONTABLE.value,
        has_export=True,
        has_upload=True,
        process_func=process_certificados_obras,
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
            event = dataframe(
                df_certificados,
                key=f"{REPORTE_OBRAS}_df_certificados",
                height=300,
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
                    btn_edit = button_edit("Editar", key=f"btn_edit_{REPORTE_OBRAS}")
                    btn_del = button_delete("Borrar", key=f"btn_delete_{REPORTE_OBRAS}")

                # --- EL PLACEHOLDER VA AQUÍ (DEBAJO DE LOS BOTONES) ---
                error_placeholder = st.empty()

        if event is not None:
            if len(event.selection.rows) > 0:
                selected_row_index = event.selection.rows[0]
                datos_obras = df_certificados.iloc[selected_row_index].to_dict()
                payload_retenciones = build_retenciones_payload(datos_obras)

                # Extraemos los datos crudos
                lista_ret = payload_retenciones.get("retenciones", [])

                # Ordenamos la lista de retenciones por el código (convertido a entero)
                lista_ordenada = sorted(lista_ret, key=lambda x: int(x["codigo"]))

                # Construimos el diccionario manteniendo el orden de inserción (Python 3.7+)
                datos_fila = {
                    item["codigo"]: item["importe"] for item in lista_ordenada
                }
                datos_fila["TOTAL"] = sum(datos_fila.values())

                st.markdown("### Resumen de Retenciones Calculadas")
                with st.container(horizontal=False, border=True, width="stretch"):
                    dataframe(
                        pd.DataFrame([datos_fila]),
                        key=f"retenciones_{REPORTE_OBRAS}",
                        height=80,  # Altura pequeña ya que es solo una fila
                    )

        if btn_add:
            if len(event.selection.rows) > 0:
                selected_row_index = event.selection.rows[0]
                datos_obras = df_certificados.iloc[selected_row_index].to_dict()

                # Traemos el cuit desde el DF de proveedores para completar los datos que le pasamos al modal
                df_proveedores = get_proveedores()
                coincidencias = df_proveedores[
                    df_proveedores["desc_proveedor"] == datos_obras["beneficiario"]
                ]
                if not coincidencias.empty:
                    fila = coincidencias[["cuit"]].iloc[0]
                    datos_obras.update(fila.to_dict())
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
                        st.stop()  # Detenemos la ejecución para que no abra el modal vacío

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
                # print(datos_obras)
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
