from dataclasses import dataclass
from typing import Tuple

from p import P
from rule import Rule


@dataclass(frozen = True, eq = True)
class Derivation:
    statement : P
    history : Tuple[Rule]

    def __str__(self):
        return "{} ({})".format(str(self.statement), "->".join(map(str,self.history)))
