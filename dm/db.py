import psycopg2


def get_database(**kwargs):
    return psycopg2.connect(**kwargs)


class Manager:
    def __init__(self, settings):
        self.__settings = settings

    def connect(self):
        return get_database(**self.__settings)
