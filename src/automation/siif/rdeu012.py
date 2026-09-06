#!/usr/bin/env python3
"""
Author : Fernando Corrales <fscpython@gmail.com>
Date   : 21-jul-2025
Purpose: Read, process and write SIIF's rdeu012 () report
"""

__all__ = ["Rdeu012"]

import asyncio
import datetime as dt
import inspect
import os
from datetime import timedelta
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
class Rdeu012(SIIFReportManager):
    # --------------------------------------------------
    async def download_and_process_report(
        self, mes: str = dt.datetime.strftime(dt.datetime.now(), "%Y-%m")
    ) -> pd.DataFrame:
        """Download and process the rdeu012 report for a specific year."""
        try:
            await self.go_to_specific_report()
            self.download = await self.download_report(mes=str(mes))
            if self.download is None:
                raise ValueError("No se pudo descargar el reporte rdeu012.")
            await self.read_xls_file()
            return await self.process_dataframe()
        except Exception as e:
            print(f"Error al descargar y procesar el reporte: {e}")

    # --------------------------------------------------
    async def go_to_specific_report(self) -> None:
        await self.select_report_module(module=ReportCategory.Gastos)
        await self.select_specific_report_by_id(report_id="267")

    # --------------------------------------------------
    async def download_report(
        self, mes: str = dt.datetime.strftime(dt.datetime.now(), "%m-%Y")
    ) -> Download:
        try:
            self.download = None
            # Getting DOM elements
            input_cod_fuente = self.siif.reports_page.locator(
                "//input[@id='pt1:inputText3::content']"
            )
            input_fecha_desde = self.siif.reports_page.locator(
                "//input[@id='pt1:idFechaDesde::content']"
            )
            input_fecha_hasta = self.siif.reports_page.locator(
                "//input[@id='pt1:idFechaHasta::content']"
            )
            btn_get_reporte = self.siif.reports_page.locator(
                "//div[@id='pt1:btnVerReporte']"
            )
            btn_xls = self.siif.reports_page.locator(
                "//input[@id='pt1:rbtnXLS::content']"
            )
            await btn_xls.click()

            # Fuente
            await input_cod_fuente.clear()
            await input_cod_fuente.fill("0")
            # Fecha desde
            await input_fecha_desde.clear()
            await input_fecha_desde.fill("01/01/2010")
            # Fecha hasta
            int_ejercicio = int(mes[-4:])
            if int_ejercicio > 2010 and int_ejercicio <= dt.datetime.now().year:
                fecha_hasta = dt.datetime(
                    year=(int_ejercicio), month=int(mes[0:2]), day=1
                )
                next_month = fecha_hasta.replace(day=28) + timedelta(days=4)
                fecha_hasta = next_month - timedelta(days=next_month.day)
                fecha_hasta = min(fecha_hasta.date(), dt.date.today())
                fecha_hasta = dt.datetime.strftime(fecha_hasta, "%d/%m/%Y")
                await input_fecha_hasta.clear()
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

        df["6"] = df["6"].replace(to_replace="TODOS", value="")
        df.loc[df["6"] != "27", "fuente"] = df["6"]
        df["fecha_desde"] = df.iloc[15, 2].split(" ")[2]
        df["fecha_hasta"] = df.iloc[15, 2].split(" ")[6]
        df["fecha_desde"] = pd.to_datetime(df["fecha_desde"], format="%d/%m/%Y")
        df["fecha_hasta"] = pd.to_datetime(df["fecha_hasta"], format="%d/%m/%Y")
        df["mes_hasta"] = (
            df["fecha_hasta"].dt.month.astype(str).str.zfill(2)
            + "/"
            + df["fecha_hasta"].dt.year.astype(str)
        )
        df = df.replace(to_replace="", value=None)
        df = df.tail(-13)
        df["fuente"] = df["fuente"].ffill()
        df = df.dropna(subset=["2"])
        df = df.dropna(subset=["23"])
        df = df.rename(
            columns={
                "2": "nro_entrada",
                "4": "nro_origen",
                "7": "fecha_aprobado",
                "9": "org_fin",
                "10": "importe",
                "15": "saldo",
                "17": "nro_expte",
                "18": "cta_cte",
                "21": "glosa",
                "23": "cuit",
                "24": "beneficiario",
            }
        )

        to_numeric = ["importe", "saldo"]
        df[to_numeric] = df[to_numeric].apply(pd.to_numeric).astype(np.float64)

        df["fecha_aprobado"] = pd.to_datetime(
            df["fecha_aprobado"], format="%Y-%m-%d %H:%M:%S"
        )
        df["mes_aprobado"] = df["fecha_aprobado"].dt.strftime("%m/%Y")

        df["fecha"] = np.where(
            df["fecha_aprobado"] > df["fecha_hasta"],
            df["fecha_hasta"],
            df["fecha_aprobado"],
        )

        # CYO aprobados en enero correspodientes al ejercicio anterior
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")
        condition = (df["mes_aprobado"].str[0:2] == "01") & (
            df["nro_entrada"].astype(int) > 1500
        )
        df.loc[condition, "fecha"] = (
            pd.to_numeric(df["mes_hasta"].loc[condition].str[-4:])
        ).astype(str) + "-12-31"

        df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")

        # df["ejercicio"] = df["fecha"].dt.year
        df["ejercicio"] = df["fecha_hasta"].dt.strftime("%Y")
        df["mes"] = df["fecha"].dt.strftime("%m/%Y")

        df["nro_comprobante"] = (
            df["nro_entrada"].str.zfill(5) + "/" + df["mes"].str[-2:]
        )

        df["fecha"] = df["fecha"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )
        df["fecha_aprobado"] = df["fecha_aprobado"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )
        df["fecha_desde"] = df["fecha_desde"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )
        df["fecha_hasta"] = df["fecha_hasta"].apply(
            lambda x: x.to_pydatetime() if pd.notnull(x) else None
        )

        df = df.loc[
            :,
            [
                "ejercicio",
                "mes",
                "fecha",
                "mes_hasta",
                "fuente",
                "cta_cte",
                "nro_comprobante",
                "importe",
                "saldo",
                "cuit",
                "beneficiario",
                "glosa",
                "nro_expte",
                "nro_entrada",
                "nro_origen",
                "fecha_aprobado",
                "fecha_desde",
                "fecha_hasta",
                "org_fin",
            ],
        ]

        self.clean_df = df
        return self.clean_df

    # --------------------------------------------------
    def cta_cte_unifier(self, token: Optional[str] = None):
        self.clean_df = cta_cte_unifier(
            original_df=self.clean_df,
            cta_cte_nexo="siif_contabilidad_cta_cte",
            token=token,
        )


# ──────────────────────────────────────────────
# Inicialización de Typer
# ──────────────────────────────────────────────

app = typer.Typer(help="Read, process and write SIIF's rdeu012", add_completion=False)


# --------------------------------------------------
@app.command()
def main(
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Username for SIIF access"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Password for SIIF access"
    ),
    meses: List[str] = typer.Option(
        ["01" + str(dt.datetime.now().year)],
        "--meses",
        "-m",
        help="Lista de mes y año en formato mmyyyy (ej: 072025)",
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
        help="SIIF' rdeu012.xls report's full file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Lee, procesa y escribe el reporte rdeu012 del SIIF.
    """

    # 1. Validación de lógica de negocio (Exclusión mutua)
    if file and download:
        typer.secho(
            "❌ Error: No puedes usar --file y --download al mismo tiempo.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    # Validación de meses
    meses_ok = []
    for mesyano in meses:
        mes = int(mesyano[0:2])
        ejercicio = mesyano[-4:]
        if ejercicio not in list(
            range(2010, dt.datetime.now().year + 1)
        ) and mes not in list(range(1, 13)):
            typer.secho(
                f"❌ Error: Mes {mesyano} fuera del rango permitido (01/2010 - 12/{dt.datetime.now().year}).",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)
        else:
            meses_ok.append(mesyano)

    meses = meses_ok

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
    asyncio.run(run_automation(username, password, meses, download, headless, file))


# --------------------------------------------------
async def run_automation(
    username: str,
    password: str,
    meses: List[str],
    download: bool,
    headless: bool,
    file: Optional[Path],
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
                typer.echo("⏳ Descargando reporte rdeu012...")

                # 1. Login
                connect_siif = await login(
                    username, password, playwright=p, headless=headless
                )

                # 2. Navegación inicial
                siif = Rdeu012(siif=connect_siif)
                await siif.go_to_reports()
                await siif.go_to_specific_report()

                # 3. Bucle de meses
                for mes in meses:
                    typer.echo(f"⏳ Procesando: {mes}...")
                    # Descarga y guardado físico
                    await siif.download_report(mes=str(mes))
                    await siif.save_xls_file(
                        save_path=save_path,
                        file_name=mes[-4:] + mes[0:2] + "-rdeu012.xls",
                    )
                    # Feedback visual de éxito
                    typer.secho(
                        f"✅ Período {mes} descargado con éxito.",
                        fg=typer.colors.GREEN,
                    )

                    # 4. Lectura y Procesamiento
                    await siif.read_xls_file()
                    # print(siif.df)
                    await siif.process_dataframe()
                    # Feedback visual de éxito
                    typer.secho(
                        f"✅ Período {mes} procesado con éxito.",
                        fg=typer.colors.GREEN,
                    )
                    print_rich_table(siif.clean_df, title=f"Resultados Período {mes}")

                # 5. Logout
                await siif.logout()

            else:
                siif = Rdeu012()
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

    # poetry run python -m src.automation.siif.rdeu012 -d
    # poetry run python -m src.automation.siif.rdeu012 -f "D:\Proyectos IT\invico_streamlit\src\automation\siif\202601-rdeu012.xls"
