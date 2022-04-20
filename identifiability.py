from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

from variable import Variable
from structural_equation import StructuralEquation
from graph import Graph
from derivation import Derivation
from p import P
from rule import RuleI, RuleII, RuleIII
from util import _parsed

MAX_VISITED = 100

def identifiable(statement : Union[P,str], graph : Union[Graph,str]) -> Derivation:
    statement = _parsed(statement,P)
    graph     = _parsed(graph,Graph)
    return identifiable_BFS(statement, graph)


def valid_rule_applications(derivation, graph):
    statement = derivation.statement
    return  [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleI.bindings(statement, graph)   if rule_instance.is_compatible_with(graph) ] +\
            [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleII.bindings(statement, graph)  if rule_instance.is_compatible_with(graph) ] +\
            [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleIII.bindings(statement, graph) if rule_instance.is_compatible_with(graph) ]
            


def identifiable_BFS(statement : P, graph : Graph):
    derivation = Derivation(statement, history = ())
    queue, visited = [derivation], { derivation }
    while len(queue) > 0 and len(visited) < MAX_VISITED:
        derivation_ = queue.pop()
        if hat_free(derivation_.statement):
            return derivation_
        else:
            for r,s in valid_rule_applications(derivation_, graph):
                if s not in visited:
                    visited.add(s)
                    queue.append(Derivation(s, derivation_.history + (r,)))
    return None

def hat_free(statement):
    return len(statement.do) == 0


if __name__ == "__main__":

    graph = Graph(
        {
            Variable("X"),
            Variable("Y")
        },
        structural_equations = {
            StructuralEquation({ Variable("X") }, Variable("Y"))
        }
    )

    statement = P({ Variable("Y")}, do = { Variable("X")}, Z = {})


    print(identifiable(statement, graph))