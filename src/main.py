from vacancies.api_hhru import get_vacancies_data, condition_check, check_by_model
from vacancies.clasterization_skills import splitter, clasterization_skills
import time

if __name__ == "__main__":
    while True:
        for vacid in get_vacancies_data("python"):
            condition_check(check_by_model(vacid), vacid)
        time.sleep(3600)