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
  job_specialization = '1.221' #id специализации из справочника: https://api.hh.ru/specializations
  search_area = '1' #id региона из справочника: https://api.hh.ru/areas
  period = '30'

  vacancies = []
  payload = {
    'text': f'Программист {language}',
    'specialization': job_specialization,
    'area': search_area,
    'period': period,
    'per_page': '100'
  }
  for page in itertools.count(start=0, step=1):
    payload['page'] = page
    response = requests.get('https://api.hh.ru/vacancies', params=payload)
    response.raise_for_status()
    decoded_response = response.json()
    vacancies.extend(decoded_response['items'])

    last_page = decoded_response['pages'] - 1
    if page >= last_page:
      break
  found = decoded_response['found']
  return found, vacancies


def get_average_salaries_hh(language):
  found, vacancies = get_vacancies_hh(language)

  predicted_salaries = []
  for vacancy in vacancies:
    salary = vacancy['salary']
    if salary and salary['currency'] == 'RUR':
      if salary['from'] or salary['to']:
        predicted_salaries.append(predict_rub_salary(salary['from'], salary['to']))

  if predicted_salaries:
    language_average_salaries = {
      'average_salary': int(mean(predicted_salaries)),
      'vacancies_processed': len(predicted_salaries),
      'vacancies_found': found
    }

  return language_average_salaries


def get_vacancies_sj(language, sj_key):
  search_area = '4' #id города из справочника: https://api.superjob.ru/2.0/towns/
  job_specialization = '48' #id специализации из справочника: https://api.superjob.ru/2.0/catalogues/

  vacancies = []
  headers = {
    'X-Api-App-Id': sj_key
  }
  payload = {
    'count': '100',
    'town': search_area,
    'catalogues': job_specialization,
    'keyword': f'Программист {language}'
  }

  for page in itertools.count(start=0, step=1):
    payload['page'] = page
    response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
    response.raise_for_status()
    response_json = response.json()

    vacancies.extend(response_json['objects'])
    if not response_json['more']:
      break

  found = response_json['total']
  return found, vacancies


def get_average_salaries_sj(language, sj_key):
  found, vacancies = get_vacancies_sj(language, sj_key)

  predicted_salaries = []
  for vacancy in vacancies:
    if vacancy['currency'] == 'rub':
      if vacancy['payment_from'] or vacancy['payment_to']:
        predicted_salaries.append(predict_rub_salary(vacancy['payment_from'], vacancy['payment_to']))

  if predicted_salaries:
    language_average_salaries = {
      'average_salary': int(mean(predicted_salaries)),
      'vacancies_processed': len(predicted_salaries),
      'vacancies_found': found
    }


  return language_average_salaries


def create_table(title, average_salaries):
  table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]

  for language, language_average_salaries in average_salaries.items():
    table_row = list(language_average_salaries.values())
    table_row.reverse()
    table_row.insert(0, language)
    table_data.append(table_row)

  table = AsciiTable(table_data, title)
  return table.table


def main():
  load_dotenv()
  sj_key = os.getenv('SJ_KEY')

  languages = ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', 'C', 'Go']

  hh_average_salaries = {}
  sj_average_salaries = {}

  for language in languages:
    hh_average_salaries[language] = get_average_salaries_hh(language)
    sj_average_salaries[language] = get_average_salaries_sj(language, sj_key)

  print(create_table('HeadHunter Moscow', hh_average_salaries))
  print(create_table('SuperJob Moscow', sj_average_salaries))


if __name__ == '__main__':
  main()
