from p import P, Marginalization, Product, Expression, Variable
from graph import Graph
from typing import FrozenSet
# This algorithm is taken from Ilya Shpister's paper

class IDFailure(Exception):
    witness : Expression
    def __init__(self, witness):
        self.witness = witness

def ID(statement : P, graph : Graph):

    V = graph.variables
    Y = statement.Y
    X = statement.do

    # Line 1
    if len(statement.do) == 0:
        return Marginalization(P(V), V - Y)
    # Line 2
    elif len(V - graph.ancestors(Y)) > 0:
        # TODO: how to represent marginalized distribution
        return ID(P(Y, X | graph.ancestors(Y)), graph.ancestor_graph(Y))
    
    # Line 3
    W = (V - X) - graph.orphan(X).ancestors(Y)
    if len(W) == 0:
        return ID(P(Y,X | W, graph))

    # Line 4
    CtreeX = Ctree(graph.variables - X, graph)
    if len(CtreeX) > 1:
        terms = []
        for Si in CtreeX:
            Si = frozenset({Si})
            terms.append(ID(P(Si, V - Si, graph)))
        product = Product(terms)
        return Marginalization(product, V - (Y|X))
    elif len(CtreeX) == 1:
        S = list(CtreeX)[0]
        # Line 5
        CtreeG = Ctree(graph.variables, graph)
        if CtreeG == graph.variables:
            raise IDFailure(S)
        # Line 6
        if S in CtreeG:
            # ???
            return None
        # Line 7
        if CtreeX.isin(CtreeG):
            return ID(P(Y, X | CtreeG), thing, CtreeG)

