from dataclasses import dataclass, field
from p import P, Marginalization, Product, Variable, Quotient
from graph import Graph
from typing import FrozenSet, List, Union
# This algorithm is taken from Ilya Shpister's paper

@dataclass(frozen = True, eq = True)
class Hedge:
    F : FrozenSet[Variable]
    F_ : FrozenSet[Variable]

@dataclass(frozen = True, eq = True)
class IDFailure(Exception):
    witness : Hedge
    def __init__(self, witness):
        self.witness = witness

# TODO: some kind of derivation

def IDC(Y : FrozenSet[Variable],
    X : FrozenSet[Variable],
    Z : FrozenSet[Variable],
    graph : Graph,
    latents : FrozenSet[Variable]):

    V = graph.variables - latents
    p = P(V)

    try:
        return IDC_rec(Y, X, Z, p, graph, latents)
    except IDFailure as fail:
        return fail.hedge

def IDC_rec(Y : FrozenSet[Variable],
    X : FrozenSet[Variable],
    Z : FrozenSet[Variable],
    p : P,
    graph : Graph,
    latents : FrozenSet[Variable]):
    
    graph_ = graph.orphan(X).bereave(Z)
    z = next([z for z in Z if graph_.conditionally_independent(Y, {z}, X | Z - {z})], None)
    if z is not None:
        return IDC_rec(Y, X | { z }, Z - { z }, p, graph, latents)
    else:
        # I don't understand this step
        P_ = ID_rec(Y | Z, X, p, graph, latents)
        denom = Marginalization(P_, Y)
        return Quotient(P_, denom)

def ID(Y: FrozenSet[Variable],
    X : FrozenSet[Variable],
    graph : Graph,
    latents : FrozenSet[Variable]):

    V = graph.variables - latents
    p = P(V)
    
    try:
        return ID_rec(Y, X, p, graph, latents)
    except IDFailure as fail:
        return fail.hedge

def ID_rec(Y: FrozenSet[Variable], 
        X : FrozenSet[Variable], 
        p : P, 
        graph : Graph,
        latents : FrozenSet[Variable]):

    V = graph.variables - latents
    anY = graph.ancestors(Y,True)
    anY_doX = graph.orphan(X).ancestors(Y,True)

    # Line 1 - marginalize out non-Y variable if X is the empty set
    if len(X) == 0:
        return Marginalization(P(V), V - Y)
    
    # Line 2 - marginalize out non-ancestors of Y if they exist
    elif len(V - anY) > 0:
        X_ = X & anY
        P_ = Marginalization(P, V - anY)        
        # I'm pretty sure that the an(Y) subgraph preserves all bidirected edges from A to B in an(Y) anyway,
        # but just to be safe I'm invoking the bidirected edge preserving version of the sub_graph method
        # (What I really need is a graph representation which includes latents and/or bidirected edges explicitly, but that's a big refactor)
        graph_ = graph.bidirected_edge_preserving_sub_graph(anY)
        return ID_rec(Y, X_, P_, graph_)
    
    # Line 3
    W = (V - X) - anY_doX
    if len(W) != 0:
        X_ = X | W
        return ID_rec(P(Y, X_, P, graph))

    # Line 4
    C_of_G_less_X = graph.sub_graph(V - X).maximal_C_components(latents)
    if len(C_of_G_less_X) > 1:
        terms = []
        for c_component in C_of_G_less_X:
            Y_ = c_component
            X_ = V - c_component
            term = ID_rec(Y_, X_, P, graph)
            terms.append(term)
        product = Product(terms)
        return Marginalization(product, V - (Y|X))
    elif len(C_of_G_less_X) == 1:
        G = graph.variables - latents
        (S,) = C_of_G_less_X
        C_of_G = graph.maximal_C_components(latents)
        if C_of_G == frozenset({ G }):
            raise IDFailure(Hedge(G, S))
        elif S in C_of_G:
            terms = []
            for V_i in S:
                y_ = frozenset({ V_i })
                z_ = graph.parents(y_)
                statement = P(y_, Z = z_)
                terms.append(statement)
            product = Product(terms)
            return Marginalization(product, S - Y)
        else:
            S_ = next([ S.issubset(C) for C in C_of_G ], None)
            # if S_ is None ???
            X_ = X & S_
            terms = []
            for V_i in S_:
                y_ = frozenset({ V_i })
                z_ = (graph.parents(y_) & S_) | (graph.parents(y_) - S_)
                statement = P(y_, Z = z_)
                terms.append(statement)
            product = Product(terms)
            return ID_rec(Y, X_, product, graph.bidirected_edge_preserving_sub_graph(S_))

    """
        # Proof sketch.
        # The subgraph of the ancestors of Y in G will not eliminate any bidirected edges between ancestors of Y which are present in G.
        # If there was some bidirected edge missing, it would imply that either:
        #   1. An unobserved variable in the bidirected edge was excluded or...
        #   2. The begining or end of the bidirected edge was excluded or...
        #   3. A collider of unobserved variables was turned into a non-collider
        #   (3) is impossible - excluding varaibles does not change the direction of arrows.
        #   (2) is impossible - as both the beginning and the end of the bidirected edge are in an(Y) by assumption
        #   (1) is impossible. 
        #       By contradiction. sketch. 
        #       Suppose that there is some unobserved variable U in a bidirected edge from A to B which is not an ancestor of A and not an ancestor of B (meaning it could possibly not be in anc(Y))
                This means that there is some node U' which is part of an inverted fork on the portion of the bidirected edge from A to U
                    (there must be an inverted fork to interrupt the ancestor path to U, otherwise there must be a collider which is not allowed on a bidirected path)
                This also means that there is some node U'' which is part of an inverted fork on the portion of the bidirected edge from U to B
                    (there must be an inverted fork, otherwise there must be a collider)
                This implies there is a collider somewhere between U' and U'' on the bidirected edge, which is a contradiction.
                
        #  


    """