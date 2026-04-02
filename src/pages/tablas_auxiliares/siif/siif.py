"""Página Principal: Tablas Auxiliares - SIIF."""

import streamlit as st

from src.pages.tablas_auxiliares.siif import (
    rcg01_uejp,
    rci02,
    rf602,
    rf610,
    rfondo07tp,
    rfondos04,
    rfp_p605b,
    ri102,
    rpa03g,
    rvicon03,
)


def main() -> None:

    (
        tab_rvicon03,
        tab_ri102,
        tab_rci02,
        tab_rfp_p605b,
        tab_rf602,
        tab_rf610,
        tab_rcg01_uejp,
        tab_rpa03g,
        tab_rfondo07tp,
        tab_rfondos04,
    ) = st.tabs(
        [
            "rvicon03",
            "ri102",
            "rci02",
            "rfp_p605b",
            "rf602",
            "rf610",
            "rcg01_uejp",
            "rpa03g",
            "rfondo07tp",
            "rfondos04",
        ]
    )

    with tab_rvicon03:
        rvicon03.render()

    with tab_ri102:
        ri102.render()

    with tab_rci02:
        rci02.render()

    with tab_rfp_p605b:
        rfp_p605b.render()

    with tab_rf602:
        rf602.render()

    with tab_rf610:
        rf610.render()

    with tab_rcg01_uejp:
        rcg01_uejp.render()

    with tab_rpa03g:
        rpa03g.render()

    with tab_rfondo07tp:
        rfondo07tp.render()

    with tab_rfondos04:
        rfondos04.render()


# tab1, tab2 = st.tabs(["Chart", "Data"], on_change="rerun")

# if tab1.open:
#     with st.spinner("Loading Tab 1..."):
#         time.sleep(2)
#     with tab1:
#         st.line_chart({"data": [1, 5, 2, 6]})

# if tab2.open:
#     with st.spinner("Loading Tab 2..."):
#         time.sleep(2)
#     with tab2:
#         st.dataframe({"col1": [1, 2, 3]})

if __name__ == "__main__":
    main()
