"""
Cliente HTTP genérico para comunicación con la API de INVICO.

Encapsula las llamadas GET/PATCH con headers JWT desde session_state.
Todas las páginas deben usar este módulo en lugar de llamar a httpx
directamente.
"""

__all__ = [
    "fetch_data",
    "fetch_excel_stream",
    "post_request",
    "put_request",
    "patch_request",
    "delete_request",
    "fetch_dataframe",
]

import json
from io import BytesIO
from typing import Any, Optional

import httpx
import pandas as pd
import streamlit as st

from src.config import settings
from src.utils.exceptions import APIConnectionError, APIResponseError

BASE_URL = settings.BASE_URL


# --------------------------------------------------
def _get_headers(token: Optional[str] = None) -> dict[str, str]:
    # """Construye headers de autorización desde session_state."""
    # token = st.session_state.get("token")
    # if not token:
    #     # Nota: En lugar de error, podrías redirigir a login
    #     raise APIConnectionError("No hay token de sesión. Inicie sesión nuevamente.")
    # return {"Authorization": f"Bearer {token}"}

    """
    Obtiene headers. Si se pasa un token, lo usa.
    Si no, intenta sacarlo de Streamlit.
    """
    if token:
        return {"Authorization": f"Bearer {token}"}

    # Intento obtenerlo de Streamlit solo si estamos en un contexto de app
    st_token = st.session_state.get("token")
    if not st_token:
        # Nota: En lugar de error, podrías redirigir a login
        raise APIConnectionError("No hay token de sesión. Inicie sesión nuevamente.")
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------
def fetch_data(
    endpoint: str,
    params: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """
    Realiza un GET genérico a la API y retorna la lista de registros.

    Args:
        endpoint: Ruta relativa del endpoint (ej. "/siif/rf602/").
        params: Parámetros de query opcionales.

    Returns:
        Lista de diccionarios con los datos.

    Raises:
        APIConnectionError: Si no hay conexión.
        APIResponseError: Si la API retorna un error.
    """
    headers = _get_headers()
    clean_params = (
        {k: v for k, v in params.items() if v is not None} if params else None
    )

    try:
        response = httpx.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=clean_params,
            timeout=settings.DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        return _handle_response(response)

    except httpx.RequestError as e:
        raise APIConnectionError(f"Error de conexión (GET): {e}")


# --------------------------------------------------
def fetch_dataframe(
    endpoint: str,
    params: Optional[dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Realiza un GET y retorna los datos como pd.DataFrame.

    Si no hay datos, retorna un DataFrame vacío.
    """
    data = fetch_data(endpoint, params)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


# --------------------------------------------------
def fetch_excel_stream(endpoint: str, params: dict):
    headers = _get_headers()
    # Limpiamos None y nos aseguramos de no enviar listas si la API espera valores únicos
    clean_params = {}
    if params:
        for k, v in params.items():
            if v is not None:
                # Si es una lista (de un multiselect), tomamos el primer elemento
                clean_params[k] = v[0] if isinstance(v, list) else v

    try:
        response = httpx.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=clean_params,
            timeout=settings.DEFAULT_TIMEOUT + 60.0,
            follow_redirects=True,  # <--- CRÍTICO: Esto soluciona el error 307
        )

        # Ojo: Si _handle_response intenta hacer response.json(), va a fallar
        # porque un Excel es binario. Validamos manualmente:
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            # Aquí sí puedes usar tu lógica de error habitual
            return _handle_response(response)

    except httpx.RequestError as e:
        raise APIConnectionError(f"Error de conexión (GET): {e}")


# --------------------------------------------------
def patch_request(
    endpoint: str,
    json_body: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Realiza un PATCH genérico a la API.

    Args:
        endpoint: Ruta relativa del endpoint.
        json_body: Cuerpo JSON opcional.

    Returns:
        Diccionario con la respuesta.
    """
    headers = _get_headers()

    try:
        response = httpx.patch(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            json=json_body,
            timeout=settings.DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
    except httpx.RequestError as e:
        raise APIConnectionError(f"Error de conexión con el servidor: {e}") from e

    if response.status_code == 401:
        raise APIResponseError("Token expirado o inválido. Inicie sesión nuevamente.")
    if response.status_code != 200:
        raise APIResponseError(
            f"Error de API ({response.status_code}): {response.text}"
        )

    return response.json()


# --------------------------------------------------
def post_request(
    endpoint: str,
    json_body: Optional[Any] = None,
    token: Optional[str] = None,
) -> dict[str, Any]:
    """
    Realiza un POST genérico a la API. Útil para actualizar base de datos
    tras ejecuciones de Playwright/Pywinauto.
    """
    headers = _get_headers(token=token)

    # --- FIX: Convertir Timestamps a strings ---
    if json_body is not None:
        # Serializamos a string y volvemos a cargar a dict
        # Esto convierte automáticamente los Timestamps a strings
        json_body = json.loads(
            json.dumps(
                json_body,
                default=lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x),
            )
        )
    # --------------------------------------------

    try:
        response = httpx.post(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            json=json_body,
            timeout=settings.DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        return _handle_response(response)
    except httpx.RequestError as e:
        raise APIConnectionError(f"Error de conexión (POST): {e}") from e


# --------------------------------------------------
def put_request(
    endpoint: str,
    json_body: Optional[Any] = None,
    token: Optional[str] = None,
) -> dict[str, Any]:
    """
    Realiza un PUT genérico a la API. Útil para actualizar base de datos
    tras ejecuciones de Playwright/Pywinauto.
    """
    headers = _get_headers(token=token)

    # --- FIX: Convertir Timestamps a strings ---
    if json_body is not None:
        # Serializamos a string y volvemos a cargar a dict
        # Esto convierte automáticamente los Timestamps a strings
        json_body = json.loads(
            json.dumps(
                json_body,
                default=lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x),
            )
        )
    # --------------------------------------------

    try:
        response = httpx.put(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            json=json_body,
            timeout=settings.DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        return _handle_response(response)
    except httpx.RequestError as e:
        raise APIConnectionError(f"Error de conexión (PUT): {e}") from e


# --------------------------------------------------
def delete_request(
    endpoint: str,
    token: Optional[str] = None,
) -> dict[str, Any]:
    """
    Realiza un DELETE genérico a la API. Útil para actualizar base de datos
    tras ejecuciones de Playwright/Pywinauto.
    """
    headers = _get_headers(token=token)

    try:
        response = httpx.delete(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            timeout=settings.DEFAULT_TIMEOUT,
            follow_redirects=True,
        )
        return _handle_response(response)
    except httpx.RequestError as e:
        raise APIConnectionError(f"Error de conexión (DELETE): {e}") from e


# --------------------------------------------------
def _handle_response(response: httpx.Response) -> Any:
    """Centraliza la validación de respuestas HTTP."""
    if response.status_code == 401:
        raise APIResponseError("Sesión expirada. Por favor, ingrese de nuevo.")

    # # Manejo de estados de despliegue en Koyeb (503 Service Unavailable)
    if response.status_code == 503:
        raise APIConnectionError(
            "El servidor está despertando. Reintente en unos segundos..."
        )

    if not (200 <= response.status_code < 300):
        raise APIResponseError(
            f"Error de API ({response.status_code}): {response.text}"
        )

    return response.json()
