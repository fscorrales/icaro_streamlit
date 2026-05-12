"""Página Principal: Estructura"""

import streamlit as st

from src.pages.estructura import completo, programas, subprogramas


def main() -> None:

    tab_completo, tab_prog, tab_subprog, tab_proy, tab_act = st.tabs(
        ["Completo", "Programas", "Subprogramas", "Proyectos", "Actividades"]
    )

    with tab_completo:
        completo.render()

    with tab_prog:
        programas.render()

    with tab_subprog:
        subprogramas.render()

    with tab_proy:
        pass

    with tab_act:
        pass


if __name__ == "__main__":
    main()
