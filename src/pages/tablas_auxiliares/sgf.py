"""Página Principal: Tablas Auxiliares - SGF."""

import streamlit as st

from src.pages.tablas_auxiliares import sgf_resumen_rend_prov


def main() -> None:
    # Sidebar menu logic
    st.sidebar.markdown("### Menú SGF")
    
    menu_selection = st.sidebar.radio(
        "Reportes Disponibles",
        options=["Resumen Rendiciones Proveedores"],
        label_visibility="collapsed",
    )
    

    # Render selected sub-page
    if menu_selection == "Resumen Rendiciones Proveedores":
        sgf_resumen_rend_prov.render()


if __name__ == "__main__":
    main()
