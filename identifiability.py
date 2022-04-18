from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

from variable import Variable
from structural_equation import StructuralEquation
from graph import Graph
from derivation import Derivation
from p import P

MAX_VISITED = 100

def identifiable(statement : P, graph : Graph) -> Derivation:
    return identifiable_BFS(statement, graph)

def neighbor_derivations(derivation, graph):
    pass

def identifiable_BFS(statement : P, graph : Graph):
    derivation = Derivation(statement, history = ())
    queue, visited = [derivation], { derivation }
    while len(queue) > 0 and len(visited) < MAX_VISITED:
        derivation_ = queue.pop()
        if hat_free(derivation_.statement):
            return derivation_
        else:
            for neighbor_derivation in neighbor_derivations(derivation_, graph):
                if neighbor_derivation.statement not in visited:
                    visited.add(neighbor_derivation.statement)
                    queue.append(neighbor_derivation)
    return None

def hat_free(statement):
    return len(statement.do) == 0