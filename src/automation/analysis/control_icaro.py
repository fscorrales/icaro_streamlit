from typing import List

from playwright.async_api import async_playwright

from src.automation.siif import (
    GtoRpa03g,
    Rcg01Uejp,
    Rf602,
    Rf610,
    Rfondo07tp,
    login,
    logout,
)
from src.constants.endpoints import Endpoints
from src.services import post_request


# --------------------------------------------------
async def sync_control_icaro_from_siif(
    siif_username: str, siif_password: str, ejercicios: List[int]
) -> List[str]:

    async with async_playwright() as p:
        connect_siif = await login(
            username=siif_username,
            password=siif_password,
            playwright=p,
            headless=False,
        )

        results = []
        # 🔹 RF602
        rf602 = Rf602(siif=connect_siif)
        await rf602.go_to_reports()
        for ej in ejercicios:
            df_clean = await rf602.download_and_process_report(ejercicio=ej)
            if df_clean is not None and not df_clean.empty:
                # Send to backend
                json_data = df_clean.to_dict(orient="records")
                response = post_request(Endpoints.SIIF_RF602.value, json_body=json_data)
                results.append(f"RF602 Ejercicio {ej}: {response}")

        # 🔹 RF610
        rf610 = Rf610(siif=connect_siif)
        for ej in ejercicios:
            df_clean = await rf610.download_and_process_report(ejercicio=ej)
            if df_clean is not None and not df_clean.empty:
                # Send to backend
                json_data = df_clean.to_dict(orient="records")
                response = post_request(Endpoints.SIIF_RF610.value, json_body=json_data)
                results.append(f"RF610 Ejercicio {ej}: {response}")

        # 🔹 Rcg01Uejp
        rcg01uejp = Rcg01Uejp(siif=connect_siif)
        for ej in ejercicios:
            df_clean = await rcg01uejp.download_and_process_report(ejercicio=ej)
            if df_clean is not None and not df_clean.empty:
                # Send to backend
                json_data = df_clean.to_dict(orient="records")
                response = post_request(
                    Endpoints.SIIF_RCG01_UEJP.value, json_body=json_data
                )
                results.append(f"Rcg01Uejp Ejercicio {ej}: {response}")

        # 🔹 Rfondo07tp
        rfondo07tp = Rfondo07tp(siif=connect_siif)
        for ej in ejercicios:
            df_clean = await rfondo07tp.download_and_process_report(ejercicio=ej)
            if df_clean is not None and not df_clean.empty:
                # Send to backend
                json_data = df_clean.to_dict(orient="records")
                response = post_request(
                    Endpoints.SIIF_RFONDO07TP.value, json_body=json_data
                )
                results.append(f"Rfondo07tp Ejercicio {ej}: {response}")

        # 🔹 GtoRpa03g
        gto_rpa03g = GtoRpa03g(siif=connect_siif)
        # GRUPOS = get_grupos_partidas_siif_list(
        #     update_trigger=st.session_state.grupos_partidas_siif_uploader_iteration
        # )
        GRUPOS = ["1", "2", "3", "4"]
        for ej in ejercicios:
            for grupo in GRUPOS:
                df_clean = await gto_rpa03g.download_and_process_report(
                    ejercicio=ej, grupo_partida=grupo
                )
                if df_clean is not None and not df_clean.empty:
                    # Send to backend
                    json_data = df_clean.to_dict(orient="records")
                    response = post_request(
                        Endpoints.SIIF_GTO_RPA03G.value, json_body=json_data
                    )
                    results.append(f"GtoRpa03g Ejercicio {ej}: {response}")

        await logout(connect=connect_siif)

        print("✅ SIIF Finalizado")
        return results
