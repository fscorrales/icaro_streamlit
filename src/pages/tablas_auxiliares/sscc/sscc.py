"""Página Principal: Tablas Auxiliares - SSCC."""

import streamlit as st

from src.pages.tablas_auxiliares.sscc import banco_invico, ctas_ctes


def main() -> None:
    tab_banco_invico, tab_ctas_ctes = st.tabs(["Banco INVICO", "Ctas Ctes"])

    with tab_banco_invico:
        banco_invico.render()

    with tab_ctas_ctes:
        ctas_ctes.render()


if __name__ == "__main__":
    main()
