from vacancies.connect_to_hhru import get_vacancies_data, condition_check, check_by_model

if __name__ == "__main__":
    for vacid in get_vacancies_data("Python"):
        condition_check(check_by_model(vacid), vacid)