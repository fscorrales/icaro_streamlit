import tomllib  # Disponible en Python 3.11+
from pathlib import Path

import typer


# --------------------------------------------------
def get_version():
    # Buscamos el pyproject en la raíz (ajusta la ruta según tu estructura)
    path = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    with open(path, "rb") as f:
        data = tomllib.load(f)
        return data["tool"]["poetry"]["version"]


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
