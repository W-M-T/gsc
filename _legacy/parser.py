#!/usr/bin/env python3

from lib.util.util import TOKEN

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


def rule_iter(node, func):
    result = []
    if type(node) == dict:
        result.extend([i for s in map(lambda x: rule_iter(x, func), node.values())for i in s])
    elif type(node) in [List, Choice]:
        if not type(node.val) == list:
            raise Exception("Expected a list in the rule, instead got {} ({})".format(node.val, type(node.val)))
        result.extend([i for s in map(lambda x: rule_iter(x, func), node.val) for i in s] )
    elif type(node) in [Many, Many1, Maybe, Rule]:
        result.extend(rule_iter(node.val, func))
    elif type(node) in [str, Tok]:
        result.extend(func(node))
    else:
        raise Exception("Unexpected value: {}".format(node))
    return result



ROOT_RULE = "SPL"
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


# TODO move this to a testing file and convert the intermediate "return False"s to tests
def validRuleSet(rules):
    # Test if structure correct
    # i.e. Test if List and Choice have lists
    # if not the case these tests raise an exception
    try:
        # Test if all rules are used in a rule, except for the root rule (SPL)
        # Also: Test if all used strings are also rule names
        rulenames = list(rules.keys())
        rulenames.remove(ROOT_RULE)
        rulenames = set(rulenames)

        found = set(rule_iter(RULES,
            lambda x: [x] if type(x) == str else []
            ))
        if not rulenames == found:
            return False

        # Test if all possible token types are consumed in some rule
        tokens_to_consume = set(TOKEN)

        found = set(rule_iter(RULES,
            lambda x: [x.val] if type(x) == Tok else []
            ))
        if not tokens_to_consume == found:
            return False

    except Exception as e:
        print(e)
        return False
    
    return True


'''
    Give a tuple of the next symbol to parse + the resulting rest of rule matching that
'''
def expandRule(rule):
    options = []
    typ = type(rule)

    if typ == Tok:
        options += [(rule, [])]

    elif typ == str: # TODO abstract out this ruleset
        options += expandRule(RULES[rule])

    elif typ == Rule:
        options += expandRule(rule.val)

    elif typ == List:
        templist = rule.val

        if len(templist) == 1:
            options += expandRule(templist[0])
        else:
            head = templist[0]
            tail = templist[1:]


            res_list = expandRule(head)
            res_list = list(map(lambda x: (x[0], List(x[1] + tail)), res_list)) # Produce list of expanded first and tail
            options += res_list

    elif typ == Many:
        temp = rule.val

        res_list = expandRule(temp)
        res_list = list(map(lambda x: (x[0], List(x[1] + [rule])), res_list)) # Produce list of expanded content and unmodified many
        options += res_list
        options += (None, []) # Empty parse

    elif typ == Many1:
        temp = rule.val

        res_list = expandRule(temp)
        res_list = list(map(lambda x: (x[0], List(x[1] + [Many(temp)])), res_list)) # Produce list of expanded content and many instead of many1
        options += res_list

    elif typ == Choice:
        templist = rule.val

        reslist = [x for y in list(map(expandRule, templist)) for x in y] # Produce flattened list of expanded options
        options += reslist

    elif typ == Maybe:
        temp = rule.val

        res_list = expandRule(temp) # Non-empty parse
        options += res_list
        options += (None, []) # Empty parse
    else:
        print("ERROR",typ)

    #for i in options:
    #    print(i[0], i[1])
    return options


'''
Geen pseudo-stack nodig, de recursiediepte is niet geweldig hoog omdat alle many en many1 geen recursie veroorzaken.
Alleen sterk geneste expressies genereren recursiediepte
Staat om bij te houden:
Huidige positie in de regel
Al gevonden resultaten
Gekozen alternatieven

List-> index
Maybe-> yes/no
Choice-> alternative (index)

Eerste parse naar een naïve AST volgens zelfde structuur als de regels, zodat de prettyprint nog werkt.
Dan implementeren we een tree-transformer map naar de echte AST
'''
def parseTokenStream(instream, active_rules = [RULES["SPL"]]):
    # obtain expected symbol / rules
    # then pop one from instream, compare

    #print([str(k) for k in list(instream)])
    pass



if __name__ == "__main__":
    from argparse import ArgumentParser
    from lib.parser.lexer import tokenize
    argparser = ArgumentParser(description="SPL Parser")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()

    
    '''
    for rule, content in RULES.items():
        print("{}:".format(rule))
        print(content)
        print()
    
    exit()
    '''


    print(expandRule(RULES[ROOT_RULE]))
    print("DONE")
    exit()

    with open(args.infile, "r") as infile:
        tokenstream = tokenize(infile)
        parseTokenStream(tokenstream)
        '''
        tokenlist = list(tokenstream)
        import random
        randtoken = random.choice(tokenlist)
        print(randtoken)
        print(pointToPosition(infile, randtoken.pos))
        '''

    print("DONE")

