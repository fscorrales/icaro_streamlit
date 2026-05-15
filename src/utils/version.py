import sys
import tomllib  # Disponible en Python 3.11+
from pathlib import Path

import typer


# --------------------------------------------------
def get_version():
    # Si la app está empaquetada, PyInstaller define _MEIPASS
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent.parent.parent

    path = base_path / "pyproject.toml"

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
            return data["tool"]["poetry"]["version"]
    except FileNotFoundError:
        return "0.0.0-desconocida"


# except:
#     return "0.10.0"  # Valor por defecto si falla

app = typer.Typer(help="Read, process and write SIIF's rf602", add_completion=False)


# --------------------------------------------------
@app.command()
def main():
    typer.echo(get_version())


# --------------------------------------------------
if __name__ == "__main__":
    app()

# poetry run python -m src.utils.version
