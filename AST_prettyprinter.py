#!/usr/bin/env python3

from util import Token, TOKEN
from AST import AST, FunKind, Accessor
import itertools

def flatten(xs):
    return list(itertools.chain(*xs))

def map_print(xs):
    return list(map(lambda y: print_node(y), xs))

LOOKUP = {
    AST.SPL : (lambda x:
        [
            *flatten(map_print(x.imports)),
            *flatten(map_print(x.decls))
        ]),
    AST.IMPORT : (lambda x:
            ["from {} import {}".format(x.name.val, "*" if x.importlist is None else ", ".join(map_print(x.importlist)))]
        ),
    AST.IMPORTNAME : (lambda x:
            x.name.val if x.alias is None else "{} as {}".format(x.name.val, x.alias.val)
        ),
    AST.DECL : (lambda x:
            print_node(x.val)
        ),
    AST.VARDECL : (lambda x:
            ["{}{} = {};".format("{} ".format(print_node(x.type) if x.type is not None else "var"), x.id.val, print_node(x.expr))]
        ),
    AST.FUNDECL : [],
    AST.TYPESYN : (lambda x:
            ["type {} = {}".format(x.type_id.val, print_node(x.def_type))]
        ),
    AST.TYPE : (lambda x:
            print_node(x.val)
        ),
    AST.BASICTYPE : (lambda x:
            x.type_id.val
        ),
    AST.TUPLETYPE : [],
    AST.LISTTYPE : (lambda x:
            "[{}]".format(print_node(x.type))
        ),
    AST.FUNTYPE : [],
    AST.STMT : [],
    AST.IFELSE : [],
    AST.CONDBRANCH : [],
    AST.LOOP : [],
    AST.ACTSTMT : [],
    AST.RETURN : (lambda x:
            "return"
        ),
    AST.BREAK : [],
    AST.CONTINUE : [],
    AST.ASSIGNMENT : [],
    AST.FUNCALL : [],
    AST.DEFERREDEXPR : (lambda x: # THIS IS TEMP
            " ".join(list(map(lambda y: str(y.val), x.contents)))
        ),
    AST.PARSEDEXPR : [],
    AST.VARREF : [],
}

def printAST(root):
    return print_node(root)

def print_node(node):
    if type(node) in LOOKUP:
        if LOOKUP[type(node)] == []:
            print(type(node),"not defined yet")
            return []
        else:
            return LOOKUP[type(node)](node)
    else:
        print(type(node),"not handled in lambda")
        print(node)
        return []


if __name__ == "__main__":
    test = AST.SPL(
        imports=[
            AST.IMPORT(
                name=Token(None,TOKEN.IDENTIFIER,"stdlib"),
                importlist=None
            ),
            AST.IMPORT(
                name=Token(None,TOKEN.IDENTIFIER, "math"),
                importlist=[
                    AST.IMPORTNAME(
                        name=Token(None,TOKEN.IDENTIFIER, "power"),
                        alias=Token(None,TOKEN.IDENTIFIER, "pow")
                    )
                ]
            )
        ],
        decls=[
            AST.VARDECL(
                type=None,
                id=Token(None,TOKEN.IDENTIFIER, "temp"),
                expr=AST.DEFERREDEXPR(
                    contents=[
                        Token(None,TOKEN.INT, 2)
                    ]
                )
            ),
            AST.VARDECL(
                type=AST.TYPE(
                    val=AST.BASICTYPE(
                        type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                    )
                ), # TODO make this work for type node
                id=Token(None,TOKEN.IDENTIFIER, "hey"),
                expr=AST.DEFERREDEXPR(
                    contents=[
                        Token(None,TOKEN.CHAR, 'a')
                    ]
                )
            ),
            AST.TYPESYN(
                type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "String"),
                def_type=AST.TYPE(
                    val=AST.LISTTYPE(
                        type=AST.BASICTYPE(
                            type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                        )
                    )
                )
            )
        ]
    )


    print(printAST(test))