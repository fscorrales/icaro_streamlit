__all__ = ["modal_agregar_gasto"]

from datetime import date

import streamlit as st

from src.components import button_cancel, button_submit
from src.constants import Endpoints
from src.services import get_ctas_ctes, get_obras, get_proveedores, post_request


# --- MODAL: AGREGAR COMPROBANTE DE GASTO ---
@st.dialog("Agregar Comprobante Gasto", width="medium")
def modal_agregar_gasto(key_prefix: str, datos_edicion: dict = None):
    # Si datos_edicion existe, lo usamos. Si no, inicializamos vacío.
    form_data = datos_edicion if datos_edicion else {}

    # Traemos los DATOS
    df_obras = get_obras()
    df_ctas_ctes = get_ctas_ctes()
    df_prov = get_proveedores()

    # Inicializamos el índice de cta_cte en el state si no existe
    if f"{key_prefix}_cuenta_index" not in st.session_state:
        # Si estamos editando, buscamos el índice de la cuenta que ya traía el registro
        cta_previa = form_data.get("cta_cte")
        lista_cuentas = df_ctas_ctes.icaro_cta_cte.to_list()

        if cta_previa in lista_cuentas:
            st.session_state[f"{key_prefix}_cuenta_index"] = lista_cuentas.index(
                cta_previa
            )
        else:
            st.session_state[f"{key_prefix}_cuenta_index"] = None

    # Inicializá el contador al principio del modal
    if f"{key_prefix}_refresh_cuenta" not in st.session_state:
        st.session_state[f"{key_prefix}_refresh_cuenta"] = 0

    # Inicializamos el índice de fuente en el state si no existe
    if f"{key_prefix}_fuente_index" not in st.session_state:
        # Si estamos editando, buscamos el índice de la cuenta que ya traía el registro
        fuente_previa = form_data.get("fuente")
        lista_fuentes = ["10", "11", "13"]

        if fuente_previa in lista_fuentes:
            st.session_state[f"{key_prefix}_fuente_index"] = lista_fuentes.index(
                fuente_previa
            )
        else:
            st.session_state[f"{key_prefix}_fuente_index"] = None

    # Inicializá el contador al principio del modal
    if f"{key_prefix}_refresh_fuente" not in st.session_state:
        st.session_state[f"{key_prefix}_refresh_fuente"] = 0

    # Definimos la función de actualización del cta_cte sugerido
    def handle_obra_change():
        obra_elegida = st.session_state.get(f"{key_prefix}_obra")
        if obra_elegida:
            try:
                # Buscamos la cta_cte sugerida
                fila_obra = df_obras[df_obras.desc_obra == obra_elegida]
                if not fila_obra.empty:
                    # Buscamos el índice en la lista de cuentas
                    cta_sugerida = fila_obra["cta_cte"].iloc[0]
                    lista_cuentas = df_ctas_ctes.icaro_cta_cte.to_list()
                    if cta_sugerida in lista_cuentas:
                        # Actualizamos el índice
                        st.session_state[f"{key_prefix}_cuenta_index"] = (
                            lista_cuentas.index(cta_sugerida)
                        )
                        # INCREMENTAMOS un disparador de refresco
                        st.session_state[f"{key_prefix}_refresh_cuenta"] += 1
                    else:
                        st.session_state[f"{key_prefix}_cuenta_index"] = None

                    # Buscamos el índice en la lista de fuentes
                    fuente_sugerida = fila_obra["fuente"].iloc[0]
                    lista_fuentes = ["10", "11", "13"]
                    if fuente_sugerida in lista_fuentes:
                        # Actualizamos el índice
                        st.session_state[f"{key_prefix}_fuente_index"] = (
                            lista_fuentes.index(fuente_sugerida)
                        )
                        # INCREMENTAMOS un disparador de refresco
                        st.session_state[f"{key_prefix}_refresh_fuente"] += 1
                    else:
                        st.session_state[f"{key_prefix}_fuente_index"] = None

            except Exception as e:
                st.session_state[f"{key_prefix}_fuente_index"] = None

    # FILA 1: 4 Columnas (Nro, Fecha, Nro ICARO, Tipo)
    col1_1, col1_2, col1_3, col1_4 = st.columns([2, 2, 2, 1])

    nro_comprobante = col1_1.text_input(
        "Nro Comprobante",
        key=f"{key_prefix}_nro",
        value=form_data.get("nro_comprobante", "")[:5],
    )

    # Para el caso de la fecha, hay que convertirla a objeto date si viene como string
    fecha_previa = form_data.get("fecha", date.today())
    fecha = col1_2.date_input(
        "Fecha", value=fecha_previa, format="DD-MM-YYYY", key=f"{key_prefix}_fecha"
    )

    # El Nro ICARO suele ser autogenerado o gris en tu imagen
    nro_icaro = col1_3.text_input(
        "Nro ICARO",
        placeholder="Autogenerado",
        disabled=True,
        value=form_data.get("nro_comprobante", ""),
        key=f"{key_prefix}_icaro",
    )

    lista_tipos = ["CYO", "REG", "PA6"]
    tipo_previo = form_data.get("tipo")
    idx_tipo = lista_tipos.index(tipo_previo) if tipo_previo in lista_tipos else None
    tipo_gasto = col1_4.selectbox(
        "Tipo", index=idx_tipo, options=lista_tipos, key=f"{key_prefix}_tipo"
    )

    # FILA 2: CUIT Contratista (Ancho Completo con Info)
    # Creamos un diccionario donde la clave es el CUIT y el valor es el Nombre
    # Esto hace que el mapeo en format_func sea instantáneo
    lista_cuit = df_prov.cuit.to_list()
    cuit_previo = form_data.get("cuit")
    idx_cuit = lista_cuit.index(cuit_previo) if cuit_previo in lista_cuit else None
    mapeo_contratistas = dict(zip(df_prov.cuit, df_prov.desc_proveedor))

    cuit_contratista = st.selectbox(
        "Contratista",
        index=idx_cuit,
        placeholder="Elegir un Contratista.",
        options=df_prov.cuit.to_list(),
        format_func=lambda x: f"{x} - {mapeo_contratistas.get(x, '')}",
        key=f"{key_prefix}_cuit",
        help="Seleccione el contratista de la base de datos.",
    )

    # FILA 3: Descripcion Obra (Ancho Completo con Info)
    # Reemplazá con tu consulta de obras activas
    lista_obras = df_prov.cuit.to_list()
    desc_obra_previo = form_data.get("desc_obra")
    idx_obra = (
        lista_obras.index(desc_obra_previo) if desc_obra_previo in lista_obras else None
    )

    mapeo_obras = dict(zip(df_obras.desc_obra, df_obras.actividad))

    desc_obra = st.selectbox(
        "Descripcion Obra",
        index=idx_obra,
        placeholder="Elegir una Obra.",
        options=df_obras.desc_obra.to_list(),
        format_func=lambda x: f"{x} ({mapeo_obras.get(x, '')})",
        key=f"{key_prefix}_obra",
        help="Seleccione la obra asociada al gasto.",
        on_change=handle_obra_change,
    )

    # Si hay una obra elegida, mostramos el "renglón extra" manualmente
    if desc_obra:
        st.caption(f"**Descripción:** {desc_obra}")
        # st.caption(f"**Imputación:** {mapeo_obras.get(desc_obra, '')}")

    # FILA 4: Cuenta Bancaria + Fuente Financiamiento
    col4_1, col4_2 = st.columns(2)
    mapeo_ctas_ctes = dict(zip(df_ctas_ctes.icaro_cta_cte, df_ctas_ctes.desc_cta_cte))

    cuenta_bancaria = col4_1.selectbox(
        "Cuenta Bancaria",
        index=st.session_state[f"{key_prefix}_cuenta_index"],
        placeholder="Elegir una Cuenta Bancaria.",
        options=df_ctas_ctes.icaro_cta_cte.to_list(),
        format_func=lambda x: f"{x} ({mapeo_ctas_ctes.get(x, '')})",
        key=f"{key_prefix}_cuenta_{st.session_state.get(f'{key_prefix}_refresh_cuenta', 0)}",
    )

    # FILA 5: Fuente Financiamiento
    # Reemplazá con tus fuentes de INVICO
    # fuentes_fin = ["Fto. 10", "Fto. 11", "Fto. 13"]
    # denominaciones_fuentes = {
    #     "Fto. 10": "TESORO PROVINCIAL",
    #     "Fto. 11": "RECURSOS PROPIOS",
    #     "Fto. 13": "FONAVI",
    # }

    fuente = col4_2.selectbox(
        "Fuente Financiamiento",
        index=st.session_state[f"{key_prefix}_fuente_index"],
        placeholder="Elegir una Fuente de Financiamiento.",
        options=["10", "11", "13"],
        key=f"{key_prefix}_fuente_{st.session_state.get(f'{key_prefix}_refresh_fuente', 0)}",
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

    with st.container(
        horizontal=True, border=False, horizontal_alignment="center", gap="large"
    ):
        # Botón Cancelar (Alineado a la derecha del expander de error o confirmación)
        if button_cancel("Cancelar", type="secondary", key=f"{key_prefix}_btn_cancel"):
            st.rerun()  # Cierra el modal de forma segura

        # Botón AGREGAR (Primary, Color Principal)
        if button_submit("Agregar", key=f"{key_prefix}_btn_add"):
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
