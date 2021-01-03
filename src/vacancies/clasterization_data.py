import psycopg2
import json
import re
from collections import OrderedDict


connection = psycopg2.connect(user = "selezard",
                        password = "huipyhui",
                        host = "192.168.10.4",
                        port = "5432",
                        database = "bigdata")
cursor = connection.cursor()



cursor.execute("SELECT experience, salary, skils FROM public.data")
data = cursor.fetchall()


newdict = {                
            "0": {},
            "1": {},
            "3": {},
            "6": {},
        }

def splitter(dataframe):
    salary = digits(dataframe[1])
    skils = [i.strip() for i in (["None"] if not dataframe[2] else dataframe[2].lower().split(","))]
    # skils = [i.strip() for i in skils]
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

def digits(string):
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



for i in data:
    splitter(i)


print(json.dumps(newdict, ensure_ascii=False))
