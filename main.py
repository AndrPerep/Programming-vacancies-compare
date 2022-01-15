import itertools
import requests
import os

from dotenv import load_dotenv
from statistics import mean
from terminaltables import AsciiTable


def predict_rub_salary(payment_from, payment_to):
  if payment_from and payment_to:
    return (payment_from + payment_to)/2
  elif payment_from:
    return payment_from * 1.2
  elif payment_to:
    return payment_to * 0.8


def get_vacancies_hh(language):
  job_specialization = '1.221'
  search_area = '1'
  period = '30'

  vacancies = []
  for page in itertools.count(start=0, step=1):
    payload = {
      'text': f'Программист {language}',
      'specialization': job_specialization,
      'area': search_area,
      'period': period,
      'page': page,
      'per_page': '100'
    }
    response = requests.get('https://api.hh.ru/vacancies', params=payload)
    response.raise_for_status()

    decoded_response = response.json()
    pages_number = decoded_response['pages']

    for vacancy in decoded_response['items']:
      vacancies.append(vacancy)

    if page > pages_number or page == 19:
      break
  found = decoded_response['found']
  return found, vacancies


def get_average_salary_hh(languages):
  hh_average_salaries = {}
  for language in languages:
    found, vacancies = get_vacancies_hh(language)

    predict_salaries = []
    for vacancy in vacancies:
      salary = vacancy['salary']
      if salary:
        if salary['currency'] == 'RUR':
          predict_salaries.append(predict_rub_salary(salary['from'], salary['to']))

    language_average_salaries = {
      'average_salary': int(mean(predict_salaries)),
      'vacancies_processed': len(predict_salaries),
      'vacancies_found': found
    }
    hh_average_salaries[language] = language_average_salaries

  return hh_average_salaries


def get_vacancies_sj(language, sj_key):
  search_area = '4'
  job_specialization = '48'

  vacancies = []
  headers = {
    'X-Api-App-Id': sj_key
  }
  for page in itertools.count(start=0, step=1):
    payload = {
      'page': page,
      'count': '100',
      'town': search_area,
      'catalogues': job_specialization,
      'keyword': f'Программист {language}'
    }
    response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
    response.raise_for_status()
    response_json = response.json()

    for vacancy in response_json['objects']:
      vacancies.append(vacancy)
    if response_json['more'] == False:
      break

  found = response_json['total']
  return found, vacancies


def get_average_salary_sj(languages, sj_key):
  sj_average_salaries = {}

  for language in languages:
    found, vacancies = get_vacancies_sj(language, sj_key)

    predict_salaries = []
    for vacancy in vacancies:
      if vacancy['currency'] == 'rub':
        predict_salaries.append(predict_rub_salary(vacancy['payment_from'], vacancy['payment_to']))

    language_average_salaries = {
      'average_salary': int(mean(predict_salaries)),
      'vacancies_processed': len(predict_salaries),
      'vacancies_found': found
    }
    sj_average_salaries[language] = language_average_salaries

  return sj_average_salaries


def create_table(title, average_salaries):
  table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]

  for language in average_salaries:
    language_average_salaries = average_salaries[language]
    table_row = list(language_average_salaries.values())
    table_row.insert(0, language)

    table_data.append(table_row)

  table = AsciiTable(table_data, title)
  return table.table


def main():
  load_dotenv()
  sj_key = os.getenv('SJ_KEY')

  languages = ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', 'C', 'Go']
  print(create_table('HeadHunter Moscow', get_average_salary_hh(languages)))
  print(create_table('SuberJob Moscow', get_average_salary_sj(languages, sj_key)))


if __name__ == '__main__':
  main()
