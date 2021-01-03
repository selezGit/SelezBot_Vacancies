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

from vacancies.vector import check_coincidence
import redis

from vacancies.models import Session, Vacancy_responce, valid_responce

#connect to redis
cache = redis.Redis(host='192.168.10.4', port=6379)

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




def get_token_user():
    """зайти по ссылке https://hh.ru/oauth/authorize?response_type=code&client_id=CLIENT_ID и после редиректа получить AUTHORIZATION_CODE
    access_token действует только 2 недели, для его обноления нужен refresh_token(используется только 1 раз)"""
    global ACCESS_TOKEN_USER, REFRESH_TOKEN_USER
    try:
        AUTHORIZATION_CODE = 'K5BOLLH44CTI59KMMHDO9LCF8MDBBR2FCOD9IU24RS2MF09M2QQCIKT8VJ0ITDUO'
        r = requests.post(ACCESS_TOKEN_URL, data={'grant_type': 'authorization_code',
                                                  'code': AUTHORIZATION_CODE,
                                                  'client_id': CLIENT_ID,
                                                  'client_secret': CLIENT_SECRET,
                                                  'redirect_uri': REDIRECT_URI})

        assert r.status_code == 200
        ACCESS_TOKEN_USER = "Bearer " + r.json()["access_token"]
        REFRESH_TOKEN_USER = r.json()["refresh_token"]
        EXPIRES_IN = r.json()["expires_in"]
        cache.mset({'ACCESS_TOKEN_USER': ACCESS_TOKEN_USER,
                 'REFRESH_TOKEN_USER': REFRESH_TOKEN_USER,
                  'EXPIRES_IN': time.time() + EXPIRES_IN})
        return ACCESS_TOKEN_USER, REFRESH_TOKEN_USER
    except AssertionError:
        print("Ответ сервера не 200")
        return None, None


def update_token_user():
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
        cache.mset({'ACCESS_TOKEN_USER': ACCESS_TOKEN_USER,
                 'REFRESH_TOKEN_USER': REFRESH_TOKEN_USER,
                  'EXPIRES_IN': time.time() + EXPIRES_IN})
        return ACCESS_TOKEN_USER, REFRESH_TOKEN_USER
    except AssertionError:
        print("Ответ сервера не 200")
        return None, None


def check_token(method: str):
    try:
        r = requests.get(URL+method, headers={"User-Agent": "selezBot",
                                              "Host": "api.hh.ru",
                                              "Accept": "*/*",
                                              "Authorization": ACCESS_TOKEN_USER})
        assert r.status_code == 200
        
        return r.json()
    except AssertionError:
        return r.status_code, r.text


def send_to_responce(message: str, vacancy_id: int):
    """функция отправки отклика на вакансию"""
    try:
        print("отклик отправлен")

        # r = requests.post(URL+"/negotiations", headers={"User-Agent": "selezBot",
        #                                                 "Host": "api.hh.ru",
        #                                                 "Accept": "*/*",
        #                                                 "Authorization": ACCESS_TOKEN_USER},
        #                                         data={"vacancy_id": vacancy_id,
        #                                                 "resume_id": "bb9635efff02d3a6470039ed1f48647864316d",
        #                                                 "message": message.encode('utf-8')})
        # assert r.status_code == 201
        # return r.status_code
        return 201 #убрать после теста

    except AssertionError:
        # print(f"Ответ сервера: {r.status_code}")
        print("Отлик не отправлен")

# print(r, r.content.decode())


def get_vacancies_data(search_for_name: str):
    """Поиск вакансий по названию"""
    sess = Session()
    lst = []
    for page in range(0, 20):
        r = requests.get(URL+"/vacancies", headers={"User-Agent": "selezBot",
                                                    "Host": "api.hh.ru",
                                                    "Accept": "*/*",
                                                    "Authorization": ACCESS_TOKEN_USER},
                                            params={'text': search_for_name,
                                                    'area': 2,  # saint-petersburg
                                                    'page': page,
                                                    'per_page': 100
                                                    })
        assert r.status_code == 200
        # Учитываем случай когда страниц меньше 20
        if (r.json()['pages'] - page) <= 0:
            break
        for i in r.json()["items"]:
            # lst.append(get_vacancy_data(i['id']))
            data = get_vacancy_data(i['id'])
            tfidf = check_coincidence(data['_full'])
            skills = check_weight_skills(data)
            coincidence = round(((tfidf+skills)/2)*100)

            already_in_base = sess.query(Vacancy_responce).filter_by(vacid=data['vacancy_id']).first()
            print(coincidence)
            if coincidence > 30 and not already_in_base: #   + ОТПРАВИТЬ СООБЩЕНИЕ ТЕЛЕГРАМ БОТУ
                print(f'tfidf:{tfidf}, skills:{skills}')
                rows_count = sess.query(Vacancy_responce).count()

                message = f'''Добрый день! 

                            Меня зовут Дима. Я ищу работу. 

                            Я написал job-бота на python, с помощью которого обработал уже {rows_count} вакансий. Моё резюме соответствует вашей вакансии на {coincidence}%. 

                            Опыта коммерческой разработки у меня нет, но я умею писать код. Вот ссылка на репозиторий бота. https://github.com/selezGit/SelezBot_Vacancies

                            Буду рад приглашению на собеседование. 

                            Это письмо было отправлено автоматически. Я всегда доступен для связи по телефону 8 921 553 56 01. 

                            Спасибо за внимание!'''
                status_code = send_to_responce(message, data['vacancy_id'])
                if status_code == 201:
                    try:
                        vac = Vacancy_responce(vacid=data['vacancy_id'],
                                                state=1,
                                                timestamp=datetime.datetime.utcnow(),
                                                score=coincidence
                                                )
                        sess.add(vac)
                        sess.commit()
                    except:
                        sess.rollback()
                sess.close()
            # time.sleep(5)
            # return # остановочный ключ, убрать после дебага
        r.close()
        print(f"parsing data in page: {page}")
    return lst


def get_vacancy_data(vacancy_id: int):
    """Функция для получения полного описания вакансии"""
    dictionary = {}
    r = requests.get(URL+f"/vacancies/{vacancy_id}", headers={"User-Agent": "selezBot",
                                                              "Host": "api.hh.ru",
                                                              "Accept": "*/*",
                                                              "Authorization": ACCESS_TOKEN_USER})
    #тут будем получать только нужные нам ключи
    '''Предположительно будем дёргать следующие ключи:
        salary, arhived, expirience, description, key_skills, alternate_url, id'''
    data = r.json()
    dictionary['vacancy_id'] = data['id']
    dictionary['name'] = data['name']
    dictionary['link'] = data['alternate_url']
    dictionary['experience'] = [x for x in data['experience']['name'] if x.isdigit()] if not 'Нет опыта' in data['experience']['name'] else ['0']
    dictionary['salary'] = get_real_salary([x for x in data['salary'].values() if not x in ['null', 'RUR', False, True, None]]) if data['salary'] else ['з/п не указана']
    dictionary['_full'] = re.sub(r'<.*?>', '' , data['description'])
    dictionary['skills'] = [i['name'].lower() for i in data['key_skills']] if data['key_skills'] else ['None']
    assert r.status_code == 200
    return dictionary

def get_real_salary(salary):
    '''Вычисляем з/п в рублях и оставляем двухзначное представление'''
    if 'USD' in salary:
        return [str((i*70)//1000) for i in salary if isinstance(i, int)]
    elif 'EUR' in salary:
        return [str((i*90)//1000) for i in salary if isinstance(i, int)]
    else:
        return [str(i//1000) for i in salary if isinstance(i, int)]

my_skills = ['python', 'администрирование серверов windows', 'git', 'l2tp+ipsec openvpn', 'sqlite', 'диагностика и модульный ремонт пк', 'linux', 'nginx', 'html', 'css',
 'postgresql', 'selenium', 'навыки написания скриптов на python, настройки базовых сервисов (ntp, ftp, postgresql, vps(aws))',
  'чтение технической документации на английском языке', 'docker', 'flask', 'tcp/ip', 'sql', 'linux ubuntu server', 'mikrotik']


def check_weight_skills(vacancy: list):
    with open('vacancies/updated_data.json', 'r') as outfile:
        s = json.load(outfile)
    total = 0
    for i in vacancy['experience']:
        for j in vacancy['salary']:
            if j in s[i]:
                for k in vacancy['skills']:
                    if k in my_skills and k in s[i][j]:
                        total += s[i][j][k][2]
            else:
                for k in vacancy['skills']:
                    if k in my_skills:
                        # print(k, [1, "вес навыка:", 1/len(vacancy['skills'])])
                        total += 1/len(vacancy['skills'])

    if len(vacancy['experience']) == 2:
        total = total / 2
    return total



if __name__ == "__main__":
    if time.time() > float(cache.get('EXPIRES_IN').decode("utf-8")):
        print(update_token_user())
        print("token is updated")
    # print(check_token("/me"))


    vac_python = get_vacancies_data("Python")
    # tfidf = check_coincidence(vac_python[0]['_full'])
    # skills = check_weight_skills(vac_python[0], s)
    # coincidence = round((tfidf+skills)*100)
    # print(f'питон: {tfidf+skills}')

    # print(f'python: tfidf:{tfidf}, skills:{skills}, sum:{tfidf+skills}')

    # print(f'shop_ass: tfidf:{tfidf}, skills:{skills}, sum:{tfidf+skills}')
    




'''возможно пригодится'''
    # vac_shop_assistant = get_vacancies_data("Продавец-консультант")
    # tfidf = check_coincidence(vac_shop_assistant[0]['_full'])
    # skills = check_weight_skills(vac_shop_assistant[0], s)
    # print(f'НЕ питон: {tfidf+skills}')