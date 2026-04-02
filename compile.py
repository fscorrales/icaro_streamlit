import os
import shutil

import PyInstaller.__main__

# --- CONFIGURACIÓN ---
APP_NAME = "INVICO Dashboard"
ENTRY_POINT = "run.py"  # El script lanzador
STREAMLIT_APP = "app.py"  # Tu app principal
SRC_DIR = "src"  # Carpeta con tu lógica y .env
ICON_FILE = "logo_invico.ico"  # El archivo de icono de la app


def build():
    # 1. Limpiar carpetas de compilaciones previas
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Borrando {folder}...")

    # 2. Definir los argumentos de PyInstaller
    args = [
        ENTRY_POINT,
        f"--name={APP_NAME}",
        "--onefile",
        # "--windowed",  # Para que no se abra una consola negra detrás (opcional)
        "--additional-hooks-dir=.",
        # Recolección de librerías "rebeldes"
        "--collect-all=streamlit",
        "--collect-all=httpx",
        "--collect-all=pydantic_settings",
        "--collect-all=playwright",
        "--copy-metadata=streamlit",
        "--copy-metadata=playwright",
        # Inclusión de archivos y carpetas
        f"--add-data={STREAMLIT_APP}{os.pathsep}.",
        f"--add-data={SRC_DIR}{os.pathsep}{SRC_DIR}",
        f"--icon={ICON_FILE}",
    ]

    # 3. Ejecutar PyInstaller
    print(f"Iniciando compilación de {APP_NAME}...")
    PyInstaller.__main__.run(args)
    print("\n¡Compilación finalizada! Revisa la carpeta /dist")


if __name__ == "__main__":
    build()

# poetry run python compile.py
