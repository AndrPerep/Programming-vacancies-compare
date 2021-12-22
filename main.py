import requests
import os

from dotenv import load_dotenv
from statistics import mean
from terminaltables import AsciiTable


def predict_rub_salary(payment_from, payment_to):
  if payment_from and payment_to:
    predict_salary = (payment_from + payment_to)/2
  elif payment_from:
    predict_salary = payment_from * 1.2
  else:
    predict_salary = payment_to * 0.8
  return predict_salary


def get_vacancies_hh(language, pages=1):
  vacancies = []
  for page in range(0, pages):
    payload = {
      'text': f'Программист {language}',
      'specialization': '1.221',
      'area': '1',
      'period': '30',
      'only_with_salary': True,
      'page': f'{page}',
      'per_page': '100'
    }
    response = requests.get('https://api.hh.ru/vacancies', params=payload)
    response.raise_for_status()
    for vacancy in response.json()['items']:
      vacancies.append(vacancy)
  found = response.json()['found']
  pages = response.json()['pages']
  return pages, found, vacancies


def get_average_salary_hh(languages):
  hh_average_salaries = {}
  for language in languages:
    language_average_salaries = {}
    pages, found, vacancies = get_vacancies_hh(language)  # получает количество страниц для запроса
    pages, found, vacancies = get_vacancies_hh(language, pages)

    predict_salaries = []
    for vacancy in vacancies:
      salary = vacancy['salary']
      if salary['currency'] == 'RUR':
        predict_salaries.append(predict_rub_salary(salary['from'], salary['to']))

    language_average_salaries['average_salary'] = int(mean(predict_salaries))
    language_average_salaries['vacancies_processed'] = len(predict_salaries)
    language_average_salaries['vacancies_found'] = found

    hh_average_salaries[language] = language_average_salaries

  return hh_average_salaries


def get_vacancies_sj(language):
  vacancies = []
  headers = {
    'X-Api-App-Id': os.getenv('SJ_KEY')
  }
  for page in range(0, 6):
    payload = {
      'page': f'{page}',
      'count': '100',
      'town': '4',
      'catalogues': '48',
      'keyword': f'Программист {language}'
    }
    response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
    response.raise_for_status()
    for vacancy in response.json()['objects']:
      vacancies.append(vacancy)
    found = response.json()['total']

  return found, vacancies


def get_average_salary_sj(languages):
  sj_average_salaries = {}
  for language in languages:
    language_average_salaries = {}
    found, vacancies = get_vacancies_sj(language)

    predict_salaries = []
    for vacancy in vacancies:
      if vacancy['currency'] == 'rub':
        predict_salaries.append(predict_rub_salary(vacancy['payment_from'], vacancy['payment_to']))

    language_average_salaries['average_salary'] = int(mean(predict_salaries))
    language_average_salaries['vacancies_processed'] = len(predict_salaries)
    language_average_salaries['vacancies_found'] = found

    sj_average_salaries[language] = language_average_salaries

  return sj_average_salaries


def table(title, average_salaries):
  table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
  for language in average_salaries:
    language_average_salaries = average_salaries[language]
    table_row = [
      language,
      language_average_salaries['vacancies_found'],
      language_average_salaries['vacancies_processed'],
      language_average_salaries['average_salary']
    ]
    table_data.append(table_row)

  table = AsciiTable(table_data, title)
  print(table.table)


def main():
  load_dotenv()
  languages = ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', 'C', 'Go']
  table('HeadHunter Moscow', get_average_salary_hh(languages))
  table('SuberJob Moscow', get_average_salary_sj(languages))


if __name__ == '__main__':
  main()
