import streamlit as st
from app.database.session import SessionLocal
from app.database import crud
from app.auth.roles import get_current_user


def show_dashboard():
    user = get_current_user()
    st.title(f"Добро пожаловать, {user.username}!")
    st.markdown("---")

    db = SessionLocal()
    try:
        total_uploads = len(crud.get_all_uploads(db, limit=1000))
        user_uploads = len(crud.get_uploads_by_user(db, user.id, limit=1000))
        total_users = len(crud.get_all_users(db))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ваших загрузок", user_uploads)
        with col2:
            st.metric("Всего загрузок", total_uploads)
        with col3:
            st.metric("Пользователей", total_users)

        st.markdown("---")

        st.subheader("Быстрые действия")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Загрузить документ", use_container_width=True):
                st.query_params["page"] = "upload"
                st.rerun()
        with col2:
            if st.button("История загрузок", use_container_width=True):
                st.query_params["page"] = "history"
                st.rerun()

        st.markdown("---")

        st.subheader("Последние загрузки")
        recent_uploads = crud.get_uploads_by_user(db, user.id, limit=5)
        if recent_uploads:
            for upload in recent_uploads:
                status_emoji = {"pending": "⏳", "processing": "🔄", "done": "✅", "error": "❌"}
                with st.container():
                    st.markdown(f"**{upload.filename}** {status_emoji.get(upload.status, '')}")
                    st.caption(f"{upload.created_at.strftime('%d.%m.%Y %H:%M')} — {upload.status}")
                    if upload.status == "done":
                        if st.button("Просмотреть", key=f"view_{upload.id}"):
                            st.query_params["page"] = "analysis"
                            st.query_params["id"] = str(upload.id)
                            st.rerun()
                    st.markdown("---")
        else:
            st.info("У вас пока нет загруженных файлов")

    finally:
        db.close()
