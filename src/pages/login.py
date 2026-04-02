import streamlit as st

import src.utils.exceptions as ex
from src.services.auth_service import get_current_user, login, register


# --------------------------------------------------
def render_login() -> None:
    """Renderiza el formulario de login y registro de forma compacta."""
    # Usamos columnas para centrar el formulario y que no ocupe todo el ancho
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.title("Acceso al Sistema")

        tab_login, tab_register = st.tabs(["🔒 Iniciar Sesión", "📝 Registrarse"])

        with tab_login:
            st.info("Ingrese sus credenciales para continuar.")
            with st.form("login_form"):
                username = st.text_input("Usuario", key="login_username")
                password = st.text_input(
                    "Contraseña", type="password", key="login_password"
                )
                submitted = st.form_submit_button("Ingresar", use_container_width=True)

                if submitted:
                    with st.spinner("Autenticando en el Sistema..."):
                        try:
                            token = login(username, password)
                            st.session_state["token"] = token

                            user_data = get_current_user(token)
                            st.session_state["user"] = {
                                "role": user_data.role.value,
                                "username": user_data.username,
                                "id": user_data.id,
                            }
                            st.rerun()

                        except (
                            ex.AppBaseException
                        ) as e:  # Captura cualquier error definido por ti
                            st.error(f"Error: {e}")
                        except Exception as e:
                            st.error(f"Ocurrió un error inesperado. {e}")

        with tab_register:
            st.info("Complete los datos para crear una nueva cuenta.")

            # Mensaje de recomendación visible
            st.markdown("""
                💡 **Recomendación:** Para mayor facilidad, te sugerimos utilizar el **mismo usuario** que 
                        utilizas en los otros sistemas de **INVICO** (ej. `JPEREZ o jperez`). Además, 
                        la **contraseña** debe tener **al menos 4 caracteres**.
            """)
            with st.form("register_form"):
                # Usamos placeholder para dar un ejemplo visual y help para la instrucción
                new_user = st.text_input(
                    "Usuario deseado",
                    key="reg_username",
                    placeholder="Ej: jperez o JPEREZ",
                    help="Se recomienda usar tu usuario estándar de INVICO para no olvidarlo.",
                )
                new_pass = st.text_input(
                    "Contraseña",
                    type="password",
                    key="reg_password",
                    help="Mínimo 4 caracteres.",
                )
                conf_pass = st.text_input(
                    "Confirmar Contraseña", type="password", key="reg_confirm"
                )
                submitted_reg = st.form_submit_button(
                    "Crear Cuenta", use_container_width=True
                )

                if submitted_reg:
                    # 1. Validación de campos vacíos
                    if not new_user or not new_pass:
                        st.error("Todos los campos son obligatorios.")

                    # 2. NUEVA VALIDACIÓN: Longitud mínima
                    elif len(new_pass) < 4:
                        st.error("⚠️ La contraseña debe tener al menos 4 caracteres.")

                    # 3. Validación de coincidencia
                    elif new_pass != conf_pass:
                        st.error("Las contraseñas no coinciden.")

                    # 4. Proceso de registro
                    else:
                        with st.spinner("Registrando usuario..."):
                            try:
                                register(new_user, new_pass)
                                st.success(
                                    "✅ Registro solicitado exitosamente. "
                                    "Ahora puede intentar iniciar sesión."
                                )
                            except ex.AppBaseException as e:
                                st.error(f"Error: {e}")
                            except Exception as e:
                                st.error(f"Error inesperado: {e}")
