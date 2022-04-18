from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

from variable import Variable

@dataclass 
class P:
    # outcomes
    Y : set[Variable]
    # interventions
    do : set[Variable]
    # conditioning set
    Z : set[Variable]