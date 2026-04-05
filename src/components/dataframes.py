import streamlit as st


# --------------------------------------------------
def dataframe(data, key: str = "df", **kwargs):
    # --- GENERACIÓN DINÁMICA DE FORMATO ---
    column_config = {}

    # for col in data.columns:
    #     # Si la columna es numérica (int64, float64, etc.)
    #     if pd.api.types.is_numeric_dtype(data[col]):
    #         # Si el nombre de la columna sugiere que NO es un monto (ej: año, id, codigo)
    #         # podemos excluirla del formato moneda para que no ponga "$" a un año.
    #         if any(
    #             word in col.lower()
    #             for word in ["ejercicio", "id", "codigo", "anio", "year"]
    #         ):
    #             column_config[col] = st.column_config.NumberColumn(
    #                 format="%d"  # Número entero sin separador de miles para años
    #             )
    #         else:
    #             # Formato genérico para montos: $ 1.234.567,89
    #             column_config[col] = st.column_config.NumberColumn(
    #                 format="%.2f",  # El formato usa estilo financiero
    #             )

    with st.container(border=False, width="stretch"):
        return st.dataframe(
            data,
            key=key,
            width="stretch",
            hide_index=True,
            **kwargs,
        )
