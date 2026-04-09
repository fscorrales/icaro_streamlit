__all__ = ["process_resumen_rend_obras", "process_resumen_rend_prov"]

import numpy as np
import pandas as pd


# --------------------------------------------------
def process_resumen_rend_prov(dataframe: pd.DataFrame) -> pd.DataFrame:
    """ "Transform read xls file"""
    df = dataframe.copy()
    df["origen"] = df["6"].str.split("-", n=1).str[0]
    df["origen"] = df["origen"].str.split("=", n=1).str[1]
    df["origen"] = df["origen"].str.replace('"', "")
    df["origen"] = df["origen"].str.strip()

    if df.loc[0, "origen"] == "OBRAS":
        df = df.rename(
            columns={
                "23": "beneficiario",
                "25": "libramiento_sgf",
                "26": "fecha",
                "27": "movimiento",
                "24": "cta_cte",
                "28": "importe_bruto",
                "29": "gcias",
                "30": "sellos",
                "31": "iibb",
                "32": "suss",
                "33": "invico",
                "34": "otras",
                "35": "importe_neto",
            }
        )
        df["destino"] = ""
        df["seguro"] = "0"
        df["salud"] = "0"
        df["mutual"] = "0"
    else:
        df = df.rename(
            columns={
                "26": "beneficiario",
                "27": "destino",
                "29": "libramiento_sgf",
                "30": "fecha",
                "31": "movimiento",
                "28": "cta_cte",
                "32": "importe_bruto",
                "33": "gcias",
                "34": "sellos",
                "35": "iibb",
                "36": "suss",
                "37": "invico",
                "38": "seguro",
                "39": "salud",
                "40": "mutual",
                "41": "importe_neto",
            }
        )
        df["otras"] = "0"

    df["ejercicio"] = df["fecha"].str[-4:]
    df["mes"] = df["fecha"].str[3:5] + "/" + df["ejercicio"]
    df["cta_cte"] = np.where(
        df["beneficiario"] == "CREDITO ESPECIAL", "130832-07", df["cta_cte"]
    )

    df = df.loc[
        :,
        [
            "origen",
            "ejercicio",
            "mes",
            "fecha",
            "beneficiario",
            "destino",
            "libramiento_sgf",
            "movimiento",
            "cta_cte",
            "importe_bruto",
            "gcias",
            "sellos",
            "iibb",
            "suss",
            "invico",
            "seguro",
            "salud",
            "mutual",
            "otras",
            "importe_neto",
        ],
    ]

    df.loc[:, "importe_bruto":] = df.loc[:, "importe_bruto":].apply(
        lambda x: x.str.replace(",", "").astype(float)
    )

    df["retenciones"] = df.loc[:, "gcias":"otras"].sum(axis=1)

    df["importe_bruto"] = np.where(
        df["origen"] == "EPAM",
        df["importe_bruto"] + df["invico"],
        df["importe_bruto"],
    )

    df["ejercicio"] = df["fecha"].str[-4:]
    df["mes"] = df["fecha"].str[3:5] + "/" + df["ejercicio"]
    df["ejercicio"] = pd.to_numeric(df["ejercicio"], errors="coerce")
    df["cta_cte"] = np.where(
        df["beneficiario"] == "CREDITO ESPECIAL", "130832-07", df["cta_cte"]
    )

    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")
    df["fecha"] = df["fecha"].apply(
        lambda x: x.to_pydatetime() if pd.notnull(x) else None
    )

    return df


# --------------------------------------------------
def process_resumen_rend_obras(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = dataframe.copy()
    df.loc[df["55"] != "", "obra"] = df["25"]
    df.loc[df["obra"] == "", "obra"] = df["38"]
    df["obra"] = df["obra"].ffill()
    df = df.assign(
        obra=df["obra"],
        beneficiario=df["25"].where(df["55"] == "", df["36"]),
        libramiento_sgf=df["26"].where(df["55"] == "", df["37"]),
        destino=df["27"].where(df["55"] == "", df["38"]),
        fecha=df["28"].where(df["55"] == "", df["39"]),
        movimiento=df["29"].where(df["55"] == "", df["40"]),
        importe_bruto=df["39"].where(df["55"] == "", df["50"]),
        gcias=df["31"].where(df["55"] == "", df["42"]),
        sellos=df["32"].where(df["55"] == "", df["43"]),
        lp=df["33"].where(df["55"] == "", df["44"]),
        iibb=df["34"].where(df["55"] == "", df["45"]),
        suss=df["35"].where(df["55"] == "", df["46"]),
        seguro=df["36"].where(df["55"] == "", df["47"]),
        salud=df["37"].where(df["55"] == "", df["48"]),
        mutual=df["38"].where(df["55"] == "", df["49"]),
        retenciones="0",
        importe_neto=df["30"].where(df["55"] == "", df["41"]),
    )
    df["ejercicio"] = df["fecha"].str[-4:]
    df["mes"] = df["fecha"].str[3:5] + "/" + df["ejercicio"]
    df[["cod_obra", "_"]] = df["obra"].str.split(pat="-", n=1, expand=True)
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y")
    df = df.replace(to_replace="", value="0")
    df["cod_obra"] = df["cod_obra"].str.strip()
    to_numeric_cols = [
        "importe_bruto",
        "gcias",
        "sellos",
        "lp",
        "iibb",
        "suss",
        "seguro",
        "salud",
        "mutual",
        "importe_neto",
    ]
    df[to_numeric_cols] = df[to_numeric_cols].apply(
        lambda x: x.str.replace(",", "").astype(float)
    )
    cols_to_sum = [
        col for col in to_numeric_cols if col not in ["importe_neto", "importe_bruto"]
    ]
    df["retenciones"] = df[cols_to_sum].sum(axis=1)
    df = df.loc[
        :,
        [
            "ejercicio",
            "mes",
            "fecha",
            "beneficiario",
            "cod_obra",
            "obra",
            "destino",
            "libramiento_sgf",
            "movimiento",
            "importe_bruto",
            "gcias",
            "sellos",
            "lp",
            "iibb",
            "suss",
            "seguro",
            "salud",
            "mutual",
            "retenciones",
            "importe_neto",
        ],
    ]

    return df
