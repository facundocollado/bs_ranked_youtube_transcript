FROM python:3.10-slim
WORKDIR /app
COPY shared shared
COPY main.py requirements.txt ./
RUN pip install -r requirements.txt
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8080"]
