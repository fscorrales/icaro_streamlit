__all__ = ["modal_comprobante_gasto", "modal_delete_comprobante"]

from datetime import date, datetime

import streamlit as st

import src.utils.exceptions as ex
from src.components import button_cancel, button_submit
from src.constants import Endpoints
from src.services import (
    delete_request,
    get_ctas_ctes,
    get_obras,
    get_proveedores,
    post_request,
    put_request,
)
from src.utils.transform_data import build_retenciones_payload


# --- MODAL: AGREGAR COMPROBANTE DE GASTO ---
@st.dialog("Agregar / Editar Comprobante Gasto", width="medium")
def modal_comprobante_gasto(
    key_prefix: str, datos_carga: dict = None, es_edicion: bool = False
):
    # Si datos_carga existe, lo usamos. Si no, inicializamos vacío.
    form_data = datos_carga if datos_carga else {}

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

            except Exception:
                st.session_state[f"{key_prefix}_fuente_index"] = None

    # FILA 1: 4 Columnas (Nro, Fecha, Nro ICARO, Tipo)
    col1_1, col1_2, col1_3, col1_4 = st.columns([1, 2, 2, 1])

    raw_nro_comprobante = col1_1.text_input(
        "Nro Comprobante",
        max_chars=5,
        key=f"{key_prefix}_nro",
        value=form_data.get("nro_comprobante", "")[:5],
    )
    nro_solo_numeros = "".join(filter(str.isdigit, raw_nro_comprobante))

    # Para el caso de la fecha, hay que convertirla a objeto date si viene como string
    fecha_previa = form_data.get("fecha", date.today())
    fecha = col1_2.date_input(
        "Fecha", value=fecha_previa, format="DD-MM-YYYY", key=f"{key_prefix}_fecha"
    )

    formato_contable = (
        f"{nro_solo_numeros.zfill(5)}/{fecha.strftime('%y')}"
        if nro_solo_numeros
        else ""
    )
    nro_comprobante = col1_3.text_input(
        "Nro Autogerado ICARO",
        disabled=True,
        value=formato_contable,
        key=f"{key_prefix}_nro_comprobante_{formato_contable}",
    )

    lista_tipos = ["CYO", "REG", "PA6"]
    tipo_previo = form_data.get("tipo")
    idx_tipo = lista_tipos.index(tipo_previo) if tipo_previo in lista_tipos else None
    tipo = col1_4.selectbox(
        "Tipo",
        index=idx_tipo,
        options=lista_tipos,
        key=f"{key_prefix}_tipo",
        placeholder="",
    )

    # FILA 2: CUIT Contratista (Ancho Completo con Info)
    # Creamos un diccionario donde la clave es el CUIT y el valor es el Nombre
    # Esto hace que el mapeo en format_func sea instantáneo
    lista_cuit = df_prov.cuit.to_list()
    cuit_previo = form_data.get("cuit")
    idx_cuit = lista_cuit.index(cuit_previo) if cuit_previo in lista_cuit else None
    mapeo_contratistas = dict(zip(df_prov.cuit, df_prov.desc_proveedor))

    cuit = st.selectbox(
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
    lista_obras = df_obras.desc_obra.to_list()
    desc_obra_previo = form_data.get("desc_obra")
    idx_obra = (
        lista_obras.index(desc_obra_previo) if desc_obra_previo in lista_obras else None
    )
    imputaciones = [
        f"{act}-{part}" for act, part in zip(df_obras.actividad, df_obras.partida)
    ]
    mapeo_obras = dict(
        zip(df_obras.desc_obra, imputaciones)
    )  # Mapeo para mostrar actividad y partida juntos

    desc_obra = st.selectbox(
        "Descripcion Obra",
        index=idx_obra,
        placeholder="Elegir una Obra.",
        options=lista_obras,
        format_func=lambda x: f"{x} ({mapeo_obras.get(x, '')})",
        key=f"{key_prefix}_obra",
        help="Seleccione la obra asociada al gasto.",
        on_change=handle_obra_change,
    )

    # Si hay una obra elegida, mostramos el "renglón extra" manualmente
    if desc_obra:
        imputacion_completa = mapeo_obras.get(desc_obra, "")
        partes = imputacion_completa.split("-")
        if len(partes) > 1:
            partida = partes[-1]
            # Reconstruimos la actividad uniendo todo lo anterior con guiones
            actividad = "-".join(partes[:-1])
        else:
            actividad, partida = imputacion_completa, ""
        st.caption(
            f"**Descripción:** {desc_obra} - **Estructura:** {imputacion_completa}"
        )
        # st.caption(f"**Imputación:** {mapeo_obras.get(desc_obra, '')}")

    # FILA 4: Cuenta Bancaria + Fuente Financiamiento
    col4_1, col4_2 = st.columns(2)
    mapeo_ctas_ctes = dict(zip(df_ctas_ctes.icaro_cta_cte, df_ctas_ctes.desc_cta_cte))

    cta_cte = col4_1.selectbox(
        "Cuenta Bancaria",
        index=st.session_state[f"{key_prefix}_cuenta_index"],
        placeholder="Elegir una Cuenta Bancaria.",
        options=df_ctas_ctes.icaro_cta_cte.to_list(),
        format_func=lambda x: f"{x} ({mapeo_ctas_ctes.get(x, '')})",
        key=f"{key_prefix}_cuenta_{st.session_state.get(f'{key_prefix}_refresh_cuenta', 0)}",
    )

    fuente = col4_2.selectbox(
        "Fuente Financiamiento",
        index=st.session_state[f"{key_prefix}_fuente_index"],
        placeholder="Elegir una Fuente de Financiamiento.",
        options=["10", "11", "13"],
        key=f"{key_prefix}_fuente_{st.session_state.get(f'{key_prefix}_refresh_fuente', 0)}",
    )

    # FILA 5: Monto Bruto, Avance Fisico, Nro Certificado
    # Usamos numbers inputs y text inputs con formato para replicar la imagen.
    col5_1, col5_2, col5_3 = st.columns([2, 1.5, 2])

    importe = col5_1.number_input(
        "Monto Bruto",
        min_value=0.0,
        value=form_data.get("importe", 0.0),
        step=1000.0,
        format="%.2f",
        key=f"{key_prefix}_importe",
    )

    avance = col5_2.number_input(
        "Avance Fisico Acum. %",
        min_value=0.0,
        max_value=100.0,
        value=float(form_data.get("avance", 0.0) * 100),
        step=10.0,
        label_visibility="visible",
        format="%.2f",
        key=f"{key_prefix}_avance",
    )

    nro_certificado = col5_3.text_input(
        "Nro Certificado",
        placeholder="",
        key=f"{key_prefix}_nro_certificado",
        value=form_data.get("nro_certificado", ""),
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
        if button_submit(
            "Editar" if es_edicion else "Agregar",
            key=f"{key_prefix}_btn_add",
        ):
            # 1. Validación de Datos
            errores = []
            if raw_nro_comprobante is None:
                errores.append(
                    "El número de comprobante es obligatorio y debe ser numérico."
                )
            if not tipo or tipo == "":
                errores.append("Debe seleccionar un Tipo de Comprobante.")
            if not cuit or cuit == "":
                errores.append("Debe seleccionar un Contratista.")
            if not desc_obra or desc_obra == "":
                errores.append("Debe seleccionar una Obra.")
            if not cta_cte or cta_cte == "":
                errores.append("Debe seleccionar una Cuenta Bancaria.")
            if not fuente or fuente == "":
                errores.append("Debe seleccionar una Fuente de Financiamiento.")
            if importe <= 0:
                errores.append("El importe debe ser mayor a $0.")
            if avance < 0:
                errores.append("El avance físico debe ser mayor o igual a 0%.")

            if errores:
                for err in errores:
                    st.toast(err, icon="⚠️")
            else:
                with st.spinner("Procesando y Guardando..."):
                    # 2. Preparación del payload para el POST
                    payload = {
                        "ejercicio": int(fecha.year),
                        "mes": f"{str(fecha.month).zfill(2)}/{str(fecha.year)}",
                        "fecha": fecha.strftime("%Y-%m-%d"),  # Formato ISO para MongoDB
                        "id_carga": f"{nro_comprobante}{tipo[:1]}",
                        "nro_comprobante": nro_comprobante,
                        "tipo": tipo,
                        "fuente": fuente,
                        "actividad": actividad,
                        "partida": partida,
                        "cta_cte": cta_cte,
                        "cuit": cuit,
                        "importe": importe,
                        "fondo_reparo": 0,
                        "avance": (avance / 100)
                        if (avance > 0)
                        else 0,  # Convertimos a decimal para la API
                        "nro_certificado": nro_certificado,
                        "desc_obra": desc_obra,
                        "origen": form_data.get("origen", ""),
                        "updated_at": form_data.get(
                            "updated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ),
                    }
                    # print(
                    #     "Payload a enviar a ICARO:", payload
                    # )  # Debug: Ver el payload en la consola
                    # 3. Llamada al POST_REQUEST (Usando tus funciones existentes)
                    try:
                        if es_edicion:
                            id = str(form_data.get("id"))
                            # print(f"ID para edición: {id}")  # Debug: Ver el ID en la consola
                            res = put_request(
                                endpoint=f"{Endpoints.ICARO_CARGA.value}/update_one/{id}",
                                json_body=payload,
                            )
                        else:
                            res = post_request(
                                endpoint=Endpoints.ICARO_CARGA.value + "/add_one",
                                json_body=payload,
                            )

                        # if res.status_code in [200, 201]:
                        if res:
                            # Feedback visual como vimos antes
                            st.snow()
                            st.toast(
                                f"✅ Comprobante N° {nro_comprobante} {'agreagado' if not es_edicion else 'editado'} con éxito",
                                icon="📈",
                            )
                            # Procedemos a cargar las retenciones si vengo de AUTOCARGA
                            if not es_edicion and form_data.get("origen") != "":
                                payload = build_retenciones_payload(datos_carga)
                                res_ret = post_request(
                                    endpoint=Endpoints.ICARO_RETENCIONES.value
                                    + f"/add_many/{nro_comprobante}{tipo[:1]}",
                                    json_body=payload,
                                )
                                if res_ret:
                                    st.toast(
                                        "✅ Retenciones asociadas agregadas con éxito",
                                        icon="🧾",
                                    )
                                else:
                                    st.toast(
                                        "⚠️ Error al agregar retenciones asociadas. Por favor, revisa el comprobante.",
                                        icon="⚠️",
                                    )

                            # Guardamos un flag para el rerun final si es necesario
                            st.session_state[f"{key_prefix}_post_success"] = True
                            st.session_state["carga_dataframes_iteration"] += 1

                            # Usamos un pequeño delay para que disfrute los globos y el toast
                            import time

                            time.sleep(2)
                            st.rerun()  # Esto cierra el modal y recarga la página principal
                        # else:
                        #     st.error(f"⚠️ Error de API ({res.status_code}): {res.text}")

                    except (
                        ex.AppBaseException
                    ) as e:  # Captura cualquier error definido por ti
                        st.error(f"❌ Error: {e}")
                    except Exception as e:
                        st.error(f"❌ Ocurrió un error inesperado. {e}")


# --- MODAL: ELIMINAR COMPROBANTE DE GASTO ---
@st.dialog("Confirmar Eliminación PERMANENTE", width="small")
def modal_delete_comprobante(
    id_mongo: str, id_carga_contable: str, key_prefix: str = ""
):
    st.warning(
        f"⚠️ ¿Estás seguro de que deseás eliminar el comprobante **{id_carga_contable}**?"
    )
    st.write(
        "Esta acción es permanente y también eliminará todas las retenciones asociadas."
    )

    st.markdown("---")
    with st.container(
        horizontal=True, border=False, horizontal_alignment="center", gap="large"
    ):
        if button_cancel("Cancelar", key=f"{key_prefix}_btn_cancel", type="secondary"):
            st.rerun()

        if button_submit("Si, Eliminar", key=f"{key_prefix}_btn_eliminar"):
            with st.spinner("Eliminando registros..."):
                try:
                    print(id_mongo)
                    # 1. Borramos Retenciones (Cascada)
                    # Usamos el id_carga contable (ej: 00999/26C) como string
                    # res_ret = delete_request(
                    #     f"{Endpoints.ICARO_RETENCIONES.value}/delete_many/{id_carga_contable}"
                    # )

                    # 2. Borramos el Comprobante de Carga
                    # Usamos el ID técnico de MongoDB
                    res_carga = delete_request(
                        f"{Endpoints.ICARO_CARGA.value}/delete_one/{id_mongo}"
                    )

                    if res_carga:
                        st.success("Registros eliminados correctamente.")
                        st.session_state["carga_dataframes_iteration"] += 1
                        import time

                        time.sleep(2)
                        st.rerun()

                except Exception as e:
                    st.error(f"Error al eliminar: {e}")
