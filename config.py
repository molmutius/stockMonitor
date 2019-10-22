import configparser
import ast

config = configparser.ConfigParser()
config.read('config.ini')

email_smtp_server = config['alarm']['email_smtp_server']
email_sender = config['alarm']['email_sender']
email_password = config['alarm']['email_password']
email_recepients = ast.literal_eval(config['alarm']['email_recepients'])

default_min_rsi = int(config['thresholds']['min_rsi'])
default_max_rsi = int(config['thresholds']['max_rsi'])

data_quandl_api_key = config['data']['quandl_api_key']
data_iex_api_key = config['data']['iex_api_key']
use_database = config['data']['use_database']

history_output_file = config['history']['output_file']

def custom_rsi(symbol):
    '''Returns custom rsi as array if present for that symbol. Raises KeyError if not present.'''
    return ast.literal_eval(config['thresholds']['custom_rsis'])[symbol]