FROM python

WORKDIR /app

COPY src ./

RUN pip3 install -r requirements.txt

ENTRYPOINT bash -c 'python3 -u init_dbs.py && gunicorn -c gunicorn_config.py main:app'

# CMD ["python","-u","init_dbs.py"]