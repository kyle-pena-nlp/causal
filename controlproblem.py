from p import P, Variable
from graph import Graph
from typing import FrozenSet

def gen_solve_control_problem(Y : FrozenSet[Variable], X: FrozenSet[Variable], graph : Graph, latents : FrozenSet[Variable]):
    
    for admissible_ordering in graph.gen_admissible_orderings(X):
        pass
        # TODO: generating action-avoiding blocking sets
                