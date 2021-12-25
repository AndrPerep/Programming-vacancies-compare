import itertools
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


def get_vacancies_hh(language):
  vacancies = []
  for page in itertools.count(start=0, step=1):
    payload = {
      'text': f'Программист {language}',
      'specialization': '1.221',
      'area': '1',
      'period': '30',
      'page': page,
      'per_page': '100'
    }
    response = requests.get('https://api.hh.ru/vacancies', params=payload)
    response.raise_for_status()

    pages_number = response.json()['pages']

    for vacancy in response.json()['items']:
      vacancies.append(vacancy)

    if page > pages_number or page == 19:
      break
  found = response.json()['found']
  return found, vacancies


def get_average_salary_hh(languages):
  hh_average_salaries = {}
  for language in languages:
    language_average_salaries = {}
    found, vacancies = get_vacancies_hh(language)

    predict_salaries = []
    for vacancy in vacancies:
      salary = vacancy['salary']
      if salary:
        if salary['currency'] == 'RUR':
          predict_salaries.append(predict_rub_salary(salary['from'], salary['to']))

    language_average_salaries['average_salary'] = int(mean(predict_salaries))
    language_average_salaries['vacancies_processed'] = len(predict_salaries)
    language_average_salaries['vacancies_found'] = found

    hh_average_salaries[language] = language_average_salaries

  return hh_average_salaries


def get_vacancies_sj(language, sj_key):
  vacancies = []
  headers = {
    'X-Api-App-Id': sj_key
  }
  for page in itertools.count(start=0, step=1):
    payload = {
      'page': page,
      'count': '100',
      'town': '4',
      'catalogues': '48',
      'keyword': f'Программист {language}'
    }
    response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
    response.raise_for_status()

    for vacancy in response.json()['objects']:
      vacancies.append(vacancy)
    if response.json()['more'] == False:
      break

  found = response.json()['total']
  return found, vacancies


def get_average_salary_sj(languages, sj_key):
  sj_average_salaries = {}
  for language in languages:
    language_average_salaries = {}
    found, vacancies = get_vacancies_sj(language, sj_key)

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
  sj_key = os.getenv('SJ_KEY')

  languages = ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', 'C', 'Go']
  table('HeadHunter Moscow', get_average_salary_hh(languages))
  table('SuberJob Moscow', get_average_salary_sj(languages, sj_key))


if __name__ == '__main__':
  main()
