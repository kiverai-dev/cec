import streamlit as st
from datetime import datetime
from app.database.session import SessionLocal
from app.database import crud
from app.auth.roles import get_current_user


def show_history_page():
    st.title("История загрузок")
    user = get_current_user()

    db = SessionLocal()
    try:
        if user.role == "admin":
            st.info("Режим администратора: отображаются все загрузки")
            uploads = crud.get_all_uploads(db, limit=100)
        else:
            uploads = crud.get_uploads_by_user(db, user.id, limit=100)

        status_filter = st.selectbox(
            "Фильтр по статусу",
            options=["Все", "pending", "processing", "done", "error"],
            index=0
        )

        if status_filter != "Все":
            uploads = [u for u in uploads if u.status == status_filter]

        if not uploads:
            st.info("Загрузки не найдены")
            return

        st.markdown(f"**Найдено:** {len(uploads)} записей")
        st.markdown("---")

        for upload in uploads:
            status_colors = {
                "pending": "🟡",
                "processing": "🔵",
                "done": "🟢",
                "error": "🔴"
            }
            status_names = {
                "pending": "Ожидает",
                "processing": "В обработке",
                "done": "Готово",
                "error": "Ошибка"
            }

            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])

                with col1:
                    st.markdown(f"**{upload.filename}**")
                    if user.role == "admin":
                        st.caption(f"Пользователь: {upload.user.username}")

                with col2:
                    st.markdown(f"{status_colors.get(upload.status, '')} {status_names.get(upload.status, upload.status)}")
                    st.caption(upload.created_at.strftime("%d.%m.%Y %H:%M"))

                with col3:
                    if upload.status == "done":
                        if st.button("Открыть", key=f"open_{upload.id}"):
                            st.query_params["page"] = "analysis"
                            st.query_params["id"] = str(upload.id)
                            st.rerun()
                    elif upload.status == "error":
                        with st.expander("Ошибка"):
                            st.error(upload.error_message or "Неизвестная ошибка")

                st.markdown("---")

    finally:
        db.close()
