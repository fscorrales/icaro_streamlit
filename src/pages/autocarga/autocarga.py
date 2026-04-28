"""Página Principal: Autocarga"""

import streamlit as st

from src.pages.autocarga import epam, obras


def main() -> None:

    tab_obras, tab_epam = st.tabs(["Obras", "EPAM"])

    with tab_obras:
        obras.render()

    with tab_epam:
        epam.render()


if __name__ == "__main__":
    main()
