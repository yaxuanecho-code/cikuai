FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import spacy,spacy.cli; spacy.cli.download('en_core_web_sm')"

COPY app.py /app/

EXPOSE 8000
CMD uvicorn app:app --host 0.0.0.0 --port 8000
