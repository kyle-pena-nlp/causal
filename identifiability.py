from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict, FrozenSet
from collections import Counter
from itertools import chain, combinations, product

from parseable import Parseable
from p import Variable, Expression, Product, Marginalization, P
from structural_equation import StructuralEquation
from graph import Graph
from derivation import Derivation
from rule import RuleI, RuleII, RuleIII
from argparse import ArgumentParser


def statement_with_backdoor_adjustment_identifiable(statement : Union[str,P], graph : Union[Graph,str], latents : FrozenSet[Variable]) -> Derivation:
    pass

def statement_do_forward_identifiable(statement : Union[str,P], graph : Union[Graph,str]) -> Derivation:
    """
        Is a statement identifiable using simply the 3 forward rules of do-calculus
        (No inverse of the rules, no marginalization tricks, etc.)
    """
    statement = P.parse(statement)
    graph     = Graph.parse(graph)
    _assert_statement_compatible_with_graph(statement, graph)
    return _statement_do_forward_identifiable_BFS(statement, graph)

def _statement_do_forward_identifiable_BFS(statement, graph : Graph):
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

def _statement_valid_rule_applications(derivation, graph, latents):
    statement = derivation.statement
    return  [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleI.bindings(statement, graph, latents) ] +\
            [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleII.bindings(statement, graph, latents) ] +\
            [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleIII.bindings(statement, graph, latents) ] 

def _assert_statement_compatible_with_graph(p : P, graph : Graph):
    statement_variables = p.Y | p.do | p.Z
    if not statement_variables.issubset(graph.variables):
        raise Exception("Some variables appearing in statement do not appear in graph.")

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("--graph", type = str, required = False, default = "X->Y")
    parser.add_argument("--statement", type = str, required = False, default = "P(Y|do(X))")
    parser.add_argument("--latents", type = str, required = False, default = "")
    parser.add_argument("--method", type = str, default = "do_forward_identifiable")
    args = parser.parse_args()

    graph = Graph.parse(args.graph)
    statement = P.parse(args.statement)
    latents = Parseable.parse_list(Variable, args.latents)
    method = args.method

    if method == "do_forward_identifiable":
        derivation = statement_do_forward_identifiable(statement, graph)
        print(derivation)

