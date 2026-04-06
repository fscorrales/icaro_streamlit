__all__ = [
    "get_ejercicios_list",
    "get_tipos_comprobantes_siif_list",
    "get_grupos_partidas_siif_list",
    "get_partidas_principales_siif_list",
    "get_ctas_ctes_df",
    "get_ctas_ctes_list",
]

import datetime as dt
from typing import Any

import pandas as pd
import streamlit as st

from src.constants.endpoints import Endpoints
from src.services.api_client import fetch_data


@st.cache_data
# --------------------------------------------------
def get_ejercicios_list() -> list[int]:
    return list(range(2010, dt.date.today().year + 1))


@st.cache_data
# --------------------------------------------------
def get_tipos_comprobantes_siif_list() -> list[dict[str, Any]]:
    return fetch_data(Endpoints.SIIF.value + "/tiposComprobantes")


@st.cache_data
# --------------------------------------------------
def get_grupos_partidas_siif_list() -> list[dict[str, Any]]:
    return fetch_data(Endpoints.SIIF.value + "/gruposPartidas")


@st.cache_data
# --------------------------------------------------
def get_partidas_principales_siif_list() -> list[dict[str, Any]]:
    return fetch_data(Endpoints.SIIF.value + "/partidasPrincipales")


@st.cache_data
# --------------------------------------------------
def get_ctas_ctes_df() -> pd.DataFrame:
    data = fetch_data(Endpoints.CTAS_CTES.value)
    return pd.DataFrame(data)


@st.cache_data
# --------------------------------------------------
def get_ctas_ctes_list() -> list[str]:
    data = get_ctas_ctes_df().copy()
    return data["map_to"].tolist()
