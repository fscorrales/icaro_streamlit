"""Página Principal: Autocarga"""

import streamlit as st

from src.pages.autocarga import epam, obras


def main() -> None:

    tab_certificados, tab_epam = st.tabs(["Certificados", "EPAM"])

    with tab_certificados:
        obras.render()

    with tab_epam:
        epam.render()


if __name__ == "__main__":
    main()
