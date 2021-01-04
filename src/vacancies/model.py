#!/usr/bin/python3

import pandas as pd
import nltk
import numpy as np
import json

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import pairwise_distances

from nltk.corpus import stopwords
from pymystem3 import Mystem
from string import punctuation


nltk.download('punkt')
nltk.download("stopwords")
#Create lemmatizer and stopwords list
mystem = Mystem() 
russian_stopwords = stopwords.words("russian")

my_attainments = '''
# Технические навыки
• Администрирование GNU/Linux Ubuntu, OS Windows XP/7/10, Server 2012/2016;
• Опыт инсталляции и эксплуатации Nginx;
• СУБД: PostgreSQL, SQLite, Redis;
• Развертывание: Docker, VirtualBox, Proxmox, OpenVPN;
• Коммерческого опыта разработки не имею, писал скрипты для друзей и знакомых;
• Скрипт по отслеживанию скидок на различных торговых площадках, с последующими уведомлениями
     в телеграм канал, скрипт по поиску работы, различные скрипты по парсингу сайтов с использованием selenium;
• Администрирование сетевого операторского оборудования (D-Link, MikroTik);
• Знание основ построения сетей и передачи данных (коммутация, IP-маршрутизация), понимание
    принципов работы сетевых технологий и протоколов (TCP/IP, DHCP, DNS, VLAN, IGMP, SNMP, NAT, QoS, VPN);

# Личные качества
• Легко осваиваю новое, способен к быстрому усвоению информации;
• Способность к самостоятельному мышлению и оперативному принятию обоснованных решений;
• Придерживаюсь системного подхода в решении вопросов, аналитические способности;
• Организованность, в работе проявляю инициативу;
• Вредных привычек не имею;
Чего жду от работы:
• Дружный молодой коллектив;
• Бесплатные уроки английского языка;
• Полис ДМС;
'''

my_skills = ['python', 'администрирование серверов windows', 'git', 'l2tp+ipsec openvpn', 'sqlite', 'диагностика и модульный ремонт пк', 'linux', 'nginx', 'html', 'css',
 'postgresql', 'selenium', 'навыки написания скриптов на python, настройки базовых сервисов (ntp, ftp, postgresql, vps(aws))',
  'чтение технической документации на английском языке', 'docker', 'flask', 'tcp/ip', 'sql', 'linux ubuntu server', 'mikrotik']

def text_normalization(text: str) -> str:
    '''Приводим текст к лемме'''
    tokens = mystem.lemmatize(text.lower())
    tokens = [token for token in tokens if token not in russian_stopwords\
              and token != " " \
              and token.strip() not in punctuation\
              and token.isdigit() != True]
    
    text = " ".join(tokens)
    return text

def check_coincidence(text: str) -> float:
    '''Переводим оба текста в вектор
     и считаем косинусное сходство'''
    cv = CountVectorizer()
    #создаём вектор из полного описания вакансии
    X = cv.fit_transform([text_normalization(text)]).toarray()
    df_bow= pd.DataFrame(X, columns = cv.get_feature_names())
    #делаем вектор из описания моего резюме
    Question_lemma = text_normalization(my_attainments)
    Question_bow = cv.transform([Question_lemma]).toarray() 
    #опеределяем косинусное сходство между двумя векторами
    cosine_value = 1- pairwise_distances(df_bow, Question_bow, metric='cosine')
    return int(*cosine_value[0]*100)/100

def check_weight_skills(vacancy: list) -> float:
    '''функция определения веса навыка
     на основе данных из 3500 вакансий'''
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
                        total += 1/len(vacancy['skills'])
    '''усредняем случай когда требуемый опыт работы,
    указан диапазоном например от 1 до 3 лет, 
    так как скрипт в этом случае сделает 2 прохода'''
    if len(vacancy['experience']) == 2:
        total = total / 2
    return total
