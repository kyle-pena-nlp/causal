from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict, FrozenSet
from collections import Counter
from itertools import chain, combinations, product


from p import Variable, Expression, Product, Marginalization, P
from structural_equation import StructuralEquation
from graph import Graph
from derivation import Derivation
from rule import RuleI, RuleII, RuleIII
from util import maybe_parse, maybe_parse_frozenset

from argparse import ArgumentParser

def gen_frontdoor_adjustment_identifications(statement : Union[P,str], graph : Union[Graph,str], latents : Union[str,FrozenSet[Variable]]):
    
    # input normalization
    statement = maybe_parse(P, statement)
    graph = maybe_parse(Graph, graph)
    latents = maybe_parse_frozenset(Variable, latents)

    # todo: generalize here
    assert len(statement.Z) == 0
    assert len(statement.Y) == 1
    assert len(statement.do) == 1

    Y = next(iter(statement.Y))
    do = next(iter(statement.do))

    sufficient_mediator_sets = _gen_sufficient_mediator_sets(statement, graph, latents)

    for sufficient_mediator_set in sufficient_mediator_sets:

        outcome_to_mediator = P(Y = frozenset({Y}), do = frozenset({do}), Z = sufficient_mediator_set)
        iter_outcome_to_mediator_identifications = gen_backdoor_adjustment_identifications(outcome_to_mediator, graph, latents)

        mediator_to_treatment = P(Y = frozenset({Y}), do = frozenset({ do }))
        mediator_to_treatment_identifications = list(gen_backdoor_adjustment_identifications(mediator_to_treatment, graph, latents))

        for x in iter_outcome_to_mediator_identifications:
            for y in mediator_to_treatment_identifications:
                yield Product(frozenset({x,y}))

def _gen_sufficient_mediator_sets(statement, graph : Graph, latents):
    
    X = next(iter(statement.do))
    Y = next(iter(statement.Y))

    causal_paths = graph.causal_paths(X, Y)

    sufficient_blocker_sets = _gen_sufficient_adjustment_sets(causal_paths, latents)
    for sufficient_blocker_set in sufficient_blocker_sets:
        yield sufficient_blocker_set


def gen_backdoor_adjustment_identifications(statement : Union[P,str], graph : Union[Graph,str], latents : Union[str,FrozenSet[Variable]]):
    
    # input normalization
    statement = maybe_parse(P, statement)
    graph = maybe_parse(Graph, graph)
    latents = maybe_parse_frozenset(Variable, latents)
    
    # todo: generalize here
    assert len(statement.Z) == 0
    assert len(statement.Y) == 1
    assert len(statement.do) == 1
    
    Y = next(iter(statement.Y))
    do = next(iter(statement.do))
    
    sufficient_adjustment_sets = _gen_sufficient_adjustment_sets(Y,do,graph,latents)
    
    for sufficient_adjustment_set in sufficient_adjustment_sets:
        marginalized_statement = P(Y = frozenset({Y}), do = frozenset({do}), Z = sufficient_adjustment_set)
        derivation = statement_identifiable(marginalized_statement, graph)
        if derivation is not None:
            marginalization = _adjust_for(derivation.statement, sufficient_adjustment_set)
            yield marginalization


def _adjust_for(statement : P, adjustment_set : FrozenSet[Variable]):
    return Marginalization(Product(frozenset([statement, P(Y = adjustment_set)])), margins = adjustment_set)

# todo: sets of variables
def _gen_sufficient_adjustment_sets(Y : Variable, X : Variable, graph : Graph,latents : FrozenSet[Variable]):

    backdoor_paths = graph.backdoor_paths(X,Y)
    return _gen_blocker_sets(backdoor_paths, graph, latents, X, Y)


def _gen_blocker_sets(paths, graph : Graph, latents : FrozenSet[Variable], X : Variable, Y : Variable):

    # Get the list of all possible blockers for each path
    backdoor_path_blocker_lists = [ list(graph.path_blockers(path) - ({ X, Y }|latents)) for path in paths ]
    
    # Within each blocker list for a path, prioritize the blockers that most commonly co-occur amongst all paths
    # Thus when we do product(blocker_lists) we tend to generate the most economical blocker paths first
    blocker_ordering = [ blocker for (blocker,_) in Counter([blocker for blocker_list in backdoor_path_blocker_lists for blocker in blocker_list ]).most_common() ]
    for blocker_list in backdoor_path_blocker_lists:
        blocker_list.sort(key = lambda blocker: blocker_ordering.index(blocker))

    # Gen all unique combos of blockers that block all paths
    adjustment_sets = set()
    for blocker_list in product(*backdoor_path_blocker_lists):
        adjustment_set = frozenset(blocker_list)
        if adjustment_set in adjustment_sets:
            continue
        adjustment_sets.add(adjustment_set)
        sufficient = all(graph.path_is_blocked(path = path[0], path_arrows = path[1], blockers = adjustment_set) for path in paths)
        if sufficient:
            yield frozenset(adjustment_set)    

def statement_identifiable(statement : Union[str,P], graph : Union[Graph,str]) -> Derivation:
    statement = maybe_parse(P, statement)
    graph     = maybe_parse(Graph, graph)
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
    parser.add_argument("--graph", type = str, required = False, default = "X->Y;U->X;U->Y;V->X;V->Y")
    parser.add_argument("--statement", type = str, required = False, default = "P(Y|do(X))")
    parser.add_argument("--latents", type = str, required = False, default = "")
    args = parser.parse_args()

    for expression in gen_backdoor_adjustment_identifications(args.statement, args.graph, args.latents):
        print(expression)
