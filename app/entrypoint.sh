#!/bin/bash
set -e

cd /app
python -c "from app.database.session import init_db; init_db()"
streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
