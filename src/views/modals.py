__all__ = ["modal_agregar_gasto"]

from datetime import date

import streamlit as st

from src.constants import Endpoints
from src.services import post_request, get_proveedores, get_obras


# --- MODAL: AGREGAR COMPROBANTE DE GASTO ---
@st.dialog("Agregar Comprobante Gasto", width="medium")
def modal_agregar_gasto(key_prefix: str):
    """
    Réplica visual del formulario de la imagen.
    WIDTH='large' es clave para que las 4-5 columnas no se amontonen.
    """

    # Usamos session_state para que los 'callbacks' de los selects carguen los 'Denominacion'
    # sin cerrar el modal por accidente.
    form_data = st.session_state.get(f"{key_prefix}_form_data", {})

    # FILA 1: 4 Columnas (Nro, Fecha, Nro ICARO, Tipo)
    col1_1, col1_2, col1_3, col1_4 = st.columns([2, 2, 2, 1])

    nro_comprobante = col1_1.text_input("Nro Comprobante", key=f"{key_prefix}_nro")

    fecha = col1_2.date_input(
        "Fecha", value=date.today(), format="DD-MM-YYYY", key=f"{key_prefix}_fecha"
    )

    # El Nro ICARO suele ser autogenerado o gris en tu imagen
    nro_icaro = col1_3.text_input(
        "Nro ICARO",
        placeholder="Autogenerado",
        disabled=True,
        key=f"{key_prefix}_icaro",
    )

    tipo_gasto = col1_4.selectbox(
        "Tipo", options=["CYO", "OBRA", "OTRO"], index=0, key=f"{key_prefix}_tipo"
    )

    # FILA 2: CUIT Contratista (Ancho Completo con Info)
    # Creamos un diccionario donde la clave es el CUIT y el valor es el Nombre
    # Esto hace que el mapeo en format_func sea instantáneo (O(1))
    df_prov = get_proveedores()
    mapeo_contratistas = dict(zip(df_prov.cuit, df_prov.desc_proveedor))

    cuit_contratista = st.selectbox(
        "Contratista",
        index= None,
        placeholder="Elegir un Contratista.",
        options=df_prov.cuit.to_list(),
        format_func=lambda x: f"{x} - {mapeo_contratistas.get(x, '')}",
        key=f"{key_prefix}_cuit",
        help="Seleccione el contratista de la base de datos.",
    )

    # FILA 3: Descripcion Obra (Ancho Completo con Info)
    # Reemplazá con tu consulta de obras activas
    df_obras = get_obras()

    desc_obra = st.selectbox(
        "Descripcion Obra",
        index= None,
        placeholder="Elegir una Obra.",
        options=df_obras.desc_obra.to_list(),
        help="Seleccione la obra asociada al gasto.",
        key=f"{key_prefix}_obra",
    )

    # FILA 4: Cuenta Bancaria (2 Columnas: Select + Texto Disabled)
    # Reemplazá con tus cuentas de INVICO
    cuentas_bancarias = ["CUENTA 1234/5", "CUENTA 6789/0"]
    denominaciones_cuentas = {
        "CUENTA 1234/5": "CTA. CTE. BANCO CORRIENTES - FDO. PROPIO",
        "CUENTA 6789/0": "CTA. CTE. BANCO NACION - FDO. NACIONAL",
    }

    col4_1, col4_2 = st.columns([1, 2])

    # Callback para actualizar la denominación de forma reactiva
    def update_denom_cuenta():
        sel_cuenta = st.session_state[f"{key_prefix}_cuenta"]
        st.session_state[f"{key_prefix}_denom_cuenta"] = denominaciones_cuentas.get(
            sel_cuenta, "Elija una cuenta válida"
        )

    cuenta_bancaria = col4_1.selectbox(
        "Cuenta Bancaria",
        options=["Elegir una opción"] + cuentas_bancarias,
        key=f"{key_prefix}_cuenta",
        on_change=update_denom_cuenta,
    )

    denominacion_cuenta = col4_2.text_input(
        "Denominacion Cuenta Bancaria",
        value=st.session_state.get(f"{key_prefix}_denom_cuenta", ""),
        disabled=True,
        key=f"{key_prefix}_denom_cuenta_input",
    )

    # FILA 5: Fuente Financiamiento (2 Columnas: Select + Texto Disabled)
    # Reemplazá con tus fuentes de INVICO
    fuentes_fin = ["Fto. 10", "Fto. 11", "Fto. 13"]
    denominaciones_fuentes = {
        "Fto. 10": "TESORO PROVINCIAL",
        "Fto. 11": "RECURSOS PROPIOS",
        "Fto. 13": "FONAVI",
    }

    col5_1, col5_2 = st.columns([1, 2])

    # Callback para la fuente
    def update_denom_fuente():
        sel_fuente = st.session_state[f"{key_prefix}_fuente"]
        st.session_state[f"{key_prefix}_denom_fuente"] = denominaciones_fuentes.get(
            sel_fuente, "Elija una fuente válida"
        )

    fuente_fin = col5_1.selectbox(
        "Fuente Financiamiento",
        options=["Elegir una opción"] + fuentes_fin,
        key=f"{key_prefix}_fuente",
        on_change=update_denom_fuente,
    )

    denominacion_fuente = col5_2.text_input(
        "Denominacion Fuente",
        value=st.session_state.get(f"{key_prefix}_denom_fuente", ""),
        disabled=True,
        key=f"{key_prefix}_denom_fuente_input",
    )

    # FILA 6: Monto Bruto, Avance Fisico, Nro Certificado
    # Usamos numbers inputs y text inputs con formato para replicar la imagen.
    col6_1, col6_2, col6_3 = st.columns([2, 1.5, 2])

    monto_bruto = col6_1.number_input(
        "Monto Bruto",
        min_value=0.0,
        value=0.0,
        step=1000.0,
        format="%.2f",
        key=f"{key_prefix}_monto",
    )

    avance_fisico = col6_2.number_input(
        "Avance Fisico Acum. %",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.01,
        label_visibility="visible",
        key=f"{key_prefix}_avance",
    )

    # # Replicamos la cajita '%' de la imagen
    # with col6_2:
    #     col6_2_1, col6_2_2 = st.columns([3, 1])
    #     avance_fisico = col6_2_1.number_input(
    #         "Avance Fisico Acum. %",
    #         min_value=0.0,
    #         max_value=100.0,
    #         value=0.0,
    #         step=0.01,
    #         label_visibility="visible",
    #         key=f"{key_prefix}_avance",
    #     )
    #     col6_2_2.markdown("## ")  # Alineación vertical
    #     col6_2_2.markdown("## **%**")

    nro_certificado = col6_3.text_input(
        "Nro Certificado", placeholder="Ej: Cert. N° 4", key=f"{key_prefix}_certificado"
    )

    # st.markdown("## ")  # Espaciado final

    # FILA 7: BOTONES (Cancel, Agregar) Alineados a la Derecha
    # En Streamlit, esto es lo más difícil sin usar CSS Sucio. Usamos columnas para empujar a la derecha.
    col_btn1, col_btn2, col_btn3 = st.columns([8, 2, 2])

    # Botón Cancelar (Alineado a la derecha del expander de error o confirmación)
    if col_btn2.button("CANCELAR", type="secondary", key=f"{key_prefix}_btn_cancel"):
        st.rerun()  # Cierra el modal de forma segura

    # Botón AGREGAR (Primary, Color Principal)
    if col_btn3.button("AGREGAR", type="primary", key=f"{key_prefix}_btn_add"):
        # 1. Validación de Datos (Fundamental para INVICO)
        if (
            nro_comprobante == ""
            or cuit_contratista == "Elegir una opción"
            or desc_obra == "Elegir una opción del listado"
            or cuenta_bancaria == "Elegir una opción"
            or monto_bruto <= 0
        ):
            st.error("❌ Por favor complete todos los campos obligatorios.")
        else:
            with st.spinner("Procesando y Guardando..."):
                # 2. Preparación del payload para el POST
                payload = {
                    "nroComprobante": nro_comprobante.strip(),
                    "fecha": fecha.strftime("%Y-%m-%d"),  # Formato ISO para MongoDB
                    "tipo": tipo_gasto,
                    "cuitContratista": cuit_contratista.strip(),
                    "descObra": desc_obra.strip(),
                    "codObra": desc_obra.strip().split(" - ")[
                        0
                    ],  # Si tenés el cod_obra ahí
                    "cuentaBancaria": cuenta_bancaria,
                    "denomCuenta": denominacion_cuenta,
                    "fuenteFin": fuente_fin,
                    "denomFuente": denominacion_fuente,
                    "montoBruto": monto_bruto,
                    "avanceFisico": avance_fisico,
                    "nroCertificado": nro_certificado.strip(),
                    "updated_at": date.today().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # 3. Llamada al POST_REQUEST (Usando tus funciones existentes)
                # Reemplazá 'carga' con la ruta real relativa a tu Endpoints.ICARO_CARGA
                try:
                    res = post_request(
                        endpoint=Endpoints.ICARO_CARGA.value + "/add_one",
                        json_body=payload,
                    )

                    if res.status_code in [200, 201]:
                        # Feedback visual como vimos antes
                        st.balloons()
                        st.toast(
                            f"✅ Comprobante N° {nro_comprobante} agregado con éxito a ICARO.",
                            icon="📈",
                        )

                        # Guardamos un flag para el rerun final si es necesario
                        st.session_state[f"{key_prefix}_post_success"] = True

                        # Usamos un pequeño delay para que disfrute los globos y el toast
                        import time

                        time.sleep(2)
                        st.rerun()  # Esto cierra el modal y recarga la página principal
                    else:
                        st.error(f"⚠️ Error de API ({res.status_code}): {res.text}")

                except Exception as e:
                    # Usamos tu handler si lo tenés
                    # handle_api_error(e)
                    st.error(
                        f"❌ Error de Conexión: No se pudo contactar con la API de ICARO. {e}"
                    )
