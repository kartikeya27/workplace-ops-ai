FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY workplace_ops ./workplace_ops
COPY web ./web
RUN mkdir -p /app/artifacts
EXPOSE 8000
CMD ["uvicorn", "workplace_ops.app:app", "--host", "0.0.0.0", "--port", "8000"]
