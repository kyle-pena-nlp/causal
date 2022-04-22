from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter
import re

@dataclass(frozen = True, eq = True)
class Variable:
    name : str

    def __post_init__(self):
        if not self.name.strip():
            raise Exception("Variable name must be non-blank")
        elif re.findall("[\s\]\[\*;,\(\)]",self.name):
            raise Exception("Name cannot contain whitespace or any of these characters: []();,*")

    def __lt__(self, other : 'Variable'):
        return self.name < other.name

    def __eq__(self, other : 'Variable'):
        return self.name == other.name

    def __str__(self):
        return self.name    

    @staticmethod
    def parse(name):
        return Variable(name)