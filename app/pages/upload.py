import os
import json
from typing import Optional
import streamlit as st
from app.database.session import SessionLocal
from app.database import crud
from app.auth.roles import require_role, get_current_user
from app.utils.validators import validate_uploaded_file, get_file_extension
from app.utils.archive import extract_archive, get_archive_filenames, is_archive
from app.core.pdf_extractor import extract_text_from_pdf
from app.core.analyzer import extract_json_from_text, analyze_extracted_data


def process_single_pdf(pdf_path: str) -> tuple[dict, Optional[str]]:
    pdf_text = extract_text_from_pdf(pdf_path)
    if not pdf_text.strip():
        return {}, "Не удалось извлечь текст из PDF"
    
    json_result, error = extract_json_from_text(pdf_text)
    if error and not json_result:
        return {}, error
    
    try:
        parsed = json.loads(json_result) if json_result else {}
        return parsed, None
    except json.JSONDecodeError:
        return {"raw_text": json_result}, "Невалидный JSON"


def process_archive(archive_path: str, progress_callback=None) -> tuple[list, list]:
    extract_dir = archive_path.replace(".zip", "_extracted").replace(".rar", "_extracted")
    os.makedirs(extract_dir, exist_ok=True)
    
    success, extracted_files, error = extract_archive(archive_path, extract_dir)
    if not success:
        return [], [error]
    
    pdf_files = [f for f in extracted_files if f.endswith(".pdf")]
    if not pdf_files:
        return [], ["В архиве не найдено PDF файлов"]
    
    all_results = []
    errors = []
    
    for i, pdf_file in enumerate(pdf_files):
        if progress_callback:
            progress_callback(i + 1, len(pdf_files), os.path.basename(pdf_file))
        
        result, error = process_single_pdf(pdf_file)
        if error:
            errors.append(f"{os.path.basename(pdf_file)}: {error}")
        if result:
            result["_source_file"] = os.path.basename(pdf_file)
            all_results.append(result)
    
    return all_results, errors


@require_role("admin", "analyst")
def show_upload_page():
    st.title("Загрузка документа")
    user = get_current_user()

    if "last_upload_id" in st.session_state:
        if st.button("Перейти к результату", type="primary"):
            st.query_params["page"] = "analysis"
            st.query_params["id"] = str(st.session_state["last_upload_id"])
            del st.session_state["last_upload_id"]
            st.rerun()
        st.markdown("---")

    st.markdown("""
    Загрузите PDF файл или архив (ZIP/RAR) с медицинскими документами для анализа.
    """)

    uploaded_file = st.file_uploader(
        "Выберите файл",
        type=["pdf", "zip", "rar"],
        help="Поддерживаемые форматы: PDF, ZIP, RAR. Максимальный размер: 50 MB"
    )

    if uploaded_file is not None:
        is_valid, error_msg = validate_uploaded_file(uploaded_file)
        if not is_valid:
            st.error(error_msg)
            return

        st.success(f"Файл: {uploaded_file.name}")

        if is_archive(uploaded_file.name):
            st.info("Обнаружен архив. Каждый PDF будет обработан отдельно.")

        if st.button("Загрузить и проанализировать", type="primary"):
            upload_dir = f"data/uploads/user_{user.id}"
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            db = SessionLocal()
            try:
                upload_record = crud.create_upload(db, user.id, uploaded_file.name, file_path)
                crud.update_upload_status(db, upload_record.id, "processing")

                try:
                    ext = get_file_extension(uploaded_file.name)

                    if ext == ".pdf":
                        with st.spinner("Извлечение данных из PDF..."):
                            pdf_text = extract_text_from_pdf(file_path)
                            if not pdf_text.strip():
                                raise ValueError("Не удалось извлечь текст из PDF")

                            json_result, json_error = extract_json_from_text(pdf_text)
                            analysis_result = None
                            analysis_error = None
                            
                            if json_result:
                                analysis_result, analysis_error = analyze_extracted_data(json_result)
                                if json_error:
                                    st.warning(json_error)

                        if not json_result:
                            crud.update_upload_status(db, upload_record.id, "error", json_error or "Не удалось извлечь данные")
                            st.error(f"Не удалось извлечь данные из PDF: {json_error}")
                        else:
                            crud.create_analysis(db, upload_record.id, json_result, analysis_result or "")
                            crud.update_upload_status(db, upload_record.id, "done")
                            st.session_state["last_upload_id"] = upload_record.id
                            if analysis_error:
                                st.warning(analysis_error)
                            st.success("Анализ завершён! Нажмите 'Перейти к результату' выше.")
                            st.rerun()

                    elif ext in [".zip", ".rar"]:
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        def update_progress(current, total, filename):
                            progress_bar.progress(current / total)
                            status_text.text(f"Обработка: {filename} ({current}/{total})")

                        with st.spinner("Обработка архива..."):
                            results, errors = process_archive(file_path, update_progress)

                        progress_bar.progress(1.0)
                        
                        if errors:
                            for err in errors:
                                st.warning(err)

                        if not results:
                            crud.update_upload_status(db, upload_record.id, "error", "Не удалось обработать файлы")
                            st.error("Не удалось извлечь данные из архива")
                        else:
                            combined_json = json.dumps(results, ensure_ascii=False, indent=2)
                            
                            status_text.text("Генерация аналитики...")
                            analysis_result = None
                            analysis_error = None
                            
                            try:
                                analysis_result, analysis_error = analyze_extracted_data(combined_json)
                            except Exception as e:
                                analysis_error = f"Ошибка при генерации аналитики: {str(e)}"
                                st.warning(f"Не удалось сгенерировать аналитику, но JSON данные сохранены: {str(e)}")

                            crud.create_analysis(db, upload_record.id, combined_json, analysis_result or "")
                            crud.update_upload_status(db, upload_record.id, "done")
                            st.session_state["last_upload_id"] = upload_record.id
                            if analysis_error:
                                st.warning(analysis_error)
                            if analysis_result:
                                st.success(f"Анализ завершён! Обработано файлов: {len(results)}. Нажмите 'Перейти к результату' выше.")
                            else:
                                st.info(f"Данные извлечены из {len(results)} файлов. Аналитика недоступна. Нажмите 'Перейти к результату' выше.")
                            st.rerun()

                except Exception as e:
                    crud.update_upload_status(db, upload_record.id, "error", str(e))
                    st.error(f"Ошибка при обработке файла: {str(e)}")

            finally:
                db.close()
