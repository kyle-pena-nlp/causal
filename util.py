from typing import Union, Iterable, Any
from parseable import Parseable
from p import Expression

def flatten(iterable_of_iterables):
    return [ item for iterable in iterable_of_iterables for item in iterable ]