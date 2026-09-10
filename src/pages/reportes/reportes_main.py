"""Reportes de ICARO"""

import streamlit as st

from src.pages.reportes import acum_desc_siif, carga_with_desc_prov


def main() -> None:
    tab_group_desc_siif, tab_carga_with_desc_prov = st.tabs(
        ["Carga Agrupada", "Carga Con Desc. Prov."]
    )
    with tab_group_desc_siif:
        acum_desc_siif.render()

    with tab_carga_with_desc_prov:
        carga_with_desc_prov.render()


if __name__ == "__main__":
    main()
