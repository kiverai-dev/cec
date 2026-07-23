import streamlit as st
from app.database.session import SessionLocal
from app.database import crud


def show_login_page():
    st.title("Вход в систему")

    with st.form("login_form"):
        username = st.text_input("Имя пользователя", max_chars=50)
        password = st.text_input("Пароль", type="password", max_chars=100)
        submitted = st.form_submit_button("Войти")

        if submitted:
            if not username or not password:
                st.error("Заполните все поля")
                return

            db = SessionLocal()
            try:
                user = crud.authenticate_user(db, username, password)
                if user:
                    if not user.is_active:
                        st.error("Пользователь деактивирован")
                        return
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Неверное имя пользователя или пароль")
            finally:
                db.close()


def show_setup_page():
    st.title("Создание администратора")
    st.info("Это первый запуск системы. Создайте учётную запись администратора.")

    with st.form("setup_form"):
        username = st.text_input("Имя пользователя", max_chars=50)
        password = st.text_input("Пароль", type="password", max_chars=100)
        password_confirm = st.text_input("Подтвердите пароль", type="password", max_chars=100)
        submitted = st.form_submit_button("Создать администратора")

        if submitted:
            if not username or not password:
                st.error("Заполните все поля")
                return
            if len(username) < 3:
                st.error("Имя пользователя должно содержать минимум 3 символа")
                return
            if len(password) < 6:
                st.error("Пароль должен содержать минимум 6 символов")
                return
            if password != password_confirm:
                st.error("Пароли не совпадают")
                return

            db = SessionLocal()
            try:
                if crud.get_user_by_username(db, username):
                    st.error("Пользователь с таким именем уже существует")
                    return
                user = crud.create_user(db, username, password, role="admin")
                st.session_state["user"] = user
                st.success("Администратор создан! Выполняется вход...")
                st.rerun()
            finally:
                db.close()


def show_logout_button():
    if st.button("Выйти"):
        st.session_state.clear()
        st.rerun()
