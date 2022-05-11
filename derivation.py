from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen = True, eq = True)
class Derivation:
    statement : 'P'
    history : Tuple['StatementRule']

    def __str__(self):
        return "{} ({})".format(str(self.statement), "->".join(map(str,self.history)))
