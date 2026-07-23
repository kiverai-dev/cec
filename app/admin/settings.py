import streamlit as st
from app.database.session import SessionLocal
from app.database import crud
from app.auth.roles import require_role
from app.core.llm_client import get_llm_client
from app.core.analyzer import (
    DEFAULT_PROMPT_EXTRACT, DEFAULT_PROMPT_ANALYZE,
    DEFAULT_SYSTEM_EXTRACT, DEFAULT_SYSTEM_ANALYZE
)
from app.config import DEFAULT_SETTINGS


@require_role("admin")
def show_admin_settings():
    st.title("Настройки")

    tab1, tab2 = st.tabs(["API", "Промпты"])

    with tab1:
        show_api_settings()

    with tab2:
        show_prompt_settings()


def show_api_settings():
    st.header("Настройки LLM API")

    db = SessionLocal()
    try:
        current_settings = crud.get_all_settings(db)

        api_url = current_settings.get("api_url", DEFAULT_SETTINGS["api_url"])
        model_name = current_settings.get("model_name", DEFAULT_SETTINGS["model_name"])
        api_key = current_settings.get("api_key", "")
        temperature = float(current_settings.get("temperature", DEFAULT_SETTINGS["temperature"]))
        max_tokens = int(current_settings.get("max_tokens", DEFAULT_SETTINGS["max_tokens"]))

        st.markdown("""
        Настройте подключение к API вашей LLM модели. Поддерживаются:
        - **OpenAI API** (gpt-4, gpt-3.5-turbo и др.)
        - **Локальные серверы** (llama.cpp, ollama, vLLM)
        - **Другие OpenAI-совместимые API** (Anthropic через прокси, Azure OpenAI и т.д.)
        """)

        with st.form("settings_form"):
            st.subheader("Параметры подключения")

            new_url = st.text_input(
                "API URL", 
                value=api_url,
                help="Например: https://api.openai.com или http://localhost:8080"
            )
            
            new_model = st.text_input(
                "Имя модели", 
                value=model_name,
                help="Например: gpt-4, gpt-3.5-turbo, local-model"
            )
            
            new_api_key = st.text_input(
                "API ключ (опционально)", 
                value=api_key,
                type="password",
                help="Оставьте пустым для локальных серверов без авторизации"
            )

            col1, col2 = st.columns(2)
            with col1:
                new_temp = st.slider("Температура", min_value=0.0, max_value=2.0, value=temperature, step=0.1)
            with col2:
                new_tokens = st.number_input("Max токенов", min_value=100, max_value=8192, value=max_tokens, step=100)

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Сохранить настройки", type="primary")
            with col2:
                test_btn = st.form_submit_button("Проверить соединение")

            if submitted:
                crud.set_setting(db, "api_url", new_url)
                crud.set_setting(db, "model_name", new_model)
                if new_api_key:
                    crud.set_setting(db, "api_key", new_api_key)
                crud.set_setting(db, "temperature", str(new_temp))
                crud.set_setting(db, "max_tokens", str(new_tokens))
                st.success("Настройки сохранены")

            if test_btn:
                with st.spinner("Проверка соединения..."):
                    client = get_llm_client()
                    success, message = client.test_connection()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        st.markdown("---")
        
        with st.expander("Примеры конфигурации"):
            st.markdown("""
            **OpenAI API:**
            - URL: `https://api.openai.com`
            - Модель: `gpt-4` или `gpt-3.5-turbo`
            - API ключ: `sk-...`
            
            **Локальный llama.cpp:**
            - URL: `http://localhost:8080`
            - Модель: `local-model`
            - API ключ: пусто
            
            **Ollama:**
            - URL: `http://localhost:11434`
            - Модель: `llama3` или `mistral`
            - API ключ: пусто
            
            **vLLM:**
            - URL: `http://localhost:8000`
            - Модель: имя вашей модели
            - API ключ: опционально
            """)

    finally:
        db.close()


def show_prompt_settings():
    st.header("Настройка промптов")
    
    st.markdown("""
    Настройте промпты для анализа медицинских документов. 
    
    **Переменные для подстановки:**
    - `{pdf_text}` — текст из PDF документа
    - `{json_data}` — извлечённые данные в формате JSON
    """)

    db = SessionLocal()
    try:
        current_settings = crud.get_all_settings(db)

        prompt_extract = current_settings.get("prompt_extract", "")
        prompt_analyze = current_settings.get("prompt_analyze", "")
        system_extract = current_settings.get("system_extract", "")
        system_analyze = current_settings.get("system_analyze", "")

        st.subheader("Извлечение данных (PDF → JSON)")
        
        with st.expander("Системный промпт для извлечения", expanded=False):
            new_system_extract = st.text_area(
                "system_extract",
                value=system_extract if system_extract else DEFAULT_SYSTEM_EXTRACT,
                height=100,
                help="Задаёт роль и контекст для LLM при извлечении данных"
            )

        with st.expander("Пользовательский промпт для извлечения", expanded=True):
            if prompt_extract:
                display_prompt_extract = prompt_extract
            else:
                display_prompt_extract = DEFAULT_PROMPT_EXTRACT
            
            new_prompt_extract = st.text_area(
                "prompt_extract",
                value=display_prompt_extract,
                height=400,
                help="Используйте {pdf_text} для вставки текста документа"
            )

        st.markdown("---")
        st.subheader("Анализ данных (JSON → Отчёт)")
        
        with st.expander("Системный промпт для анализа", expanded=False):
            new_system_analyze = st.text_area(
                "system_analyze",
                value=system_analyze if system_analyze else DEFAULT_SYSTEM_ANALYZE,
                height=100,
                help="Задаёт роль и контекст для LLM при анализе"
            )

        with st.expander("Пользовательский промпт для анализа", expanded=True):
            if prompt_analyze:
                display_prompt_analyze = prompt_analyze
            else:
                display_prompt_analyze = DEFAULT_PROMPT_ANALYZE
            
            new_prompt_analyze = st.text_area(
                "prompt_analyze",
                value=display_prompt_analyze,
                height=400,
                help="Используйте {json_data} для вставки извлечённых данных"
            )

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Сохранить промпты", type="primary"):
                if new_prompt_extract != DEFAULT_PROMPT_EXTRACT:
                    crud.set_setting(db, "prompt_extract", new_prompt_extract)
                if new_prompt_analyze != DEFAULT_PROMPT_ANALYZE:
                    crud.set_setting(db, "prompt_analyze", new_prompt_analyze)
                if new_system_extract != DEFAULT_SYSTEM_EXTRACT:
                    crud.set_setting(db, "system_extract", new_system_extract)
                if new_system_analyze != DEFAULT_SYSTEM_ANALYZE:
                    crud.set_setting(db, "system_analyze", new_system_analyze)
                st.success("Промпты сохранены")
        
        with col2:
            if st.button("Сбросить к default"):
                crud.set_setting(db, "prompt_extract", "")
                crud.set_setting(db, "prompt_analyze", "")
                crud.set_setting(db, "system_extract", "")
                crud.set_setting(db, "system_analyze", "")
                st.success("Промпты сброшены к значениям по умолчанию")
                st.rerun()

    finally:
        db.close()
