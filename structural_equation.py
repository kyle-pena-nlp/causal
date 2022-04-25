from dataclasses import dataclass
from typing import FrozenSet, Union, Tuple, Dict
from collections import Counter
from p import Variable

@dataclass(frozen = True, eq = True)
class StructuralEquation:
    X : FrozenSet[Variable]
    Y : Variable

    #def __post_init__(self):
    #    self.X = _ensure_is_frozen_set(self.X)

    @staticmethod
    def parse(eq : str):
        if "->" in eq:
            LHS,RHS = eq.split("->")
        elif "<-" in eq:
            RHS,LHS = eq.split("<-")
        else:
            raise Exception("Must contain either <- or ->")
        RHSs = RHS.split(",")
        if len(RHSs) != 1:
            raise Exception("Structural Equation must have one and only one result")
        LHSs = LHS.split(",")
        X = frozenset([ Variable(x.strip()) for x in LHSs ])
        Y = Variable(RHS.strip())
        return StructuralEquation(X, Y)

    def __str__(self):
        params = ",".join(sorted(map(str,self.X)))
        if len(self.X) > 1:
            return "({})->{}".format(params, self.Y)
        else:
            return "{}->{}".format(params, self.Y)