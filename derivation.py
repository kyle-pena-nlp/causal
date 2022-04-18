from dataclasses import dataclass
from typing import Tuple

from p import P
from rule import Transformation


@dataclass 
class Derivation:
    statement : P
    history : Tuple[Transformation]
