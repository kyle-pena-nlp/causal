from dataclasses import dataclass
from typing import FrozenSet
from expression import Expression
from marginalization import Marginalization
from p import P

@dataclass(frozen = True, eq = True)
class Product(Expression):

    terms : FrozenSet[Expression]

    @staticmethod
    def parse(string : str):
        expressions = []
        tokens = string.split("*")
        for token in tokens:
            token = token.strip()
            if token.startswith("E["):
                expressions.add(Marginalization.parse(token))
            else:
                expressions.add(P.parse(token))
        return Product(frozenset(expressions))

    def __str__(self):
        return " * ".join((map(str,self.terms)))

    def hat_free(self):
        return all(term.hat_free() for term in self.terms)