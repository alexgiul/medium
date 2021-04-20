# Load the Pandas libraries with alias 'pd'
import pandas as pd
import requests
import os
import csv

_ALPHA_VANTAGE_API_KEY = '1B12WIHQVF242FLA'
_ALPHA_VANTAGE_API_URL = "https://www.alphavantage.co/query?"
_ALPHA_VANTAGE_TIMESERIES = 'TIME_SERIES_DAILY_ADJUSTED'

if not os.path.exists("C:\\Dati\\projects\\medium\\data"):
    os.makedirs("C:\\Dati\\projects\\medium\\data")


# https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&outputsize=full&apikey=demo
def retrieve_data(symbol, output_format='json', output_size='compact'):
    """
    up to 5 API requests per minute and 500 requests per day
    output_size: compact (last 100 bar), full( 20 years)
    """
    response = requests.get("%sfunction=%s&symbol=%s&apikey=%s&datatype=%s&outputsize=%s" % (
        _ALPHA_VANTAGE_API_URL, _ALPHA_VANTAGE_TIMESERIES, symbol, _ALPHA_VANTAGE_API_KEY, output_format, output_size
    ))
    if response.status_code != 200:
        print("Abort Status code: " + str(response.status_code))
        exit(1)

    if 'json' in output_format:
        json_response = response.json()
        if "Error Message" in json_response:
            raise ValueError(json_response["Error Message"])
        elif "Information" in json_response:
            raise ValueError(json_response["Information"])
        return json_response
    else:
        lines = response.text.splitlines()
        header = [h.strip() for h in lines[0].split(',')]  # read and trim header row
        csv_response = csv.DictReader(lines[1:], fieldnames=header)
        if not csv_response:
            raise ValueError(
                'Error getting data from the api, no return was given.')
        return csv_response

def convert_data(timestamp, row):
    retValue = {}
    retValue['adjusted_close'] = float(row['5. adjusted close'])
    retValue['close'] = float(row['4. close'])
    retValue['high'] = float(row['2. high'])
    retValue['low'] = float(row['3. low'])
    retValue['open'] = float(row['1. open'])
    retValue['volume'] = int(row['6. volume'])
    retValue['timestamp'] = int(timestamp.replace("-", ""))
    return retValue


# Read data from file 'filename.csv'
# (in the same directory that your python process is based)
# Control delimiters, rows, column names with read_csv (see later)
df = pd.read_csv("C:\\Dati\\projects\\medium\\ccc.csv", sep=";")
# Preview the first 5 lines of the loaded data
for index, row in df.iterrows():
    ticker = row['ticker']

#data = retrieve_data('SPY', output_format='csv', output_size='compact')
data = retrieve_data('SPY', output_format='csv', output_size='full')

f = open('C:\\Dati\\projects\\medium\\data\\SPY.csv', 'w', newline='\n', encoding='utf-8')

# http://zetcode.com/python/csv/

with f:
    writer = csv.writer(f)

    header = False
    for row in data:
        if header==False:
            writer.writerow(row)
            header=True
        writer.writerow(row.values())
