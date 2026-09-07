#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 01-jul-2025
Purpose: Read, process and write SIIF's rf610 () report
"""

__all__ = ["Rf610"]


import asyncio
import datetime as dt
import inspect
import os
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import typer
from playwright.async_api import Download, async_playwright

from src.automation.siif.connect_siif import (
    ReportCategory,
    SIIFReportManager,
    login,
)
from src.utils.print_tables import print_rich_table


# --------------------------------------------------
class Rf610(SIIFReportManager):
    # --------------------------------------------------
    async def download_and_process_report(
        self, ejercicio: int = dt.datetime.now().year
    ) -> pd.DataFrame:
        """Download and process the rf610 report for a specific year."""
        try:
            await self.go_to_specific_report()
            self.download = await self.download_report(ejercicio=str(ejercicio))
            if self.download is None:
                raise ValueError("No se pudo descargar el reporte rf610.")
            await self.read_xls_file()
            return await self.process_dataframe()
        except Exception as e:
            print(f"Error al descargar y procesar el reporte: {e}")

    # --------------------------------------------------
    async def go_to_specific_report(self) -> None:
        await self.select_report_module(module=ReportCategory.Gastos)
        await self.select_specific_report_by_id(report_id="7")

    # --------------------------------------------------
    async def download_report(
        self, ejercicio: str = str(dt.datetime.now().year)
    ) -> Download:
        try:
            self.download = None
            # Getting DOM elements
            input_ejercicio = self.siif.reports_page.locator(
                "//input[@id='pt1:txtAnioEjercicio::content']"
            )
            btn_get_reporte = self.siif.reports_page.locator(
                "//div[@id='pt1:btnVerReporte']"
            )
            btn_xls = self.siif.reports_page.locator(
                "//input[@id='pt1:rbtnXLS::content']"
            )
            await btn_xls.click()

            await input_ejercicio.clear()
            await input_ejercicio.fill(str(ejercicio))

            # 1. Esperar la apertura de la ventana (popup) Y el evento de descarga a nivel contexto
            async with self.siif.context.expect_page() as popup_info:
                await btn_get_reporte.click()

            popup_page = await popup_info.value

            # Si el popup se redirigió al login, lanzamos error explícito para reloguear
            await popup_page.wait_for_load_state("domcontentloaded")
            if "login.jspx" in popup_page.url:
                await popup_page.close()
                raise Exception(
                    "La sesión expiro al intentar generar el reporte en SIIF."
                )

            # 2. Esperar la descarga directamente desde el popup o el contexto
            async with popup_page.expect_download(timeout=120000) as download_info:
                # Si el popup requiere una acción o auto-descarga:
                pass

            self.download = await download_info.value

            # Cierre limpio del popup
            if not popup_page.is_closed():
                await popup_page.close()

            await self.go_back_to_reports_list()

            return self.download

        except Exception as e:
            print(f"Error al descargar el reporte: {e}")
            # await self.logout()

    # --------------------------------------------------
    async def process_dataframe(self, dataframe: pd.DataFrame = None) -> pd.DataFrame:
        """ "Transform read xls file"""
        if dataframe is None:
            df = self.df.copy()
        else:
            df = dataframe.copy()

        df = self.df.replace(to_replace="", value=None)
        df["ejercicio"] = pd.to_numeric(df.iloc[9, 33][-4:], errors="coerce")
        df = df.rename(
            columns={
                "5": "programa",
                "7": "subprograma",
                "8": "proyecto",
                "11": "actividad",
                "13": "grupo",
                "16": "partida",
                "19": "desc_partida",
                "37": "credito_original",
                "43": "credito_vigente",
                "48": "comprometido",
                "54": "ordenado",
                "59": "saldo",
            }
        )
        df = df.tail(-30)
        df = df.loc[
            :,
            [
                "ejercicio",
                "programa",
                "subprograma",
                "proyecto",
                "actividad",
                "grupo",
                "partida",
                "desc_partida",
                "credito_original",
                "credito_vigente",
                "comprometido",
                "ordenado",
                "saldo",
            ],
        ]
        df["ejercicio"] = pd.to_numeric(df["ejercicio"], errors="coerce")
        df["programa"] = df["programa"].ffill()
        df["subprograma"] = df["subprograma"].ffill()
        df["proyecto"] = df["proyecto"].ffill()
        df["actividad"] = df["actividad"].ffill()
        df["grupo"] = df["grupo"].ffill()
        df["partida"] = df["partida"].ffill()
        df["desc_partida"] = df["desc_partida"].ffill()
        df = df.dropna(subset=["credito_original"])
        df[["programa", "desc_programa"]] = df["programa"].str.split(n=1, expand=True)
        df[["subprograma", "desc_subprograma"]] = df["subprograma"].str.split(
            n=1, expand=True
        )
        df[["proyecto", "desc_proyecto"]] = df["proyecto"].str.split(n=1, expand=True)
        df[["actividad", "desc_actividad"]] = df["actividad"].str.split(
            n=1, expand=True
        )
        df[["grupo", "desc_grupo"]] = df["grupo"].str.split(n=1, expand=True)
        df["programa"] = df["programa"].str.zfill(2)
        df["subprograma"] = df["subprograma"].str.zfill(2)
        df["proyecto"] = df["proyecto"].str.zfill(2)
        df["actividad"] = df["actividad"].str.zfill(2)
        df["desc_programa"] = df["desc_programa"].str.strip()
        df["desc_subprograma"] = df["desc_subprograma"].str.strip()
        df["desc_proyecto"] = df["desc_proyecto"].str.strip()
        df["desc_actividad"] = df["desc_actividad"].str.strip()
        df["desc_grupo"] = df["desc_grupo"].str.strip()
        df["desc_partida"] = df["desc_partida"].str.strip()
        df["estructura"] = (
            df["programa"]
            + "-"
            + df["subprograma"]
            + "-"
            + df["proyecto"]
            + "-"
            + df["actividad"]
            + "-"
            + df["partida"]
        )
        to_numeric_cols = [
            "credito_original",
            "credito_vigente",
            "comprometido",
            "ordenado",
            "saldo",
        ]
        df[to_numeric_cols] = (
            df[to_numeric_cols].apply(pd.to_numeric).astype(np.float64)
        )

        first_cols = [
            "ejercicio",
            "estructura",
            "programa",
            "desc_programa",
            "subprograma",
            "desc_subprograma",
            "proyecto",
            "desc_proyecto",
            "actividad",
            "desc_actividad",
            "grupo",
            "desc_grupo",
            "partida",
            "desc_partida",
        ]
        df = df.loc[:, first_cols].join(df.drop(first_cols, axis=1))

        self.clean_df = df
        return self.clean_df


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(help="Read, process and write SIIF's rf610", add_completion=False)


# --------------------------------------------------
@app.command()
def main(
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Username for SIIF access"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Password for SIIF access"
    ),
    ejercicios: List[int] = typer.Option(
        [dt.datetime.now().year],
        "--ejercicios",
        "-e",
        help="Ejercicios to download from SIIF",
    ),
    download: bool = typer.Option(
        False, "--download", "-d", help="Download report from SIIF"
    ),
    headless: bool = typer.Option(
        False, "--headless", help="Run browser in headless mode"
    ),
    file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="SIIF' rf610.xls report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Lee, procesa y escribe el reporte rf610 del SIIF.
    """

    # 1. Validación de lógica de negocio (Exclusión mutua)
    if file and download:
        typer.secho(
            "❌ Error: No puedes usar --file y --download al mismo tiempo.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    # Validación de ejercicios
    ejercicios_ok = []
    for ejercicio in ejercicios:
        if ejercicio not in list(range(2010, dt.datetime.now().year + 1)):
            typer.secho(
                f"❌ Error: Ejercicio {ejercicio} fuera del rango permitido (2010-{dt.datetime.now().year}).",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)
        else:
            ejercicios_ok.append(ejercicio)

    ejercicios = ejercicios_ok

    # 2. Carga de credenciales (Lógica que tenías en get_args)
    if username is None or password is None:
        try:
            from ...config import settings

            username = username or settings.SIIF_USERNAME
            password = password or settings.SIIF_PASSWORD
        except ImportError:
            pass

        if not username or not password:
            typer.secho(
                "❌ Error: Se requieren credenciales (vía argumentos o config).",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)

    # 3. Ejecución de la lógica asíncrona
    asyncio.run(
        run_automation(username, password, ejercicios, download, headless, file)
    )


# --------------------------------------------------
async def run_automation(username, password, ejercicios, download, headless, file):
    """
    Lógica de ejecución asíncrona de Playwright.
    """
    # Determinamos la ruta de guardado
    save_path = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    async with async_playwright() as p:
        try:
            if download:
                typer.echo("⏳ Descargando reporte rf610...")

                # 1. Login
                connect_siif = await login(
                    username, password, playwright=p, headless=headless
                )

                # 2. Navegación inicial
                siif = Rf610(siif=connect_siif)
                await siif.go_to_reports()
                await siif.go_to_specific_report()

                # 3. Bucle de ejercicios
                for ejercicio in ejercicios:
                    typer.echo(f"⏳ Procesando ejercicio: {ejercicio}...")
                    # Descarga y guardado físico
                    await siif.download_report(ejercicio=str(ejercicio))
                    await siif.save_xls_file(
                        save_path=save_path,
                        file_name=str(ejercicio) + "-rf610.xls",
                    )
                    # Feedback visual de éxito
                    typer.secho(
                        f"✅ Ejercicio {ejercicio} descargado con éxito.",
                        fg=typer.colors.GREEN,
                    )

                    # 4. Lectura y Procesamiento
                    await siif.read_xls_file()
                    # print(siif.df)
                    await siif.process_dataframe()
                    # Feedback visual de éxito
                    typer.secho(
                        f"✅ Ejercicio {ejercicio} procesado con éxito.",
                        fg=typer.colors.GREEN,
                    )
                    print_rich_table(
                        siif.clean_df, title=f"Resultados Ejercicio {ejercicio}"
                    )

                # 5. Logout
                await siif.logout()

            else:
                siif = Rf610()
                # 1. Lectura y Procesamiento
                typer.echo(f"⏳ Procesando archivo: {file.name}...")
                await siif.read_xls_file(file)
                await siif.process_dataframe()
                typer.secho(
                    f"✅ Archivo {file.name} procesado con éxito.",
                    fg=typer.colors.GREEN,
                )
                print_rich_table(siif.clean_df, title=f"Datos del archivo: {file.name}")

        except Exception as e:
            typer.secho(
                f"💥 Error durante la ejecución: {e}", fg=typer.colors.RED, err=True
            )


# --------------------------------------------------
if __name__ == "__main__":
    app()

    # From /invico_streamlit

    # poetry run python -m src.automation.siif.rf610 -d
    # poetry run python -m src.automation.siif.rf610 -f "D:\Proyectos IT\invico_streamlit\src\automation\siif\2026-rf610.xls"
