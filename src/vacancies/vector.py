#!/usr/bin/python3

import pandas as pd
import nltk
import numpy as np
import json

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import pairwise_distances
import psycopg2

from nltk.corpus import stopwords
from pymystem3 import Mystem
from string import punctuation


nltk.download('punkt')
nltk.download("stopwords")
#--------#
#Create lemmatizer and stopwords list
mystem = Mystem() 
russian_stopwords = stopwords.words("russian")
save_in_base = False #Если требуется запись вектора в базу пиши тру



# connection = psycopg2.connect(user = "selezard",
#                         password = "huipyhui",
#                         host = "127.0.0.1",
#                         port = "5432",
#                         database = "bigdata")
# cursor = connection.cursor()

my_attainments = '''# Технические навыки
• Администрирование GNU/Linux Ubuntu, OS Windows XP/7/10, Server 2012/2016;
• Опыт инсталляции и эксплуатации Nginx;
* СУБД: PostgreSQL, SQLite, Redis;
* Развертывание: Docker, VirtualBox, Proxmox, OpenVPN;
• Коммерческого опыта разработки не имею, писал скрипты для друзей и знакомых;
*Скрипт по отслеживанию скидок на различных торговых площадках, с последующими уведомлениями в телеграм канал, скрипт по поиску работы, различные скрипты по парсингу сайтов с использованием selenium.
• Администрирование сетевого операторского оборудования (D-Link, MikroTik);
• Знание основ построения сетей и передачи данных (коммутация, IP-маршрутизация), понимание
принципов работы сетевых технологий и протоколов (TCP/IP, DHCP, DNS, VLAN, IGMP, SNMP, NAT, QoS, VPN);

# Личные качества
• Легко осваиваю новое, способен к быстрому усвоению информации;
• Способность к самостоятельному мышлению и оперативному принятию обоснованных решений;
• Придерживаюсь системного подхода в решении вопросов, аналитические способности;
• Организованность, в работе проявляю инициативу;
• Вредных привычек не имею.
Чего жду от работы:
• Дружный молодой коллектив.
• Бесплатные уроки английского языка
• Полис ДМС.
'''

def text_normalization(text):
    tokens = mystem.lemmatize(text.lower())
    tokens = [token for token in tokens if token not in russian_stopwords\
              and token != " " \
              and token.strip() not in punctuation\
              and token.isdigit() != True]
    
    text = " ".join(tokens)
    return text

# cursor.execute("SELECT _full FROM public.data")
# data = cursor.fetchall()

        
def check_coincidence(text):
    cv = CountVectorizer()
    #создаём вектор из полного описания вакансии
    X = cv.fit_transform([text_normalization(text)]).toarray()

    df_bow= pd.DataFrame(X, columns = cv.get_feature_names())
    #делаем вектор из описания моих навыков
    Question_lemma = text_normalization(my_attainments)
    Question_bow = cv.transform([Question_lemma]).toarray() 

    #опеределяем косинусное сходство между двумя векторами
    cosine_value = 1- pairwise_distances(df_bow, Question_bow, metric='cosine')
    #Записываем данные вектора в базу
    # if save_in_base == True:
    #     sql_update_query = '''UPDATE public.data SET vector=%s WHERE _full=%s'''
    #     cursor.execute(sql_update_query, (str(df_bow.to_dict()), text))
    #     connection.commit()

        # df_bow = pd.DataFrame.from_dict(test)
    # result = tfidf * (tfidf*(min_chars_text/max_char_text))
    return int(*cosine_value[0]*100)/100


def check_json():
    with open('data.json', 'r') as outfile:
        s = json.load(outfile)
    for i in s:
        for j in s[i]:
            keys = []
            for k in s[i][j]:
                keys.append(s[i][j][k])
            for k in s[i][j]:
                s[i][j][k] = [s[i][j][k], "вес навыка:", s[i][j][k]/sum(keys)]
    with open('updated_data.json', 'w') as outfile:
        json.dump(s, outfile, ensure_ascii=False)
    return s


if __name__ == "__main__":
    pass
    
    # for i in s['1']['80']:
    #     if i in my_attainments:
    #         print(i, s['1']['80'][i][2])

    # for i in s['6']['560']:
    #     if i in my_attainments:
    #         print(i, s['6']['560'][i][2])

    # connection.close()
    