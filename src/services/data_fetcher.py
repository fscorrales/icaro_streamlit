__all__ = ["get_estructuras"]

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
