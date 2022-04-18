from dataclasses import dataclass
from typing import Tuple

from p import P
from rule import Rule


@dataclass 
class Derivation:
    statement : P
    history : Tuple[Rule]
