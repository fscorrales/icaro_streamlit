__all__ = ["metric_card"]

import streamlit as st


# --------------------------------------------------
def metric_card(title, value, delta):
    """Un componente reutilizable para mostrar métricas."""
    with st.container(border=True):
        st.write(f"### {title}")
        st.metric(label="Estado actual", value=value, delta=delta)
        if st.button(f"Ver detalles de {title}", key=title):
            st.info(f"Desglosando datos para {title}...")
