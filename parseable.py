import inspect
from dataclasses import dataclass, fields, Field, is_dataclass
from typing import Any, get_origin, get_args, Set, Union
from collections import defaultdict
from abc import ABC
from dataclasses import dataclass
import tatsu

# TODO: generate the grammar based on dataclass annotations
# something like:
#  @parsing("P([X],[do],[Z])")
# and for collection fields:
#  @collection_parsing(sep=",")

EBNF_GRAMMAR = """WS = /\s*/ ;
EXPRESSION = expression: ( QUOTIENT | PRODUCT | P | MARGINALIZATION ) ;
QUOTIENT = quotient:(( '(' WS NUMERATOR WS '/' WS DENOMINATOR WS ')' ) | ( WS NUMERATOR WS '/' WS DENOMINATOR WS )) ;
NUMERATOR = numerator:EXPRESSION ;
DENOMINATOR = denominator:EXPRESSION ;
PRODUCT = product:( TERMS ) ;
TERMS = terms:((EXPRESSION WS '*' WS EXPRESSION) { '*' WS EXPRESSION }* ) ;
MARGINALIZATION = marginalization:( 'E[' WS MARGINALIZATION_EXPRESSION WS ';' WS MARGINALIZATION_MARGINS WS ']' ) ;
MARGINALIZATION_EXPRESSION = expression:EXPRESSION ;
MARGINALIZATION_MARGINS = margins:VARIABLE_LIST ;
VARIABLE_LIST = ( VARIABLE { ',' WS VARIABLE }* );
VARIABLE = variable:( NAME ) ;
NAME = name:/[A-Z][A-Z0-9]*/ ;
P = p:( 'P(' WS P_INNER WS ')' );
P_INNER = (Y_RULE '|' DO_RULE ',' Z_RULE) |
          (Y_RULE '|' Z_RULE ) |
          (Y_RULE '|' DO_RULE ) |
          (Y_RULE);
DO_ITEM = 'do(' WS VARIABLE WS ')' ;
DO_LIST = DO_ITEM { ',' WS DO_ITEM }* ;          
Y_RULE = Y:VARIABLE_LIST ;
DO_RULE = do:DO_LIST ;
Z_RULE = Z:VARIABLE_LIST ;
"""
MODELS = {}
TAG_2_KLASS = {}
KLASS_2_TAG = {}
KLASS_2_TAGS = defaultdict(lambda: set())
REGISTERED_KLASSES = [] # parsing order will register from most abstract to least abstract

def grammar_register_tag(tag):
    def decorator(klass):
        TAG_2_KLASS[tag] = klass
        KLASS_2_TAG[klass] = tag
        KLASS_2_TAGS[klass].add(tag)
        for k in inspect.getmro(klass)[1:]:
            if k in REGISTERED_KLASSES:
                KLASS_2_TAGS[k].add(tag)
        REGISTERED_KLASSES.append(klass)
        return klass
    return decorator

@dataclass(frozen = True, eq = True)
class Parseable(ABC):
    """
        A thing you can parse from a string
    """

    MODELS = {}

    @staticmethod
    def get_model(tatsu_ebnf : str):
        if tatsu_ebnf not in MODELS:
            MODELS[tatsu_ebnf] = tatsu.compile(tatsu_ebnf)
        return MODELS[tatsu_ebnf]

    @classmethod
    def parse(cls, string : str):
        """
            Take a string and turn it into an instance of cls
        """
        start_statement = "start = EXPRESSION ;"
        grammar = "\n".join([ start_statement, EBNF_GRAMMAR ])
        try:
            AST = Parseable.get_model(grammar).parse(string)
        except:
            print(grammar)
            print(string)
            raise
        instance = Parseable.parse_instance(cls, AST)
        return instance

    # TODO: properly handle left recursion  with list of expression
    @staticmethod
    def parse_list(klass, string : str):
        tag = KLASS_2_TAG[klass]
        start_statement = "start = LIST_ROOT ;".format(tag)
        # Making a strong assumption here that the production rule for the type is the tag name uppercased
        rule = "LIST_ROOT = {}_list:( ( {} {{ ',' WS {} }}* ) | WS ) ;".format(tag, tag.upper(), tag.upper())
        grammar = "\n".join([ start_statement, rule, EBNF_GRAMMAR ])
        try:
            AST = Parseable.get_model(grammar).parse(string)
        except:
            print(grammar)
            print(string)
            raise
        results = []
        Parseable._parse_instances(klass, AST, results)
        return results

    @staticmethod
    def parse_instance(klass, AST):
        is_typing_type = get_origin(klass) is not None
        if is_typing_type:
            return Parseable._parse_typing_type(klass, AST)
        if is_dataclass(klass) and inspect.isabstract(klass):
            return Parseable._parse_abstract_dataclass(klass, AST)
        elif is_dataclass(klass):
            return Parseable._parse_dataclass_instance(klass, AST)
        else:
            return klass(AST)

    @staticmethod
    def _parse_abstract_dataclass(klass, AST):
        # This isn't quite right for the case in which you have ABSTRACT > CONCRETE_A > CONCRETE_B and the AST has ABSTRACT : CONCRETE_A : CONCRETE_B
        # What we really need to do is find and instantiate most derived subclass of klass in AST which isn't a parameter of some nested instance
        # this is good enough for now, however
        # ordered from most derived to least derived (note the ::-1)
        subklasses = [ subklass for subklass in REGISTERED_KLASSES if issubclass(subklass, klass) and not inspect.isabstract(subklass) ][::-1]
        subklass_tags = [ KLASS_2_TAG[subklass] for subklass in subklasses ]
        if isinstance(AST, dict):
            for tag,ast_ in AST.items():
                if tag in subklass_tags:
                    subklass = TAG_2_KLASS[tag]
                    return Parseable.parse_instance(subklass, ast_)
                else:
                    result = Parseable._parse_abstract_dataclass(klass, ast_)
                    if result is not None:
                        return result
        elif isinstance(AST, (list,tuple)):
            for ast_ in AST:
                result = Parseable._parse_abstract_dataclass(klass, ast_)
                if result is not None:
                    return result
        elif isinstance(AST, str):
            pass
        else:
            raise Exception("Unknown AST type {}".format(AST))

    @staticmethod
    def _parse_dataclass_instance(klass, AST):
        dataclass_fields = list(fields(klass))
        field_values = {}
        while len(dataclass_fields) > 0:
            dataclass_field = dataclass_fields.pop(0)
            instance = Parseable._parse_dataclass_field(AST, dataclass_field)
            if instance is not None:
                field_values[dataclass_field.name] = instance
        return klass(**field_values)

    @staticmethod
    def _parse_dataclass_field(AST, dataclass_field : Field):
        result = Parseable._find_first_value_of_tag(dataclass_field.name, AST)
        if result is None:
            return None
        _,ast_ = result
        """
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
        """
        return Parseable.parse_instance(dataclass_field.type, ast_)


    @staticmethod
    def _parse_typing_type(klass, AST):
        # TODO: better typing type support
        outer_type,inner_type = Parseable._decompose_type(klass)
        if outer_type in (tuple,list,set,frozenset):
            instances = []
            Parseable._parse_instances(inner_type, AST, instances)
            return outer_type(instances)
        else:
            raise Exception("Unknown typing type: {}".format(outer_type))

    @staticmethod
    def _parse_instances(klass, AST, results: list):
        tag = KLASS_2_TAG[klass]
        if isinstance(AST, dict):
            for tag_,ast_ in AST.items():
                if tag_ == tag:
                    results.append(Parseable.parse_instance(klass, ast_))
                else:
                    Parseable._parse_instances(klass, ast_, results)
        elif isinstance(AST, (tuple,list)):
            for ast_ in AST:
                Parseable._parse_instances(klass, ast_, results)
        elif isinstance(AST, str):
            pass
        else:
            raise Exception("Unknown AST type: {}".format(type(AST)))


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
            inner_type = args[0] if len(args) == 1 else args
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