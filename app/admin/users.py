import streamlit as st
from app.database.session import SessionLocal
from app.database import crud
from app.auth.roles import require_role


@require_role("admin")
def show_admin_users():
    st.title("Управление пользователями")

    db = SessionLocal()
    try:
        tab1, tab2 = st.tabs(["Пользователи", "Создать пользователя"])

        with tab1:
            users = crud.get_all_users(db)

            if not users:
                st.info("Пользователи не найдены")
            else:
                for user in users:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                        with col1:
                            st.markdown(f"**{user.username}**")
                            st.caption(f"ID: {user.id}")

                        with col2:
                            role_names = {"admin": "Администратор", "analyst": "Аналитик", "viewer": "Просмотр"}
                            st.markdown(f"Роль: {role_names.get(user.role, user.role)}")
                            status = "✅ Активен" if user.is_active else "❌ Деактивирован"
                            st.caption(status)

                        with col3:
                            new_role = st.selectbox(
                                "Изменить роль",
                                options=["admin", "analyst", "viewer"],
                                index=["admin", "analyst", "viewer"].index(user.role),
                                key=f"role_{user.id}"
                            )
                            if new_role != user.role:
                                if st.button("Сохранить", key=f"save_role_{user.id}"):
                                    crud.update_user(db, user.id, role=new_role)
                                    st.success("Роль обновлена")
                                    st.rerun()

                        with col4:
                            if user.is_active:
                                if st.button("Деактивировать", key=f"deactivate_{user.id}"):
                                    crud.set_user_active(db, user.id, False)
                                    st.success("Пользователь деактивирован")
                                    st.rerun()
                            else:
                                if st.button("Активировать", key=f"activate_{user.id}"):
                                    crud.set_user_active(db, user.id, True)
                                    st.success("Пользователь активирован")
                                    st.rerun()

                        st.markdown("---")

        with tab2:
            st.subheader("Создать нового пользователя")

            with st.form("create_user_form"):
                new_username = st.text_input("Имя пользователя", max_chars=50)
                new_password = st.text_input("Пароль", type="password", max_chars=100)
                new_role = st.selectbox("Роль", options=["analyst", "viewer", "admin"])
                submitted = st.form_submit_button("Создать")

                if submitted:
                    if not new_username or not new_password:
                        st.error("Заполните все поля")
                    elif len(new_username) < 3:
                        st.error("Имя пользователя должно содержать минимум 3 символа")
                    elif len(new_password) < 6:
                        st.error("Пароль должен содержать минимум 6 символов")
                    else:
                        if crud.get_user_by_username(db, new_username):
                            st.error("Пользователь с таким именем уже существует")
                        else:
                            crud.create_user(db, new_username, new_password, new_role)
                            st.success(f"Пользователь '{new_username}' создан")
                            st.rerun()

    finally:
        db.close()
