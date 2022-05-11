
from abc import ABC, abstractmethod, abstractclassmethod
from dataclasses import dataclass
from typing import FrozenSet, Union, Tuple, Dict, Iterable
from collections import Counter
from structural_equation import StructuralEquation
from graph import Graph
from p import P
from p import Variable, P, Quotient, Product, Marginalization, Expression
from derivation import Derivation
from argparse import ArgumentParser
from parseable import Parseable

@dataclass(frozen = True, eq = True)
class StatementRule(ABC):

    @abstractmethod
    def is_compatible_with(self, graph : Graph, latents : FrozenSet[Variable]) -> bool:
        """
            Tests if the application of the rule is compatible with the CI assumptions implied by the graph
        """
        pass

    @abstractmethod
    def apply(self, statement : Expression) -> Expression:
        """
            transforms the statement according to the rule
        """
        pass

    @abstractclassmethod
    def bindings(cls, statement : Expression, graph : Graph, latents : FrozenSet[Variable]) -> Iterable['StatementRule']:
        """
            Generates (*possibly* graph compatible) instances of the rule
        """
        pass

    @abstractmethod
    def __str__(self):
        pass


@dataclass(frozen = True, eq = True)
class RuleI(StatementRule):
    """
        Drop Z from the conditioning set in the statement:
        P(Y|do(X),Z,W)
    """

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    Z: FrozenSet[Variable]
    W : FrozenSet[Variable]

    def mutilate(self, graph : Graph) -> Graph:
        X = self.doX
        return graph.orphan(X)

    def is_compatible_with(self, graph : Graph, latents : FrozenSet[Variable]) -> bool:
        Y = self.Y
        Z = self.Z
        W = self.W
        return self.mutilate(graph).conditionally_independent(Y, Z, W)

    def apply(self, statement : P) -> P:
        return P(Y = statement.Y, do = statement.do, Z = statement.Z - self.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]) -> Iterable[StatementRule]:
        for z in statement.Z:
            Z_ = { z }
            W_ = statement.Z - Z_
            rule = cls(Y =statement.Y, doX = statement.do, Z = Z_, W = W_)
            if rule.is_compatible_with(graph, latents):
                yield rule

    def __str__(self):
        return "Rule I"

@dataclass(frozen = True, eq = True)
class RuleIinv(StatementRule):
    """
        Introduce Z into the conditioning set when Rule I applies to the resulting statement
    """
    
    Y: FrozenSet[Variable]
    doX : FrozenSet[Variable]
    Z : FrozenSet[Variable]
    W : FrozenSet[Variable]

    def is_compatible_with(self, graph: Graph, latents : FrozenSet[Variable]) -> bool:
        ruleI = RuleI(Y = self.Y, doX = self.doX, Z = self.Z, W = self.W)
        return ruleI.is_compatible_with(graph, latents)

    def apply(self, statement : P):
        return P(Y = statement.Y, do = statement.do, Z = statement.Z | self.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]) -> Iterable[StatementRule]:
        candidates = graph.variables - ( statement.Y | statement.do | statement.Z )
        for candidate in candidates:
            candidate = frozenset({candidate})
            rule = cls(Y = statement.Y, doX = statement.do, Z = candidate, W = statement.Z)
            if rule.is_compatible_with(graph, latents):
                yield rule

    def __str__(self):
        return "Rule I inverse"


@dataclass(frozen = True, eq = True)
class RuleII(StatementRule):

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    doZ : FrozenSet[Variable]
    W : FrozenSet[Variable]   

    def mutilate(self, graph : Graph) -> Graph:
        X = self.doX
        Z = self.doZ
        return graph.orphan(X).bereave(Z)

    def is_compatible_with(self, graph : Graph, latents : FrozenSet[Variable]) -> bool:
        Y = self.Y
        Z = self.doZ
        W = self.W       
        X = self.doX 
        return self.mutilate(graph).conditionally_independent(Y, Z, W | X)

    def apply(self, statement : P) -> P:
        return P(Y = statement.Y, do = statement.do - self.doZ, Z = statement.Z | self.doZ)

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]) -> Iterable[StatementRule]:
        for doZ in statement.do:
            doZ_ = { doZ }
            W_ = statement.Z
            rule = cls(Y = statement.Y, doX = statement.do - doZ_, doZ = doZ_, W = W_)
            if rule.is_compatible_with(graph, latents):
                yield rule

    def __str__(self):
        return "Rule II"

@dataclass(frozen = True, eq = True)
class RuleIIinv(StatementRule):
    """
        Promote Z into the intervention set when RuleII applies to the statement produced by this rule
    """
    
    Y: FrozenSet[Variable]
    doX : FrozenSet[Variable]
    Z : FrozenSet[Variable]
    W: FrozenSet[Variable]

    def is_compatible_with(self, graph : Graph, latents : FrozenSet[Variable]) -> bool:
        ruleII = RuleII(Y = self.Y, doX = self.doX, doZ = self.Z, W = self.W)
        return ruleII.is_compatible_with(graph, latents)

    def apply(self, statement : P) -> P:
        return P(Y = statement.Y, do = statement.do | self.Z, Z = statement.Z - self.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]) -> Iterable[StatementRule]:
        for Z in statement.Z:
            Z = frozenset({ Z })
            rule = cls(Y = statement.Y, doX = statement.do, Z = Z, W = statement.Z - Z)
            if rule.is_compatible_with(graph, latents):
                yield rule

    def __str__(self):
        return "Rule II inverse"
    

@dataclass(frozen = True, eq = True)
class RuleIII(StatementRule):

    Y : FrozenSet[Variable]
    doX : FrozenSet[Variable]
    doZ : FrozenSet[Variable]
    W : FrozenSet[Variable]    

    def mutilate(self, graph : Graph) -> Graph:
        X = self.doX
        Z = self.doZ
        W = self.W
        return graph.orphan(X).orphan(Z - graph.orphan(X).ancestors(W))

    def is_compatible_with(self, graph : Graph, latents : FrozenSet[Variable]):
        Y = self.Y
        Z = self.doZ
        X = self.doX
        W = self.W
        return self.mutilate(graph).conditionally_independent(Y, Z, X | W)

    def apply(self, statement : P):
        return P(Y = statement.Y, do = statement.do - self.doZ, Z = statement.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]) -> Iterable[StatementRule]:
        for doZ in statement.do:
            doZ_ = { doZ }
            W_ = statement.Z
            rule = cls(Y = statement.Y, doX = statement.do - doZ_, doZ = doZ_, W = W_)
            if rule.is_compatible_with(graph, latents):
                yield rule

    def __str__(self):
        return "Rule III"

@dataclass(frozen = True, eq = True)
class RuleIIIinv(StatementRule):

    Y: FrozenSet[Variable]
    doX : FrozenSet[Variable]
    doZ : FrozenSet[Variable]
    W : FrozenSet[Variable]

    def is_compatible_with(self, graph : Graph, latents : FrozenSet[Variable]):
        return RuleIII(Y = self.Y, doX = self.doX, doZ = self.doZ, W = self.W).is_compatible_with(graph, latents)

    def apply(self, statement : P):
        return P(Y = statement.Y, do = self.doX | self.doZ, Z = statement.Z)

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]) -> Iterable[StatementRule]:
        for do_Z_ in graph.variables - {statement.Y | statement.do | statement.Z}:
            do_Z_ = frozenset({ do_Z_ })
            rule = cls(Y = statement.Y, doX = statement.do, doZ = do_Z_, W = statement.Z)
            if rule.is_compatible_with(graph, latents):
                yield rule


# TODO: Get the rule class hierarchy worked out
@dataclass(frozen = True, eq = True)
class BackdoorAdjustmentRule(StatementRule):
    
    Y : FrozenSet[Variable]
    do : FrozenSet[Variable]
    Z : FrozenSet[Variable]
    adjustment_set : FrozenSet[Variable]

    def is_compatible_with(self, graph : Graph, latents : FrozenSet[Variable]):
        if self.adjustment_set not in graph.gen_sufficient_backdoor_adjustment_sets(self.do, self.Y, latents = latents, current_adjustment_set = self.Z):
            return False
        return not self.adjustment_set & (latents | self.Y | self.do | self.Z)

    def apply(self, statement : P) -> Expression:
        adjustment_set = self.adjustment_set
        terms = [ statement.condition_on(adjustment_set), P(Y = adjustment_set) ]
        return Marginalization(Product(terms), adjustment_set)

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]) -> Iterable[StatementRule]:
        treatment = statement.do
        exposure = statement.Y
        current_adjustment_set = statement.Z
        for sufficient_backdoor_adjustment_set in graph.gen_sufficient_backdoor_adjustment_sets(treatment, exposure, latents, current_adjustment_set):
            if not sufficient_backdoor_adjustment_set:
                # If the sufficient backdoor adjustment is the empty set, don't generate a binding (no point in performing the adjustment)
                continue
            yield cls(Y = statement.Y, do = statement.do, Z = statement.Z, adjustment_set = sufficient_backdoor_adjustment_set)

    def __str__(self):
        return "Backdoor Adjustment on {}".format(",".join(map(str,sorted(self.adjustment_set))))

# TODO: get the rule class hierarchy worked out
@dataclass(frozen = True, eq = True)
class StatementForwardIdentifiabilityRule(StatementRule):

    Y: FrozenSet[Variable]
    do: FrozenSet[Variable]
    Z: FrozenSet[Variable]
    derivation : Tuple[StatementRule]
    
    def is_compatible_with(self, graph : Graph, latents : FrozenSet[Variable]):
        return all(rule.is_compatible_with(graph, latents) for rule in self.derivation)

    def apply(self, statement : P) -> P:
        for rule in self.derivation:
            statement = rule.apply(statement)
        return statement

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]):
        for derivation in StatementForwardIdentifiabilityRule._gen_derivations(statement, graph, latents):
            yield cls(Y = statement.Y, do = statement.do, Z = statement.Z, derivation = derivation.history)

    @staticmethod
    def _gen_derivations(statement : P, graph : Graph, latents : FrozenSet[Variable]) -> Iterable[Derivation]:
        derivation = Derivation(statement, history = ())
        queue, visited = [derivation], { derivation }
        while len(queue) > 0:
            derivation_ = queue.pop()
            if (derivation_.statement.hat_free()):
                yield derivation_
            else:
                for r,s in StatementForwardIdentifiabilityRule._statement_valid_rule_applications(derivation_, graph, latents):
                    if s not in visited:
                        visited.add(s)
                        queue.append(Derivation(s, derivation_.history + (r,)))

    @staticmethod
    def _statement_valid_rule_applications(derivation : Derivation, graph : Graph, latents : FrozenSet[Variable]):
        statement = derivation.statement
        return  [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleI.bindings(statement, graph, latents) ] +\
                [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleII.bindings(statement, graph, latents) ] +\
                [ (rule_instance,rule_instance.apply(statement)) for rule_instance in RuleIII.bindings(statement, graph, latents) ] 


    def __str__(self):
        return "Forward Identifiability: {}".format(", ".join(map(str,self.derivation.history)))


class InterventionAsCanonicalStatement(StatementRule):

    Y: FrozenSet[Variable]
    do: FrozenSet[Variable]
    Z : FrozenSet[Variable]

    def apply(self, statement : P, graph: Graph, latents : FrozenSet[Variable]):
        graph = graph.orphan(self.do)
        factorization = graph.joint_distribution(Z = self.do | self.Z)
        Marginalization(factorization, )


# TODO: get the rule class hierarchy worked out
@dataclass(frozen = True, eq = True)
class FrontdoorAdjustmentRule(StatementRule):

    Y : FrozenSet[Variable]
    do : FrozenSet[Variable]
    mediation_set : FrozenSet[Variable]

    def is_compatible_with(self, graph: Graph, latents: FrozenSet[Variable]) -> bool:

        any_unintercepted_directed_paths = len(graph.causal_paths(self.do, self.Y, self.mediation_set)) > 0
        if any_unintercepted_directed_paths:
            return False

        # There are no unblocked backdoor paths from doX to the mediation set
        any_unblocked_backdoor_paths = len(graph.backdoor_paths(self.do, self.mediation_set)) > 0
        if any_unblocked_backdoor_paths:
            return False

        # All backdoor paths from the mediation to the outcome are blocked by X
        any_unblocked_backdoor_paths = len(graph.backdoor_paths(self.mediation_set, self.Y, self.do)) > 0
        if any_unblocked_backdoor_paths:
            return False

        return True


    def apply(self, statement: Expression) -> Expression:

        # to match the notation given on pg. 83
        Y = self.Y
        X = self.do
        Z = self.mediation_set

        margin_1 = Marginalization(P(Y = Z, Z = X), margins = Z)
        margin_2 = Marginalization(Product(terms = [P(Y = Y, Z = X | Z), P(Y = X)]), margins = X)
        return Product(terms = [margin_1, margin_2])     

    @classmethod
    def bindings(cls, statement : P, graph : Graph, latents : FrozenSet[Variable]):

        # Not sure how to do perform a backdoor adjustment with P(Y|do(x),Z)
        if len(statement.Z) > 0:
            return

        for sufficient_mediation_set in graph.gen_sufficient_mediation_set(X = statement.do, Y = statement.Y, latents = latents, current_adjustment_set = statement.Z):
            rule = cls(Y = statement.Y, do = statement.do, mediation_set = sufficient_mediation_set)
            if rule.is_compatible_with(graph, latents):
                yield rule

    def __str__(self):
        pass

if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("--statement", type = str, default = "P(Y|do(X))")
    parser.add_argument("--graph", type = str, default = "X->Y;U->X;U->Y")
    parser.add_argument("--method", type = str, default = "backdoor_adjustment")
    parser.add_argument("--latents", type = str, default = "")
    args = parser.parse_args()

    statement = P.parse(args.statement)
    graph = Graph.parse(args.graph)
    latents = Parseable.parse_list(Variable, args.latents)
    method = args.method

    if method == "backdoor_adjustment":
        for rule in BackdoorAdjustmentRule.bindings(statement, graph, latents = latents):
            print(rule.apply(statement))
    elif method == "frontdoor_adjustment":
        for rule in FrontdoorAdjustmentRule.bindings(statement, graph, latents = latents):
            print(rule.apply(statement))
    elif method == "identifiability":
        for rule in StatementForwardIdentifiabilityRule.bindings(statement, graph, latents):
            print(rule.apply(statement))