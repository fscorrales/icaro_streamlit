# 1. El desafío de PyInstaller + Streamlit
# Empaquetar Streamlit con PyInstaller es un poco "mañoso" porque Streamlit no es un script convencional,
# sino un framework que necesita un servidor web corriendo.

# Tip: Muchos desarrolladores usan un pequeño script run_app.py que llama a streamlit.web.cli.main
# para que PyInstaller pueda "ver" el punto de entrada.

# Alternativa moderna: Dale una mirada a Pydentity o Stlite si quieres algo más liviano,
# aunque para usar Pywinauto, el ejecutable clásico de PyInstaller sigue siendo el estándar.

# Ejemplo básico para generar el ejecutable
# poetry run pyinstaller --onefile --additional-hooks-dir=. --collect-all streamlit --copy-metadata streamlit --add-data "app.py;." --add-data "src;src" run.py

# Tip para "Antigravity": Como vas a usar Pywinauto y Playwright, recordá que PyInstaller
# a veces no incluye los binarios de los navegadores automáticamente. Si el ejecutable final
# te da error de "Browser not found", podrías necesitar indicarle a PyInstaller que incluya
# la carpeta donde Playwright descarga los navegadores
# (usualmente %USERPROFILE%\AppData\Local\ms-playwright).

# import os
# import subprocess


# def run_streamlit_app():
#     # Obtiene la  ruta del script de Streamlit
#     script_path = os.path.join(os.path.dirname(__file__), "app.py")

#     # Ejecuta Streamlit con la ruta del script
#     subprocess.run(["streamlit", "run", script_path])

#     # # Ensure the current working directory is the script's directory
#     # script_dir = os.path.dirname(os.path.abspath(__file__))
#     # os.chdir(script_dir)

#     # # Run the Streamlit app using subprocess
#     # subprocess.run(["streamlit", "run", "streamlit_app.py"])


import os
import sys

from streamlit.web import cli as stcli


def get_resource_path(relative_path):
    try:
        # Ruta temporal de PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        # Ruta en modo desarrollo
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def run_streamlit_app():
    # Buscamos app.py dentro de la carpeta temporal del ejecutable
    app_path = get_resource_path("app.py")

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--browser.gatherUsageStats=false",  # <-- Esto desactiva el envío de estadísticas
    ]

    # TRUCO EXTRA: Forzar el modo "headless" en la configuración
    from streamlit import config

    config.set_option("browser.gatherUsageStats", False)

    sys.exit(stcli.main())


if __name__ == "__main__":
    run_streamlit_app()

# poetry run python -m run
# poetry run streamlit run src/app.py
