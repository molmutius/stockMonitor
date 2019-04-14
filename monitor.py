"""
TODO: Abstract data access
TODO: Time series to sql
TODO: Add 'web' data access type (web crawler), which also creates pandas dataframe (https://www.ariva.de/basf-aktie/historische_kurse)
TODO: Webserver: representation and control of data
"""

import threading
import csv
import time

import config
import technical_indicators
from stock import Stock
from emailer import Emailer

emailer = Emailer()
quandl_stocks = []
DAYS = 100

# Append and get are each atomic ops according to python doc, so
# no synchronization required when accessed from different threads
alarms = []

def send_alarm(alarm_symbols):
    if (len(alarm_symbols) > 0):
        for recepient in config.email_recepients:
            print('Sending alarm mail to ' + recepient)
            message = ''
            for alarm_symbol in alarm_symbols:
                message += "Ticker: " + alarm_symbol.name + " (" + alarm_symbol.symbol + ") exceeded treshold. RSI: " + str(f'{alarm_symbol.get_latest_rsi():2.2f}') + "\n"
            print (message + "\n")
            subject = "Stock Monitor: Symbols exceeded their thresholds"
            emailer.send_mail(recepient, subject, message)

def evaluate_quandl_stocks():
    print('Started evaluating QUANDL stocks ...')

    with open('quandl-fse-stocks.csv', newline='') as csvfile:
        print('Building stock list ...')
        file_reader = csv.reader(csvfile, delimiter=',')
        next(file_reader)
        for row in file_reader:
            name = row[1]
            symbol = 'FSE' + row[0]
            stock = Stock(DAYS, name, symbol)
            quandl_stocks.append(stock)

    for stock in quandl_stocks:
        last_rsi = stock.get_latest_rsi()
        print('RSI for ' + stock.symbol + ': ' + str(last_rsi) + '\n')
        if (last_rsi > 0 and (last_rsi < config.default_min_rsi or last_rsi > config.default_max_rsi)):
            alarms.append(stock)
        #indicators_to_plot = [technical_indicators.Indicators.EMA10]
        #stock.draw_plot(indicators_to_plot)

quandl_thread = threading.Thread(target=evaluate_quandl_stocks)
quandl_thread.start()
quandl_thread.join()

send_alarm(alarms)