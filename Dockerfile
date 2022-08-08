FROM python:3.10-bullseye

WORKDIR /opt/garage-api

COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app"]