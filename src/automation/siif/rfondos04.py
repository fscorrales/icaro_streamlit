#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 19-jun-2025
Purpose: Read, process and write SIIF's rfondos04 (...) report
"""

__all__ = ["Rfondos04"]


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
from src.services.models import TipoComprobanteSIIF
from src.utils.print_tables import print_rich_table


# --------------------------------------------------
class Rfondos04(SIIFReportManager):
    # --------------------------------------------------
    async def download_and_process_report(
        self,
        ejercicio: int = dt.datetime.now().year,
        tipo_comprobante: TipoComprobanteSIIF = TipoComprobanteSIIF.reversion_viatico.value,
    ) -> pd.DataFrame:
        """Download and process the rfondos04 report for a specific year."""
        try:
            await self.go_to_specific_report()
            self.download = await self.download_report(
                ejercicio=str(ejercicio), tipo_comprobante=str(tipo_comprobante)
            )
            if self.download is None:
                raise ValueError("No se pudo descargar el reporte rfondos04.")
            await self.read_xls_file()
            return await self.process_dataframe()
        except Exception as e:
            print(f"Error al descargar y procesar el reporte: {e}")

    # --------------------------------------------------
    async def go_to_specific_report(self) -> None:
        await self.select_report_module(module=ReportCategory.Gastos)
        await self.select_specific_report_by_id(report_id="477")

    # --------------------------------------------------
    async def download_report(
        self,
        ejercicio: str = str(dt.datetime.now().year),
        tipo_comprobante: TipoComprobanteSIIF = TipoComprobanteSIIF.reversion_viatico.value,
    ) -> Download:
        try:
            self.download = None
            # Getting DOM elements
            input_ejercicio = self.siif.reports_page.locator(
                "//input[@id='pt1:txtAnioEjercicio::content']"
            )
            input_tipo_comprobante = self.siif.reports_page.locator(
                "//input[@id='pt1:txtTipoCte::content']"
            )
            btn_get_reporte = self.siif.reports_page.locator(
                "//div[@id='pt1:btnVerReporte']"
            )
            btn_xls = self.siif.reports_page.locator(
                "//input[@id='pt1:rbtnXLS::content']"
            )
            await btn_xls.click()

            # Ejercicio
            await input_ejercicio.clear()
            await input_ejercicio.fill(str(ejercicio))
            # Tipo Comprobante
            await input_tipo_comprobante.clear()
            await input_tipo_comprobante.fill(tipo_comprobante)

            await btn_get_reporte.click()

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
    async def process_dataframe(
        self,
        dataframe: pd.DataFrame = None,
    ) -> pd.DataFrame:
        """ "Transform read xls file"""
        if dataframe is None:
            df = self.df.copy()
        else:
            df = dataframe.copy()

        df = df.replace(to_replace="", value=None)
        # df["ejercicio"] = pd.to_numeric(df.iloc[4, 1][-4:], errors="coerce")
        # df["tipo_comprobante"] = tipo_comprobante
        df = df.tail(-17)  # Eliminar filas de encabezado innecesarias
        df = df.dropna(subset=["10"])
        df = df.rename(
            columns={
                "2": "ejercicio",
                "4": "nro_comprobante",
                "6": "nro_fondo",
                "13": "tipo_comprobante",
                "14": "fecha",
                "15": "importe",
                "19": "glosa",
                "20": "saldo_c01",
                "23": "saldo_asiento",
            }
        )

        df["mes"] = df["fecha"].str[5:7] + "/" + df["ejercicio"].astype(str)
        df["nro_comprobante"] = df["nro_fondo"].str.zfill(5) + "/" + df["mes"].str[-2:]

        # 👇 conversión a datetime64[ns]
        df["fecha"] = pd.to_datetime(
            df["fecha"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
        )

        # 👇 conversión explícita a datetime.datetime de Python
        # df["fecha"] = df["fecha"].dt.to_pydatetime()
        df["fecha"] = df["fecha"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )

        to_numeric_cols = ["importe", "saldo_c01", "saldo_asiento"]
        df[to_numeric_cols] = (
            df[to_numeric_cols].apply(pd.to_numeric).astype(np.float64)
        )

        df = df.loc[
            :,
            [
                "ejercicio",
                "mes",
                "fecha",
                "tipo_comprobante",
                "nro_comprobante",
                "nro_fondo",
                "glosa",
                "importe",
                "saldo_c01",
                "saldo_asiento",
            ],
        ]

        self.clean_df = df
        return self.clean_df


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(help="Read, process and write SIIF's rfondos04", add_completion=False)


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
    tipos_comprobantes: List[str] = typer.Option(
        ["REV"],
        "--tipos_comprobantes",
        "-tc",
        help="Tipos Comprobante to download from SIIF",
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
        help="SIIF' rfondos04.xls report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Lee, procesa y escribe el reporte rfondos04 del SIIF.
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
    tipos_comprobantes_ok = []
    for tipo_comprobante in tipos_comprobantes:
        if tipo_comprobante not in [c.value for c in TipoComprobanteSIIF]:
            typer.secho(
                f"❌ Error: Tipo Comprobante {tipo_comprobante} no reconocido.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)
        else:
            tipos_comprobantes_ok.append(tipo_comprobante)

    tipos_comprobantes = tipos_comprobantes_ok

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
            username, password, ejercicios, download, headless, file, tipos_comprobantes
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
    tipos_comprobantes: List[str],
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
                typer.echo("⏳ Descargando reporte rfondos04...")

                # 1. Login
                connect_siif = await login(
                    username, password, playwright=p, headless=headless
                )

                # 2. Navegación inicial
                siif = Rfondos04(siif=connect_siif)
                await siif.go_to_reports()
                await siif.go_to_specific_report()

                # 3. Bucle de ejercicios
                for ejercicio in ejercicios:
                    for tipo_comprobante in tipos_comprobantes:
                        typer.echo(
                            f"⏳ Procesando cuenta {tipo_comprobante} del ejercicio: {ejercicio}..."
                        )
                        # Descarga y guardado físico
                        await siif.download_report(
                            ejercicio=str(ejercicio), tipo_comprobante=tipo_comprobante
                        )
                        await siif.save_xls_file(
                            save_path=save_path,
                            file_name=str(ejercicio)
                            + "-rfondos04 ("
                            + str(tipo_comprobante)
                            + ").xls",
                        )
                        # Feedback visual de éxito
                        typer.secho(
                            f"✅ Tipo comprobante {tipo_comprobante} del ejercicio {ejercicio} descargado con éxito.",
                            fg=typer.colors.GREEN,
                        )

                        # 4. Lectura y Procesamiento
                        await siif.read_xls_file()
                        # print(siif.df)
                        await siif.process_dataframe()
                        # Feedback visual de éxito
                        typer.secho(
                            f"✅ Tipo comprobante {tipo_comprobante} del ejercicio {ejercicio} procesado con éxito.",
                            fg=typer.colors.GREEN,
                        )
                        print_rich_table(
                            siif.clean_df,
                            title=f"Resultados Tipo Comprobante {tipo_comprobante} del Ejercicio {ejercicio}",
                        )

                # 5. Logout
                await siif.logout()

            else:
                siif = Rfondos04()
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

    # poetry run python -m src.automation.siif.rfondos04 -d
    # poetry run python -m src.automation.siif.rfondos04 -f "D:\Proyectos IT\invico_streamlit\src\automation\siif\2026-rfondos04 (REV).xls"
