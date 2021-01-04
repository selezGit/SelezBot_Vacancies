# pylint: disable=no-member

'''Вспомогательный файл для кластеризации навыков,
    за основу были взяты данные из 3500 вакансий
     по Питеру и Москве '''

import json
import re
from collections import OrderedDict
from Db_model import Session, Vacancy_data

newdict = {                
            "0": {},
            "1": {},
            "3": {},
            "6": {},
        }

def splitter() -> dict:
    sess = Session()
    data = sess.query(Vacancy_data.experience, Vacancy_data.salary, Vacancy_data.skils).all()
    print(data)
    for dataframe in data: 
        salary = conversion_currency(dataframe[1])
        skils = [i.strip() for i in (["None"] if not dataframe[2] else dataframe[2].lower().split(","))]
        if '1–3 года' in dataframe[0]:
            for i in salary:
                if not newdict["1"].get(i):
                    newdict["1"][i] = {}
                for j in skils:
                    if not newdict["1"][i].get(j):
                        newdict["1"][i][j] = 1
                    else:
                        newdict["1"][i][j] += 1 

                if not newdict["3"].get(i):
                    newdict["3"][i] = {}
                for j in skils:
                    if not newdict["3"][i].get(j):
                        newdict["3"][i][j] = 1
                    else:
                        newdict["3"][i][j] += 1 
        elif '3–6 лет' in dataframe[0]:
            for i in salary:
                if not newdict["3"].get(i):
                    newdict["3"][i] = {}
                for j in skils:
                    if not newdict["3"][i].get(j):
                        newdict["3"][i][j] = 1
                    else:
                        newdict["3"][i][j] += 1 

                if not newdict["6"].get(i):
                    newdict["6"][i] = {}
                for j in skils:
                    if not newdict["6"][i].get(j):
                        newdict["6"][i][j] = 1
                    else:
                        newdict["6"][i][j] += 1 
        elif 'более 6 лет' in dataframe[0]:
            for i in salary:
                if not newdict["6"].get(i):
                    newdict["6"][i] = {}
                for j in skils:
                    if not newdict["6"][i].get(j):
                        newdict["6"][i][j] = 1
                    else:
                        newdict["6"][i][j] += 1
        elif "не требуется" in dataframe[0]:
            for i in salary:
                if not newdict["0"].get(i):
                    newdict["0"][i] = {}
            for j in skils:
                if not newdict["0"][i].get(j):
                    newdict["0"][i][j] = 1
                else:
                    newdict["0"][i][j] += 1
    sess.close()

def conversion_currency(string: str) -> list:
    '''Конвертирует валюту в рубли'''
    if "руб." in string:
        rub = re.findall(r'\d+', string.replace(" ", ""))
        return [int(x)//1000 for x in rub]
    elif "USD" in string:
        usd = re.findall(r'\d+', string.replace(" ", ""))
        return [(int(x)*80)//1000 for x in usd]
    elif "EUR" in string:
        eur = re.findall(r'\d+', string.replace(" ", ""))
        return [(int(x)*90)//1000 for x in eur]
    else:
        return ["з/п не указана"]

def clasterization_skills() -> json:
    '''Функция кластеризации навыков 
    и подсчёта их веса в кластере'''
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
    splitter()
    clasterization_skills()


# print(json.dumps(newdict, ensure_ascii=False))
