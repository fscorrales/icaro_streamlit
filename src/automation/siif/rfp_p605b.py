#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 18-jul-2025
Purpose: Read, process and write SIIF's rfp_p605b () report
"""

__all__ = ["RfpP605b"]

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
class RfpP605b(SIIFReportManager):
    # --------------------------------------------------
    async def download_and_process_report(
        self, ejercicio: int = dt.datetime.now().year
    ) -> pd.DataFrame:
        """Download and process the rfp_p605b report for a specific year."""
        try:
            await self.go_to_specific_report()
            self.download = await self.download_report(ejercicio=str(ejercicio))
            if self.download is None:
                raise ValueError("No se pudo descargar el reporte rfp_p605b.")
            await self.read_xls_file()
            return await self.process_dataframe()
        except Exception as e:
            print(f"Error al descargar y procesar el reporte: {e}")

    # --------------------------------------------------
    async def go_to_specific_report(self) -> None:
        await self.select_report_module(module=ReportCategory.Formulacion)
        await self.select_specific_report_by_id(report_id="890")

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
                "//div[@id='pt1:btnEjecutarReporte']"
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

        df = df.replace(to_replace="", value=None)
        df["ejercicio"] = pd.to_numeric(df.iloc[13, 1][-4:], errors="coerce")
        df = df.drop(range(22))

        df["programa"] = np.where(
            df["3"].str[0:8] == "Programa", df["3"].str[22:], None
        )
        df["programa"] = df["programa"].ffill()
        df["prog"] = df["programa"].str[:2]
        df["prog"] = df["prog"].str.strip()
        df["desc_prog"] = df["programa"].str[3:]
        df["desc_prog"] = df["desc_prog"].str.strip()
        df["subprograma"] = np.where(
            df["3"].str[0:11] == "SubPrograma", df["3"].str[19:], None
        )
        df["proyecto"] = np.where(
            df["3"].str[0:8] == "Proyecto", df["3"].str[24:], None
        )
        df["actividad"] = np.where(
            df["3"].str[0:9] == "Actividad", df["3"].str[20:], None
        )
        df["grupo"] = np.where(df["10"] != "", df["10"].str[0:3], None)
        df["grupo"] = df["grupo"].ffill()
        df["partida"] = np.where(df["9"] != "", df["9"], None)
        df["fuente_11"] = df["22"]
        df["fuente_10"] = df["19"]
        df = df.loc[
            :,
            [
                "ejercicio",
                "prog",
                "desc_prog",
                "subprograma",
                "proyecto",
                "actividad",
                "grupo",
                "partida",
                "fuente_11",
                "fuente_10",
            ],
        ]
        df = df.dropna(
            subset=["subprograma", "proyecto", "actividad", "partida"], how="all"
        )
        df["subprograma"] = df["subprograma"].ffill()
        df = df.dropna(subset=["proyecto", "actividad", "partida"], how="all")
        df["proyecto"] = df["proyecto"].ffill()
        df = df.dropna(subset=["actividad", "partida"], how="all")
        df["actividad"] = df["actividad"].ffill()
        df = df[df["partida"].str.len() == 3]
        df["sub"] = df["subprograma"].str[:2]
        df["sub"] = df["sub"].str.strip()
        df["desc_subprog"] = df["subprograma"].str[3:]
        df["desc_subprog"] = df["desc_subprog"].str.strip()
        df["proy"] = df["proyecto"].str[:2]
        df["proy"] = df["proy"].str.strip()
        df["desc_proy"] = df["proyecto"].str[3:]
        df["desc_proy"] = df["desc_proy"].str.strip()
        df["act"] = df["actividad"].str[:2]
        df["act"] = df["act"].str.strip()
        df["desc_act"] = df["actividad"].str[3:]
        df["desc_act"] = df["desc_act"].str.strip()
        df["fuente_10"] = df["fuente_10"].astype(float)
        df["fuente_11"] = df["fuente_11"].astype(float)
        df["fuente"] = np.where(
            df["fuente_10"].astype(int) > 0,
            "10",
            np.where(df["fuente_11"].astype(int) > 0, "11", ""),
        )
        df["formulado"] = df["fuente_10"] + df["fuente_11"]
        df["prog"] = df["prog"].str.zfill(2)
        df["sub"] = df["sub"].str.zfill(2)
        df["proy"] = df["proy"].str.zfill(2)
        df["act"] = df["act"].str.zfill(2)
        df["estructura"] = (
            df["prog"]
            + "-"
            + df["sub"]
            + "-"
            + df["proy"]
            + "-"
            + df["act"]
            + "-"
            + df["partida"]
        )
        df = df.loc[
            :,
            [
                "ejercicio",
                "estructura",
                "fuente",
                "prog",
                "desc_prog",
                "sub",
                "desc_subprog",
                "proy",
                "desc_proy",
                "act",
                "desc_act",
                "grupo",
                "partida",
                "formulado",
            ],
        ]
        df = df.rename(
            columns={
                "prog": "programa",
                "sub": "subprograma",
                "proy": "proyecto",
                "act": "actividad",
                "desc_prog": "desc_programa",
                "desc_subprog": "desc_subprograma",
                "desc_proy": "desc_proyecto",
                "desc_act": "desc_actividad",
            }
        )

        self.clean_df = df
        return self.clean_df


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(help="Read, process and write SIIF's rfp_p605b", add_completion=False)


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
        help="SIIF' rfp_p605b.xls report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Lee, procesa y escribe el reporte rfp_p605b del SIIF.
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
                typer.echo("⏳ Descargando reporte rfp_p605b...")

                # 1. Login
                connect_siif = await login(
                    username, password, playwright=p, headless=headless
                )

                # 2. Navegación inicial
                siif = RfpP605b(siif=connect_siif)
                await siif.go_to_reports()
                await siif.go_to_specific_report()

                # 3. Bucle de ejercicios
                for ejercicio in ejercicios:
                    typer.echo(f"⏳ Procesando ejercicio: {ejercicio}...")
                    # Descarga y guardado físico
                    await siif.download_report(ejercicio=str(ejercicio))
                    await siif.save_xls_file(
                        save_path=save_path,
                        file_name=str(ejercicio) + "-rfp_p605b.xls",
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
                siif = RfpP605b()
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

    # poetry run python -m src.automation.siif.rfp_p605b -d
    # poetry run python -m src.automation.siif.rfp_p605b -f "D:\Proyectos IT\invico_streamlit\src\automation\siif\2026-rfp_p605b.xls"
