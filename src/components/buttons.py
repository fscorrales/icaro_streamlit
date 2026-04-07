__all__ = [
    "button_update",
    "button_export",
    "button_add",
    "button_edit",
    "button_delete",
    "button_selfadd",
]

import streamlit as st

# DEFAULT_BUTTON_STYLES = {
#     "button_update": {"type": "secondary"},
#     "button_export": {"type": "secondary"},
#     "button_add": {"type": "secondary"},
#     "button_edit": {"type": "secondary"},
#     "button_delete": {"type": "secondary"},
#     "button_selfadd": {"type": "secondary"},
# }

DEFAULT_WIDTH = 120


# --------------------------------------------------
def button_update(label: str, key: str = "button_update", **kwargs) -> bool:
    """Un componente reutilizable que retorna True si se presiona."""
    with st.container(border=False, width="content"):
        return st.button("🔄 " + label, key=key, width=DEFAULT_WIDTH, **kwargs)


# --------------------------------------------------
def button_export(label: str, key: str = "button_export", **kwargs):
    """Un componente reutilizable"""
    with st.container(border=False, width="content"):
        return st.button("📤 " + label, key=key, width=DEFAULT_WIDTH, **kwargs)


# --------------------------------------------------
def button_add(label: str, key: str = "button_add", **kwargs):
    """Un componente reutilizable"""
    with st.container(border=False, width="content"):
        return st.button("💾 " + label, key=key, width=DEFAULT_WIDTH, **kwargs)


# --------------------------------------------------
def button_edit(label: str, key: str = "button_edit", **kwargs):
    """Un componente reutilizable"""
    with st.container(border=False, width="content"):
        return st.button("✏️ " + label, key=key, width=DEFAULT_WIDTH, **kwargs)


# --------------------------------------------------
def button_delete(label: str, key: str = "button_delete", **kwargs):
    """Un componente reutilizable"""
    with st.container(border=False, width="content"):
        return st.button("🗑️ " + label, key=key, width=DEFAULT_WIDTH, **kwargs)


# --------------------------------------------------
def button_selfadd(label: str, key: str = "button_selfadd", **kwargs):
    """Un componente reutilizable"""
    with st.container(border=False, width="content"):
        return st.button("🔮 " + label, key=key, width=DEFAULT_WIDTH, **kwargs)
