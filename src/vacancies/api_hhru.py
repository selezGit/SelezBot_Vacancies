#!/usr/bin/python3
# pylint: disable=no-member
# pylint: disable=import-error

import datetime
import json
import requests
import re
import os
import psycopg2
import time
import redis

from vacancies.model import check_coincidence, check_weight_skills
from vacancies.Db_model import Session, Vacancy_responce

#connect to redis
cache = redis.Redis(host='redis')
    
# urls
URL = 'https://api.hh.ru'
REDIRECT_URI = 'https://none'
ACCESS_TOKEN_URL = 'https://hh.ru/oauth/token'

# secrets
CLIENT_ID = cache.get('CLIENT_ID').decode("utf-8")
CLIENT_SECRET = cache.get('CLIENT_SECRET').decode("utf-8")

# program_token
ACCESS_TOKEN_PROGRAMM = cache.get('ACCESS_TOKEN_PROGRAMM').decode("utf-8")

# user_token
ACCESS_TOKEN_USER = cache.get('ACCESS_TOKEN_USER').decode("utf-8")
REFRESH_TOKEN_USER = cache.get('REFRESH_TOKEN_USER').decode("utf-8")



def get_token_user() -> str:
    """зайти по ссылке https://hh.ru/oauth/authorize?response_type=code&client_id=CLIENT_ID и после редиректа получить AUTHORIZATION_CODE
    access_token действует только 2 недели, для его обноления нужен refresh_token(используется только 1 раз)"""
    global ACCESS_TOKEN_USER, REFRESH_TOKEN_USER
    try:
        AUTHORIZATION_CODE = '<YOUR AUTHORIZATION_CODE HERE>'
        r = requests.post(ACCESS_TOKEN_URL, data={'grant_type': 'authorization_code',
                                                  'code': AUTHORIZATION_CODE,
                                                  'client_id': CLIENT_ID,
                                                  'client_secret': CLIENT_SECRET,
                                                  'redirect_uri': REDIRECT_URI})

        assert r.status_code == 200
        ACCESS_TOKEN_USER = "Bearer " + r.json()["access_token"]
        REFRESH_TOKEN_USER = r.json()["refresh_token"]
        EXPIRES_IN = r.json()["expires_in"]
        #Записываем полученный ключ в redis
        cache.mset({'ACCESS_TOKEN_USER': ACCESS_TOKEN_USER,
                 'REFRESH_TOKEN_USER': REFRESH_TOKEN_USER,
                  'EXPIRES_IN': time.time() + EXPIRES_IN})
        return ACCESS_TOKEN_USER, REFRESH_TOKEN_USER
    except AssertionError:
        print("Ответ сервера не 200")
        return None, None

def update_token_user() -> str:
    """Обновляет токен пользователя,
     в случае если он закончился"""
    global ACCESS_TOKEN_USER, REFRESH_TOKEN_USER
    try:
        r = requests.post(ACCESS_TOKEN_URL, data={'grant_type': 'refresh_token',
                                                  'client_id': CLIENT_ID,
                                                  'client_secret': CLIENT_SECRET,
                                                  'refresh_token': REFRESH_TOKEN_USER})
        assert r.status_code == 200
        ACCESS_TOKEN_USER = "Bearer " + r.json()["access_token"]
        REFRESH_TOKEN_USER = r.json()["refresh_token"]
        EXPIRES_IN = r.json()["expires_in"]
        #Записываем обновлённый ключ в redis
        cache.mset({'ACCESS_TOKEN_USER': ACCESS_TOKEN_USER,
                 'REFRESH_TOKEN_USER': REFRESH_TOKEN_USER,
                  'EXPIRES_IN': time.time() + EXPIRES_IN})
        return ACCESS_TOKEN_USER, REFRESH_TOKEN_USER
    except AssertionError:
        print("Ответ сервера не 200")
        return None, None

#Проверка на актуальность ключа
if time.time() > float(cache.get('EXPIRES_IN').decode("utf-8")):
    update_token_user()
    print("token is updated")

def check_token(method: str) -> any:
    try:
        r = requests.get(URL+method, headers={"User-Agent": "selezBot",
                                              "Host": "api.hh.ru",
                                              "Accept": "*/*",
                                              "Authorization": ACCESS_TOKEN_USER})
        assert r.status_code == 200
        
        return r.json()
    except AssertionError:
        return r.status_code, r.text

def check_sent_request() -> list:
    '''Возвращает список id вакансий, 
    с отправленными откликами или 
    полученными приглашениями'''
    try:
        r = requests.get(URL+"/negotiations", headers={"User-Agent": "selezBot",
                                              "Host": "api.hh.ru",
                                              "Accept": "*/*",
                                              "Authorization": ACCESS_TOKEN_USER})
        assert r.status_code == 200
        
        return [x['vacancy']['id'] for x in r.json()['items']]
    except AssertionError:
        return r.status_code, r.text

def send_to_responce(message: str, vacancy_id: int) -> int:
    """функция отправки отклика на вакансию"""
    try:
        r = requests.post(URL+"/negotiations", headers={"User-Agent": "selezBot",
                                                        "Host": "api.hh.ru",
                                                        "Accept": "*/*",
                                                        "Authorization": ACCESS_TOKEN_USER},
                                                data={"vacancy_id": vacancy_id,
                                                        "resume_id": "bb9635efff02d3a6470039ed1f48647864316d",
                                                        "message": message.encode('utf-8')})
        assert r.status_code in [201, 303]
        return r.status_code
    except AssertionError:
        print(f"Ответ сервера: {r.status_code, r.text}")

def get_vacancies_data(search_for_name: str) -> list:
    """Поиск вакансий по названию"""
    all_vacancies_id = []
    for page in range(0, 20):
        r = requests.get(URL+"/vacancies", headers={"User-Agent": "selezBot",
                                                    "Host": "api.hh.ru",
                                                    "Accept": "*/*",
                                                    "Authorization": ACCESS_TOKEN_USER},
                                            params={'text': f'NAME:{search_for_name}',
                                                    'area': [1, 2],  # saint-petersburg + moscow
                                                    'page': page,
                                                    'per_page': 100
                                                    })
        assert r.status_code == 200
        # Учитываем случай когда страниц меньше 20
        if (r.json()['pages'] - page) <= 0:
            break
        '''создаём список только из id вакансий, 
        игнорируем те, в которых нужно сделать тестовое задание'''
        all_vacancies_id += [x['id'] for x in r.json()['items'] if not x['has_test']] 
    return all_vacancies_id

def check_by_model(vac_id: int) -> int:
    '''Проверяет вакансию по описанной модели'''
    sess = Session()
    if not sess.query(Vacancy_responce).filter_by(vacid=vac_id).first():
        data = creating_dictionary(get_vacancy_data(vac_id))
        tfidf = check_coincidence(data['_full'])
        skills = check_weight_skills(data)
        coincidence = round(((tfidf+skills)/2)*100)
        sess.close()
        return coincidence
    else:
        sess.close()
        return -1

def condition_check(coincidence: int, vacid: int):
    '''функция проверки соответствия моего резюме - вакансии'''
    #убираем лишний запрос если итем уже в базе
    if coincidence == -1:
        return
    sess = Session()
    if coincidence > 25:
        rows_count = sess.query(Vacancy_responce).count()
        message = f'''Добрый день! 

                    Меня зовут Дима. Я ищу работу. 

                    Я написал job-бота на python, с помощью которого обработал уже {rows_count} вакансий. Моё резюме соответствует вашей вакансии на {coincidence}%. 

                    Опыта коммерческой разработки у меня нет, но я умею писать код. Вот ссылка на репозиторий бота. https://github.com/selezGit/SelezBot_Vacancies

                    Буду рад приглашению на собеседование. 

                    Это письмо было отправлено автоматически. Я всегда доступен для связи по телефону 8 921 553 56 01. 

                    Спасибо за внимание!'''
        assert send_to_responce(message, vacid) == 201
        add_to_base(state=1, coincidence=coincidence, vacid=vacid)
        print("new_resp_sended")
    else:
        add_to_base(state=0, coincidence=coincidence, vacid=vacid)
        print("new_vac_added")
    sess.close()

def add_to_base(state: int, coincidence: int, vacid: int):
    '''Добавляет в базу'''
    sess = Session()
    try:
        vac = Vacancy_responce(vacid=vacid,
                            state=state,
                            timestamp=datetime.datetime.utcnow(),
                            score=coincidence
                            )
        sess.add(vac)
        sess.commit()
    except:
        sess.rollback()
    finally:
        sess.close()

def get_vacancy_data(vacancy_id: int) -> json:
    """Функция для получения полного описания одной вакансии"""
    r = requests.get(URL+f"/vacancies/{vacancy_id}", headers={"User-Agent": "selezBot",
                                                              "Host": "api.hh.ru",
                                                              "Accept": "*/*",
                                                              "Authorization": ACCESS_TOKEN_USER})
    assert r.status_code == 200
    time.sleep(1)
    return r.json()

def creating_dictionary(data: json) -> dict:
    '''записываем в словарь нужные нам ключи'''
    dictionary = {}
    dictionary['vacancy_id'] = data['id']
    dictionary['name'] = data['name']
    dictionary['link'] = data['alternate_url']
    dictionary['experience'] = [x for x in data['experience']['name'] if x.isdigit()] if not 'Нет опыта' in data['experience']['name'] else ['0']
    dictionary['salary'] = convert_to_real_salary([x for x in data['salary'].values() if not x in ['null', 'RUR', False, True, None]]) if data['salary'] else ['з/п не указана']
    dictionary['_full'] = re.sub(r'<.*?>', '' , data['description'])
    dictionary['skills'] = [i['name'].lower() for i in data['key_skills']] if data['key_skills'] else ['None']
    return dictionary

def convert_to_real_salary(salary: list) -> list:
    '''Вычисляем з/п в рублях и отсекаем 3 знака'''
    if 'USD' in salary:
        return [str((i*70)//1000) for i in salary if isinstance(i, int)]
    elif 'EUR' in salary:
        return [str((i*90)//1000) for i in salary if isinstance(i, int)]
    else:
        return [str(i//1000) for i in salary if isinstance(i, int)]

if __name__ == "__main__":
    pass
    