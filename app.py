"""
ICARO — Entrypoint principal.

Usa st.navigation() con secciones agrupadas para construir
el sidebar de navegación MPA. La sección "Administración"
solo es visible para usuarios con rol admin.
"""

import os
import time

import streamlit as st

from src.pages.login import render_login
from src.services.data_fetcher import (
    get_ctas_ctes,
    get_estructuras,
    get_obras,
    get_proveedores,
)
from src.utils.version import get_version

st.set_page_config(
    page_title="ICARO",
    page_icon="🪽",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stAppDeployButton {
            display: none !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# 1. Al principio de tu app (o donde manejes la navegación)
if "app_closing" not in st.session_state:
    st.session_state.app_closing = False

# Si la app se está cerrando, mostramos la pantalla limpia y salimos
if st.session_state.app_closing:
    st.empty()  # Limpia lo que haya quedado arriba
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {display: none;} /* Oculta la barra lateral */
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.write("#")
    st.success("### 🔒 Sesión Finalizada")
    st.write("La aplicación de **ICARO** se ha detenido correctamente.")
    st.info("Ya puedes cerrar esta ventana del navegador.")

    time.sleep(1)
    os._exit(0)


# ──────────────────────────────────────────────
# Inicialización del estado de sesión
# ──────────────────────────────────────────────
def initialize_state() -> None:
    """Inicializa las claves mínimas en session_state."""
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "user" not in st.session_state:
        st.session_state["user"] = None


# ──────────────────────────────────────────────
# Navegación MPA
# ──────────────────────────────────────────────
def build_navigation() -> None:
    """Construye la navegación plana y ejecuta la página."""

    # Verificación de seguridad
    if "user" not in st.session_state:
        st.error("Sesión no iniciada.")
        return

    role = st.session_state["user"].get("role", "pending")
    username = st.session_state["user"].get("username", "Usuario")

    # 1. Definimos la lista base de páginas
    pages = [
        st.Page("src/pages/carga.py", title="Carga", icon="🏠"),
        st.Page("src/pages/autocarga/autocarga.py", title="Autocarga", icon="🔮"),
        st.Page("src/pages/estructura/estructura.py", title="Estructura", icon="🏢"),
        st.Page("src/pages/obras.py", title="Obras", icon="🏘️"),
        st.Page(
            "src/pages/proveedores.py",
            title="Proveedores",
            icon="👷‍♂️",
        ),
    ]

    # 2. Agregamos páginas extra según el rol (sin crear una sección nueva)
    if role == "admin":
        pages.append(
            st.Page(
                "src/pages/gestion_usuarios.py",
                title="Gestión de Usuarios",
                icon="👥",
            )
        )

    # 3. Inicializar y ejecutar
    # Al pasar una lista, Streamlit no crea encabezados de sección
    pg = st.navigation(pages)

    # 3. Sidebar: Info de usuario y Logout
    with st.sidebar:
        if st.button(
            "🔄 Sincronizar Datos",
            use_container_width=True,
            help="Descarga los datos más recientes de la API",
        ):
            # Incrementamos el trigger de las funciones con .parquet
            st.session_state.estructuras_uploader_iteration += 1
            get_estructuras(
                update_trigger=st.session_state.estructuras_uploader_iteration
            )
            st.session_state.obras_uploader_iteration += 1
            get_obras(update_trigger=st.session_state.obras_uploader_iteration)
            st.session_state.proveedores_uploader_iteration += 1
            get_proveedores(
                update_trigger=st.session_state.proveedores_uploader_iteration
            )
            st.session_state.ctas_ctes_uploader_iteration += 1
            get_ctas_ctes(update_trigger=st.session_state.ctas_ctes_uploader_iteration)

            # Opcional: limpiar el caché de Streamlit para asegurar que no haya basura
            st.cache_data.clear()
            st.toast("Sincronizando con el servidor...", icon="🚀")
            time.sleep(1)  # Simula un pequeño delay para que se vea el toast

            st.rerun()

        # Generamos espacio en blanco dinámico
        # Si tienes 6 páginas, unos 12 a 15 st.write("") suelen bastar
        # para mandarlo al fondo en una pantalla estándar.
        for _ in range(10):
            st.write("")

        st.divider()

        # Bloque de Usuario
        cols = st.columns([0.6, 0.4], vertical_alignment="center")
        cols[0].write(f"👤 **{username}**")

        if cols[1].button("Log out", key="logout_spacer"):
            st.session_state.app_closing = True
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()

        with st.container():
            st.sidebar.caption(f"Versión: {get_version()}", text_alignment="center")

    # 4. CSS para eliminar el espacio que dejó el Header anterior
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1rem !important; /* Espacio mínimo arriba */
            }
            /* Mantenemos el botón del sidebar visible pero bajamos el header */
            .stAppHeader {
                background-color: transparent !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 3. Ejecutar la página
    pg.run()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main() -> None:
    initialize_state()

    if not st.session_state["token"]:
        render_login()
    else:
        build_navigation()


# --------------------------------------------------
if __name__ == "__main__":
    main()
