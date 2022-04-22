from variable import Variable
from typing import Union, Iterable, Any

ParseableAsVariableFrozenSet = Union[str,Variable,Iterable[Union[str,Variable]]]

def _ensure_is_frozen_set(x):
    if isinstance(x, Variable):
        return frozenset([ x ])
    elif isinstance(x, (list, tuple, set)):
        return frozenset(x)
    else:
        raise Exception("Could not make object of type '{}' into a frozen set".format(type(x)))

def _parsed(x : str, cls : type):
    if isinstance(x,cls):
        return x
    return getattr(cls,"parse")(x)

def _parsed_frozenset(x : Union[str,Any,Iterable[Union[str,Any]]], cls, sep = ","):
    if isinstance(x, str) and x.strip() == "":
        return frozenset()
    if isinstance(x, str) and sep not in x:
        return frozenset({ _parsed(x, cls) })
    elif isinstance(x,str) and sep in x:
        tokens = x.split(sep)
        return frozenset({ _parsed(token.strip(), cls) for token in tokens })
    elif isinstance(x, cls):
        return frozenset({ x })
    else:
        result = set()
        for x_ in x:
            result.add(_parsed(x_, cls))
        return frozenset(result)