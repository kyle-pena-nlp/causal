from dataclasses import dataclass
from typing import FrozenSet
from p import Variable
from graph import Graph


class CComponent:
    F: FrozenSet[Variable]

class CTree:
    F: FrozenSet[Variable]

class CForest:
    F : FrozenSet[Variable]

    def root(self, graph : Graph):
        pass

    def compatible_with(self, graph : Graph, latents : FrozenSet[Variable]):
        """
            Does this collection of varaibles form a CForest for this graph?
        """
        pass

class Hedge:
    F  : FrozenSet[Variable]
    F_ : FrozenSet[Variable]

    def compatible_with(self, graph : Graph, latents : FrozenSet[Variable]):
        pass