__all__ = ["build_retenciones_payload"]


# --------------------------------------------------
def build_retenciones_payload(data: dict) -> dict:
    # Mapeo de campos del objeto a códigos contables de ICARO
    mapeo_codigos = {
        "iibb": "112",
        "gcias": "113",
        "suss": "114",
        "lp": "110",
        "invico": "337",
    }

    payload_items = []

    for campo, codigo in mapeo_codigos.items():
        # Obtenemos el valor, si no existe o no es numérico usamos 0
        valor = data.get(campo, 0)

        # Filtro: Solo agregamos si es mayor a 0
        if valor > 0:
            payload_items.append(
                {
                    "codigo": codigo,
                    "importe": round(float(valor), 2),  # Aseguramos 2 decimales
                }
            )

    return {"retenciones": payload_items}
