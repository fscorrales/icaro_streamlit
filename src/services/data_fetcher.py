__all__ = [
    "get_estructuras",
    "get_proveedores",
    "get_obras",
    "get_autocarga_epam",
    "get_autocarga_certificados",
    "get_ctas_ctes",
]

import pandas as pd
import streamlit as st

from src.constants import Endpoints
from src.services.api_client import fetch_dataframe


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_estructuras(filtro_avanzado: str = ""):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Estructuras
    df = fetch_dataframe(Endpoints.ICARO_ESTRUCTURAS.value, params=params_peticion)
    if not df.empty:
        df = df.sort_values(["estructura"], ascending=True)

    return df


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_proveedores(filtro_avanzado: str = ""):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Proveedores
    df = fetch_dataframe(Endpoints.ICARO_PROVEEDORES.value, params=params_peticion)
    if not df.empty:
        df = df.sort_values(["desc_proveedor"], ascending=True)

    return df


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_obras(filtro_avanzado: str = ""):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Obras
    df = fetch_dataframe(Endpoints.ICARO_OBRAS.value, params=params_peticion)
    if not df.empty:
        df = df.sort_values(
            ["actividad", "partida", "fuente", "desc_obra"], ascending=True
        )

    return df


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_autocarga_certificados(filtro_avanzado: str = "", update_trigger: int = 0):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Certificados
    df = fetch_dataframe(Endpoints.ICARO_INFORME_CONTABLE.value, params=params_peticion)
    if not df.empty:
        # df = df.loc[df["id_carga"] == ""]
        df = df.sort_values(
            ["beneficiario", "desc_obra", "nro_certificado"],
            ascending=True,
        )

    return df


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_autocarga_epam(
    filtro_avanzado: str = "", update_trigger: int = 0
) -> pd.DataFrame:
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Certificados
    df = fetch_dataframe(
        Endpoints.ICARO_RESUMEN_REND_OBRAS.value, params=params_peticion
    )
    # if not df.empty:
    #     df = df.loc[df["id_carga"] == ""]
    #     df = df.sort_values(
    #         ["beneficiario", "desc_obra", "nro_certificado"],
    #         ascending=True,
    #     )

    return df


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_ctas_ctes(filtro_avanzado: str = ""):
    df = pd.DataFrame()

    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    # Tabla Proveedores
    df = fetch_dataframe(Endpoints.CTAS_CTES.value, params=params_peticion)
    if not df.empty:
        df = df.loc[df["icaro_cta_cte"] != ""]
        df = df.sort_values(["map_to"], ascending=True)

    return df
