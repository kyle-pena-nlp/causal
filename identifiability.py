from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict, FrozenSet
from collections import Counter
from itertools import chain, combinations, product


from p import Variable, Expression, Product, Marginalization, P
from structural_equation import StructuralEquation
from graph import Graph
from derivation import Derivation
from rule import RuleI, RuleII, RuleIII
from util import _parsed

from argparse import ArgumentParser


def backdoor_adjustment_identifiable(statement : P, graph : Union[Graph,str], latents : FrozenSet[Variable]):
    assert len(statement.Z) == 0
    Y = statement.Y
    do = statement.do
    sufficient_adjustment_sets = _gen_sufficient_adjustment_sets(Y,do,graph,latents)
    for sufficient_adjustment_set in sufficient_adjustment_sets:
        marginalized_statement = P(Y = Y, do = do, Z = sufficient_adjustment_set)
        derivation = statement_identifiable(marginalized_statement, graph)
        if derivation is not None:
            marginalization = Marginalization(derivation.statement, margins = sufficient_adjustment_set)
            yield marginalization


def frontdoor_adjustment_identifiable(statement : P, graph : Union[Graph,str], latents : FrozenSet[Variable]):
    # find all paths from Y to X
    # for each path, see if each direct causal effect is identifiable via backdoor adjustment
    # when a path from Y to X is complete, yield a solution
    pass


def _gen_sufficient_adjustment_sets(Y : FrozenSet[Variable],X : FrozenSet[Variable], graph : Graph,latents : FrozenSet[Variable]):

    # Get all backdoor paths
    paths = graph.backdoor_paths(X,Y)

    # Get the list of all blockers for each path
    blocker_lists = [ list(graph.path_blockers(path) - (X|Y|latents)) for path in paths ]
    
    # Within each blocker list for  apth, put the blockers that most commonly co-occur as blockers in other paths first
    # Thus when we do product(blocker_lists) we tend to generate the most economical blocker paths first
    blocker_ordering = [ blocker for (blocker,count) in Counter([blocker for blocker_list in blocker_lists for blocker in blocker_list ]).most_common() ]
    for blocker_lists in blocker_lists:
        blocker_set.sort(key = lambda blocker: blocker_ordering.index(blocker))
    
    # Gen all unique combos of blockers that block all paths
    adjustment_sets = set()
    for blocker_set in product(*blocker_lists):
        adjustment_set = set(blocker_set)
        if adjustment_set in adjustment_sets:
            continue
        adjustment_sets.add(adjustment_set)
        sufficient = graph.conditionally_independent(Y,X,adjustment_set)
        if sufficient:
            yield frozenset(adjustment_set)


def statement_identifiable(statement : Union[str,P], graph : Union[Graph,str]) -> Derivation:
    statement = P.parse(statement) if isinstance(statement,str) else statement
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
