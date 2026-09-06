#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 18-jun-2025
Purpose: Read, process and write SIIF's gto_rpa03g (Detalle Partidas 'ordenados' por entidad, año, periodo y grupo de partida) report
"""

__all__ = ["GtoRpa03g"]

import argparse
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
from src.services.models import GrupoPartidaSIIF
from src.utils.print_tables import print_rich_table


# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description="Read, process and write SIIF's gto_rpa03g",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-u",
        "--username",
        help="Username for SIIF access",
        metavar="username",
        type=str,
        default=None,
    )

    parser.add_argument(
        "-p",
        "--password",
        help="Password for SIIF access",
        metavar="password",
        type=str,
        default=None,
    )

    parser.add_argument(
        "-e",
        "--ejercicios",
        metavar="ejercicios",
        default=[dt.datetime.now().year],
        type=int,
        choices=range(2010, dt.datetime.now().year + 1),
        nargs="+",
        help="Ejercicios to download from SIIF",
    )

    parser.add_argument(
        "-g",
        "--grupo_partida",
        metavar="grupo_partida",
        default=4,
        type=int,
        choices=[int(c.value) for c in GrupoPartidaSIIF],
        help="Ejercicios to download from SIIF",
    )

    parser.add_argument(
        "-d", "--download", help="Download report from SIIF", action="store_true"
    )

    parser.add_argument(
        "--headless", help="Run browser in headless mode", action="store_true"
    )

    parser.add_argument(
        "-f",
        "--file",
        metavar="xls_file",
        default=None,
        type=argparse.FileType("r"),
        help="SIIF' rf602.xls report. Must be in the same folder",
    )

    args = parser.parse_args()

    if args.username is None or args.password is None:
        from ...config import settings

        args.username = settings.SIIF_USERNAME
        args.password = settings.SIIF_PASSWORD
        if args.username is None or args.password is None:
            parser.error("Both --username and --password are required.")

    if args.file and args.download:
        parser.error("You cannot use --file and --download together. Choose one.")

    return args


# --------------------------------------------------
class GtoRpa03g(SIIFReportManager):
    # --------------------------------------------------
    async def download_and_process_report(
        self,
        ejercicio: int = dt.datetime.now().year,
        grupo_partida: GrupoPartidaSIIF = GrupoPartidaSIIF.bienes_capital.value,
    ) -> pd.DataFrame:
        """Download and process the gto_rpa03g report for a specific year."""
        try:
            await self.go_to_specific_report()
            self.download = await self.download_report(
                ejercicio=str(ejercicio), grupo_partida=grupo_partida
            )
            if self.download is None:
                raise ValueError("No se pudo descargar el reporte gto_rpa03g.")
            await self.read_xls_file()
            return await self.process_dataframe()
        except Exception as e:
            print(f"Error al descargar y procesar el reporte: {e}")

    # --------------------------------------------------
    async def go_to_specific_report(self) -> None:
        await self.select_report_module(module=ReportCategory.Gastos)
        await self.select_specific_report_by_id(report_id="1175")

    # --------------------------------------------------
    async def download_report(
        self,
        ejercicio: str = str(dt.datetime.now().year),
        grupo_partida: str = str(GrupoPartidaSIIF.bienes_capital.value),
    ) -> Download:
        try:
            self.download = None
            # Getting DOM elements
            input_ejercicio = self.siif.reports_page.locator(
                "//input[@id='pt1:txtAnioEjercicio::content']"
            )
            input_gpo_partida = self.siif.reports_page.locator(
                "//input[@id='pt1:txtGrupoPartida::content']"
            )
            input_mes_desde = self.siif.reports_page.locator(
                "//input[@id='pt1:txtMesDesde::content']"
            )
            input_mes_hasta = self.siif.reports_page.locator(
                "//input[@id='pt1:txtMesHasta::content']"
            )
            btn_get_reporte = self.siif.reports_page.locator(
                "//div[@id='pt1:btnVerReporte']"
            )
            btn_xls = self.siif.reports_page.locator(
                "//input[@id='pt1:rbtnXLS::content']"
            )
            await btn_xls.click()

            # Mes Desde
            await input_mes_desde.clear()
            await input_mes_desde.fill("1")
            # Mes Hasta
            await input_mes_hasta.clear()
            await input_mes_hasta.fill("12")
            # Ejercicio
            await input_ejercicio.clear()
            await input_ejercicio.fill(str(ejercicio))
            # Grupo de Partida
            grupo_partida_str = str(grupo_partida)
            if grupo_partida_str.startswith("str:"):
                grupo_partida_str = grupo_partida_str[4:]
            await input_gpo_partida.clear()
            await input_gpo_partida.fill(grupo_partida_str)

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
        df["ejercicio"] = pd.to_numeric(df.iloc[3, 18][-4:], errors="coerce")
        df = df.tail(-21)
        df = df.dropna(subset=["1"])
        df = df.rename(
            columns={
                "1": "nro_entrada",
                "5": "nro_origen",
                "8": "importe",
                "14": "fecha",
                "17": "partida",
                "19": "nro_expte",
                "21": "glosa",
                "23": "beneficiario",
            }
        )
        df["importe"] = pd.to_numeric(df["importe"]).astype(np.float64)
        df["grupo"] = df["partida"].str[0]
        df["mes"] = df["fecha"].str[5:7] + "/" + df["ejercicio"].astype(str)
        df["nro_comprobante"] = (
            df["nro_entrada"].str.zfill(5) + "/" + df["mes"].str[-2:]
        )

        df["fecha"] = pd.to_datetime(
            df["fecha"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
        )
        df["fecha"] = df["fecha"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )

        df = df.loc[
            :,
            [
                "ejercicio",
                "mes",
                "fecha",
                "nro_comprobante",
                "importe",
                "grupo",
                "partida",
                "nro_entrada",
                "nro_origen",
                "nro_expte",
                "glosa",
                "beneficiario",
            ],
        ]

        self.clean_df = df
        return self.clean_df


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(
    help="Read, process and write SIIF's gto_rpa03g", add_completion=False
)


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
    grupos_partidas: List[str] = typer.Option(
        [GrupoPartidaSIIF.bienes_capital.value],
        "--grupos_partidas",
        "-g",
        help="Grupos de Partidas to download from SIIF",
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
        help="SIIF' gto_rpa03g.xls report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Lee, procesa y escribe el reporte gto_rpa03g del SIIF.
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

    # Validación de tipos de comprobantes
    grupos_partidas_ok = []
    for grupo_partida in grupos_partidas:
        if grupo_partida not in [str(c.value) for c in GrupoPartidaSIIF]:
            typer.secho(
                f"❌ Error: Grupo de partida {grupo_partida} no reconocido entre {[c.value for c in GrupoPartidaSIIF]}.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)
        else:
            grupos_partidas_ok.append(grupo_partida)

    grupos_partidas = grupos_partidas_ok

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
        run_automation(
            username, password, ejercicios, download, headless, file, grupos_partidas
        )
    )


# --------------------------------------------------
async def run_automation(
    username: str,
    password: str,
    ejercicios: List[int],
    download: bool,
    headless: bool,
    file: Optional[Path],
    grupos_partidas: List[int],
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
                typer.echo("⏳ Descargando reporte gto_rpa03g...")

                # 1. Login
                connect_siif = await login(
                    username, password, playwright=p, headless=headless
                )

                # 2. Navegación inicial
                siif = GtoRpa03g(siif=connect_siif)
                await siif.go_to_reports()
                await siif.go_to_specific_report()

                # 3. Bucle de ejercicios
                for ejercicio in ejercicios:
                    for grupo_partida in grupos_partidas:
                        typer.echo(
                            f"⏳ Procesando grupo partida {grupo_partida} del ejercicio: {ejercicio}..."
                        )
                        # Descarga y guardado físico
                        await siif.download_report(
                            ejercicio=str(ejercicio), grupo_partida=str(grupo_partida)
                        )
                        await siif.save_xls_file(
                            save_path=save_path,
                            file_name=str(ejercicio)
                            + "-gto_rpa03g (Gpo "
                            + str(grupo_partida)
                            + "00).xls",
                        )
                        # Feedback visual de éxito
                        typer.secho(
                            f"✅ Grupo Partida {grupo_partida} del ejercicio {ejercicio} descargado con éxito.",
                            fg=typer.colors.GREEN,
                        )

                        # 4. Lectura y Procesamiento
                        await siif.read_xls_file()
                        # print(siif.df)
                        await siif.process_dataframe()
                        # Feedback visual de éxito
                        typer.secho(
                            f"✅ Grupo Partida {grupo_partida} del ejercicio {ejercicio} procesado con éxito.",
                            fg=typer.colors.GREEN,
                        )
                        print_rich_table(
                            siif.clean_df,
                            title=f"Resultados Grupo Partida {grupo_partida} del Ejercicio {ejercicio}",
                        )

                # 5. Logout
                await siif.logout()

            else:
                siif = GtoRpa03g()
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

    # poetry run python -m src.automation.siif.gto_rpa03g -d
    # poetry run python -m src.automation.siif.gto_rpa03g -f "D:\Proyectos IT\invico_streamlit\src\automation\siif\2026-gto_rpa03g (Gpo 400).xls"
