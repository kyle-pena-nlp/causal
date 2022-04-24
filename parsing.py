import json, dataclasses
from argparse import ArgumentParser
import tatsu
from variable import Variable
from p import Quotient, Product, Marginalization, P






def parse(s : str):
    AST = MODEL.parse(s)
    parsed_items = []
    _parse_rec(AST, parsed_items)
    return parsed_items

def _parse_rec(AST, parsed_items):
    if isinstance(AST,str):
        pass
    elif isinstance(AST, list):
        for item in AST:
            _parse_rec(item, parsed_items)
    elif isinstance(AST, dict):
        for tag,value in AST.items():
            klass = GRAMMAR_TAG_2_CLASS[tag]
            klass_args = {}
            klass._parse_AST(value)
            parsed_item = klass(**klass_args)
            parsed_items.append(parsed_item)
    else:
        raise Exception("Unknown type: {}".format(type(AST)))

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--s", type = str, required = True)
    s = parser.parse_args().s
    ast = MODEL.parse(s, whitespace = r'\s*')
    print(json.dumps(ast, indent = 1))
    