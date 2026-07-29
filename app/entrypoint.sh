#!/bin/bash
set -e

cd /app
export LOG_LEVEL=${LOG_LEVEL:-INFO}
python -c "from app.database.session import init_db; init_db()"
streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0 --logger.level=${LOG_LEVEL}
