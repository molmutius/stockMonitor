from datetime import datetime, timedelta

def get_date_in_the_past(days):
    '''Returns date x days in the past from today'''
    return datetime.strftime(datetime.now() - timedelta(days), '%Y-%m-%d')