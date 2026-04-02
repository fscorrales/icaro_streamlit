import streamlit as st


# --------------------------------------------------
def text_input_advance_filter(key: str = "text_input_advance_filter", **kwargs):
    """Un componente reutilizable"""
    with st.container(border=False, width="stretch"):
        text = st.text_input("Filtro avanzado", value="", key=key, **kwargs)
    return text
