FROM python

WORKDIR /app

COPY src/* ./

RUN pip3 install -r requirements.txt

ENTRYPOINT bash -c 'python3 init_dbs.py && gunicorn -c gunicorn_config.py main:app'