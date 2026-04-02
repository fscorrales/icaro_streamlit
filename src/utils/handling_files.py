#!/usr/bin/env python3
"""
Author: Fernando Corrales <fscpython@gmail.com>
Purpose: Working With Files in Python
Source: https://realpython.com/working-with-files-in-python/#:~:text=To%20get%20a%20list%20of,scandir()%20in%20Python%203.
"""

__all__ = [
    "get_df_from_sql_table",
    "read_xls",
]


import sqlite3

import pandas as pd


# --------------------------------------------------
def get_df_from_sql_table(sqlite_path: str, table: str) -> pd.DataFrame:
    with sqlite3.connect(sqlite_path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)


# --------------------------------------------------
def read_xls(PATH: str, header: int = None) -> pd.DataFrame:
    """ "Read from xls report"""
    df = pd.read_excel(PATH, index_col=None, header=header, na_filter=False, dtype=str)
    if header is None:
        df.columns = [str(x) for x in range(df.shape[1])]
    return df
