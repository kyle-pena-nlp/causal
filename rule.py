
from abc import ABC, abstractmethod, abstractclassmethod
from dataclasses import dataclass
from typing import FrozenSet, Union, Tuple, Dict, Iterable
from collections import Counter
from structural_equation import StructuralEquation
from graph import Graph
from p import P
from p import Variable, P, Quotient, Product, Marginalization, Expression



@dataclass(frozen = True, eq = True)
class StatementRule(ABC):

    @abstractmethod
    def is_compatible_with(self, graph : Graph) -> bool:
        """
            Tests if the application of the rule is compatible with the CI assumptions implied by the graph
        """
        pass

    @abstractmethod
    def apply(self, statement : P) -> P:
        """
            transforms the statement according to the rule
        """
        pass

    @abstractclassmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable['StatementRule']:
        """
            Generates (*possibly* graph compatible) instances of the rule
        """
        pass

    @abstractmethod
    def __str__(self):
        pass


@dataclass(frozen = True, eq = True)
class RuleI(StatementRule):
    """
        Drop Z from the conditioning set in the statement:
        P(Y|do(X),Z,W)
    """

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    Z: FrozenSet[Variable]
    W : FrozenSet[Variable]

    def mutilate(self, graph : Graph) -> Graph:
        X = self.doX
        return graph.orphan(X)

    def is_compatible_with(self, graph : Graph) -> bool:
        Y = self.Y
        Z = self.Z
        W = self.W
        return self.mutilate(graph)._conditionally_independent(Y, Z, W)

    def apply(self, statement : P) -> P:
        return P(Y = statement.Y, do = statement.do, Z = statement.Z - self.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable[StatementRule]:
        for z in statement.Z:
            Z_ = { z }
            W_ = statement.Z - Z_
            rule = cls(Y =statement.Y, doX = statement.do, Z = Z_, W = W_)
            if rule.is_compatible_with(graph):
                yield rule

    def __str__(self):
        return "Rule I"

@dataclass(frozen = True, eq = True)
class RuleIinv(StatementRule):
    """
        Introduce Z into the conditioning set when Rule I applies to the resulting statement
    """
    
    Y: FrozenSet[Variable]
    doX : FrozenSet[Variable]
    Z : FrozenSet[Variable]
    W : FrozenSet[Variable]

    def is_compatible_with(self, graph: Graph) -> bool:
        ruleI = RuleI(Y = self.Y, doX = self.doX, Z = self.Z, W = self.W)
        return ruleI.is_compatible_with(graph)

    def apply(self, statement : P):
        return P(Y = statement.Y, do = statement.do, Z = statement.Z | self.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable[StatementRule]:
        candidates = graph.variables - ( statement.Y | statement.do | statement.Z )
        for candidate in candidates:
            candidate = frozenset({candidate})
            rule = cls(Y = statement.Y, doX = statement.do, Z = candidate, W = statement.Z)
            if rule.is_compatible_with(graph):
                yield rule

    def __str__(self):
        return "Rule I inverse"


@dataclass(frozen = True, eq = True)
class RuleII(StatementRule):

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    doZ : FrozenSet[Variable]
    W : FrozenSet[Variable]   

    def mutilate(self, graph : Graph) -> Graph:
        X = self.doX
        Z = self.doZ
        return graph.orphan(X).bereave(Z)

    def is_compatible_with(self, graph : Graph) -> bool:
        Y = self.Y
        Z = self.doZ
        W = self.W       
        X = self.doX 
        return self.mutilate(graph)._conditionally_independent(Y, Z, W | X)

    def apply(self, statement : P) -> P:
        return P(Y = statement.Y, do = statement.do - self.doZ, Z = statement.Z | self.doZ)

    @classmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable[StatementRule]:
        for doZ in statement.do:
            doZ_ = { doZ }
            W_ = statement.Z
            rule = cls(Y = statement.Y, doX = statement.do - doZ_, doZ = doZ_, W = W_)
            if rule.is_compatible_with(graph):
                yield rule

    def __str__(self):
        return "Rule II"

@dataclass(frozen = True, eq = True)
class RuleIIinv(StatementRule):
    """
        Promote Z into the intervention set when RuleII applies to the statement produced by this rule
    """
    
    Y: FrozenSet[Variable]
    doX : FrozenSet[Variable]
    Z : FrozenSet[Variable]
    W: FrozenSet[Variable]

    def is_compatible_with(self, graph : Graph) -> bool:
        ruleII = RuleII(Y = self.Y, doX = self.doX, doZ = self.Z, W = self.W)
        return ruleII.is_compatible_with(graph)

    def apply(self, statement : P) -> P:
        return P(Y = statement.Y, do = statement.do | self.Z, Z = statement.Z - self.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable[StatementRule]:
        for Z in statement.Z:
            Z = frozenset({ Z })
            rule = cls(Y = statement.Y, doX = statement.do, Z = Z, W = statement.Z - Z)
            if rule.is_compatible_with(graph):
                yield rule

    def __str__(self):
        return "Rule II inverse"
    

@dataclass(frozen = True, eq = True)
class RuleIII(StatementRule):

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    doZ : FrozenSet[Variable]
    W : FrozenSet[Variable]    

    def mutilate(self, graph : Graph) -> Graph:
        X = self.doX
        Z = self.doZ
        W = self.W
        return graph.orphan(X).orphan(Z - graph.orphan(X).ancestors(W))

    def is_compatible_with(self, graph : Graph):
        Y = self.Y
        Z = self.doZ
        X = self.doX
        W = self.W
        return self.mutilate(graph)._conditionally_independent(Y, Z, X | W)

    def apply(self, statement : P):
        return P(Y = statement.Y, do = statement.do - self.doZ, Z = statement.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable[StatementRule]:
        for doZ in statement.do:
            doZ_ = { doZ }
            W_ = statement.Z
            rule = cls(Y = statement.Y, doX = statement.do - doZ_, doZ = doZ_, W = W_)
            if rule.is_compatible_with(graph):
                yield rule

    def __str__(self):
        return "Rule III"

@dataclass(frozen = True, eq = True)
class RuleIIIinv(StatementRule):

    Y: FrozenSet[Variable]
    doX : FrozenSet[Variable]
    doZ : FrozenSet[Variable]
    W : FrozenSet[Variable]

    def is_compatible_with(self, graph : Graph):
        return RuleIII(Y = self.Y, doX = self.doX, doZ = self.doZ, W = self.W).is_compatible_with(graph)

    def apply(self, statement : P):
        return P(Y = statement.Y, do = self.doX | self.doZ, Z = statement.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable[StatementRule]:
        for do_Z_ in graph.variables - {statement.Y | statement.do | statement.Z}:
            do_Z_ = frozenset({ do_Z_ })
            rule = cls(Y = statement.Y, doX = statement.do, doZ = do_Z_, W = statement.Z)
            if rule.is_compatible_with(graph):
                yield rule


# TODO: Rules over expressions, including adjustments, baye's rules, mediations, etc.


@dataclass(frozen = True, eq = True)
class ExpressionRule(ABC):

    @abstractmethod
    def is_compatible_with(self, graph : Graph) -> bool:
        """
            Tests if the application of the rule is compatible with the CI assumptions implied by the graph
        """
        pass

    @abstractmethod
    def apply(self, expression : P) -> Expression:
        """
            transforms the statement according to the rule
        """
        pass

    @abstractclassmethod
    def bindings(cls, expression : Expression, graph : Graph) -> Iterable['StatementRule']:
        """
            Generates (*possibly* graph compatible) instances of the rule
        """
        pass

@dataclass(frozen = True, eq = True)
class FactorizeRule:
    # TODO: apply Baye's rule to factorize statements according to the graph
    pass

@dataclass(frozen = True, eq = True)
class AdjustmentRule(ExpressionRule):


    adjustment_set : FrozenSet[Variable]
    
    # You can always compute an adjustment
    def is_compatible_with(self, graph: Graph, latents : FrozenSet[Variable]) -> bool:
        return not (self.adjustment_set & latents)

    def apply(self, statement : P) -> Expression:
        return Marginalization(Product([statement, P(Y = self.adjustment_set)]), self.adjustment_set)

@dataclass(frozen = True, eq = True)
class MediationRule(ExpressionRule):
    pass