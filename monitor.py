"""
TODO: Add 'web' data access type (web crawler), which also creates pandas dataframe (https://www.ariva.de/basf-aktie/historische_kurse)
TODO: Webserver: representation and control of data
"""

import threading
import csv
import signal, sys, os

import config
import technical_indicators
from datetime import datetime
from stock import Stock
from emailer import Emailer
from data_access import DataAccess
from history import History

emailer = Emailer()
history = History()
DAYS = 60

# Append and get are each atomic ops according to python doc, so
# no synchronization required when accessed from different threads
alarms_above = []
alarms_below = []

fse_stocks = []
sandp500_stocks = []
iex_stocks = []

def handler(signum, frame):
    print ('Bye')
    sys.exit()

def send_alarm(alarms_below, alarms_above):
    today = datetime.strftime(datetime.now(), '%Y-%m-%d')
    total_stocks = len(fse_stocks) + len(sandp500_stocks) + len(iex_stocks)
    history.add_date(today, len(alarms_below), len(alarms_above), total_stocks)
    history.save_plot(config.history_output_file)
    message = f'RSI Stockmonitor from {today}.\n'
    message += '\n'
    message += f'Total stocks: {total_stocks}\n'
    message += f'Stocks below min RSI threshold: {len(alarms_below)} == {get_percentage(total_stocks, len(alarms_below))}%\n'
    message += f'Stocks above max RSI threshold: {len(alarms_above)} == {get_percentage(total_stocks, len(alarms_above))}%\n'
    message += '\n'
    for symbol in alarms_below:
        message += get_mail_text(symbol)
    message += '\n'
    for symbol in alarms_above:
        message += get_mail_text(symbol)
    print ("\n" + message)
    subject = "Stock Monitor: Symbols exceeded their thresholds"
    for recepient in config.email_recepients:
        print('Sending alarm mail to ' + recepient)
        emailer.send_mail(recepient, subject, message, config.history_output_file)

def get_mail_text(symbol):
    text = ''
    text += "RSI: " + str(f'{symbol.get_latest_rsi():2.2f}') + ". "
    text += f'Exceeded since: {str(symbol.get_rsi_exceeded_since_date())}'
    text += f'\tSymbol: {symbol.name} ({symbol.symbol})'
    text += '\n'
    return text

def get_percentage(total, part):
    if total == 0:
        return 0
    return f'{(part/total)*100:2.2f}'

def evaluate_sandp500_stocks():
    print('Started evaluating STOOQ.com stocks ...', flush=True)
    data_access = DataAccess('sandp500')
    global sandp500_stocks
    sandp500_stocks = evaluate_stocks('stooq', 'sandp500.csv', data_access)

def evaluate_fse_stocks():
    print('Started evaluating QUANDL stocks ...', flush=True)
    data_access = DataAccess('quandl_fse_stocks')
    global fse_stocks
    fse_stocks = evaluate_stocks('quandl', 'quandl_fse_stocks.csv', data_access)

def evaluate_iex_stocks():
    print('Started evaluating IEX stocks ...', flush=True)
    os.environ["IEX_API_KEY"] = config.data_iex_api_key
    data_access = DataAccess('sandp_top_100')
    global iex_stocks
    iex_stocks = evaluate_stocks('iex', 'sandp_top_100.csv', data_access)

def evaluate_stocks(remote_source, csv_file, data_access):
    output_list = []
    # First create a list of stocks to query
    with open(csv_file, newline='') as csvfile:
        file_reader = csv.reader(csvfile, delimiter=',')
        # Skip the csv header
        next(file_reader)
        for row in file_reader:
            name = row[1]
            if remote_source == 'quandl':
                symbol = 'FSE/' + row[0]
            elif remote_source == 'stooq':
                symbol = row[0] + '.US'
            elif remote_source == 'iex':
                symbol = row[0]
            min_rsi = config.default_min_rsi
            max_rsi = config.default_max_rsi
            try:
                min_rsi = config.custom_rsi(symbol)[0]
                max_rsi = config.custom_rsi(symbol)[1]
                print(f'{symbol}: Using custom RSI values ({min_rsi}, {max_rsi})', flush=True)
            except KeyError:
                print(f'{symbol}: Using default values for RSI thresholds for', flush=True)
            stock = Stock(DAYS, name, symbol, data_access, remote_source, min_rsi, max_rsi)
            output_list.append(stock)

    # Calculate RSI values for all stocks
    for stock in output_list:
        last_rsi = stock.get_latest_rsi()
        print(f'RSI for {stock.symbol}: {str(last_rsi)} \n', flush=True)
        if (last_rsi > 0):
            if (last_rsi < stock.min_rsi):
                alarms_below.append(stock)
            if (last_rsi > stock.max_rsi):
                alarms_above.append(stock)
        #indicators_to_plot = [technical_indicators.Indicators.EMA10, technical_indicators.Indicators.SMA10]
        #stock.draw_plot(indicators_to_plot)

    return output_list

signal.signal(signal.SIGINT, handler)

iex_thread = threading.Thread(target=evaluate_iex_stocks)
iex_thread.start()

fse_thread = threading.Thread(target=evaluate_fse_stocks)
fse_thread.start()

#sandp500_thread = threading.Thread(target=evaluate_sandp500_stocks)
#sandp500_thread.start()

iex_thread.join()
fse_thread.join()
#sandp500_thread.join()

alarms_below = sorted(alarms_below, key=lambda stock: stock.last_rsi)
alarms_above = sorted(alarms_above, key=lambda stock: stock.last_rsi)
send_alarm(alarms_below, alarms_above)