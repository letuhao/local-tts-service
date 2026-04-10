FROM python:3.12-slim

WORKDIR /app

# Install requirements (static-ffmpeg downloads its own binary during pip install)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import static_ffmpeg; static_ffmpeg.add_paths()"

COPY app/ app/

# Model and voice files are mounted at runtime
VOLUME ["/app/models", "/app/voices"]

EXPOSE 9880

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9880"]
