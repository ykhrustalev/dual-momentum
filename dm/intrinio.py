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
    end = date(today.year, today.month, 1) - relativedelta(days=1)
    start = end - relativedelta(months=months)
    return start, end


PriceItem = namedtuple('PriceItem', ['day', 'open', 'close'])


def parse_item(item):
    return PriceItem(
        parse(item['date']).date(),
        int(item['open'] * 100),
        int(item['close'] * 100),
    )


class Client:
    DEFAULT_URL = 'https://api.intrinio.com'

    def __init__(self, session, base_url=DEFAULT_URL):
        self.__session = session
        self.__base_url = base_url

    def __url(self, path):
        return "{}{}".format(self.__base_url, path)

    def get_monthly_prices(self, ticker, months):
        start, end = get_range(months)

        url = self.__url('/prices')
        query = {"identifier": ticker,
                 "start_date": start.isoformat(),
                 "end_date": end.isoformat(),
                 "frequency": "monthly"}
        r = self.__session.get(url, params=query)
        r.raise_for_status()

        data = r.json()
        assert data['total_pages'] == 1

        items = data['data']
        return [parse_item(item) for item in items]


def get_client(api_key):
    return Client(get_session(api_key))
