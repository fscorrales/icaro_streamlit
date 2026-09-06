#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 28-aug-2025
Purpose: Migrate from Planillometro Historico (Patricia) in XLSX
"""

__all__ = ["PlanillometroHist"]


import json
from pathlib import Path

import numpy as np
import pandas as pd
import typer

from src.utils.handling_files import read_xls_file
from src.utils.print_tables import print_rich_table

from ...constants import Endpoints
from ...migration.migration_client import MigrationClient


# --------------------------------------------------
def validate_excel_file(value: Path):
    # Typer ya validó que el archivo existe y es legible.
    # Solo validamos extensión e integridad.
    if value and value.suffix.lower() not in [".xlsx", ".xls"]:
        raise typer.BadParameter(
            f"El archivo '{value}' no parece ser un archivo Excel (.xlsx o .xls)"
        )

    try:
        # Intentamos leer solo la primera fila para validar que no esté corrupto
        pd.read_excel(value, nrows=1)
    except Exception as e:
        raise typer.BadParameter(f"Error al abrir el archivo Excel: {e}")

    return value


# --------------------------------------------------
class PlanillometroHist:
    # --------------------------------------------------
    def __init__(self):
        self.clean_df = pd.DataFrame()

    # --------------------------------------------------
    def migrate_df_to_mongodb(self, df: pd.DataFrame) -> None:
        """Migrate DataFrame to MongoDB."""
        client = MigrationClient(token="token_bypassed")
        try:
            # 🕵️‍♂️ RASTREO PASO A PASO:
            print("1️⃣ Generando diccionario de registros...")
            records = df.to_dict(orient="records")

            print(f"2️⃣ Intentando iniciar sesión en: {client.base_url}/auth/login ...")
            client.login()  # 🚀 Movido adentro del try
            print("✅ Login exitoso. Token obtenido.")

            print("3️⃣ Intentando enviar el lote de registros a MongoDB...")
            # Aplicamos tu FIX directamente aquí
            clean_records = json.loads(
                json.dumps(
                    records,
                    default=lambda x: (
                        x.isoformat() if hasattr(x, "isoformat") else str(x)
                    ),
                )
            )

            # El cliente maneja internamente el login y el POST
            result = client.post_batch(
                endpoint=Endpoints.SIIF_PLANILLOMETRO_HIST.value, records=clean_records
            )
            # post_request(endpoint=endpoint, json_body=records, token=token)
            print(
                f"Successfully migrated Planllometro Hist's {len(records)} records to MongoDB."
            )

        except Exception as e:
            print(f"Error migrar el DataFrame a MongoDB: {e}")

    # --------------------------------------------------
    def from_excel(self, excel_path: Path) -> pd.DataFrame:
        df = read_xls_file(excel_path, header=0)
        df = df.replace("", None)
        df["desc_programa"] = np.where(
            df["proy"].isna(), df["prog"] + " - " + df["Descripción"], np.nan
        )
        df["desc_programa"] = df["desc_programa"].ffill()
        df["desc_subprograma"] = df["subprog"] + " - --"
        df["desc_proyecto"] = np.where(
            df["obra"].isna(), df["proy"] + " - " + df["Descripción"], np.nan
        )
        df["desc_proyecto"] = df["desc_proyecto"].ffill()
        df["desc_actividad"] = np.where(
            ~df["estructura"].isna(), df["obra"] + " - " + df["Descripción"], np.nan
        )
        df = df.dropna(subset=["estructura"])
        df["acum_2008"] = df["acum_2008"].astype(float)
        df = df.loc[
            :,
            [
                "desc_programa",
                "desc_subprograma",
                "desc_proyecto",
                "desc_actividad",
                "actividad",
                "partida",
                "estructura",
                "alta",
                "acum_2008",
            ],
        ]
        self.clean_df = df
        return self.clean_df

    # --------------------------------------------------
    def migrate_planillometro(self):
        self.migrate_df_to_mongodb(df=self.clean_df)


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(
    help="Migrate from Planillometro Historico in XLSX to MongoDB", add_completion=False
)


# --------------------------------------------------
@app.command()
def main(
    file: Path = typer.Option(
        None,
        "--file",
        "-f",
        help="XLS de Planillometro Historico (Patricia) report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        callback=validate_excel_file,
    ),
):
    """
    Lee, procesa y escribe el reporte planillometro_hist de Patricia.
    """
    try:
        siif = PlanillometroHist()
        siif.from_excel(excel_path=file)
        print_rich_table(siif.clean_df, title=f"Datos del archivo: {file.name}")
        siif.migrate_planillometro()
    except Exception as e:
        typer.secho(
            f"💥 Error durante la ejecución: {e}", fg=typer.colors.RED, err=True
        )


# --------------------------------------------------
if __name__ == "__main__":
    app()
    # From /invico_streamlit

    # poetry run python -m src.automation.siif.planillometro_hist -f "D:\Datos INVICO\IT\invico_streamlit\src\automation\siif\planillometro_hist.xlsx"
    # poetry run python -m src.automation.siif.planillometro_hist -f"C:\IT\Proyectos\Python\invico_streamlit\src\automation\siif\planillometro_hist.xls"
