
from abc import ABC, abstractmethod, abstractclassmethod
from dataclasses import dataclass
from typing import FrozenSet, Union, Tuple, Dict, Iterable
from collections import Counter
from structural_equation import StructuralEquation
from graph import Graph
from p import P
from p import Variable, P, Quotient, Product, Marginalization



@dataclass(frozen = True, eq = True)
class StatementRule(ABC):

    @abstractmethod
    def mutilate(self, graph : Graph) -> Graph:
        pass

    @abstractmethod
    def is_compatible_with(self, graph : Graph) -> bool:
        pass

    @abstractmethod
    def apply(self, statement : P) -> P:
        pass

    @abstractclassmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable['StatementRule']:
        pass


@dataclass(frozen = True, eq = True)
class BayesRule(StatementRule):

    Z : FrozenSet[Variable]

    def apply(self, statement : P):
        joint = P(Y = statement.Y | self.Z, do = statement.do, Z = statement.Z - self.Z) 
        conditional = P(Y = statement.Z, do = frozenset(), Z = frozenset())
        return Quotient(Product(frozenset({ joint })), Product(frozenset({ conditional })))

    @abstractclassmethod
    def bindings(cls, statement : P, graph : Graph) -> Iterable['StatementRule']:
        pass

@dataclass(frozen = True, eq = True)
class RuleI(StatementRule):

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    Z: FrozenSet[Variable]
    W : FrozenSet[Variable]
    
    #def __post_init__(self):
    #    self.Y = _ensure_is_frozen_set(self.Y)
    #    self.doX = _ensure_is_frozen_set(self.doX)
    #    self.Z = _ensure_is_frozen_set(self.Z)        
    #    self.W = _ensure_is_frozen_set(self.W)

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
            yield rule

    def __str__(self):
        return "Rule I"

@dataclass(frozen = True, eq = True)
class RuleII(StatementRule):

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    doZ : FrozenSet[Variable]
    W : FrozenSet[Variable]

    #def __post_init__(self):
    #    self.Y = _ensure_is_frozen_set(self.Y)
    #    self.doX = _ensure_is_frozen_set(self.doX)
    #    self.doZ = _ensure_is_frozen_set(self.doZ)        
    #    self.W = _ensure_is_frozen_set(self.W)    

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
            yield rule

    def __str__(self):
        return "Rule II"

@dataclass(frozen = True, eq = True)
class RuleIII(StatementRule):

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    doZ : FrozenSet[Variable]
    W : FrozenSet[Variable]

    #def __post_init__(self):
    #    self.Y = _ensure_is_frozen_set(self.Y)
    #    self.doX = _ensure_is_frozen_set(self.doX)
    #    self.doZ = _ensure_is_frozen_set(self.doZ)        
    #    self.W = _ensure_is_frozen_set(self.W)        

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
            yield rule

    def __str__(self):
        return "Rule III"