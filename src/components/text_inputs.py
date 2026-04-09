__all__ = ["text_input_advance_filter"]

import streamlit as st


# --------------------------------------------------
def text_input_advance_filter(key: str = "text_input_advance_filter", **kwargs):
    """Un componente reutilizable"""
    helper_text = """ 
        ### 🔍 Guía de Filtros Dinámicos
        Podés combinar múltiples filtros usando comas (`,`).

        | Operador | Significado | Ejemplo |
        | :--- | :--- | :--- |
        | `=` | Igual a | `ejercicio=2024` |
        | ` ! ` ` = ` | Desigual | `fuente!=str:11` |
        | `>` | Mayor que | `importe>50000` |
        | `>` `=` | Mayor o igual | `fecha>=2024-01-01` |
        | `<` | Menor que | `limite<100` |
        | `<` `=` | Menor o igual | `offset<=10` |
        | `~` | Contiene (Regex) | `desc_obra~54 viv` |

        ---

        ### 💡 Tips de Formato
        * **Forzar Texto:** `grupo=str:2` (útil para IDs numéricos guardados como texto).
        * **Forzar Número:** `codigo=num:101`.

        ---

        ### 🧩 Atajos de Búsqueda (Regex)
        El operador ` ~ ` es insensible a mayúsculas y permite usar comodines:

        * **Posición:**
            * ` ^ ` Inicio: `desc_obra~^54` (Empieza con 54).
            * ` $ ` Fin: `expediente~2023$` (Termina en 2023).
        * **Comodines:**
            * ` . ` Uno solo: `obra~v.v` (Busca viv, vav, vuv...).
            * ` .* ` Varios: `obra~54.*viv` (Busca '54' seguido de cualquier cosa y luego 'viv').
        * **Lógica:**
            * ` | ` O (OR): `fuente~10|11` (Que sea fuente 10 o fuente 11).
            * ` [ ] ` Rango: `ejercicio~202[4-6]` (Busca 2024, 2025 o 2026).
        * **Especiales:**
            * ` ^(?!.*texto) ` No contiene: `obra~^(?!.*cancelada)` (Obras que NO digan cancelada).
        """
    with st.container(border=False, width="stretch"):
        text = st.text_input(
            "Filtro avanzado",
            value="",
            placeholder="ej: ejercicio=2024, fuente!=str:11",
            help=helper_text,
            key=key,
            **kwargs,
        )
    return text


op_map = {
    ">=": "$gte",
    "<=": "$lte",
    "!=": "$ne",
    ">": "$gt",
    "<": "$lt",
    "=": "$eq",
    "~": "$regex",
}
