
from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

from variable import Variable
from structural_equation import StructuralEquation
from graph import Graph
from p import P

@dataclass
class Rule:

    # I, II, III, Iinv, IIinv, IIIinv
    rule : str

    # antecedent
    Y : Set[Variable]
    doX : Set[Variable]
    doZ : Set[Variable]
    Z: Set[Variable]
    W : Set[Variable]


    def mutilate(self, graph : Graph, X : Set[Variable], Z : Set[Variable], W : Set[Variable]) -> Graph:
        if self.rule in ("I", "Iinv"):
            return graph.orphan(X)
        elif self.rule in ("II", "IIinv"):
            return graph.orphan(X).bereave(Z)
        elif self.rule in ("III", "IIIinv"):
            return graph.orphan(X).orphan(Z - graph.ancestors(W))
        else:
            raise Exception("Unknown transformation rule: '{}'".format(self.rule))

    def applicable(self, graph : Graph):
        Y = self.Y
        Z = self.doZ + self.Z # The Z's will be in one or the other depending on the rule, so just add them up
        X = self.doX
        W = self.W
        graph = self.mutilate(graph, X, Z, W)
        return graph.cond_ind(Y, Z, X + W)

    def apply(self, statement : P):
        # Drop something from the conditional
        if self.rule == "I":
            return P(Y = statement.Y, do = statement.do, Z = statement.Z - self.Z)
        # Convert an intervention to a conditional
        elif self.rule == "II":
            return P(Y = statement.Y, do = statement.do - self.doZ, Z = statement.Z + self.doZ)
        # Drop an intervention
        elif self.rule == "III":
            return P(Y = statement.Y, do = statement.do - self.doZ, Z = statement.Z)
        # Add something to the conditional
        elif self.rule == "Iinv":
            return P(Y = statement.Y, do = statement.do, Z = statement.Z + self.Z)
        # Convert a conditional to an intervention
        elif self.rule == "IIinv":
            return P(Y = statement.Y, do = statement.do + self.doZ, Z = statement.Z - self.doZ)
        # Add an intervention
        elif self.rule == "IIIinv":
            return P(Y = statement.Y, do = statement.do + self.doZ, Z = statement.Z)
        else:
            raise Exception("Unknown transformation rule: '{}'".format(self.rule))