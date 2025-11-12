FROM python:3.11-slim

WORKDIR /app  # This matches the /backend directory

RUN apt-get update && apt-get install -y gcc

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


