FROM python

WORKDIR /app

COPY src ./

RUN pip3 install -r requirements.txt

ENTRYPOINT bash -c 'python3 -u init_dbs.py && python3 -u main.py'
