from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

@dataclass
class Variable:
    name : str
    observed: bool

    def __eq__(self, other : 'Variable'):
        return self.name == other.name