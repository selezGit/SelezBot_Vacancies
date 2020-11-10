# pylint: disable=no-member

from flask import Flask, request, Response, render_template
from psycopg2 import connect
from models import Session, Vacancy, valid_responce
from json import loads

app = Flask(__name__)


 
@app.route("/api")
def index():
    return "hello world"

@app.route("/api/vacancies", methods=[ "GET", "PUT" ])
def handle_vacancies():
    resp = Response()
    sess = Session()
    if request.method == "GET":
        data = sess.query(Vacancy).all()
        resp.data = valid_responce(data)
    elif request.method == "PUT":
        vac = Vacancy(**loads(request.data))
        sess.add(vac)
        try:
            sess.commit()
        except:
            sess.rollback()
    sess.close()
    return resp

@app.route("/api/vacancy/<vacancy_id>", methods=[ "GET", "POST", "DELETE" ])
def handle_vacancy(vacancy_id):
    resp = Response()
    sess = Session()
    if request.method == "GET":
        data = sess.query(Vacancy).filter_by(uuid=vacancy_id).first()
        resp.data = valid_responce(data)
        sess.close()
        return resp
    else:
        if request.method == "POST":
            sess.query(Vacancy).filter_by(uuid=vacancy_id).update(loads(request.data))
        elif request.method == "DELETE":
            sess.query(Vacancy).filter_by(uuid=vacancy_id).delete()
    try:
        sess.commit()
    except:
        sess.rollback()
    sess.close()
    return resp

