from collections import namedtuple
from datetime import date

from dateutil.relativedelta import relativedelta

Price = namedtuple('Price', ['day', 'price'])

AssetState = namedtuple('Status', ['ticker', 'calculated', 'ratio',
                                   'positive'])

ModuleState = namedtuple('ModuleState', ['name', 'positive', 'states'])


class NoData(Exception):
    pass


def get_asset_state(db_manager, ticker, months):
    try:
        return _get_asset_state(db_manager, ticker, months)
    except NoData:
        return AssetState(ticker, False, 0, False)


def _get_asset_state(db_manager, ticker, months):
    end = date.today()
    start = end - relativedelta(months=months)

    item0 = fetch_ticker_on_date(db_manager, ticker, start)
    item1 = fetch_ticker_on_date(db_manager, ticker, end)

    p0 = item0.price
    p1 = item1.price
    ratio = 100.0 * (p1 - p0) / p0

    return AssetState(ticker, True, ratio, False)


def fetch_ticker_on_date(db_manager, ticker, dt):
    with db_manager.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
select p.day, p.close
from prices p
where p.identifier = %s 
and p.day between (%s + '-3 days'::interval) and (%s + '3 days'::interval)
order by p.day desc  
""", (ticker, dt, dt))
            row = cur.fetchone()
            if not row:
                raise NoData("no data for {} on {}".format(ticker, dt))

            return Price(row[0], row[1])


def get_reference(db_manager, modules, months):
    ticker = modules['default'][0]
    return get_asset_state(db_manager, ticker, months)


def get_module_state(name, states, default_state):
    is_positive = any([x.ratio > default_state.ratio and x.ratio > 0
                       for x in states])

    states = sorted(states, key=lambda x: -x.ratio)

    def prepare(state):
        return AssetState(
            state.ticker,
            state.calculated,
            state.ratio,
            state.ratio > default_state.ratio and state.ratio > 0
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
