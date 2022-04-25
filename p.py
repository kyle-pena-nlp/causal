from dataclasses import dataclass, field
from argparse import ArgumentParser
from typing import FrozenSet, Any
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from parseable import grammar_register_tag, Parseable

@grammar_register_tag("expression")
@dataclass(frozen = True, eq = True)
class Expression(Parseable,ABC):  
    """
        A statement involving probabilities
    """  

    @abstractmethod
    def __str__(self):
        pass
    
    @abstractmethod
    def hat_free(self):
        pass


@grammar_register_tag("variable")
@dataclass(frozen = True, eq = True)
class Variable(Parseable):
    """
        A random variable appearing in a probability statement
    """

    name : str

    def __post_init__(self):
        if not self.name.strip():
            raise Exception("Variable name must be non-blank")
        elif re.findall("[\s\]\[\*;,\(\)/]",self.name):
            raise Exception("Name cannot contain whitespace or any of these characters: []*;,()/")

    def __lt__(self, other : 'Variable'):
        return self.name < other.name

    def __eq__(self, other : 'Variable'):
        return self.name == other.name

    def __str__(self):
        return self.name

@grammar_register_tag("p")
@dataclass(frozen = True, eq = True)
class P(Expression):
    """
        An expression involving a joint distribution and do operators and/or conditionals.
    """

    # outcomes
    Y : FrozenSet[Variable]
    # interventions
    do : FrozenSet[Variable] = field(default_factory=frozenset)
    # conditioning set
    Z : FrozenSet[Variable] = field(default_factory=frozenset)

    def __str__(self):
        ys  = ",".join(sorted(map(str,self.Y)))
        dos = [ "do({})".format(d) for d in sorted(self.do) ]
        zs  = sorted(self.Z)
        rhs_of_conditional = dos + zs
        if len(rhs_of_conditional) > 0:
            return "P({}|{})".format(ys, ",".join(map(str,rhs_of_conditional)))
        else:
            return "P({})".format(ys)

    def hat_free(self):
        return len(self.do) == 0            


@grammar_register_tag("quotient")
@dataclass(frozen = True, eq = True)
class Quotient(Expression):
    """
        A quotient of expressions involving probability statements
    """

    numerator : Expression
    denominator : Expression

    def __str__(self):
        return "{} / {}".format(str(self.numerator), str(self.denominator))

    def hat_free(self):
        return self.numerator.hat_free() and self.denominator.hat_free()
        
@grammar_register_tag("product")
@dataclass(frozen = True, eq = True)
class Product(Expression):
    """
        A product of expressions invovling probability statements
    """

    terms : FrozenSet[Expression]

    def __str__(self):
        return " * ".join((map(str,self.terms)))

    def hat_free(self):
        return all(term.hat_free() for term in self.terms)

@grammar_register_tag("marginalization")
@dataclass(frozen = True, eq = True)
class Marginalization(Expression):
    """
        A marginalization of a statement involving probabilities
    """
    
    expression : Expression
    margins: FrozenSet[Variable]

    def __str__(self):
        margins = ",".join(sorted(map(str,self.margins)))
        return "E[{};{}]".format(str(self.expression), margins)

    def hat_free(self):
        return self.expression.hat_free()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--expression", type = str, required = False, default = "P(X,Y)")
    args = parser.parse_args()
    print(Parseable.parse_list(P, args.expression))