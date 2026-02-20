FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the frontend app
COPY app.py .
RUN useradd -m -r -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
