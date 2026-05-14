__all__ = [
    "modal_comprobante_gasto",
    "modal_delete_gasto",
    "modal_obras",
    "modal_estructura",
    "modal_delete_registro_gral",
]

from datetime import date, datetime

import pandas as pd
import streamlit as st

import src.utils.exceptions as ex
from src.components import button_cancel, button_submit
from src.constants import Endpoints
from src.services import (
    delete_request,
    get_ctas_ctes,
    get_estructuras,
    get_obras,
    get_proveedores,
    patch_request,
    post_request,
    put_request,
)
from src.utils.transform_data import build_retenciones_payload


# --- MODAL: AGREGAR COMPROBANTE DE GASTO ---
@st.dialog("Agregar / Editar Comprobante Gasto", width="medium")
def modal_comprobante_gasto(
    key_prefix: str, datos_carga: dict = None, es_edicion: bool = False
):
    id_carga = ""
    # Si datos_carga existe, lo usamos. Si no, inicializamos vacío.
    form_data = datos_carga if datos_carga else {}

    # Traemos los DATOS
    df_obras = get_obras(
        update_trigger=st.session_state.get("obras_uploader_iteration", 0)
    )
    df_ctas_ctes = get_ctas_ctes()
    df_prov = get_proveedores(
        update_trigger=st.session_state.proveedores_uploader_iteration
    )

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
                    id_carga = f"{nro_comprobante}{tipo[:1]}"
                    payload = {
                        "ejercicio": int(fecha.year),
                        "mes": f"{str(fecha.month).zfill(2)}/{str(fecha.year)}",
                        "fecha": fecha.strftime("%Y-%m-%d"),  # Formato ISO para MongoDB
                        "id_carga": id_carga,
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
                            # Procedemos a cargar las retenciones y la información de autocarga
                            # si vengo de AUTOCARGA
                            if not es_edicion and form_data.get("origen") != "":
                                payload = build_retenciones_payload(datos_carga)
                                res_ret = post_request(
                                    endpoint=Endpoints.ICARO_RETENCIONES.value
                                    + f"/add_many/{id_carga}",
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

                                # Actualizamos la información de carga
                                res_aut = False
                                origen = str(form_data.get("origen")).lower()
                                if origen == "certificados":
                                    payload = {"id_carga": id_carga}
                                    res_aut = patch_request(
                                        endpoint=Endpoints.ICARO_INFORME_CONTABLE.value
                                        + f"/update_id_carga/{str(form_data.get('id'))}",
                                        json_body=payload,
                                    )
                                else:
                                    payload = {
                                        "ids": form_data.get("id"),
                                        "id_carga": id_carga,
                                    }
                                    res_aut = patch_request(
                                        endpoint=Endpoints.ICARO_RESUMEN_REND_OBRAS.value
                                        + "/update_id_carga",
                                        json_body=payload,
                                    )
                                if res_aut:
                                    st.toast(
                                        "✅ Información de carga actualizada con éxito",
                                        icon="✅",
                                    )
                                    st.session_state[
                                        f"autocarga_{'obras' if origen == 'certificados' else 'epam'}_uploader_iteration"
                                    ] += 1
                                else:
                                    st.toast(
                                        "⚠️ Error al actualizar la información de carga. Por favor, revisa el comprobante.",
                                        icon="⚠️",
                                    )

                            # Guardamos un flag para el rerun final si es necesario
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
def modal_delete_gasto(
    id_mongo: str, id_carga_contable: str, origen: str = "", key_prefix: str = ""
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
                    origen = origen.lower()
                    # 1. Borrar Carga
                    res_carga = delete_request(
                        f"{Endpoints.ICARO_CARGA.value}/delete_one/{id_mongo}"
                    )
                    # 2. Borrar Retenciones
                    res_retenciones = delete_request(
                        f"{Endpoints.ICARO_RETENCIONES.value}/delete_many/{id_carga_contable}"
                    )
                    # 3. Desvincular Informe Contable (Limpiar el campo id_carga)
                    if origen != "":
                        res_desvinculo = patch_request(
                            f"{Endpoints.ICARO_INFORME_CONTABLE.value if origen == 'certificados' else Endpoints.ICARO_RESUMEN_REND_OBRAS.value}/unlink_by_carga/{id_carga_contable}"
                        )

                    if res_carga and res_retenciones:
                        st.success(
                            "Comprobante, retenciones y vínculo eliminados correctamente."
                        )
                        st.session_state["carga_dataframes_iteration"] += 1
                        if origen != "":
                            origen = "obras" if origen == "certificados" else "epam"
                            if (
                                f"autocarga_{origen}_uploader_iteration"
                                not in st.session_state
                            ):
                                st.session_state[
                                    f"autocarga_{origen}_uploader_iteration"
                                ] = 0
                            else:
                                st.session_state[
                                    f"autocarga_{origen}_uploader_iteration"
                                ] += 1
                    else:
                        st.error(
                            "Error al eliminar los registros. Por favor, intenta nuevamente."
                        )

                    import time

                    time.sleep(2)
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al eliminar: {e}")


# --- MODAL: AGREGAR OBRA ---
@st.dialog("Agregar / Editar Obra", width="medium")
def modal_obras(
    key_prefix: str,
    datos_carga: dict = None,
    es_edicion: bool = False,
    es_autocarga: bool = False,
):
    # Si datos_carga existe, lo usamos. Si no, inicializamos vacío.
    form_data = datos_carga if datos_carga else {}

    # Traemos los DATOS
    df_ctas_ctes = get_ctas_ctes()
    df_prov = get_proveedores(
        update_trigger=st.session_state.proveedores_uploader_iteration
    )
    df_actividades = get_estructuras(
        update_trigger=st.session_state.estructuras_uploader_iteration
    )
    df_actividades = df_actividades[df_actividades["estructura"].str.len() == 11]
    df_obras = get_obras(
        update_trigger=st.session_state.get("obras_uploader_iteration", 0)
    )
    lista_localidades = (
        df_obras["localidad"].str.upper().sort_values().unique().tolist()
    )
    lista_info_adicional = df_obras["info_adicional"].sort_values().unique().tolist()

    # Inicializamos el índice de partida en el state si no existe
    if f"{key_prefix}_partida_index" not in st.session_state:
        # Si estamos editando, buscamos el índice de la partida que ya traía el registro
        partida_previa = form_data.get("partida")
        lista_partidas = ["354", "421", "422"]

        if partida_previa in lista_partidas:
            st.session_state[f"{key_prefix}_partida_index"] = lista_partidas.index(
                partida_previa
            )
        else:
            st.session_state[f"{key_prefix}_partida_index"] = None

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

    # Inicializamos el índice de localidades en el state si no existe
    if f"{key_prefix}_localidad_index" not in st.session_state:
        # Si estamos editando, buscamos el índice de la localidad que ya traía el registro
        localidad_previa = form_data.get("localidad")

        if localidad_previa in lista_localidades:
            st.session_state[f"{key_prefix}_localidad_index"] = lista_localidades.index(
                localidad_previa
            )
        else:
            st.session_state[f"{key_prefix}_localidad_index"] = None

    # Inicializamos el índice de Info Adicional en el state si no existe
    if f"{key_prefix}_info_adicional_index" not in st.session_state:
        # Si estamos editando, buscamos el índice de la localidad que ya traía el registro
        info_adicional_previa = form_data.get("info_adicional")

        if info_adicional_previa in lista_info_adicional:
            st.session_state[f"{key_prefix}_info_adicional_index"] = (
                lista_info_adicional.index(info_adicional_previa)
            )
        else:
            st.session_state[f"{key_prefix}_info_adicional_index"] = None

    # FILA 1: Descripción de la Obra (Ancho Completo)
    desc_obra = st.text_input(
        "Descripción de la Obra",
        key=f"{key_prefix}_desc_obra",
        value=form_data.get("desc_obra", ""),
        disabled=es_autocarga,
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

    # FILA 3: Actividad + Partida (Ancho Completo con Info)
    col3_1, col3_2 = st.columns([2, 1])
    lista_actividades = df_actividades.estructura.to_list()
    actividad_previa = form_data.get("actividad")
    idx_actividad = (
        lista_actividades.index(actividad_previa)
        if actividad_previa in lista_actividades
        else None
    )
    mapeo_actividades = dict(
        zip(df_actividades.estructura, df_actividades.desc_estructura)
    )

    actividad = col3_1.selectbox(
        "Actividad",
        index=idx_actividad,
        placeholder="Elegir una Actividad.",
        options=lista_actividades,
        format_func=lambda x: f"{x} - {mapeo_actividades.get(x, '')}",
        key=f"{key_prefix}_actividad",
        help="Seleccione la actividad de la base de datos.",
    )

    partida = col3_2.selectbox(
        "Partida Presupuestaria",
        index=st.session_state[f"{key_prefix}_partida_index"],
        placeholder="Elegir una Partida.",
        options=["354", "421", "422"],
        key=f"{key_prefix}_partida",
    )

    # FILA 4: Cuenta Bancaria + Fuente Financiamiento
    col4_1, col4_2 = st.columns(2)
    mapeo_ctas_ctes = dict(zip(df_ctas_ctes.icaro_cta_cte, df_ctas_ctes.desc_cta_cte))

    cta_cte = col4_1.selectbox(
        "Cuenta Bancaria",
        index=st.session_state[f"{key_prefix}_cuenta_index"],
        placeholder="Elegir una Cuenta Bancaria.",
        options=df_ctas_ctes.icaro_cta_cte.to_list(),
        format_func=lambda x: f"{x} ({mapeo_ctas_ctes.get(x, '')})",
        key=f"{key_prefix}_cuenta_corriente",
    )

    fuente = col4_2.selectbox(
        "Fuente Financiamiento",
        index=st.session_state[f"{key_prefix}_fuente_index"],
        placeholder="Elegir una Fuente de Financiamiento.",
        options=["10", "11", "13"],
        key=f"{key_prefix}_fuente",
    )

    # FILA 5: Localidad + Norma Legal + Info Adicional
    # Usamos numbers inputs y text inputs con formato para replicar la imagen.
    col5_1, col5_2, col5_3 = st.columns([1, 1, 1])

    localidad = col5_1.selectbox(
        "Localidad",
        index=st.session_state[f"{key_prefix}_localidad_index"],
        placeholder="Elegir una Localidad.",
        options=lista_localidades,
        key=f"{key_prefix}_localidad",
        accept_new_options=True,
    )

    norma_legal = col5_2.text_input(
        "Norma Legal",
        key=f"{key_prefix}_norma_legal",
        value=form_data.get("norma_legal", ""),
    )

    info_adicional = col5_3.selectbox(
        "Info Adicional",
        index=st.session_state[f"{key_prefix}_info_adicional_index"],
        placeholder="Elegir una Info Adicional.",
        options=lista_info_adicional,
        key=f"{key_prefix}_info_adicional",
        accept_new_options=True,
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
            if not desc_obra or desc_obra == "":
                errores.append("Debe ingresar una Descripción de Obra.")
            if not cuit or cuit == "":
                errores.append("Debe seleccionar un Contratista.")
            if not actividad or actividad == "":
                errores.append("Debe seleccionar una Actividad.")
            if not partida or partida == "":
                errores.append("Debe seleccionar una Partida Presupuestaria.")
            if not cta_cte or cta_cte == "":
                errores.append("Debe seleccionar una Cuenta Bancaria.")
            if not fuente or fuente == "":
                errores.append("Debe seleccionar una Fuente de Financiamiento.")
            if not localidad or localidad == "":
                errores.append("Debe seleccionar una Localidad.")

            if errores:
                for err in errores:
                    st.toast(err, icon="⚠️")
            else:
                with st.spinner("Procesando y Guardando..."):
                    # 2. Preparación del payload para el POST
                    payload = {
                        "actividad": actividad,
                        "partida": partida,
                        "fuente": fuente,
                        "desc_obra": desc_obra,
                        "localidad": localidad,
                        "norma_legal": norma_legal or "",
                        "info_adicional": info_adicional or "",
                        "cta_cte": cta_cte,
                        "cuit": cuit,
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
                                endpoint=f"{Endpoints.ICARO_OBRAS.value}/update_one/{id}",
                                json_body=payload,
                            )
                        else:
                            res = post_request(
                                endpoint=Endpoints.ICARO_OBRAS.value + "/add_one",
                                json_body=payload,
                            )

                        # if res.status_code in [200, 201]:
                        if res:
                            # Feedback visual como vimos antes
                            st.snow()
                            st.toast(
                                f"✅ La obra denominada {desc_obra} {'agregada' if not es_edicion else 'editada'} con éxito",
                                icon="📈",
                            )

                            # Guardamos un flag para el rerun final si es necesario
                            st.session_state["obras_uploader_iteration"] += 1
                            if es_edicion:
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


# --- MODAL: ELIMINAR COMPROBANTE GENERICO ---
@st.dialog("Confirmar Eliminación PERMANENTE", width="small")
def modal_delete_registro_gral(
    endpoint: str,
    desc_registro: str,
    session_state_update_key: str = None,
    key_prefix: str = "",
):
    st.warning(
        f"⚠️ ¿Estás seguro de que deseás eliminar el registro **{desc_registro}**?"
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
            with st.spinner("Eliminando registro..."):
                try:
                    res = delete_request(endpoint)

                    if res:
                        st.success("Registro eliminado correctamente.")
                        if session_state_update_key:
                            if session_state_update_key not in st.session_state:
                                st.session_state[session_state_update_key] = 0
                            else:
                                st.session_state[session_state_update_key] += 1

                    else:
                        st.error(
                            "Error al eliminar el registro. Por favor, intenta nuevamente."
                        )

                    import time

                    time.sleep(2)
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al eliminar: {e}")


# --- MODAL: AGREGAR ESTRUCTURA ---
@st.dialog("Agregar / Editar Estructura", width="medium")
def modal_estructura(
    key_prefix: str,
    datos_carga: dict = None,
    es_edicion: bool = False,
    len_estructura: int = 11,
):
    # Traemos los DATOS
    df_programa = df_subprograma = df_proyecto = df_actividad = pd.DataFrame()
    df_estructura = get_estructuras(
        update_trigger=st.session_state.estructuras_uploader_iteration
    )
    longitudes = df_estructura["estructura"].str.len()
    df_programa = df_estructura[longitudes == 2]
    if len_estructura >= 5:
        df_subprograma = df_estructura[longitudes == 5]
    if len_estructura >= 8:
        df_proyecto = df_estructura[longitudes == 8]
    if len_estructura >= 11:
        df_actividad = df_estructura[longitudes == 11]

    # Si datos_carga existe, lo usamos. Si no, inicializamos vacío.
    form_data = {}
    if datos_carga:
        form_data["id"] = datos_carga.get("id")
        form_data["updated_at"] = datos_carga.get("updated_at")
        estructura_split = datos_carga["estructura"].split("-")
        form_data["programa"] = estructura_split[0]
        match = df_programa.loc[
            df_programa.estructura == form_data.get("programa"), "desc_estructura"
        ]
        if not match.empty:
            form_data["desc_programa"] = match.values[0]
        else:
            form_data["desc_programa"] = "No encontrado"
        if len(estructura_split) > 1:
            form_data["subprograma"] = f"{estructura_split[0]}-{estructura_split[1]}"
            match = df_subprograma.loc[
                df_subprograma.estructura == form_data.get("subprograma"),
                "desc_estructura",
            ]
            if not match.empty:
                form_data["desc_subprograma"] = match.values[0]
            else:
                form_data["desc_subprograma"] = "No encontrado"
        if len(estructura_split) > 2:
            form_data["proyecto"] = (
                f"{estructura_split[0]}-{estructura_split[1]}-{estructura_split[2]}"
            )
            match = df_proyecto.loc[
                df_proyecto.estructura == form_data.get("proyecto"),
                "desc_estructura",
            ]
            if not match.empty:
                form_data["desc_proyecto"] = match.values[0]
            else:
                form_data["desc_proyecto"] = "No encontrado"
        if len(estructura_split) > 3:
            form_data["actividad"] = (
                f"{estructura_split[0]}-{estructura_split[1]}-{estructura_split[2]}-{estructura_split[3]}"
            )
            match = df_actividad.loc[
                df_actividad.estructura == form_data.get("actividad"),
                "desc_estructura",
            ]
            if not match.empty:
                form_data["desc_actividad"] = match.values[0]
            else:
                form_data["desc_actividad"] = "No encontrado"

    if f"{key_prefix}_desc_programa" not in st.session_state:
        st.session_state[f"{key_prefix}_desc_programa"] = form_data.get(
            "desc_programa", ""
        )

    if f"{key_prefix}_desc_subprograma" not in st.session_state:
        st.session_state[f"{key_prefix}_desc_subprograma"] = form_data.get(
            "desc_subprograma", ""
        )

    if f"{key_prefix}_desc_proyecto" not in st.session_state:
        st.session_state[f"{key_prefix}_desc_proyecto"] = form_data.get(
            "desc_proyecto", ""
        )

    if f"{key_prefix}_desc_actividad" not in st.session_state:
        st.session_state[f"{key_prefix}_desc_actividad"] = form_data.get(
            "desc_actividad", ""
        )

    # FILA 1: Programa + Desc Programa
    def handle_programa_change():
        prog_elegido = st.session_state.get(f"{key_prefix}_programa")
        if prog_elegido:
            # Buscamos la denominación en el DF
            fila_prog = df_programa[df_programa.estructura == prog_elegido]
            if not fila_prog.empty:
                # Actualizamos el session_state del text_input directamente
                nueva_desc = fila_prog["desc_estructura"].iloc[0]
                st.session_state[f"{key_prefix}_desc_programa"] = nueva_desc
            else:
                # Si es una opción nueva (accept_new_options),
                # podemos decidir si limpiar o dejar que el usuario escriba
                st.session_state[f"{key_prefix}_desc_programa"] = ""
        else:
            st.session_state[f"{key_prefix}_desc_programa"] = ""

        # IMPORTANTE: Resetear el todo al cambiar el programa
        if f"{key_prefix}_subprograma" in st.session_state:
            st.session_state[f"{key_prefix}_subprograma"] = None
        if f"{key_prefix}_desc_subprograma" in st.session_state:
            st.session_state[f"{key_prefix}_desc_subprograma"] = ""
        if f"{key_prefix}_proyecto" in st.session_state:
            st.session_state[f"{key_prefix}_proyecto"] = None
        if f"{key_prefix}_desc_proyecto" in st.session_state:
            st.session_state[f"{key_prefix}_desc_proyecto"] = ""
        if f"{key_prefix}_actividad" in st.session_state:
            st.session_state[f"{key_prefix}_actividad"] = None
        if f"{key_prefix}_desc_actividad" in st.session_state:
            st.session_state[f"{key_prefix}_desc_actividad"] = ""

    col1_1, col1_2 = st.columns([0.5, 3])
    lista_programas = df_programa.estructura.to_list()
    programa_prev = form_data.get("programa")
    idx_programa = (
        lista_programas.index(programa_prev)
        if programa_prev in lista_programas
        else None
    )

    programa = col1_1.selectbox(
        "Programa",
        index=idx_programa,
        placeholder="Prog",
        options=lista_programas,
        key=f"{key_prefix}_programa",
        help="Seleccione el programa de la base de datos.",
        accept_new_options=(len_estructura == 2),
        on_change=handle_programa_change,
        disabled=(es_edicion and len_estructura > 2),
    )

    prog_actual = st.session_state.get(f"{key_prefix}_programa")

    desc_programa = col1_2.text_input(
        "Descripción Programa",
        key=f"{key_prefix}_desc_programa",
        placeholder="Agregar descripción del programa",
        disabled=(len_estructura != 2),
    )

    # FILA 2: Subprograma + Desc Subprograma
    if len_estructura >= 5:

        def handle_subprograma_change():
            subprog_elegido = st.session_state.get(f"{key_prefix}_subprograma")
            if subprog_elegido:
                # Buscamos la denominación en el DF
                fila_subprog = df_subprograma[
                    df_subprograma.estructura == subprog_elegido
                ]
                if not fila_subprog.empty:
                    # Actualizamos el session_state del text_input directamente
                    nueva_desc = fila_subprog["desc_estructura"].iloc[0]
                    st.session_state[f"{key_prefix}_desc_subprograma"] = nueva_desc
                else:
                    # Si es una opción nueva (accept_new_options),
                    # podemos decidir si limpiar o dejar que el usuario escriba
                    st.session_state[f"{key_prefix}_desc_subprograma"] = ""

            # IMPORTANTE: Resetear el todo al cambiar el subprograma
            if f"{key_prefix}_proyecto" in st.session_state:
                st.session_state[f"{key_prefix}_proyecto"] = None
            if f"{key_prefix}_desc_proyecto" in st.session_state:
                st.session_state[f"{key_prefix}_desc_proyecto"] = ""
            if f"{key_prefix}_actividad" in st.session_state:
                st.session_state[f"{key_prefix}_actividad"] = None
            if f"{key_prefix}_desc_actividad" in st.session_state:
                st.session_state[f"{key_prefix}_desc_actividad"] = ""

        col2_1, col2_2 = st.columns([0.5, 3])
        prog_actual = st.session_state.get(f"{key_prefix}_programa")
        if prog_actual:
            mask = df_subprograma["estructura"].str.startswith(f"{prog_actual}-")
            lista_subprogramas = df_subprograma[mask].estructura.to_list()
        else:
            lista_subprogramas = []
        subprograma_prev = form_data.get("subprograma")
        idx_subprograma = (
            lista_subprogramas.index(subprograma_prev)
            if subprograma_prev in lista_subprogramas
            else None
        )

        subprograma = col2_1.selectbox(
            "Subprograma",
            index=idx_subprograma,
            placeholder="Subprog",
            options=lista_subprogramas,
            key=f"{key_prefix}_subprograma",
            help="Seleccione el subprograma de la base de datos.",
            accept_new_options=(len_estructura == 5),
            on_change=handle_subprograma_change,
            disabled=not prog_actual or (es_edicion and len_estructura > 5),
            format_func=lambda x: str(x)[-2:] if x else x,
        )

        desc_subprograma = col2_2.text_input(
            "Descripción Subprograma",
            key=f"{key_prefix}_desc_subprograma",
            placeholder="Agregar descripción del subprograma",
            disabled=(len_estructura != 5 or not prog_actual),
        )

    if len_estructura >= 8:

        def handle_proyecto_change():
            proy_elegido = st.session_state.get(f"{key_prefix}_proyecto")
            if proy_elegido:
                # Buscamos la denominación en el DF
                fila_proy = df_proyecto[df_proyecto.estructura == proy_elegido]
                if not fila_proy.empty:
                    # Actualizamos el session_state del text_input directamente
                    nueva_desc = fila_proy["desc_estructura"].iloc[0]
                    st.session_state[f"{key_prefix}_desc_proyecto"] = nueva_desc
                else:
                    # Si es una opción nueva (accept_new_options),
                    # podemos decidir si limpiar o dejar que el usuario escriba
                    st.session_state[f"{key_prefix}_desc_proyecto"] = ""

            # IMPORTANTE: Resetear el todo al cambiar el subprograma
            if f"{key_prefix}_actividad" in st.session_state:
                st.session_state[f"{key_prefix}_actividad"] = None
            if f"{key_prefix}_desc_actividad" in st.session_state:
                st.session_state[f"{key_prefix}_desc_actividad"] = ""

        # FILA 3: Proyecto + Desc Proyecto
        col3_1, col3_2 = st.columns([0.5, 3])
        subprog_actual = st.session_state.get(f"{key_prefix}_subprograma")
        if subprog_actual:
            mask = df_proyecto["estructura"].str.startswith(f"{subprog_actual}-")
            lista_proyectos = df_proyecto[mask].estructura.to_list()
        else:
            lista_proyectos = []
        proyecto_prev = form_data.get("proyecto")
        idx_proyecto = (
            lista_proyectos.index(proyecto_prev)
            if proyecto_prev in lista_proyectos
            else None
        )

        proyecto = col3_1.selectbox(
            "Proyecto",
            index=idx_proyecto,
            placeholder="Proy",
            options=lista_proyectos,
            key=f"{key_prefix}_proyecto",
            help="Seleccione el proyecto de la base de datos.",
            accept_new_options=(len_estructura == 8),
            on_change=handle_proyecto_change,
            disabled=not subprog_actual or (es_edicion and len_estructura > 8),
            format_func=lambda x: str(x)[-2:] if x else x,
        )

        desc_proyecto = col3_2.text_input(
            "Descripción Proyecto",
            key=f"{key_prefix}_desc_proyecto",
            placeholder="Agregar descripción del proyecto",
            disabled=(len_estructura != 8 or not subprog_actual),
        )

    if len_estructura >= 11:

        def handle_actividad_change():
            act_elegido = st.session_state.get(f"{key_prefix}_actividad")
            if act_elegido:
                # Buscamos la denominación en el DF
                fila_act = df_actividad[df_actividad.estructura == act_elegido]
                if not fila_act.empty:
                    # Actualizamos el session_state del text_input directamente
                    nueva_desc = fila_act["desc_estructura"].iloc[0]
                    st.session_state[f"{key_prefix}_desc_actividad"] = nueva_desc
                else:
                    # Si es una opción nueva (accept_new_options),
                    # podemos decidir si limpiar o dejar que el usuario escriba
                    st.session_state[f"{key_prefix}_desc_actividad"] = ""

        # FILA 4: Actividad + Desc Actividad
        col4_1, col4_2 = st.columns([0.5, 3])
        proy_actual = st.session_state.get(f"{key_prefix}_proyecto")
        if proy_actual:
            mask = df_actividad["estructura"].str.startswith(f"{proy_actual}-")
            lista_actividades = df_actividad[mask].estructura.to_list()
        else:
            lista_actividades = []
        actividad_prev = form_data.get("actividad")
        idx_actividad = (
            lista_actividades.index(actividad_prev)
            if actividad_prev in lista_actividades
            else None
        )

        actividad = col4_1.selectbox(
            "Actividad",
            index=idx_actividad,
            placeholder="Act",
            options=lista_actividades,
            key=f"{key_prefix}_actividad",
            help="Seleccione la actividad de la base de datos.",
            accept_new_options=(len_estructura == 11),
            on_change=handle_actividad_change,
            disabled=not proy_actual,
            format_func=lambda x: str(x)[-2:] if x else x,
        )

        desc_actividad = col4_2.text_input(
            "Descripción Actividad",
            key=f"{key_prefix}_desc_actividad",
            placeholder="Agregar descripción del actividad",
            disabled=(len_estructura != 11 or not proy_actual),
        )

    st.markdown("## ")  # Espaciado final

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
            if len_estructura >= 2 and (not programa or programa == ""):
                errores.append("Debe seleccionar un Programa")
            if len_estructura >= 2 and (not desc_programa or desc_programa == ""):
                errores.append("El Programa seleccionado debe tener una descripción")
            if len_estructura >= 5 and (not subprograma or subprograma == ""):
                errores.append("Debe seleccionar un Subprograma")
            if len_estructura >= 5 and (not desc_subprograma or desc_subprograma == ""):
                errores.append("El Subprograma seleccionado debe tener una descripción")
            if len_estructura >= 8 and (not proyecto or proyecto == ""):
                errores.append("Debe seleccionar un Proyecto")
            if len_estructura >= 8 and (not desc_proyecto or desc_proyecto == ""):
                errores.append("El Proyecto seleccionado debe tener una descripción")
            if len_estructura >= 11 and (not actividad or actividad == ""):
                errores.append("Debe seleccionar un Actividad")
            if len_estructura >= 11 and (not desc_actividad or desc_actividad == ""):
                errores.append("La actividad seleccionado debe tener una descripción")

            if errores:
                for err in errores:
                    st.toast(err, icon="⚠️")
            else:
                with st.spinner("Procesando y Guardando..."):
                    # 2. Preparación del payload para el POST
                    if len_estructura == 2:
                        estructura = programa
                        desc_estructura = desc_programa
                    if len_estructura == 5:
                        estructura = f"{programa}-{subprograma[-2:]}"
                        desc_estructura = desc_subprograma
                    if len_estructura == 8:
                        estructura = f"{subprograma}-{proyecto[-2:]}"
                        desc_estructura = desc_proyecto
                    if len_estructura == 11:
                        estructura = f"{proyecto}-{actividad[-2:]}"
                        desc_estructura = desc_actividad

                    payload = {
                        "estructura": estructura,
                        "desc_estructura": desc_estructura,
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
                                endpoint=f"{Endpoints.ICARO_ESTRUCTURAS.value}/update_one/{id}",
                                json_body=payload,
                            )
                        else:
                            res = post_request(
                                endpoint=Endpoints.ICARO_ESTRUCTURAS.value + "/add_one",
                                json_body=payload,
                            )

                        # if res.status_code in [200, 201]:
                        if res:
                            # Feedback visual como vimos antes
                            st.snow()
                            st.toast(
                                f"✅ La estructura {estructura} denominada {desc_estructura} {'agregada' if not es_edicion else 'editada'} con éxito",
                                icon="📈",
                            )

                            # Guardamos un flag para el rerun final si es necesario
                            st.session_state["estructuras_uploader_iteration"] += 1
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
