from functools import partial
from toolz import keyfilter, compose, curry, reduceby, merge
from pymysql.err import ProgrammingError


def pick(whitelist, d):
    return keyfilter(lambda k: k in whitelist, d)


@curry
def sum_by(key, iterand):
    return compose(sum, partial(map, lambda x: x.get(key)))(iterand)


def with_report_error_check(data_fn):
    def fn(*args, **kwargs):
        try:
            return data_fn(*args, **kwargs)
        except ProgrammingError:
            return []

    return fn


def key_by(key, items):
    return reduceby(key, lambda a, x: merge(a, x), items, {})


mapf = compose(list, map)
filterf = compose(list, filter)
