#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 18-jul-2025
Purpose: Read, process and write SIIF's rcocc31 () report
"""

__all__ = ["Rcocc31"]

import asyncio
import datetime as dt
import inspect
import os
from pathlib import Path
from typing import List, Optional

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
class Rcocc31(SIIFReportManager):
    # --------------------------------------------------
    async def download_and_process_report(
        self,
        ejercicio: int = dt.datetime.now().year,
        cta_contable: str = "1112-2-6",
    ) -> pd.DataFrame:
        """Download and process the rcocc31 report for a specific year."""
        try:
            await self.go_to_specific_report()
            self.download = await self.download_report(
                ejercicio=str(ejercicio), cta_contable=cta_contable
            )
            if self.download is None:
                raise ValueError("No se pudo descargar el reporte rcocc31.")
            await self.read_xls_file()
            return await self.process_dataframe()
        except Exception as e:
            print(f"Error al descargar y procesar el reporte: {e}")

    # --------------------------------------------------
    async def go_to_specific_report(self) -> None:
        await self.select_report_module(module=ReportCategory.Contabilidad)
        await self.select_specific_report_by_id(report_id="387")

    # --------------------------------------------------
    async def download_report(
        self,
        ejercicio: str = str(dt.datetime.now().year),
        cta_contable: str = "1112-2-6",
    ) -> Download:
        try:
            self.download = None
            # Getting DOM elements
            input_ejercicio = self.siif.reports_page.locator(
                "//input[@id='pt1:txtAnioEjercicio::content']"
            )
            input_nivel = self.siif.reports_page.locator(
                "//input[@id='pt1:txtNivel::content']"
            )
            input_mayor = self.siif.reports_page.locator(
                "//input[@id='pt1:txtMayor::content']"
            )
            input_subcuenta = self.siif.reports_page.locator(
                "//input[@id='pt1:txtSubCuenta::content']"
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
            # Cuentas Contables
            nivel, mayor, subcuenta = cta_contable.split("-")
            await input_nivel.clear()
            await input_nivel.fill(nivel)
            await input_mayor.clear()
            await input_mayor.fill(mayor)
            await input_subcuenta.clear()
            await input_subcuenta.fill(subcuenta)
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
            # await self.logout()

    # --------------------------------------------------
    async def process_dataframe(self, dataframe: pd.DataFrame = None) -> pd.DataFrame:
        """ "Transform read xls file"""
        if dataframe is None:
            df = self.df.copy()
        else:
            df = dataframe.copy()

        df["ejercicio"] = df.iloc[3, 1][-4:]
        df["cta_contable"] = (
            df.iloc[10, 6] + "-" + df.iloc[10, 11] + "-" + df.iloc[10, 12]
        )
        df = df.replace(to_replace="", value=None)
        df = df.iloc[20:, :]
        df = df.rename(
            {
                "3": "nro_entrada",
                "10": "nro_original",
                "14": "fecha_aprobado",
                "19": "auxiliar_1",
                "22": "auxiliar_2",
                "25": "tipo_comprobante",
                "26": "debitos",
                "28": "creditos",
                "29": "saldo",
            },
            axis="columns",
        )
        df = df.dropna(subset=["nro_entrada"])
        df["fecha_aprobado"] = pd.to_datetime(
            df["fecha_aprobado"], format="%Y-%m-%d %H:%M:%S"
        )
        df["fecha"] = df["fecha_aprobado"]
        # df.loc[df['fecha_aprobado'].dt.year.astype(str) == df['ejercicio'], 'fecha'] = df['fecha_aprobado']
        df.loc[df["fecha_aprobado"].dt.year.astype(str) != df["ejercicio"], "fecha"] = (
            pd.to_datetime(df["ejercicio"] + "-12-31", format="%Y-%m-%d")
        )
        df["mes"] = (
            df["fecha"].dt.month.astype(str).str.zfill(2) + "/" + df["ejercicio"]
        )

        df = df.loc[
            :,
            [
                "ejercicio",
                "mes",
                "fecha",
                "fecha_aprobado",
                "cta_contable",
                "nro_entrada",
                "nro_original",
                "auxiliar_1",
                "auxiliar_2",
                "tipo_comprobante",
                "debitos",
                "creditos",
                "saldo",
            ],
        ]
        df["ejercicio"] = pd.to_numeric(df["ejercicio"], errors="coerce")
        df["fecha"] = df["fecha"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )
        df["fecha_aprobado"] = df["fecha_aprobado"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )
        to_numeric_cols = ["debitos", "creditos", "saldo"]
        df[to_numeric_cols] = df[to_numeric_cols].apply(pd.to_numeric)

        self.clean_df = df
        return self.clean_df


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(help="Read, process and write SIIF's rcocc31", add_completion=False)


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
    cuentas: List[str] = typer.Option(
        ["1112-2-6"],
        "--cuentas",
        "-c",
        help="Cuentas Contables to download from SIIF",
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
        help="SIIF' rcocc31.xls report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Lee, procesa y escribe el reporte rcocc31 del SIIF.
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
        run_automation(
            username, password, ejercicios, download, headless, file, cuentas
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
    cuentas: List[str],
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
                typer.echo("⏳ Descargando reporte rcocc31...")

                # 1. Login
                connect_siif = await login(
                    username, password, playwright=p, headless=headless
                )

                # 2. Navegación inicial
                siif = Rcocc31(siif=connect_siif)
                await siif.go_to_reports()
                await siif.go_to_specific_report()

                # 3. Bucle de ejercicios
                for ejercicio in ejercicios:
                    for cta_contable in cuentas:
                        typer.echo(
                            f"⏳ Procesando cuenta {cta_contable} del ejercicio: {ejercicio}..."
                        )
                        # Descarga y guardado físico
                        await siif.download_report(
                            ejercicio=str(ejercicio), cta_contable=cta_contable
                        )
                        await siif.save_xls_file(
                            save_path=save_path,
                            file_name=str(ejercicio)
                            + "-rcocc31 ("
                            + cta_contable
                            + ").xls",
                        )
                        # Feedback visual de éxito
                        typer.secho(
                            f"✅ Cuenta {cta_contable} del ejercicio {ejercicio} descargado con éxito.",
                            fg=typer.colors.GREEN,
                        )

                        # 4. Lectura y Procesamiento
                        await siif.read_xls_file()
                        # print(siif.df)
                        await siif.process_dataframe()
                        # Feedback visual de éxito
                        typer.secho(
                            f"✅ Cuenta {cta_contable} del ejercicio {ejercicio} procesado con éxito.",
                            fg=typer.colors.GREEN,
                        )
                        print_rich_table(
                            siif.clean_df,
                            title=f"Resultados Cuenta {cta_contable} del Ejercicio {ejercicio}",
                        )

                # 5. Logout
                await siif.logout()

            else:
                siif = Rcocc31()
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

    # poetry run python -m src.automation.siif.rcocc31 -d
    # poetry run python -m src.automation.siif.rcocc31 -f "D:\Proyectos IT\invico_streamlit\src\automation\siif\2026-rcocc31 (1112-2-6).xls"
