__all__ = ["button_update", "button_export"]

import streamlit as st


# --------------------------------------------------
def button_update(label: str, key: str = "button_update", **kwargs) -> bool:
    """Un componente reutilizable que retorna True si se presiona."""
    with st.container(border=False, width="content"):
        return st.button("🔄 " + label, key=key, **kwargs)


# --------------------------------------------------
def button_export(label: str, key: str = "button_export", **kwargs):
    """Un componente reutilizable"""
    with st.container(border=False, width="content"):
        return st.button("🔄 " + label, key=key, **kwargs)
