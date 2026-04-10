#!/usr/bin/env python3
"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: Working With Files in Python
Source: https://realpython.com/working-with-files-in-python/#:~:text=To%20get%20a%20list%20of,scandir()%20in%20Python%203.
"""

__all__ = [
    "get_df_from_sql_table",
    "read_xls",
    "read_csv_file",
]


import sqlite3
from io import BytesIO
from pathlib import Path
from typing import Union

import pandas as pd


# --------------------------------------------------
def get_df_from_sql_table(sqlite_path: str, table: str) -> pd.DataFrame:
    with sqlite3.connect(sqlite_path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)


# --------------------------------------------------
def read_xls(PATH: str, header: int = 0) -> pd.DataFrame:
    """ "Read from xls report"""
    df = pd.read_excel(PATH, index_col=None, header=header, na_filter=False, dtype=str)
    if header == 0:
        df.columns = [str(x) for x in range(df.shape[1])]
    return df


# --------------------------------------------------
def read_csv_file(file_path: Union[Path, str, BytesIO]) -> pd.DataFrame:
    """Read csv file"""
    try:
        nombres_columnas = [str(i) for i in range(100)]
        df = pd.read_csv(
            file_path,
            names=nombres_columnas,  # Forzamos a que acepte hasta 100 columnas
            index_col=None,
            header=None,
            na_filter=False,
            dtype=str,
            encoding="ISO-8859-1",
        )
        df.columns = [str(x) for x in range(df.shape[1])]
        return df
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return pd.DataFrame()
