from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict, FrozenSet
from collections import Counter
from itertools import chain, combinations


from variable import Variable
from structural_equation import StructuralEquation
from graph import Graph
from derivation import Derivation
from expression import Expression
from p import P
from product import Product
from marginalization import Marginalization
from rule import RuleI, RuleII, RuleIII
from util import _parsed

from argparse import ArgumentParser

def statement_identifiable(statement : Union[str,P], graph : Union[Graph,str]) -> Derivation:
    statement = _parsed(statement,P)
    graph     = _parsed(graph,Graph)
    _assert_statement_compatible_with_graph(statement, graph)
    return _statement_identifiable_BFS(statement, graph)

def _statement_identifiable_BFS(statement, graph : Graph):
    derivation = Derivation(statement, history = ())
    queue, visited = [derivation], { derivation }
    while len(queue) > 0:
        derivation_ = queue.pop()
        if (derivation_.statement.hat_free()):
            return derivation_
        else:
            for r,s in _statement_valid_rule_applications(derivation_, graph):
                if s not in visited:
                    visited.add(s)
                    queue.append(Derivation(s, derivation_.history + (r,)))
    return None

def _statement_valid_rule_applications(derivation, graph):
    statement = derivation.statement
    return  [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleI.bindings(statement, graph)   if rule_instance.is_compatible_with(graph) ] +\
            [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleII.bindings(statement, graph)  if rule_instance.is_compatible_with(graph) ] +\
            [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleIII.bindings(statement, graph) if rule_instance.is_compatible_with(graph) ] 




def _assert_statement_compatible_with_graph(p : P, graph : Graph):
    statement_variables = p.Y | p.do | p.Z
    if not statement_variables.issubset(graph.variables):
        raise Exception("Some variables appearing in statement do not appear in graph.")

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("--graph", type = str, required = True)
    parser.add_argument("--p", type = str, required = True)
    args = parser.parse_args()

    print(statement_identifiable(args.p, args.graph))
