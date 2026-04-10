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


def process_certificados_obras(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = dataframe.copy()
    # 1. Lógica previa para 'obra' (ffill es clave para reportes con celdas combinadas)
    titulo_reporte = df.iloc[0, 1]

    if titulo_reporte != "Resumen de Certificaciones:":
        return pd.DataFrame()  # O manejar el error según tu flujo
    # 2. Uso de assign (Equivalente a mutate de R)
    # Nota: Usamos np.where porque es más directo: np.where(condicion, valor_si_true, valor_si_false)

    #   BD <- BD %>%
    #     transmute(NroComprobanteSIIF = "",
    #               TipoComprobanteSIIF = "",
    #               Origen = "Obras",
    #               Periodo = str_sub(X3[1], -4),
    #               Beneficiario = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X22, NA),
    #               Obra = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X23, X22),
    #               CodigoObra = str_sub(Obra, 0, 9),
    #               NroCertificado = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X24, X23),
    #               NoSe = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X25, X24),
    #               NoSe2 = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X26, X25),
    #               MontoCertificado = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X27, X26),
    #               FondoDeReparo = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X28, X27),
    #               Otros = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X29, X28),
    #               ImporteBruto = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X30, X29),
    #               IIBB = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X31, X30),
    #               LP = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X32, X31),
    #               SUSS = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X33, X32),
    #               Gcias = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X34, X33),
    #               INVICO = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X35, X34),
    #               Retenciones = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X36, X35),
    #               ImporteNeto = ifelse(X38 == "TOTALES" | X49 == "TOTALES", X37, X36)) %>%
    #     select(-NoSe, -NoSe2) %>%
    #     zoo::na.locf()

    #   BD <- BD %>%
    #     mutate(MontoCertificado = parse_number(MontoCertificado),
    #            FondoDeReparo = parse_number(FondoDeReparo),
    #            Otros = parse_number(Otros),
    #            ImporteBruto = parse_number(ImporteBruto),
    #            IIBB = parse_number(IIBB),
    #            LP = parse_number(LP),
    #            SUSS = parse_number(SUSS),
    #            Gcias = parse_number(Gcias),
    #            INVICO = parse_number(INVICO),
    #            Retenciones = parse_number(Retenciones),
    #            ImporteNeto = parse_number(ImporteNeto)) %>%
    #     select(-Retenciones, -CodigoObra, -Otros)

    #   if (ExisteTablaBD("CERTIFICADOS")) {
    #     DatosDepurados <- FiltrarBD(
    #       paste0("SELECT * FROM CERTIFICADOS WHERE NroComprobanteSIIF <> ''")
    #     )
    #     DatosDepurados <- DatosDepurados %>%
    #       bind_rows(BD)
    #   } else {
    #     DatosDepurados <- BD
    #   }

    #   DatosDepurados <- DatosDepurados %>%
    #     arrange(desc(TipoComprobanteSIIF), desc(NroComprobanteSIIF),
    #             Beneficiario, Obra, NroCertificado)

    mask_totales = (df["37"] == "TOTALES") | (df["48"] == "TOTALES")

    periodo_valor = str(df["2"].iloc[0])[-4:]

    df = df.assign(
        nro_comprobante_siif="",
        tipo_comprobante_siif="",
        origen="Obras",
        periodo=periodo_valor,
        # Lógica de desplazamiento
        beneficiario=np.where(mask_totales, df["21"], np.nan),
        obra=np.where(mask_totales, df["22"], df["21"]),
        nro_certificado=np.where(mask_totales, df["23"], df["22"]),
        monto_certificado=np.where(mask_totales, df["26"], df["25"]),
        fondo_de_reparo=np.where(mask_totales, df["27"], df["26"]),
        otros=np.where(mask_totales, df["28"], df["27"]),
        importe_bruto=np.where(mask_totales, df["29"], df["28"]),
        iibb=np.where(mask_totales, df["30"], df["29"]),
        lp=np.where(mask_totales, df["31"], df["30"]),
        suss=np.where(mask_totales, df["32"], df["31"]),
        gcias=np.where(mask_totales, df["33"], df["32"]),
        invico=np.where(mask_totales, df["34"], df["33"]),
        retenciones=np.where(mask_totales, df["35"], df["34"]),
        importe_neto=np.where(mask_totales, df["36"], df["35"]),
    )

    # 3. Derivados de fecha y obra
    df["ejercicio"] = df["fecha"].str[-4:]
    df["mes"] = df["fecha"].str[3:5] + "/" + df["ejercicio"]

    # Split seguro (si no hay "-" no rompe)
    df[["cod_obra", "desc_obra"]] = df["obra"].str.split("-", n=1, expand=True)
    df["cod_obra"] = df["cod_obra"].str.strip()

    # 4. Conversión Numérica Robusta
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

    for col in to_numeric_cols:
        # Reemplazamos vacíos por "0", quitamos comas y convertimos
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", ""), errors="coerce"
        ).fillna(0.0)

    # 5. Cálculo de Retenciones (Suma horizontal)
    cols_to_sum = [
        c for c in to_numeric_cols if c not in ["importe_neto", "importe_bruto"]
    ]
    df["retenciones"] = df[cols_to_sum].sum(axis=1)

    # 6. Formateo de fecha para MongoDB (evita errores de string)
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")

    # 7. Selección final (transmute style)
    cols_finales = [
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
    ]

    return df[cols_finales]
