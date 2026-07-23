from functools import wraps
import streamlit as st


def require_role(*roles: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = st.session_state.get("user")
            if not user:
                st.error("Требуется авторизация")
                st.stop()
            if user.role not in roles:
                st.error("Недостаточно прав")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    return st.session_state.get("user")


def is_admin():
    user = get_current_user()
    return user and user.role == "admin"


def is_analyst():
    user = get_current_user()
    return user and user.role in ["admin", "analyst"]
