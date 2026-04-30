"""Página Principal: Autocarga"""

import streamlit as st

from src.pages.autocarga import autocarga_epam, autocarga_obras


def main() -> None:

    tab_obras, tab_epam = st.tabs(["Obras", "EPAM"])

    with tab_obras:
        autocarga_obras.render()

    with tab_epam:
        autocarga_epam.render()


if __name__ == "__main__":
    main()
