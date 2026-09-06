#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 20-jul-2025
Purpose: Read, process and write SIIF's rci02 () report
"""

__all__ = ["Rci02"]

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
from src.services import cta_cte_unifier
from src.utils.print_tables import print_rich_table


# --------------------------------------------------
class Rci02(SIIFReportManager):
    # --------------------------------------------------
    async def download_and_process_report(
        self, ejercicio: int = dt.datetime.now().year
    ) -> pd.DataFrame:
        """Download and process the rci02 report for a specific year."""
        try:
            await self.go_to_specific_report()
            self.download = await self.download_report(ejercicio=str(ejercicio))
            if self.download is None:
                raise ValueError("No se pudo descargar el reporte rci02.")
            await self.read_xls_file()
            return await self.process_dataframe()
        except Exception as e:
            print(f"Error al descargar y procesar el reporte: {e}")

    # --------------------------------------------------
    async def go_to_specific_report(self) -> None:
        await self.select_report_module(module=ReportCategory.Recursos)
        await self.select_specific_report_by_id(report_id="33")

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
            input_fecha_desde = self.siif.reports_page.locator(
                "//input[@id='pt1:idFechaDesde::content']"
            )
            input_fecha_hasta = self.siif.reports_page.locator(
                "//input[@id='pt1:idFechaHasta::content']"
            )
            btn_get_reporte = self.siif.reports_page.locator(
                "//div[@id='pt1:btnEjecutarReporte']"
            )
            btn_xls = self.siif.reports_page.locator(
                "//input[@id='pt1:rbtnXLS::content']"
            )
            await btn_xls.click()

            # Ejercicio
            await input_ejercicio.clear()
            await input_ejercicio.fill(str(ejercicio))
            # Fecha Desde
            await input_fecha_desde.clear()
            fecha_desde = dt.datetime.strftime(
                dt.date(year=int(ejercicio), month=1, day=1), "%d/%m/%Y"
            )
            await input_fecha_desde.fill(fecha_desde)
            # Fecha Hasta
            await input_fecha_hasta.clear()
            fecha_hasta = dt.datetime(year=(int(ejercicio)), month=12, day=31)
            fecha_hasta = min(fecha_hasta, dt.datetime.now())
            fecha_hasta = dt.datetime.strftime(fecha_hasta, "%d/%m/%Y")
            await input_fecha_hasta.fill(fecha_hasta)

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
            raise e

    # --------------------------------------------------
    async def process_dataframe(self, dataframe: pd.DataFrame = None) -> pd.DataFrame:
        """ "Transform read xls file"""
        if dataframe is None:
            df = self.df.copy()
        else:
            df = dataframe.copy()

        df["ejercicio"] = df.iloc[3, 34]
        df = df.replace(to_replace="", value=None)
        df = df.tail(-22)
        df = df.dropna(subset=["2"])
        df = df.rename(
            columns={
                "17": "fecha",
                "6": "fuente",
                "28": "cta_cte",
                "2": "nro_entrada",
                "23": "importe",
                "32": "glosa",
                "42": "es_verificado",
                "10": "clase_reg",
                "13": "clase_mod",
            }
        )
        df["mes"] = df["fecha"].str[5:7] + "/" + df["ejercicio"]
        df["es_remanente"] = df["glosa"].str.contains("REMANENTE")
        df["es_invico"] = df["glosa"].str.contains("%")
        df["es_verificado"] = np.where(df["es_verificado"] == "S", True, False)
        df["importe"] = df["importe"].apply(pd.to_numeric).astype(np.float64)

        df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d %H:%M:%S")
        df["fecha"] = df["fecha"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )
        df = df.loc[
            :,
            [
                "ejercicio",
                "mes",
                "fecha",
                "fuente",
                "cta_cte",
                "nro_entrada",
                "importe",
                "glosa",
                "es_remanente",
                "es_invico",
                "es_verificado",
                "clase_reg",
                "clase_mod",
            ],
        ]

        df["ejercicio"] = pd.to_numeric(df["ejercicio"], errors="coerce")
        self.clean_df = df
        return self.clean_df

    # --------------------------------------------------
    def cta_cte_unifier(self, token: Optional[str] = None):
        self.clean_df = cta_cte_unifier(
            original_df=self.clean_df,
            cta_cte_nexo="siif_recursos_cta_cte",
            token=token,
        )


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(help="Read, process and write SIIF's rci02", add_completion=False)


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
        help="SIIF' rci02.xls report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Lee, procesa y escribe el reporte rci02 del SIIF.
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
                typer.echo("⏳ Descargando reporte rci02...")

                # 1. Login
                connect_siif = await login(
                    username, password, playwright=p, headless=headless
                )

                # 2. Navegación inicial
                siif = Rci02(siif=connect_siif)
                await siif.go_to_reports()
                await siif.go_to_specific_report()

                # 3. Bucle de ejercicios
                for ejercicio in ejercicios:
                    typer.echo(f"⏳ Procesando ejercicio: {ejercicio}...")
                    # Descarga y guardado físico
                    await siif.download_report(ejercicio=str(ejercicio))
                    await siif.save_xls_file(
                        save_path=save_path,
                        file_name=str(ejercicio) + "-rci02.xls",
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
                siif = Rci02()
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

    # poetry run python -m src.automation.siif.rci02 -d
    # poetry run python -m src.automation.siif.rci02 -f "D:\Proyectos IT\invico_streamlit\src\automation\siif\2026-rci02.xls"
