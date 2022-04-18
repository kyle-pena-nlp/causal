from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

from variable import Variable


@dataclass
class StructuralEquation:
    X : Set[Variable]
    Y : Variable
