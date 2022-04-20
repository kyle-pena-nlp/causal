from dataclasses import dataclass
from typing import FrozenSet, Union, Tuple, Dict
from collections import Counter
from variable import Variable
from util import _ensure_is_frozen_set
import re

@dataclass(frozen = True, eq = True)
class P:
    # outcomes
    Y : FrozenSet[Variable]
    # interventions
    do : FrozenSet[Variable]
    # conditioning set
    Z : FrozenSet[Variable]

    #def __post_init__(self):
    #    self.Y = _ensure_is_frozen_set(self.Y)
    #    self.do = _ensure_is_frozen_set(self.do)
    #    self.Z = _ensure_is_frozen_set(self.Z)

    @staticmethod
    def parse(p : str):
        Y = set()
        do = set()
        Z = set()

        m = re.match("P\((.*)\)", p)
        if m:
            p = m.group(1)
        p = p.strip()
        if p == "":
            raise Exception("Must be non-empty")
        if "|" in p:
            p = p.split("|")
            for x in p[0].split(","):
                x = x.strip()
                Y.add(x)
            for x in p[1].split(","):
                x = x.strip()
                m = re.match("do\((.*)\)", x)
                if m:
                    x = m.group(1).strip()
                    do.add(x)
                else:
                    Z.add(x)
        else:
            for x in p.split(","):
                x = x.strip()
                Y.add(x)

        if len(Y) == 0:
            raise Exception("Must contain at least one variable on LHS of conditional")

        Y  = [ Variable(y) for y in Y ]
        do = [ Variable(d) for d in do ]
        Z  = [ Variable(z) for z in Z ]

        return P(Y = frozenset(Y), do = frozenset(do), Z = frozenset(Z))

    def __str__(self):
        ys  = ",".join(sorted(map(str,self.Y)))
        dos = [ "do({})".format(d) for d in sorted(self.do) ]
        zs  = sorted(self.Z)
        rhs_of_conditional = dos + zs
        if len(rhs_of_conditional) > 0:
            return "P({}|{})".format(ys, ",".join(map(str,rhs_of_conditional)))
        else:
            return "P({})".format(ys)


if __name__ == "__main__":
    print(P.parse("P(X,Y|do(M),Z)"))