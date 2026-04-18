__all__ = [
    "get_ctas_ctes",
    "get_proveedores",
    "get_estructuras",
    "get_obras",
    "get_autocarga_epam",
    "get_autocarga_certificados",
]

import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.constants import Endpoints
from src.services.api_client import fetch_dataframe
from src.utils import get_cache_path


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=86400)
def get_estructuras(filtro_avanzado: str = "", force_update: bool = False):
    file_path = os.path.join(get_cache_path(), "estructuras_cache.parquet")

    # 1. Intentar cargar desde archivo local si no se fuerza la actualización
    if not force_update and os.path.exists(file_path):
        # Opcional: Verificar si el archivo tiene menos de 24hs
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if datetime.now() - mtime < timedelta(hours=24):
            df_local = pd.read_parquet(file_path)
            # Aplicamos el filtro si existe, aunque sea local
            if filtro_avanzado:
                # Si el filtro es complejo, quizás prefieras re-consultar la API
                pass
            return df_local

    # 2. Si no hay cache o es viejo, consultar API
    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    try:
        df = fetch_dataframe(Endpoints.ICARO_ESTRUCTURAS.value, params=params_peticion)
        if not df.empty:
            df = df.sort_values(["estructura"], ascending=True)
            # 3. Guardar en disco para la próxima vez
            df.to_parquet(file_path)
            return df

    except Exception as e:
        st.error(f"Error de conexión: {e}")
        # Si falla la API pero hay un archivo viejo, lo usamos como backup
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)

    return pd.DataFrame()


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=86400)
def get_proveedores(filtro_avanzado: str = "", force_update: bool = False):
    file_path = os.path.join(get_cache_path(), "proveedores_cache.parquet")

    # 1. Intentar cargar desde archivo local si no se fuerza la actualización
    if not force_update and os.path.exists(file_path):
        # Opcional: Verificar si el archivo tiene menos de 24hs
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if datetime.now() - mtime < timedelta(hours=24):
            df_local = pd.read_parquet(file_path)
            # Aplicamos el filtro si existe, aunque sea local
            if filtro_avanzado:
                # Si el filtro es complejo, quizás prefieras re-consultar la API
                pass
            return df_local

    # 2. Si no hay cache o es viejo, consultar API
    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    try:
        df = fetch_dataframe(Endpoints.ICARO_PROVEEDORES.value, params=params_peticion)
        if not df.empty:
            df = df.sort_values(["desc_proveedor"], ascending=True)
            # 3. Guardar en disco para la próxima vez
            df.to_parquet(file_path)
            return df

    except Exception as e:
        st.error(f"Error de conexión: {e}")
        # Si falla la API pero hay un archivo viejo, lo usamos como backup
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)

    return pd.DataFrame()


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=3600)
def get_obras(filtro_avanzado: str = "", force_update: bool = False):
    file_path = os.path.join(get_cache_path(), "obras_cache.parquet")

    # 1. Intentar cargar desde archivo local si no se fuerza la actualización
    if not force_update and os.path.exists(file_path):
        # Opcional: Verificar si el archivo tiene menos de 24hs
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if datetime.now() - mtime < timedelta(hours=24):
            df_local = pd.read_parquet(file_path)
            # Aplicamos el filtro si existe, aunque sea local
            if filtro_avanzado:
                # Si el filtro es complejo, quizás prefieras re-consultar la API
                pass
            return df_local

    # 2. Si no hay cache o es viejo, consultar API
    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    try:
        df = fetch_dataframe(Endpoints.ICARO_OBRAS.value, params=params_peticion)
        if not df.empty:
            df = df.sort_values(
                ["actividad", "partida", "fuente", "desc_obra"], ascending=True
            )
            # 3. Guardar en disco para la próxima vez
            df.to_parquet(file_path)
            return df

    except Exception as e:
        st.error(f"Error de conexión: {e}")
        # Si falla la API pero hay un archivo viejo, lo usamos como backup
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)

    return pd.DataFrame()


# --------------------------------------------------
@st.cache_data(show_spinner="Consultando base de datos...", ttl=86400)
def get_ctas_ctes(filtro_avanzado: str = "", force_update: bool = False):
    file_path = os.path.join(get_cache_path(), "ctas_ctes_cache.parquet")

    # 1. Intentar cargar desde archivo local si no se fuerza la actualización
    if not force_update and os.path.exists(file_path):
        # Opcional: Verificar si el archivo tiene menos de 24hs
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if datetime.now() - mtime < timedelta(hours=24):
            df_local = pd.read_parquet(file_path)
            # Aplicamos el filtro si existe, aunque sea local
            if filtro_avanzado:
                # Si el filtro es complejo, quizás prefieras re-consultar la API
                pass
            return df_local

    # 2. Si no hay cache o es viejo, consultar API
    params_peticion = {
        "limit": 0,
        "queryFilter": filtro_avanzado,
    }

    try:
        df = fetch_dataframe(Endpoints.CTAS_CTES.value, params=params_peticion)
        if not df.empty:
            df = df.loc[df["icaro_cta_cte"] != ""]
            df = df.sort_values(["map_to"], ascending=True)
            # 3. Guardar en disco para la próxima vez
            df.to_parquet(file_path)
            return df

    except Exception as e:
        st.error(f"Error de conexión: {e}")
        # Si falla la API pero hay un archivo viejo, lo usamos como backup
        if os.path.exists(file_path):
            return pd.read_parquet(file_path)

    return pd.DataFrame()


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
