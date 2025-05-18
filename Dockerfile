FROM python:3.10.10-slim-bullseye
WORKDIR /WORKDIR
COPY . .

RUN pip install -U pip && pip install -r requirements.txt --no-cache-dir

EXPOSE 1759
CMD ["python", "app.py"]