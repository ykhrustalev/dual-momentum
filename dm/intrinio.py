from collections import namedtuple
from datetime import date

import requests
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


def get_session(api_key):
    s = requests.Session()
    s.headers['Authorization'] = 'Bearer {}'.format(api_key)
    return s


def get_range(months):
    today = date.today()
    start = today - relativedelta(months=months + 1)
    return start, today


PriceItem = namedtuple('PriceItem', ['day', 'open', 'close'])


def parse_item(item):
    return PriceItem(
        parse(item['date']).date(),
        int(item['open'] * 100),
        int(item['close'] * 100),
    )


class Client:
    DEFAULT_URL = 'https://api-v2.intrinio.com'

    def __init__(self, session, base_url=DEFAULT_URL):
        self.__session = session
        self.__base_url = base_url

    def __url(self, path):
        return "{}{}".format(self.__base_url, path)

    def get_monthly_prices(self, ticker, months):
        start, end = get_range(months)

        url = self.__url('/securities/{}/prices'.format(ticker))
        query = {"start_date": start.isoformat(),
                 "end_date": end.isoformat(),
                 "frequency": "daily"}

        return list(iterate(self.__session, url, query))


def iterate(session, url, query):
    while True:
        r = session.get(url, params=query)
        r.raise_for_status()
        data = r.json()

        items = data['stock_prices']
        for item in items:
            yield parse_item(item)

        next_page = data.get('next_page')
        if next_page:
            query['next_page'] = next_page
        else:
            return


def get_client(api_key):
    return Client(get_session(api_key))
