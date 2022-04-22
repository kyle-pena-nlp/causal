from dataclasses import dataclass
from typing import Set, Union
import re
from variable import Variable
from p import P
from util import _parsed_frozenset
from expression import Expression

@dataclass(frozen = True, eq = True)
class Marginalization(Expression):

    X: Set[Variable]
    expression : P

    @staticmethod 
    def parse(string : str):
        m = re.match(r"E\[([^;]*);([^]]*)\]",string)
        if not m:
            raise Exception("Doesn't look like a marginalization: {}".format(string))
        p = m.group(1)
        p = P.parse(p)
        X = m.group(2)
        X = _parsed_frozenset(X, Variable)
        return Marginalization(X = X, statement = p)

    def __str__(self):
        margins = ", ".join(sorted(map(str,self.X)))
        return "E[{};{}]".format(str(self.statement), margins)

    def hat_free(self):
        return self.expression.hat_free()

