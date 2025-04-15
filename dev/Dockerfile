FROM python:latest

WORKDIR /srs

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y netcat-openbsd
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
