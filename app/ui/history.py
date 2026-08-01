import os
import shutil
import streamlit as st
from app.database.session import SessionLocal
from app.database import crud
from app.auth.roles import get_current_user


def _delete_upload_files(file_path: str):
    """Удаляет загруженный файл и распакованную директорию архива (если есть)."""
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
        extract_dir = file_path + "_extracted"
        if os.path.isdir(extract_dir):
            shutil.rmtree(extract_dir)
    except OSError:
        pass


def _can_delete(user, upload) -> bool:
    if user.role == "admin":
        return True
    return user.role == "analyst" and upload.user_id == user.id


def show_history_page():
    st.title("История загрузок")
    user = get_current_user()

    deleted_name = st.session_state.get("deleted_filename")
    if deleted_name:
        del st.session_state["deleted_filename"]
        st.success(f"«{deleted_name}» удалён")

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
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1.5])

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

                with col4:
                    if _can_delete(user, upload):
                        if st.button("Удалить", key=f"del_{upload.id}"):
                            st.session_state["confirm_delete_id"] = upload.id
                            st.rerun()

                if _can_delete(user, upload) and st.session_state.get("confirm_delete_id") == upload.id:
                    st.warning(f"Удалить «{upload.filename}»? Запись, результат анализа и файлы будут удалены безвозвратно.")
                    confirm_col, cancel_col, _ = st.columns([1, 1, 4])
                    with confirm_col:
                        if st.button("Да, удалить", key=f"confirm_del_{upload.id}", type="primary"):
                            filename = upload.filename
                            file_path = upload.file_path
                            _delete_upload_files(file_path)
                            crud.delete_upload(db, upload.id)
                            del st.session_state["confirm_delete_id"]
                            st.session_state["deleted_filename"] = filename
                            st.rerun()
                    with cancel_col:
                        if st.button("Отмена", key=f"cancel_del_{upload.id}"):
                            del st.session_state["confirm_delete_id"]
                            st.rerun()

                st.markdown("---")

    finally:
        db.close()
