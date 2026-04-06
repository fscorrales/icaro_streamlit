__all__ = ["home_carga", "home_retenciones", "home_imputaciones"]

import pandas as pd
import streamlit as st

from src.components import dataframe


# --------------------------------------------------
def home_carga(df_carga: pd.DataFrame, key: str):
    with st.container(horizontal=False, border=True, width="stretch"):
        event = dataframe(
            df_carga,
            key=f"df_carga_{key}",
            height=200,
            on_select="rerun",
            selection_mode="single-row",
            column_order=[
                "mes",
                "fecha",
                "id_carga",
                # "nro_comprobante",
                "tipo",
                "fuente",
                "cta_cte",
                "importe",
                "desc_obra",
                # "fondo_reparo",
                "avance",
                "nro_certificado",
                "cuit",
                "origen",
            ],
            column_config={
                "fecha": st.column_config.DateColumn(
                    "fecha",
                    format="DD/MM/YYYY",  # O el formato que prefieras
                ),
                "nro_certificado": st.column_config.TextColumn("cert"),
            },
        )
        with st.container(horizontal=True, border=False, width="stretch"):
            if st.button("Autocarga", key=f"btn_autocarga_df_carga_{key}"):
                pass
            if st.button("Carga Manual", key=f"btn_carga_manual_df_carga_{key}"):
                pass
            if st.button("Editar", key=f"btn_editar_carga_df_carga_{key}"):
                pass
            if st.button("Borrar", key=f"btn_borrar_df_carga_{key}"):
                pass

    return event


# --------------------------------------------------
def home_retenciones(df_ret: pd.DataFrame, key: str):

    with st.container(horizontal=True, border=False, width="stretch"):
        with st.container(horizontal=False, border=True, width="stretch"):
            dataframe(
                df_ret,
                key=f"df_ret_{key}",
                height=150,
                column_order=[
                    "codigo",
                    "importe",
                ],
            )
            with st.container(horizontal=True, border=False, width="stretch"):
                if st.button("Agregar", key=f"btn_agregar_df_ret_{key}"):
                    pass
                if st.button("Editar", key=f"btn_editar_df_ret_{key}"):
                    pass
                if st.button("Borrar", key=f"btn_borrar_df_ret_{key}"):
                    pass


# --------------------------------------------------
def home_imputaciones(df_imput: pd.DataFrame, key: str):

    with st.container(horizontal=False, border=True, width="stretch"):
        dataframe(
            df_imput,
            key=f"df_imp_{key}",
            height=150,
            column_order=[
                "actividad",
                "partida",
                "importe",
            ],
        )
        with st.container(horizontal=True, border=False, width="stretch"):
            if st.button("Agregar", key=f"btn_agregar_df_imp_{key}"):
                pass
            if st.button("Editar", key=f"btn_editar_df_imp_{key}"):
                pass
            if st.button("Borrar", key=f"btn_borrar_df_imp_{key}"):
                pass
