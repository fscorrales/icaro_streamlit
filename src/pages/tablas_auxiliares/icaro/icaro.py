"""Página Principal: Tablas Auxiliares - ICARO."""

import streamlit as st

from src.pages.tablas_auxiliares.icaro import carga


def main() -> None:
    tab_carga, tab_estructura = st.tabs(["Carga", "Estructura"])

    with tab_carga:
        carga.render()

    with tab_estructura:
        st.write("Contenido de la pestaña Estructura")


if __name__ == "__main__":
    main()
