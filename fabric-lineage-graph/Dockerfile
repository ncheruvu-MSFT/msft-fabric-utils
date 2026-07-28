# Streamlit + harvesters + stub UDF, all in one image so docker-compose can
# fork two processes from the same layer cache.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT_STREAMLIT=8501 \
    PORT_UDF=8000

WORKDIR /app

# System deps: gcc for any pandas/sqlglot wheels that need compile; curl for healthcheck.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# Install the offline runtime deps. Skip the live cloud-harvester drivers
# (pyodbc / oracledb) — they need extra system packages and are not needed
# for local container testing.
RUN sed -E '/^(pyodbc|oracledb|psycopg)/d' requirements.txt > requirements.local.txt \
 && pip install -r requirements.local.txt \
 && pip install fastapi==0.115.* uvicorn[standard]==0.32.*

COPY . .

EXPOSE 8000 8501

# Default: run Streamlit. docker-compose overrides for the UDF service.
CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
