from datetime import datetime, timedelta

def get_date_in_the_past(days):
    '''Returns date x days in the past from today'''
    return datetime.strftime(datetime.now() - timedelta(days), '%Y-%m-%d')

def get_date_object(date_string):
    '''Returns datetime object representation of the given date in the format yyyy-mm-dd'''
    return datetime.strptime(date_string, '%Y-%m-%d')