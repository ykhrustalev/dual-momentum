from collections import namedtuple

Price = namedtuple('Price', ['day', 'price'])

AssetState = namedtuple('Status', ['ticker', 'calculated', 'ratio',
                                   'positive'])

ModuleState = namedtuple('ModuleState', ['name', 'positive', 'states'])


def get_asset_state(db_manager, ticker, months):
    prices = fetch_ticker_monthly(db_manager, ticker)
    if len(prices) < months:
        return AssetState(ticker, False, 0, False)

    p0 = prices[-months].price
    p1 = prices[-1].price
    ratio = 100.0 * (p0 - p1) / p0

    return AssetState(ticker, True, ratio, False)


def fetch_ticker_monthly(db_manager, ticker):
    with db_manager.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
select latest_day as day,
       p.close    as price
from (
       select max(day) latest_day, identifier
       from prices
       where identifier = %s
       group by date_trunc('month', day), identifier
     ) days
       join prices p
            on p.day = days.latest_day and p.identifier = days.identifier
order by latest_day desc
""", (ticker,))
            rows = cur.fetchall()
            return [Price(x[0], x[1]) for x in rows]


def get_reference(db_manager, modules, months):
    ticker = modules['default'][0]
    return get_asset_state(db_manager, ticker, months)


def get_module_state(name, states, default_state):
    is_positive = any([x.ratio > default_state.ratio and x.ratio > 0
                       for x in states])

    states = sorted(states, key=lambda x: -x.ratio)

    def prepare(state):
        is_positive = state.ratio > default_state.ratio and state.ratio > 0
        return AssetState(
            state.ticker, state.calculated, state.ratio, is_positive
        )

    states = [prepare(x) for x in states]

    return ModuleState(name, is_positive, states)


def get_modules_states(db_manager, modules, months):
    default_state = get_reference(db_manager, modules, months)

    res = {}

    for module, tickers in sorted(modules.items()):
        states = [
            get_asset_state(db_manager, ticker, months) for ticker in tickers
        ]

        res[module] = get_module_state(
            module,
            states,
            default_state
        )

    return res


def _sign(v):
    return "+" if v else "-"


def draw_asset_states(states):
    res = []
    for state in states:
        if not state.calculated:
            line = "!{}(not calculated)".format(state.ticker)
        else:
            line = "{}{}({:.2f}%)".format(
                _sign(state.positive),
                state.ticker,
                state.ratio
            )

        res.append(line)

    return res


def draw_module_state(name, state3, state6, state9, state12):
    header = '{} is {}3/{}6/{}9/{}12'.format(
        name.upper(),
        _sign(state3.positive),
        _sign(state6.positive),
        _sign(state9.positive),
        _sign(state12.positive),
    )

    print("{}\n 3m: {}\n 6m: {}\n 9m: {}\n 12m: {}\n".format(
        header,
        '; '.join(draw_asset_states(state3.states)),
        '; '.join(draw_asset_states(state6.states)),
        '; '.join(draw_asset_states(state9.states)),
        '; '.join(draw_asset_states(state12.states)),
    ))


def do_suggest(conf, db_manager):
    modules = conf['modules']

    states12 = get_modules_states(db_manager, modules, 12)
    states9 = get_modules_states(db_manager, modules, 9)
    states6 = get_modules_states(db_manager, modules, 6)
    states3 = get_modules_states(db_manager, modules, 3)

    for name in sorted(modules.keys()):
        draw_module_state(
            name,
            states3[name],
            states6[name],
            states9[name],
            states12[name],
        )
