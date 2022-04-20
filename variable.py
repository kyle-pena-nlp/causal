from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

@dataclass(frozen = True, eq = True)
class Variable:
    name : str

    def __post_init__(self):
        if not self.name.strip():
            raise Exception("Variable name must be non-blank")

    def __lt__(self, other : 'Variable'):
        return self.name < other.name

    def __eq__(self, other : 'Variable'):
        return self.name == other.name

    def __str__(self):
        return self.name

    

    @staticmethod
    def parse(name):
        return Variable(name)