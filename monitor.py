"""
TODO: Abstract data access
TODO: Time series to sql
TODO: Add 'web' data access type (web crawler), which also creates pandas dataframe (https://www.ariva.de/basf-aktie/historische_kurse)
TODO: Webserver: representation and control of data
"""

import threading
import csv

import config
import technical_indicators
from stock import Stock
from emailer import Emailer
from data_access import DataAccess

emailer = Emailer()
quandl_stocks = []
DAYS = 100

# Append and get are each atomic ops according to python doc, so
# no synchronization required when accessed from different threads
alarms = []

def send_alarm(alarm_symbols):
    if (len(alarm_symbols) > 0):
        message = ''
        for alarm_symbol in alarm_symbols:
            message += ("RSI: " + str(f'{alarm_symbol.get_latest_rsi():2.2f}') + ". " +             
                "Exceeded since: " + str(alarm_symbol.get_rsi_exceeded_since_date()) +
                "\t" + alarm_symbol.name + " (" + alarm_symbol.symbol + ") exceeded treshold.\n")
        print (message + "\n")
        subject = "Stock Monitor: Symbols exceeded their thresholds"
        for recepient in config.email_recepients:
            print('Sending alarm mail to ' + recepient)
            emailer.send_mail(recepient, subject, message)

def evaluate_quandl_stocks():
    print('Started evaluating QUANDL stocks ...')

    # Needs to be created from within the same thread
    data_access = DataAccess()

    # First create a list of stocks to query
    with open('quandl_fse_stocks.csv', newline='') as csvfile:
        file_reader = csv.reader(csvfile, delimiter=',')
        next(file_reader)
        for row in file_reader:
            name = row[1]
            symbol = 'FSE/' + row[0]
            min_rsi = config.default_min_rsi
            max_rsi = config.default_max_rsi
            try:
                min_rsi = config.custom_rsi(symbol)[0]
                max_rsi = config.custom_rsi(symbol)[1]
                print(f'Using custom RSI values ({min_rsi}, {max_rsi}) for {symbol}')
            except KeyError:
                print(f'Using default values for RSI thresholds for {symbol}')
            stock = Stock(DAYS, name, symbol, data_access, min_rsi, max_rsi)
            quandl_stocks.append(stock)

    for stock in quandl_stocks:
        last_rsi = stock.get_latest_rsi()
        print(f'RSI for {stock.symbol}: {str(last_rsi)} \n')
        if (last_rsi > 0 and (last_rsi < stock.min_rsi or last_rsi > stock.max_rsi)):
            alarms.append(stock)
        #indicators_to_plot = [technical_indicators.Indicators.EMA10, technical_indicators.Indicators.SMA10]
        #stock.draw_plot(indicators_to_plot)

quandl_thread = threading.Thread(target=evaluate_quandl_stocks)
quandl_thread.start()
quandl_thread.join()

send_alarm(alarms)