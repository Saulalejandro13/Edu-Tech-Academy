FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY scr/ ./src/
RUN pip install --no-cache-dir -r requirements.txt -e .
EXPOSE 8000
CMD ["uvicorn", "edutech.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
