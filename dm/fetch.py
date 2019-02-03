from dm import intrinio


def handle_ticker(db_manager, intrinio_client, ticker):
    items = intrinio_client.get_monthly_prices(ticker, months=12)

    with db_manager.connect() as conn:
        with conn.cursor() as cur:
            for item in items:
                cur.execute(
                    """
INSERT INTO prices (identifier, day, "open", "close")
VALUES (%s, %s, %s, %s)
ON CONFLICT (identifier, day)
DO UPDATE 
SET ("open", "close")
    = (EXCLUDED.open, EXCLUDED.close)
                    """,
                    (ticker, item.day, item.open, item.close)
                )


def do_fetch(conf, db_manager):
    client = intrinio.get_client(conf['intrinio']['api_key'])

    modules = conf['modules']

    for section in modules.values():
        for ticker in section:
            print('fetching', ticker)
            handle_ticker(db_manager, client, ticker)
