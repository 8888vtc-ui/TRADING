FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt newsapi-python google-generativeai anthropic
COPY . .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
CMD ["python", "main_runner.py"]
