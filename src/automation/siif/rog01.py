#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 14-feb-2025
Purpose: Read, process and write SIIF's rog01 (Detalle de partidas) report
"""

__all__ = ["Rog01"]

import asyncio
import inspect
import os
from pathlib import Path
from typing import Optional

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
class Rog01(SIIFReportManager):
    # --------------------------------------------------
    async def download_and_process_report(self) -> pd.DataFrame:
        """Download and process the rog01 report for a specific year."""
        try:
            await self.go_to_specific_report()
            self.download = await self.download_report()
            if self.download is None:
                raise ValueError("No se pudo descargar el reporte rog01.")
            await self.read_xls_file()
            return await self.process_dataframe()
        except Exception as e:
            print(f"Error al descargar y procesar el reporte: {e}")

    # --------------------------------------------------
    async def go_to_specific_report(self) -> None:
        await self.select_report_module(module=ReportCategory.Clasificadores)
        await self.select_specific_report_by_id(report_id="67")

    # --------------------------------------------------
    async def download_report(self) -> Download:
        try:
            self.download = None
            # Getting DOM elements
            btn_get_reporte = self.siif.reports_page.locator(
                "//div[@id='pt1:btnEjecutarReporte']"
            )
            btn_xls = self.siif.reports_page.locator(
                "//input[@id='pt1:rbtnXLS::content']"
            )
            await btn_xls.click()

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

        df = df.iloc[15:, [2, 4, 5, 6, 7, 11]]
        df.columns = [
            "grupo",
            "part_parcial",
            "desc_grupo",
            "partida",
            "desc_part_parcial",
            "desc_partida",
        ]
        df = df.replace("", np.nan)
        df["grupo"] = df.grupo.ffill()
        df["part_parcial"] = df.part_parcial.ffill()
        df["desc_grupo"] = df.desc_grupo.ffill()
        df["desc_part_parcial"] = df.desc_part_parcial.ffill()
        df = df.dropna(axis=0, how="any")

        self.clean_df = df
        return self.clean_df


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────


app = typer.Typer(help="Read, process and write SIIF's rog01", add_completion=False)


# --------------------------------------------------
@app.command()
def main(
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Username for SIIF access"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Password for SIIF access"
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
        help="SIIF' rog01.xls report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Lee, procesa y escribe el reporte rog01 del SIIF.
    """

    # 1. Validación de lógica de negocio (Exclusión mutua)
    if file and download:
        typer.secho(
            "❌ Error: No puedes usar --file y --download al mismo tiempo.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

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
    asyncio.run(run_automation(username, password, download, headless, file))


# --------------------------------------------------
async def run_automation(
    username: str,
    password: str,
    download: bool,
    headless: bool,
    file: Optional[Path] = None,
):
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
                typer.echo("⏳ Descargando reporte rf602...")

                # 1. Login
                connect_siif = await login(
                    username, password, playwright=p, headless=headless
                )

                # 2. Navegación inicial
                siif = Rog01(siif=connect_siif)
                await siif.go_to_reports()
                await siif.go_to_specific_report()

                # 3. Descarga y guardado físico
                typer.echo("⏳ Procesando Reporte...")
                # Descarga y guardado físico
                await siif.download_report()
                await siif.save_xls_file(
                    save_path=save_path,
                    file_name="rog01.xls",
                )
                # Feedback visual de éxito
                typer.secho(
                    "✅ Reporte descargado con éxito.",
                    fg=typer.colors.GREEN,
                )

                # 4. Lectura y Procesamiento
                await siif.read_xls_file()
                # print(siif.df)
                await siif.process_dataframe()
                # Feedback visual de éxito
                typer.secho(
                    "✅ Reporte procesado con éxito.",
                    fg=typer.colors.GREEN,
                )
                print_rich_table(siif.clean_df, title="Resultados")

                # 5. Logout
                await siif.logout()

            else:
                siif = Rog01()
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

    # poetry run python -m src.automation.siif.rog01 -d
    # poetry run python -m src.automation.siif.rog01 -f "D:\Datos INVICO\Python INVICO\invico_streamlit\src\automation\siif\rog01.xls"
