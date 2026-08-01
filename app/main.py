import streamlit as st
from app.config import APP_NAME
from app.database.session import init_db, SessionLocal
from app.database import crud
from app.auth.pages import show_login_page, show_setup_page, show_logout_button
from app.auth.roles import get_current_user, is_admin, is_analyst
from app.ui.dashboard import show_dashboard
from app.ui.upload import show_upload_page
from app.ui.history import show_history_page
from app.ui.analysis import show_analysis_page
from app.admin.users import show_admin_users
from app.admin.settings import show_admin_settings


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


def show_sidebar():
    user = get_current_user()
    if not user:
        return

    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.markdown(f"**{user.username}**")
        role_names = {"admin": "Администратор", "analyst": "Аналитик", "viewer": "Просмотр"}
        st.caption(f"Роль: {role_names.get(user.role, user.role)}")
        st.markdown("---")

        if st.button("Главная", use_container_width=True):
            st.query_params["page"] = "dashboard"
            st.rerun()

        if is_analyst():
            if st.button("Загрузить документ", use_container_width=True):
                st.query_params["page"] = "upload"
                st.rerun()

        if st.button("История", use_container_width=True):
            st.query_params["page"] = "history"
            st.rerun()

        if is_admin():
            st.markdown("---")
            st.markdown("**Администрирование**")
            if st.button("Пользователи", use_container_width=True):
                st.query_params["page"] = "admin_users"
                st.rerun()
            if st.button("Настройки LLM", use_container_width=True):
                st.query_params["page"] = "admin_settings"
                st.rerun()

        st.markdown("---")
        show_logout_button()


def main():
    init_db()

    db = SessionLocal()
    try:
        has_users = crud.users_exist(db)
    finally:
        db.close()

    if not has_users:
        show_setup_page()
        return

    user = get_current_user()
    if not user:
        show_login_page()
        return

    show_sidebar()

    page = st.query_params.get("page", "dashboard")

    if page == "dashboard":
        show_dashboard()
    elif page == "upload":
        show_upload_page()
    elif page == "history":
        show_history_page()
    elif page == "analysis":
        show_analysis_page()
    elif page == "admin_users":
        show_admin_users()
    elif page == "admin_settings":
        show_admin_settings()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
