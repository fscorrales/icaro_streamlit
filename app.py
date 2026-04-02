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

with st.container():
    st.sidebar.caption(f"Versión: {get_version()}", text_alignment="center")


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
    st.write("La aplicación de **INVICO** se ha detenido correctamente.")
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

    role = st.session_state["user"].get("role", "viewer")

    # 1. Definimos la lista base de páginas
    pages = [
        st.Page("src/pages/controles/control_recursos.py", title="Home", icon="🏠"),
        st.Page(
            "src/pages/controles/control_icaro.py", title="Control Icaro", icon="🏗️"
        ),
        st.Page(
            "src/pages/controles/control_obras.py", title="Control Obras", icon="🔨"
        ),
        st.Page(
            "src/pages/controles/control_honorarios.py",
            title="Control Honorarios",
            icon="📋",
        ),
        st.Page(
            "src/pages/controles/control_haberes.py", title="Control Haberes", icon="👤"
        ),
    ]

    # 2. Agregamos páginas extra según el rol (sin crear una sección nueva)
    if role == "admin":
        pages.append(
            st.Page(
                "src/pages/admin/gestion_usuarios.py",
                title="Gestión de Usuarios",
                icon="👥",
            )
        )

    # 3. Inicializar y ejecutar
    # Al pasar una lista, Streamlit no crea encabezados de sección
    pg = st.navigation(pages)

    # 2. Crear un "Header" en la parte superior de la página
    with st.container(
        vertical_alignment="center", height="stretch", gap=None, horizontal=False
    ):
        with st.container(
            horizontal=True, vertical_alignment="bottom", horizontal_alignment="right"
        ):
            with st.container(width="content"):
                st.write(f"👤 **{st.session_state['user']['username']}**")
            with st.container(width="content"):
                if st.button("Log out", width="stretch"):
                    # 1.Activamos el interruptor
                    st.session_state.app_closing = True

                    # 2. Limpiamos la sesión para seguridad
                    st.session_state["token"] = None
                    st.session_state["user"] = None

                    # 3. Forzamos el rerun para que entre en la pantalla de cierre
                    st.rerun()

        st.divider()

    # 3. Ejecutar la página
    pg.run()

    # # ── Sidebar inferior: info de usuario y logout ──
    # with st.sidebar:
    #     st.divider()
    #     username = st.session_state["user"]["username"]
    #     st.caption(f"👤 {username} ({role})")

    #     if st.button("Cerrar Sesión", width="stretch"):
    #         st.session_state["token"] = None
    #         st.session_state["user"] = None
    #         st.rerun()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main() -> None:
    initialize_state()

    # TEMPORARY: Bypass Login para desarrollo
    # if not st.session_state.get("token"):
    #     st.session_state["token"] = "dev-bypass-token"
    #     st.session_state["user"] = {
    #         "role": "admin",
    #         "username": "developer",
    #         "id": "1",
    #     }

    if not st.session_state["token"]:
        render_login()
    else:
        build_navigation()


# --------------------------------------------------
if __name__ == "__main__":
    main()
