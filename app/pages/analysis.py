import streamlit as st
from app.database.session import SessionLocal
from app.database import crud
from fpdf import FPDF
import io


def generate_pdf_report(filename: str, date_str: str, result_text: str, json_data: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    
    pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", uni=True)
    
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Результат анализа", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 8, f"Файл: {filename}", ln=True)
    pdf.cell(0, 8, f"Дата: {date_str}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Аналитика", ln=True)
    pdf.ln(3)
    
    pdf.set_font("DejaVu", "", 10)
    if result_text:
        clean_text = result_text.replace("**", "").replace("*", "")
        pdf.multi_cell(0, 6, clean_text)
    else:
        pdf.cell(0, 8, "Нет данных", ln=True)
    
    pdf.ln(10)
    
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Извлечённые данные (JSON)", ln=True)
    pdf.ln(3)
    
    pdf.set_font("DejaVu", "", 9)
    if json_data:
        pdf.multi_cell(0, 5, json_data)
    else:
        pdf.cell(0, 8, "Нет данных", ln=True)
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def show_analysis_page():
    st.title("Результат анализа")

    upload_id = st.query_params.get("id")
    if not upload_id:
        st.error("Не указан ID загрузки")
        if st.button("Вернуться к истории"):
            st.query_params["page"] = "history"
            st.rerun()
        return

    db = SessionLocal()
    try:
        upload = crud.get_upload_by_id(db, int(upload_id))
        if not upload:
            st.error("Загрузка не найдена")
            return

        st.markdown(f"**Файл:** {upload.filename}")
        st.caption(f"Дата: {upload.created_at.strftime('%d.%m.%Y %H:%M')}")

        if upload.status != "done":
            st.warning("Анализ ещё не завершён или завершился с ошибкой")
            return

        analysis = crud.get_analysis_by_upload(db, upload.id)
        if not analysis:
            st.error("Результат анализа не найден")
            return

        tab1, tab2 = st.tabs(["Аналитика", "Извлечённые данные"])

        with tab1:
            st.markdown(analysis.result_text or "Нет данных")

        with tab2:
            if analysis.extracted_json:
                st.json(analysis.extracted_json)
            else:
                st.info("JSON данные не извлечены")

        st.markdown("---")
        
        st.subheader("Скачать результат")
        
        pdf_data = generate_pdf_report(
            filename=upload.filename,
            date_str=upload.created_at.strftime('%d.%m.%Y %H:%M'),
            result_text=analysis.result_text or "",
            json_data=analysis.extracted_json or ""
        )
        
        st.download_button(
            label="Скачать отчёт (.pdf)",
            data=pdf_data,
            file_name=f"report_{upload.id}.pdf",
            mime="application/pdf"
        )

        st.markdown("---")
        if st.button("Вернуться к истории"):
            st.query_params["page"] = "history"
            st.rerun()

    finally:
        db.close()
