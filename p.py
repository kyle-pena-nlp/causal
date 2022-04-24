import inspect
from dataclasses import dataclass, fields, field, Field, is_dataclass
from enum import Enum
from typing import FrozenSet, Any, get_origin, get_args, List, Set, Union
from collections import defaultdict
import re
from abc import ABC, abstractclassmethod, abstractmethod, abstractstaticmethod
from dataclasses import dataclass
import tatsu

TATSU_GRAMMAR = """
start = EXPRESSION ;
EXPRESSION = expression:( QUOTIENT | PRODUCT | P | MARGINALIZATION ) ;
QUOTIENT = quotient:( NUMERATOR '/' DENOMINATOR ) ;
NUMERATOR = numerator:EXPRESSION ;
DENOMINATOR = denominator:EXPRESSION ;
PRODUCT = product:( TERMS ) ;
TERMS = terms:((EXPRESSION '*' EXPRESSION) { '*' EXPRESSION }* ) ;
MARGINALIZATION = marginalization:( 'E[' MARGINALIZATION_EXPRESSION ';' MARGINALIZATION_MARGINS ']' ) ;
MARGINALIZATION_EXPRESSION = expression:EXPRESSION ;
MARGINALIZATION_MARGINS = margins:VARIABLE_LIST ;
VARIABLE_LIST = ( VARIABLE { ',' VARIABLE }* );
VARIABLE = variable:( NAME ) ;
NAME = name:/[A-Z]+/ ;
P = p:( 'P(' P_INNER ')' );
P_INNER = (Y_RULE '|' DO_RULE ',' Z_RULE) |
          (Y_RULE '|' Z_RULE ) |
          (Y_RULE '|' DO_RULE ) |
          (Y_RULE);
DO_ITEM = 'do(' VARIABLE ')' ;
DO_LIST = DO_ITEM { ',' DO_ITEM }* ;          
Y_RULE = Y:VARIABLE_LIST ;
DO_RULE = do:DO_LIST ;
Z_RULE = Z:VARIABLE_LIST ;
"""
MODEL = tatsu.compile(TATSU_GRAMMAR)
TAG_2_KLASS = {}
KLASS_2_TAG = {}
KLASS_2_TAGS = defaultdict(lambda: set())
REGISTERED_KLASSES = set()

def grammar_register_tag(tag):
    def decorator(klass):
        print("Registering '{}' <=> {}".format(tag, klass))
        TAG_2_KLASS[tag] = klass
        KLASS_2_TAG[klass] = tag
        KLASS_2_TAGS[klass].add(tag)
        for k in inspect.getmro(klass)[1:]:
            if k in REGISTERED_KLASSES:
                KLASS_2_TAGS[k].add(tag)
        REGISTERED_KLASSES.add(klass)
        return klass
    return decorator

@dataclass(frozen = True, eq = True)
class Parseable(ABC):
    """
        A thing you can parse from a string
    """

    @classmethod
    def parse(cls, string : str):
        """
            Take a string and turn it into an instance of cls
        """
        start_tag = KLASS_2_TAG[cls]
        AST = MODEL.parse(string) # start = start_tag
        AST = dict(AST)
        tags = KLASS_2_TAGS[cls]
        tag, ast_ = Parseable._find_first_value_of_tag(tags, AST)
        klass = TAG_2_KLASS[tag]
        instance = Parseable.parse_instance(klass, ast_)
        return instance

    @staticmethod
    def parse_instance(klass, AST):
        if is_dataclass(klass):
            return Parseable.parse_dataclass_instance(klass, AST)
        else:
            return klass(AST)

    @staticmethod
    def parse_dataclass_instance(klass, AST):
        dataclass_fields = list(fields(klass))
        field_values = {}
        while len(dataclass_fields) > 0:
            dataclass_field = dataclass_fields.pop(0)
            instance = Parseable.parse_dataclass_field(AST, dataclass_field)
            if instance is not None:
                field_values[dataclass_field.name] = instance
        return klass(**field_values)

    @staticmethod
    def parse_dataclass_field(AST, dataclass_field):
        result = Parseable._find_first_value_of_tag(dataclass_field.name, AST)
        if result is None:
            return None
        _,ast_ = result
        collection_type,inner_type = Parseable._decompose_type(dataclass_field.type)
        if collection_type is None:
            return Parseable.parse_instance(inner_type,ast_)
        else:
            tags = KLASS_2_TAGS[inner_type]
            tags_, asts_ = Parseable._find_all(tags, ast_)
            instances = []
            for (tag_, ast_) in zip(tags_, asts_):
                klass_ = TAG_2_KLASS[tag_]
                instances.append(Parseable.parse_instance(klass_,ast_))
            return collection_type(instances)


    @staticmethod
    def _find_all(tags : Set[str], AST):
        tags_,asts_ = [],[]
        Parseable._find_all_rec(tags, AST, tags_, asts_)
        return tags_, asts_

    @staticmethod
    def _find_all_rec(tags, AST, tags_, asts_):
        if isinstance(AST, dict):
            for tag_,ast_ in AST.items():
                if tag_ in tags:
                    tags_.append(tag_)
                    asts_.append(ast_)
                else:
                    Parseable._find_all_rec(tags, ast_, tags_, asts_)
        elif isinstance(AST, (tuple,list)):
            for ast_ in AST:
                Parseable._find_all_rec(tags, ast_, tags_, asts_)
        elif isinstance(AST, str):
            pass
        else:
            raise Exception("Unknown AST type: {}".format(type(AST)))

    @staticmethod
    def _parse_parameters_for_type(AST, params_dict : dict, fields_list : list):
        while len(fields_list) > 0:
            Parseable._parse_parameter(AST, params_dict, fields_list)

    @staticmethod
    def _decompose_type(type_):
        collection_type = get_origin(type_)
        if collection_type is None:
            return None,type_
        else:
            args = get_args(type_)
            inner_type = args[0]
            return collection_type,inner_type    

    @staticmethod
    def _find_first_value_of_tag(tags: Union[str,Set[str]], AST: Any):
        
        if isinstance(tags, str):
            tags = { tags }

        if isinstance(AST, str):
            return None        
        elif isinstance(AST, (tuple,list)):
            for item in AST:
                result = Parseable._find_first_value_of_tag(tags, item)
                if result is not None:
                    return result
        elif isinstance(AST, dict):
            for tag,ast_ in AST.items():
                if tag in tags:
                    return tag, AST[tag]
                else:
                    return Parseable._find_first_value_of_tag(tags,ast_)
        else:
            raise Exception("Unknown AST type: {}".format(type(AST)))


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

    @classmethod
    def _parse_AST(cls, AST : Any):
        _,name = Parseable._find_first_value_of_tag("name", AST)
        return Variable(name = name)
    

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

    @classmethod
    def _parse_AST(cls, AST):

        _,y = Expression._find_first_value_of_tag("y", AST)
        _,do = Expression._find_first_value_of_tag("do", AST)
        _,z = Expression._find_first_value_of_tag("z", AST)

        y = frozenset(Parseable._parse_all("variable", Variable, y))
        do = frozenset(Parseable._parse_all("variable", Variable, do or {}))
        z = frozenset(Parseable._parse_all("variable", Variable, z or {}))

        return P(Y = y, do = do, Z = z)

    def hat_free(self):
        return len(self.do) == 0

    def __str__(self):
        ys  = ",".join(sorted(map(str,self.Y)))
        dos = [ "do({})".format(d) for d in sorted(self.do) ]
        zs  = sorted(self.Z)
        rhs_of_conditional = dos + zs
        if len(rhs_of_conditional) > 0:
            return "P({}|{})".format(ys, ",".join(map(str,rhs_of_conditional)))
        else:
            return "P({})".format(ys)


@grammar_register_tag("quotient")
@dataclass(frozen = True, eq = True)
class Quotient(Expression):
    """
        A quotient of expressions involving probability statements
    """

    numerator : Expression
    denominator : Expression

    @classmethod
    def _parse_AST(cls, AST):
        _,numerator = Parseable._find_first_value_of_tag("numerator", AST)
        numerator = Parseable._parse_parseables(numerator)[0]
        _,denominator = Parseable._find_first_value_of_tag("denominator", AST)
        denominator = Parseable._parse_parseables(denominator)[0]
        return Quotient(numerator = numerator, denominator = denominator)

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

    @classmethod
    def _parse_AST(cls, AST):
        terms = frozenset(Parseable._parse_parseables(AST))
        return Product(terms)

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

    @classmethod
    def _parse_AST(cls, AST):
        _,expression = Parseable._find_first_value_of_tag("expression")
        _,margins  = Parseable._find_first_value_of_tag("margins")
        margins = frozenset(Parseable._parse_parseables(margins))
        return Marginalization(expression = expression, margins = margins)

    def __str__(self):
        margins = ", ".join(sorted(map(str,self.X)))
        return "E[{};{}]".format(str(self.statement), margins)

    def hat_free(self):
        return self.expression.hat_free()


if __name__ == "__main__":
    print(P.parse("P(X,Y,Z|do(M),do(N),do(O))"))
