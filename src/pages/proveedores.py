"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: ICARO's Proveedores Page
"""

import streamlit as st

from src.constants import Endpoints
from src.services import (
    get_proveedores,
    process_listado_proveedores,
)
from src.utils import APIConnectionError, APIResponseError
from src.views import dataframe_with_buttons, report_template

REPORTE = "proveedores"

ayuda_uploader = """
### 📥 Guía de Importación
1. Ingrese al **SGF**, y seleccione el menú **Archivo / Proveedores / Listado de Proveedores**
2. Presione el botón **Exportar**
3. En la ventana emergente, mantenga la opción **Archivo...** antes de presionar aceptar
4. Elija el destino del archivo a descargar y preste atención a que el tipo sea **.csv**
5. **Importar** el archivo descargado previamente
"""


# --------------------------------------------------
def render() -> None:
    report_template(
        key=REPORTE,
        title=REPORTE.capitalize(),
        description="",
        endpoint=Endpoints.ICARO_PROVEEDORES.value,
        has_export=True,
        has_upload=True,
        uploader_help=ayuda_uploader,
        uploader_func=process_listado_proveedores,
    )

    # 2. Capturamos el filtro del session_state (que el fragmento actualizó)
    filtro_actual = st.session_state.get(f"{REPORTE}_advanced_filter", "")

    # 3. Ejecutamos la lógica que necesitemos (ahora sí es reutilizable)
    try:
        df_proveedores = get_proveedores(
            filtro_actual,
            update_trigger=st.session_state.proveedores_uploader_iteration,
        )

        if df_proveedores.empty:
            st.info("No se encontraron resultados.")
        # else:
        #     st.session_state[f"data_{key}_carga"] = df_final
        #     st.session_state[f"data_{key}_retenciones"] = df_final_ret

    except APIConnectionError as e:
        st.error(f"⚠️ Error de conexión: {e}")
    except APIResponseError as e:
        st.error(f"⚠️ Error de API: {e}")

    # 4. Mostrar resultados (usando session_state para que no desaparezcan)
    if not df_proveedores.empty:
        dataframe_with_buttons(
            df_proveedores,
            key=f"{REPORTE}_df_proveedores",
            height=300,
            column_order=[
                "cuit",
                "codigo",
                "desc_proveedor",
                "domicilio",
                "localidad",
                "condicion_iva",
            ],
            show_buttons=False,
        )


if __name__ == "__main__":
    render()
