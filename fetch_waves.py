from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from cachetools import cached, TTLCache


@cached(TTLCache(maxsize=1, ttl=3600))
def extract_waves():
    url = 'https://gosurf.co.il/forecast/tel-aviv'

    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'lxml')

    all_tables_data = []

    divs_containing_tables = soup.find_all('div', class_='day_overflow_cont')

    for div_containing_table in divs_containing_tables:
        table = div_containing_table.find('table', class_='chart')

        if table:
            table_data = table_to_json(table)
            all_tables_data.append(table_data)

    return restructure_data(all_tables_data)


def translate_field_names(field):
    translation = {
        'שעה': 'Temperature',
        'גובה': 'Height',
        'גלים': 'Waves',
        'רוח': 'Wind',
        'כיוון': 'Direction',
        'סוואל': 'Swell',
        'מחזור': 'Repetition',
        'קמ״ש': '',  # Remove redundant word
        'ס״מ': '',  # Remove redundant word
        'שניות': '',  # Remove redundant word
        'מערבי': 'Western',  # Translate direction
        'צפון': 'Northern',  # Translate direction
        'מזרח': 'Eastern',  # Translate direction
        'דרום': 'Southern'  # Translate direction
    }
    return translation.get(field, field)


def restructure_data(tables_data):
    today = datetime.now().strftime('%d/%m/%Y')
    current_date = datetime.strptime(today, '%d/%m/%Y')
    restructured_data = {}

    for index, table_data in enumerate(tables_data):
        date = current_date.strftime('%d/%m/%Y')
        date_data = {}

        for row in table_data:
            hour = row.pop('')
            translated_row = {}
            for key, value in row.items():
                translated_key = translate_field_names(key)
                if translated_key:
                    if key == 'רוח' or key == 'סוואל':
                        numeric_value = ''.join(filter(str.isdigit, value))
                        unit = ''.join(filter(str.isalpha, value))
                        translated_value = f'{numeric_value}{unit}'
                    else:
                        translated_value = value.split()[0]
                    translated_row[translated_key] = translated_value

            date_data[hour] = translated_row

        restructured_data[date] = date_data
        current_date += timedelta(days=1)

    return restructured_data


def table_to_json(table):
    headers = []
    rows = []

    header_row = table.find('tr', class_='chart_header')
    if header_row:
        headers = [header.get_text(strip=True) for header in header_row.find_all('td')]

    data_rows = table.find_all('tr')
    for row in data_rows:
        if row == header_row:
            continue

        cells = [cell.get_text(strip=True) for cell in row.find_all('td')]
        row_data = dict(zip(headers, cells))
        rows.append(row_data)

    return rows


print(extract_waves())
