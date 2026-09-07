#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 21-feb-2026
Purpose: Migrate from Deuda Flotante (TPF) in PDF to MongoDB
"""

__all__ = ["Rdeu012b2Cuit"]

import re
from pathlib import Path

import pandas as pd
import pdfplumber
import typer

from src.utils.print_tables import print_rich_table


# --------------------------------------------------
def parsear_fila(texto):
    """
    Script para leer el PDF de deuda flotante (rdeu012b2_Cuit) y cargarlo en un DataFrame.
    Requiere: pip install pdfplumber pandas
    Parsea una fila del PDF con el formato:
    NroEntrada NroOrigen CodFte Org_Fin Monto SaldoAPagar NroExpediente CtaCte Descripcion

    Ejemplo:
    '393 393 13 0 5.951.535,09 1.965.478,36 900011962016 130868045 P/TRANSFERENCIAS...'
    """
    # Numeros con formato argentino: punto de miles, coma decimal. Ej: 5.951.535,09
    # patron_monto = r"\d{1,3}(?:\.\d{3})+,\d+"
    patron_monto = r"\d{1,3}(?:\.\d{3})+,\d*"  # \d+ -> \d*

    # Numero de expediente y cuenta corriente (9+ digitos consecutivos sin puntos)
    patron_expediente = r"\b\d{9,}\b"

    montos = re.findall(patron_monto, texto)
    expedientes = re.findall(patron_expediente, texto)

    partes = texto.split()
    nro_entrada = partes[0] if len(partes) > 0 else ""
    nro_origen = partes[1] if len(partes) > 1 else ""
    cod_fte = partes[2] if len(partes) > 2 else ""
    org_fin = partes[3] if len(partes) > 3 else ""

    monto = montos[0] if len(montos) > 0 else ""
    saldo_a_pagar = montos[1] if len(montos) > 1 else ""
    nro_expediente = expedientes[0] if len(expedientes) > 0 else ""
    cta_cte = expedientes[1] if len(expedientes) > 1 else ""

    desc_match = re.search(r"P/TRANSFER.*", texto, re.IGNORECASE)
    descripcion = desc_match.group(0).strip() if desc_match else ""

    return {
        "nro_entrada": nro_entrada,
        "nro_origen": nro_origen,
        "fuente": cod_fte,
        "org_fin": org_fin,
        "importe": monto,
        "saldo": saldo_a_pagar,
        "nro_expte": nro_expediente,
        "cta_cte": cta_cte,
        "glosa": descripcion,
        # "texto_completo": texto,
    }


# --------------------------------------------------
def extraer_datos_pdf(pdf_path: Path) -> pd.DataFrame:
    filas = []
    fecha_desde = None
    fecha_hasta = None
    entidad_actual = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto_pagina = page.extract_text()

            # --- Encabezado ---
            if fecha_desde is None:
                match_fechas = re.search(
                    r"DESDE\s+(\d{2}/\d{2}/\d{4})\s+HASTA\s+(\d{2}/\d{2}/\d{4})",
                    texto_pagina,
                )
                if match_fechas:
                    fecha_desde = pd.to_datetime(
                        match_fechas.group(1), format="%d/%m/%Y"
                    )
                    fecha_hasta = pd.to_datetime(
                        match_fechas.group(2), format="%d/%m/%Y"
                    )

            match_entidad = re.search(r"Entidad\s*:\s*\d+\s+(.+)", texto_pagina)
            if match_entidad:
                entidad_actual = match_entidad.group(1).strip()

            # --- Recolectar textos ya capturados por tablas ---
            textos_tabla = set()
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and row[0]:
                        textos_tabla.add(row[0].strip())

            # --- Combinar: tablas + líneas huérfanas del texto crudo ---
            textos_a_procesar = []

            for table in tables:
                for row in table:
                    if row and row[0]:
                        textos_a_procesar.append(row[0].strip())

            for linea in texto_pagina.splitlines():
                linea = linea.strip()
                if re.match(r"^\d+", linea) and linea not in textos_tabla:
                    textos_a_procesar.append(linea)

            # --- Procesar cada texto ---
            for texto in textos_a_procesar:
                if (
                    not texto
                    or texto.startswith("Nro")
                    or texto.startswith("Beneficiario")
                    or texto.startswith("Entidad")
                    or texto.startswith("DESDE")
                ):
                    continue

                if re.match(r"^\d+", texto):
                    fila = parsear_fila(texto)
                    fila["fecha_desde"] = fecha_desde
                    fila["fecha_hasta"] = fecha_hasta
                    fila["ejercicio"] = fecha_hasta.year if fecha_hasta else None
                    fila["mes_hasta"] = (
                        fecha_hasta.strftime("%m/%Y") if fecha_hasta else None
                    )
                    fila["entidad"] = entidad_actual
                    fila["ejercicio_deuda"] = (
                        int(fila["nro_expte"][-4:])
                        if fila["nro_expte"] and len(fila["nro_expte"]) >= 4
                        else None
                    )
                    filas.append(fila)

    df = pd.DataFrame(filas)

    for col in ["importe", "saldo"]:
        df[col] = df[col].str.replace(".", "", regex=False)
        df[col] = df[col].str.replace(",", ".", regex=False)
        df[col] = df[col].str.rstrip(
            "."
        )  # 👈 saca el punto residual si no había decimales
        df[col] = pd.to_numeric(df[col], errors="coerce")

    first_cols = [
        "ejercicio",
        "mes_hasta",
        "entidad",
        "ejercicio_deuda",
        "fuente",
        "nro_entrada",
        "nro_origen",
        "importe",
        "saldo",
    ]
    df = df[first_cols].join(df.drop(columns=first_cols))

    return df


# --------------------------------------------------
def validate_pdf_file(value: Path):
    # Typer ya valida 'exists' y 'file_okay' por el Option,
    # pero aquí validamos la extensión y el contenido
    if value and value.suffix.lower() != ".pdf":
        raise typer.BadParameter(f"El archivo '{value}' no parece ser un archivo PDF")

    try:
        import pdfplumber

        with pdfplumber.open(value) as pdf:
            if len(pdf.pages) == 0:
                raise typer.BadParameter(
                    f"El archivo PDF '{value}' no contiene páginas"
                )
    except Exception as e:
        raise typer.BadParameter(f"Error al abrir o validar el PDF: {e}")

    return value


# --------------------------------------------------
class Rdeu012b2Cuit:
    # --------------------------------------------------
    def __init__(self):
        self.clean_df = pd.DataFrame()

        # Repositorios por colección
        # self.rdeu012b2_cuit_repo = Rdeu012b2CuitRepository()

    # --------------------------------------------------
    def from_pdf(self, pdf_path: Path) -> pd.DataFrame:
        df = extraer_datos_pdf(pdf_path)
        self.clean_df = df
        return self.clean_df


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(
    help="Migrate from Deuda Flotante (TPF) in XLSX to MongoDB", add_completion=False
)


# --------------------------------------------------
@app.command()
def main(
    file: Path = typer.Option(
        None,
        "--file",
        "-f",
        help="PDF de Deuda Flotante (TPF) report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        callback=validate_pdf_file,
    ),
):
    """
    Lee, procesa y escribe el reporte rdeu012b2_cuit del SIIF.
    """
    try:
        siif = Rdeu012b2Cuit()
        siif.from_pdf(pdf_path=file)
        print_rich_table(siif.clean_df, title=f"Datos del archivo: {file.name}")
    except Exception as e:
        typer.secho(
            f"💥 Error durante la ejecución: {e}", fg=typer.colors.RED, err=True
        )


# --------------------------------------------------
if __name__ == "__main__":
    app()
    # From /invico_streamlit

    # poetry run python -m src.automation.siif.rdeu012b2_cuit -f "D:\Proyectos IT\invico_streamlit\src\automation\siif\rdeu012b2_cuit.pdf"
    # poetry run python -m src.automation.siif.rdeu012b2_cuit -f"C:\IT\Proyectos\Python\invico_streamlit\src\automation\siif\rdeu012b2_cuit.pdf"
