#!/usr/bin/env python3

from util import Token, TOKEN
from AST import AST, FunKind, Accessor
import itertools

def flatten(xs):
    return list(itertools.chain(*xs))

def map_print(xs):
    return list(map(lambda y: print_node(y), xs))


INFIX_STR = {
    FunKind.INFIXL : "infixl",
    FunKind.INFIXR : "infixr"
}
ACC_STR = {
    Accessor.HD : ".hd",
    Accessor.TL : ".tl",
    Accessor.FST : ".fst",
    Accessor.SND : ".snd"
}
INFIX_LOOKUP = (lambda x:
    "{} {} {} ({},{}) {}{{".format(INFIX_STR[x.kind], x.fixity, x.id.val, x.params[0].val, x.params[1].val, ":: {} ".format(print_node(x.type)) if x.type is not None else "")
)

FUN_LOOKUP = {
    FunKind.FUNC : (lambda x:
            "{} ({}) {}{{".format(x.id.val, ", ".join(map(lambda y: y.val, x.params)), ":: {} ".format(print_node(x.type)) if x.type is not None else "")
        ),
    FunKind.PREFIX : (lambda x:
            "prefix {} ({}) {}{{".format(x.id.val, x.params[0].val, ":: {} ".format(print_node(x.type)) if x.type is not None else "")
        ),
    FunKind.INFIXL : INFIX_LOOKUP,
    FunKind.INFIXR : INFIX_LOOKUP,
}

FUNCALL_LOOKUP = { #TODO test this
    FunKind.FUNC : (lambda x:
            "{}({});".format(x.id.val, ", ".join(map_print(x.args)))
        ),
    FunKind.PREFIX : (lambda x:
            "{}{}".format(x.id.val, print_node(x.args[0]))
        ),
    FunKind.INFIXL : (lambda x:
            "({}) {} {}".format(print_node(x.args[0]), x.id.val, print_node(x.args[1]))
        ),
    FunKind.INFIXR : (lambda x:
            "{} {} ({})".format(print_node(x.args[0]), x.id.val, print_node(x.args[1]))
        )
}

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
    AST.FUNDECL : (lambda x:
            [
                FUN_LOOKUP[x.kind](x),
                [
                    *flatten(map_print(x.vardecls)),
                    *flatten(map_print(x.stmts))
                ],
                "}"
            ]
        ),
    AST.TYPESYN : (lambda x:
            ["type {} = {}".format(x.type_id.val, print_node(x.def_type))]
        ),
    AST.TYPE : (lambda x:
            print_node(x.val)
        ),
    AST.BASICTYPE : (lambda x:
            x.type_id.val
        ),
    AST.TUPLETYPE : (lambda x:
            "({}, {})".format(print_node(x.a), print_node(x.b))
        ),
    AST.LISTTYPE : (lambda x:
            "[{}]".format(print_node(x.type))
        ),
    AST.FUNTYPE : (lambda x:
            "{} -> {}".format(" ".join(map_print(x.from_types)), print_node(x.to_type))
        ),
    AST.STMT : (lambda x:
            print_node(x.val)
        ),
    AST.IFELSE : [],
    AST.CONDBRANCH : [],
    AST.LOOP : [],
    AST.ACTSTMT : (lambda x:
            print_node(x.val)
        ),
    AST.RETURN : (lambda x:
            ["return {};".format(print_node(x.expr))]
        ),
    AST.BREAK : (lambda x:
            ["break;"]
        ),
    AST.CONTINUE : (lambda x:
            ["continue;"]
        ),
    AST.ASSIGNMENT : (lambda x:
            ["{} = {};".format(print_node(x.varref), print_node(x.expr))]
        ),
    AST.FUNCALL : (lambda x:
            [FUNCALL_LOOKUP[x.kind](x)]
        ),
    AST.DEFERREDEXPR : (lambda x: # THIS IS TEMP (tokens verwacht, is niet zo)
            " ".join(list(map(lambda y: str(y.val), x.contents)))
        ),
    AST.PARSEDEXPR : [],
    AST.VARREF : (lambda x:
            "{}{}".format(x.id.val, "".join(map(lambda y: ACC_STR[y], x.fields)))
        ),
}

def printAST(root):
    temp = print_node(root)
    return indent_print(temp, 0)

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

INDENT_CHARS = "  "
def indent_print(temp, level):
    res = ""
    for el in temp:
        if type(el) == list:
            res += indent_print(el, level + 1)
        else:
            res += level*INDENT_CHARS + el + "\n"
    return res


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
                        type=AST.TYPE(
                            val=AST.BASICTYPE(
                                type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                            )
                        )
                    )
                )
            ),
            AST.FUNDECL(
                kind=FunKind.INFIXL,
                fixity=4,
                id=Token(None,TOKEN.OP_IDENTIFIER, "%%"),
                params=[
                    Token(None,TOKEN.IDENTIFIER, "x"),
                    Token(None,TOKEN.IDENTIFIER, "y")
                ],
                type=AST.FUNTYPE(
                    from_types=[
                        AST.TYPE(
                            val=AST.BASICTYPE(
                                type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                            )
                        ),
                        AST.TYPE(
                            val=AST.BASICTYPE(
                                type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                            )
                        )
                    ],
                    to_type=AST.TYPE(
                        val=AST.BASICTYPE(
                            type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                        )
                    )
                ),
                vardecls=[],
                stmts=[]
            ),
            AST.FUNDECL(
                kind=FunKind.INFIXR,
                fixity=4,
                id=Token(None,TOKEN.OP_IDENTIFIER, "^^"),
                params=[
                    Token(None,TOKEN.IDENTIFIER, "x"),
                    Token(None,TOKEN.IDENTIFIER, "y")
                ],
                type=None,
                vardecls=[],
                stmts=[
                    AST.STMT(
                        val=AST.RETURN(
                            expr=None
                        )
                    ),
                    AST.STMT(
                        val=AST.RETURN(
                            expr=None
                        )
                    )
                ]
            ),
            AST.FUNDECL(
                kind=FunKind.FUNC,
                fixity=None,
                id=Token(None,TOKEN.OP_IDENTIFIER, "fib2"),
                params=[
                    Token(None,TOKEN.IDENTIFIER, "xtup"),
                    Token(None,TOKEN.IDENTIFIER, "y"),
                    Token(None,TOKEN.IDENTIFIER, "z")
                ],
                type=AST.FUNTYPE(
                    from_types=[
                        AST.TUPLETYPE(
                            a=AST.TYPE(
                                val=AST.BASICTYPE(
                                    type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                                )
                            ),
                            b=AST.TYPE(
                                val=AST.BASICTYPE(
                                    type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                                )
                            ),
                        ),
                        AST.TYPE(
                            val=AST.BASICTYPE(
                                type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                            )
                        ),
                        AST.TYPE(
                            val=AST.BASICTYPE(
                                type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                            )
                        )
                    ],
                    to_type=AST.TYPE(
                        val=AST.BASICTYPE(
                            type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                        )
                    )
                ),
                vardecls=[],
                stmts=[
                    AST.STMT(
                        val=AST.RETURN(
                            expr=None
                        )
                    ),
                    AST.STMT(
                        val=AST.RETURN(
                            expr=None
                        )
                    )
                ]
            ),
            AST.FUNDECL(
                kind=FunKind.PREFIX,
                fixity=None,
                id=Token(None,TOKEN.OP_IDENTIFIER, "!"),
                params=[
                    Token(None,TOKEN.IDENTIFIER, "x")
                ],
                type=AST.FUNTYPE(
                    from_types=[
                        AST.TYPE(
                            val=AST.BASICTYPE(
                                type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                            )
                        )
                    ],
                    to_type=AST.TYPE(
                        val=AST.BASICTYPE(
                            type_id=Token(None,TOKEN.TYPE_IDENTIFIER, "Char")
                        )
                    )
                ),
                vardecls=[],
                stmts=[
                    AST.STMT(
                        val=AST.RETURN(
                            expr=None
                        )
                    ),
                    AST.STMT(
                        val=AST.RETURN(
                            expr=None
                        )
                    )
                ]
            )
        ]
    )


    print(printAST(test))

    test2 = AST.VARREF(
        id=Token(None,TOKEN.IDENTIFIER, "xs"),
        fields=[]
    )
    print(print_node(test2))
    test3 = AST.VARREF(
        id=Token(None,TOKEN.IDENTIFIER, "xs"),
        fields=[
            Accessor.TL,
            Accessor.HD
        ]
    )
    print(print_node(test3))
    test4 = AST.FUNCALL(
        id=Token(None,TOKEN.IDENTIFIER, "pow"),
        kind=FunKind.FUNC,
        args=[
            AST.VARREF(
                id=Token(None,TOKEN.IDENTIFIER, "x"),
                fields=[]
            ),
            AST.VARREF(
                id=Token(None,TOKEN.IDENTIFIER, "x"),
                fields=[]
            )
        ]
    )
    print(print_node(test4))
    test5 = AST.FUNCALL(
        id=Token(None,TOKEN.IDENTIFIER, "*"),
        kind=FunKind.INFIXL,
        args=[
            AST.VARREF(
                id=Token(None,TOKEN.IDENTIFIER, "x"),
                fields=[]
            ),
            AST.VARREF(
                id=Token(None,TOKEN.IDENTIFIER, "x"),
                fields=[]
            )
        ]
    )
    print(print_node(test5))