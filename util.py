from typing import Union, Iterable, Any
from parseable import Parseable
from p import Expression

def maybe_parse(klass, thing):
    if isinstance(thing, klass):
        return thing
    elif isinstance(thing, str):
        return klass.parse(thing)
    else:
        raise Exception("Cannot maybe_parse - thing was not {} or str".format(klass))


def maybe_parse_frozenset(klass, thing):
    if isinstance(thing, str):
        return frozenset(Parseable.parse_list(klass, thing))
    elif isinstance(thing, (tuple,set,list,frozenset)):
        return frozenset(thing)
    elif isinstance(thing, klass):
        return frozenset({ thing })
    else:
        raise Exception("Cannot maybe_parse_frozenset - thing was not tuple,set,list,frozenset or str")