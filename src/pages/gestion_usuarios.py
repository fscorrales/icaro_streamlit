"""Página: Gestión de Usuarios (solo admin).

Permite listar usuarios, aprobar pendientes y cambiar roles
mediante las APIs GET /users/, PATCH /users/{id}/approve
y PATCH /users/{id}/role.
"""

import streamlit as st

from src.constants.endpoints import Endpoints
from src.services.api_client import (
    APIConnectionError,
    APIResponseError,
    fetch_dataframe,
    patch_request,
)

ENDPOINT = Endpoints.USERS.value


st.markdown("# Administración de Usuarios")
st.write(
    "Panel de administración para gestionar usuarios del "
    "sistema. Permite aprobar registros pendientes y "
    "modificar roles."
)

# --- Carga de usuarios ---
try:
    with st.spinner("Cargando lista de usuarios..."):
        df = fetch_dataframe(ENDPOINT, params={"limit": None})

    if df.empty:
        st.info("No se encontraron usuarios.")
    else:
        st.write(f"### Usuarios registrados: {len(df)}")
        st.dataframe(df, width="stretch")

        st.divider()

        # --- Aprobar usuario pendiente ---
        st.write("### Aprobar usuario pendiente")
        pending_users = df[
            df["roles"].apply(
                lambda user_roles: isinstance(user_roles, list)
                and "pending" in user_roles
            )
        ]

        if pending_users.empty:
            st.success("No hay usuarios pendientes de aprobación.")
        else:
            user_to_approve = st.selectbox(
                "Seleccionar usuario pendiente",
                options=pending_users["id"].tolist(),
                format_func=lambda uid: pending_users.loc[
                    pending_users["id"] == uid, "username"
                ].iloc[0],
            )

            if st.button("✅ Aprobar usuario"):
                try:
                    patch_request(f"/users/{user_to_approve}/approve")
                    st.success("Usuario aprobado exitosamente.")
                    st.rerun()
                except (APIConnectionError, APIResponseError) as e:
                    st.error(f"Error al aprobar: {e}")

        st.divider()

        # --- Cambiar rol ---
        st.write("### Cambiar rol de usuario")
        user_to_change = st.selectbox(
            "Seleccionar usuario",
            options=df["id"].tolist(),
            format_func=lambda uid: df.loc[df["id"] == uid, "username"].iloc[0],
            key="role_change_user",
        )

        current_roles = df.loc[df["id"] == user_to_change, "roles"].iloc[0]
        st.caption(
            "Roles actuales: "
            + (", ".join(current_roles) if isinstance(current_roles, list) else "-")
        )

        new_roles = st.multiselect(
            "Nuevos roles",
            options=["user", "admin", "eecc", "icaro", "pending"],
            key="role_change_roles",
        )

        if st.button("🔄 Cambiar rol"):
            if not new_roles:
                st.warning("Debe seleccionar al menos un rol.")
            else:
                try:
                    patch_request(
                        f"/users/{user_to_change}/role",
                        json_body={"roles": new_roles},
                    )
                    st.success("Roles actualizados exitosamente.")
                    st.rerun()
                except (APIConnectionError, APIResponseError) as e:
                    st.error(f"Error al cambiar roles: {e}")

except APIConnectionError as e:
    st.error(f"⚠️ Error de conexión: {e}")
except APIResponseError as e:
    st.error(f"⚠️ Error de API: {e}")
