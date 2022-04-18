from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

from variable import Variable
from structural_equation import StructuralEquation
from graph import Graph
from derivation import Derivation
from p import P
from rule import Rule

MAX_VISITED = 100

def identifiable(statement : P, graph : Graph) -> Derivation:
    return identifiable_BFS(statement, graph)

def admissible_derivations(derivation, graph):

    derivations = set()
    statement = derivation.statement
    history = derivation.history

    # Rule I: Go through candidates of which z to eliminate
    for z in statement.Z:
        Z_ = { z }
        W_ = statement.Z - Z_
        rule = Rule('I', Y =statement.Y, doX = statement.do, Z = Z_, W = W_)
        if rule.applicable(graph):
            derivations.add(rule.apply(statement), history + (rule,))

    # Rule II: Go through candidates of which x_hat to convert to conditionals
    for doZ in statement.do:
        doZ_ = { doZ }
        W_ = statement.Z
        rule = Rule('II', Y = statement.Y, doX = statement.do - doZ_, doZ = doZ_, W = W_)
        if rule.applicable(graph):
            derivations.add(rule.apply(statement), history + (rule,))

    # Rule III: Go through candidates of which x_hat to convert to condition on x
    for doZ in statement.do:
        doZ_ = { doZ }
        W_ = statement.Z
        rule = Rule('III', Y = statement.Y, doX = statement.do - doZ_, doZ = doZ_, W = W_)
        if rule.applicable(graph):
            derivations.add(rule.apply(statement), history + (rule,))

    # Rule Iinv:

    # Rule IIinv:

    # Rule IIIinv:

    # TODO: law of total probability, etc.

    return derivations

def identifiable_BFS(statement : P, graph : Graph):
    derivation = Derivation(statement, history = ())
    queue, visited = [derivation], { derivation }
    while len(queue) > 0 and len(visited) < MAX_VISITED:
        derivation_ = queue.pop()
        if hat_free(derivation_.statement):
            return derivation_
        else:
            for next_derivation in admissible_derivations(derivation_, graph):
                if next_derivation.statement not in visited:
                    visited.add(next_derivation.statement)
                    queue.append(next_derivation)
    return None

def hat_free(statement):
    return len(statement.do) == 0