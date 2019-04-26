#!/usr/bin/env python3

from util import pointToPosition, Position, TOKEN, Node

'''
Zaken als +, -, :, / etc zijn built-in methodes
String is een built-in typesynoniem

'''

'''
consumeert keywords als deze niet door iets alfabetisch gevolgd worden

=-teken wordt gewoon gelext als assignment -> dus geen geldige operatornaam
eindigen in comment-mode is error
multiline comment mode sluiten zonder flag is error -> */ geen geldige operatornaam
Vinden van commentsymbolen buiten string mode begint altijd comment
oftewel //* en /* geen geldige operatornamen


'''

'''
Top-down parser
Leftmost derivation
Non-ambigue grammatica
Convergente left-recursion
LL(1) (1 token lookahead)

Eindige recursie-diepte dmv stack.


De taal is zo gespecificeerd dat de eerstvolgende token altijd maar bij 1 regel zou moeten passen.
Zo niet geef een !!COMPILER ERROR!! want dan zijn dingen goed fout.
Een regel/parser specificeert een verwachte token + een filterfunctie (i.e. TOKEN.OP_ID met value == "="). Default is lambda _: True
Afhankelijk van je positie in de parser heb je meerdere mogelijke opties van regels/parsers.
Als een nonterminal een optie is beschouw je deze gewoon als een lijst van al diens alternatieven naar hetzelfde niveau getild als de huidige.
Houd een soort stack bij van hoe je regels afdaalt. Als het een optie is om de huidige te beeindigen (maar nog niet verplicht) bechouw je ook de regel erboven.


Als zeker is dat de huidige regel afgesloten wordt moet een waarde ge-emit worden. Deze wordt in de regel erboven gebruikt voor het emitten van diens waarde.

Second pass:
Fix de expressie-associativiteit en bindingssterkte aan de hand van de operator-definities


Accessors worden vertaald naar functiecalls met builtin functies.
Moeten ook al een soort symbol-table maken van operator-definities
'''


class Rule():
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return str(self.val)


# Combinators
class List():
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return " ".join(map(str,self.val))

class Many():
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return "({})*".format(self.val)

class Many1():
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return "({})+".format(self.val)

class Choice():
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return "({})".format(" | ".join(map((lambda x : "({})".format(x)),self.val)))

class Maybe():
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return "[{}]".format(self.val)

class Tok():
    def __init__(self, val, filter_f = (lambda x : True)):
        self.val = val
        self.filter_f = filter_f

    def __repr__(self):
        return self.val.name


RULES = {
    "SPL"       : Rule(Many1("Decl")),

    "Decl"      : Rule(Choice([
                    "VarDecl",
                    "FunDecl",
                    "TypeSyn",
                    "OpDecl"
                    ])),

    "VarDecl"   : Rule(List([
                    Choice([
                        Tok(TOKEN.VAR),
                        "Type"
                        ]),
                    Tok(TOKEN.IDENTIFIER),
                    Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == "=")),
                    "Exp",
                    Tok(TOKEN.SEMICOLON)
                    ])),

    "FunDecl"   : Rule(List([
                    Tok(TOKEN.IDENTIFIER),
                    Tok(TOKEN.PAR_OPEN),
                    Maybe("FArgs"),
                    Tok(TOKEN.PAR_CLOSE),
                    Maybe(List([
                        Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == "::")),
                        "FunType"
                        ])),
                    Tok(TOKEN.CURL_OPEN),
                    Many("VarDecl"),
                    Many1("Stmt"),
                    Tok(TOKEN.CURL_CLOSE)
                    ])),

    "OpDecl"    : Rule(Choice([
                    List([
                        Tok(TOKEN.PREFIX),
                        Tok(TOKEN.OP_IDENTIFIER),
                        Tok(TOKEN.PAR_OPEN),
                        Tok(TOKEN.IDENTIFIER),
                        Tok(TOKEN.PAR_CLOSE),
                        Maybe(List([
                            Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == "::")),
                            "FunType"
                            ])),
                        Tok(TOKEN.CURL_OPEN),
                        Many("VarDecl"),
                        Many1("Stmt"),
                        Tok(TOKEN.CURL_CLOSE)
                        ]),
                    List([
                        Choice([
                            Tok(TOKEN.INFIXL),
                            Tok(TOKEN.INFIXR)
                            ]),
                        Tok(TOKEN.INT),
                        Tok(TOKEN.OP_IDENTIFIER),
                        Tok(TOKEN.PAR_OPEN),
                        Tok(TOKEN.IDENTIFIER),
                        Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == ",")),
                        Tok(TOKEN.IDENTIFIER),
                        Tok(TOKEN.PAR_CLOSE),
                        Maybe(List([
                            Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == "::")),
                            "FunType"
                            ])),
                        Tok(TOKEN.CURL_OPEN),
                        Many("VarDecl"),
                        Many1("Stmt"),
                        Tok(TOKEN.CURL_CLOSE)
                        ])
                    ])),

    "TypeSyn"   : Rule(List([
                    Tok(TOKEN.TYPESYN),
                    Tok(TOKEN.TYPE_IDENTIFIER),
                    Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == "=")),
                    "Type"
                    ])),

    "FunType"   : Rule(List([
                    Maybe("FTypes"),
                    Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == "->")),
                    "RetType"
                    ])),

    "FTypes"    : Rule(Many1("Type")),

    "RetType"   : Rule(Choice([
                    "Type",
                    Tok(TOKEN.TYPE_IDENTIFIER, (lambda x : x == "Void"))
                    ])),

    "Type"      : Rule(Choice([
                    "BasicType",
                    List([
                        Tok(TOKEN.PAR_OPEN),
                        "Type",
                        Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == ",")),
                        "Type",
                        Tok(TOKEN.PAR_CLOSE)
                        ]),
                    List([
                        Tok(TOKEN.BRACK_OPEN),
                        "Type",
                        Tok(TOKEN.BRACK_CLOSE)
                        ]),
                    Tok(TOKEN.TYPE_IDENTIFIER)
                    ])),

    "BasicType" : Rule(Choice([
                    Tok(TOKEN.TYPE_IDENTIFIER, (lambda x : x == "Int")),
                    Tok(TOKEN.TYPE_IDENTIFIER, (lambda x : x == "Bool")),
                    Tok(TOKEN.TYPE_IDENTIFIER, (lambda x : x == "Char"))
                    ])),

    "FArgs"     : Rule(List([
                    Tok(TOKEN.IDENTIFIER),
                    Many(List([
                        Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == ",")),
                        Tok(TOKEN.IDENTIFIER)
                        ]))
                    ])),

    "Stmt"      : Rule(Choice([
                    List([
                        Tok(TOKEN.IF),
                        Tok(TOKEN.PAR_OPEN),
                        "Exp",
                        Tok(TOKEN.PAR_CLOSE),
                        Tok(TOKEN.CURL_OPEN),
                        Many("Stmt"),
                        Tok(TOKEN.CURL_CLOSE),
                        Many(List([
                            Tok(TOKEN.ELIF),
                            Tok(TOKEN.PAR_OPEN),
                            "Exp",
                            Tok(TOKEN.PAR_CLOSE),
                            Tok(TOKEN.CURL_OPEN),
                            Many("Stmt"),
                            Tok(TOKEN.CURL_CLOSE)
                            ])),
                        Maybe(List([
                            Tok(TOKEN.ELSE),
                            Tok(TOKEN.CURL_OPEN),
                            Many("Stmt"),
                            Tok(TOKEN.CURL_CLOSE)
                            ]))
                        ]),
                    List([
                        Tok(TOKEN.WHILE),
                        Tok(TOKEN.PAR_OPEN),
                        "Exp",
                        Tok(TOKEN.PAR_CLOSE),
                        Tok(TOKEN.CURL_OPEN),
                        Many("Stmt"),
                        Tok(TOKEN.CURL_CLOSE)
                        ]),
                    List([
                        Tok(TOKEN.FOR),
                        Tok(TOKEN.PAR_OPEN),
                        Maybe("ActStmt"),
                        Tok(TOKEN.SEMICOLON),
                        "Exp",
                        Tok(TOKEN.SEMICOLON),
                        "ActStmt",
                        Tok(TOKEN.PAR_CLOSE),
                        Tok(TOKEN.CURL_OPEN),
                        Many("Stmt"),
                        Tok(TOKEN.CURL_CLOSE)
                        ]),
                    List([
                        "ActStmt",
                        Tok(TOKEN.SEMICOLON)
                        ]),
                    List([
                        Tok(TOKEN.RETURN),
                        Maybe("Exp"),
                        Tok(TOKEN.SEMICOLON)
                        ])
                    ])),

    "ActStmt"   : Rule(Choice([
                    "Ass",
                    "FunCall"
                    ])),

    "Ass"       : Rule(List([
                    Tok(TOKEN.IDENTIFIER),
                    Tok(TOKEN.ACCESSOR),
                    "Field",
                    "Exp"
                    ])),

    "Exp"       : Rule(List([
                    "ConvExp",
                    Many(List([
                        Tok(TOKEN.OP_IDENTIFIER),
                        "ConvExp"
                        ]))
                    ])),

    "ConvExp"   : Rule(Choice([
                    List([
                        Tok(TOKEN.IDENTIFIER),
                        "Field"
                        ]),
                    List([
                        Tok(TOKEN.OP_IDENTIFIER),
                        "Exp"
                        ]),
                    Tok(TOKEN.INT),
                    Tok(TOKEN.CHAR),
                    Tok(TOKEN.STRING),
                    Tok(TOKEN.BOOL),
                    List([
                        Tok(TOKEN.PAR_OPEN),
                        "Exp",
                        Tok(TOKEN.PAR_CLOSE)
                        ]),
                    "FunCall",
                    Tok(TOKEN.EMPTY_LIST)
                    ])),

    "Field"     : Rule(Maybe(List([
                    Tok(TOKEN.ACCESSOR),
                    "Field"
                    ]))),

    "FunCall"   : Rule(List([
                    Tok(TOKEN.IDENTIFIER),
                    Tok(TOKEN.PAR_OPEN),
                    Maybe("ActArgs"),
                    Tok(TOKEN.PAR_CLOSE)
                    ])),

    "ActArgs"   : Rule(List([
                    "Exp",
                    Many(List([
                        Tok(TOKEN.OP_IDENTIFIER, (lambda x : x == ",")),
                        "Exp"
                        ]))
                    ]))
}

def validRuleSet(rules):
    # Test if all rules are used in another rule, except for the root rule (SPL)
    rulenames = list(rules.keys())


    # Test if all used strings are also rule names
    rulenames = list(rules.keys())

    # Test if all possible token types are consumed
    tokens_to_consume = [e.val for e in TOKEN]

    # Test if structure correct
    # i.e. Test if List and Choice have lists
    

    return False

def parseTokenStream(instream):
    active_rules = []



if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Parser")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()

    for rule, content in RULES.items():
        print("{}:".format(rule))
        print(content)
        print()

    with open(args.infile, "r") as infile:
        tokenstream = tokenize(infile)

        '''
        tokenlist = list(tokenstream)
        import random
        randtoken = random.choice(tokenlist)
        print(randtoken)
        print(pointToPosition(infile, randtoken.pos))
        '''


