#!/usr/bin/env python3

from util import pointToPosition, Position, TOKEN, Token, Node
import parsec as ps

# Evaluate return types

# Need to be tested
@ps.generate
def PrefixOpDecl():
    yield ps.token(TOKEN.PREFIX)
    operator = yield ps.token(TOKEN.OP_IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    varname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_CLOSE)
    #yield ps.optional(ps.token())
    yield ps.token(TOKEN.CURL_OPEN)
    decls = yield ps.many(VarDecl)
    stmts = yield ps.many1(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return "PrefixOpDecl"

@ps.generate
def InfixOpDecl():
    side = yield (ps.token(TOKEN.INFIXL) | ps.token(TOKEN.INFIXR))
    fixity = yield ps.token(TOKEN.INT)
    operator = yield ps.token(TOKEN.OP_IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    a = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == ","))
    b = ps.token(TOKEN.IDENTIFIER)
    return ""

OpDecl = PrefixOpDecl | InfixOpDecl


# TYPES =====================================
BasicTypeChoice = ps.token(TOKEN.TYPE_IDENTIFIER, cond=(lambda x: x == "Int")) | ps.token(TOKEN.TYPE_IDENTIFIER, cond=(lambda x: x == "Bool")) | ps.token(TOKEN.TYPE_IDENTIFIER, cond=(lambda x: x == "Char"))

@ps.generate
def BasicType():
    a = yield BasicTypeChoice
    return "BasicType " + a.val

@ps.generate
def TupType():
    yield ps.token(TOKEN.PAR_OPEN)
    a = yield Type
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == ","))
    b = yield Type
    yield ps.token(TOKEN.PAR_CLOSE)
    return (a,b)


@ps.generate
def ListType():
    yield ps.token(TOKEN.BRACK_OPEN)
    a = yield Type
    yield ps.token(TOKEN.BRACK_CLOSE)
    return [a]

'''
@ps.generate
def Type():
    a = BasicType | TupType #| ListType | ps.token(TOKEN.TYPE_IDENTIFIER)
    return a
'''

# Choice is greedy: matching left doesn't result in trying right
Type = BasicType | TupType | ListType | ps.token(TOKEN.TYPE_IDENTIFIER)

@ps.generate
def TypeSyn():
    yield ps.token(TOKEN.TYPESYN)
    identifier = yield ps.token(TOKEN.TYPE_IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == '='))
    other_type = yield Type
    return (identifier, other_type)

RetType = ps.token(TOKEN.TYPE_IDENTIFIER, cond=(lambda x: x == "Void")) | Type

@ps.generate
def FunType():
    a = yield ps.optional(ps.many1(Type))
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == "->"))
    b = yield RetType
    return (a,b)

# EXPRESSIONS ===================================================
# Need to be tested

ActStmt = Ass | FunCall

# Kijk naar de "seperated" combinator
@ps.generate
def Exp():
    a = yield ConvExp
    b = yield many(ps.token(TOKEN.OP_IDENTIFIER) >> ConvExp)
    return (a,b)

@ps.generate
def ConvExp():
    return

@ps.generate
def FunCall();
    fname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    args = yield ps.optional(ActArgs)
    yield ps.token(TOKEN.PAR_CLOSE)

# Kijk naar de "seperated" combinator
@ps.generate
def ActArgs():
    a = yield Exp
    b = yield many(ps.token(TOKEN.OP_IDENTIFIER) >> ConvExp)
    return (a,b)

@ps.generate
def Ass():
    varname = yield ps.token(TOKEN.identifier)
    field = yield many(Field)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "="))
    expression = yield Exp
    return (varname, field, expression)





def parseTokenStream(instream):

    pass



if __name__ == "__main__":
    from argparse import ArgumentParser
    from lexer import tokenize
    argparser = ArgumentParser(description="SPL Parser")
    argparser.add_argument("infile", metavar="INPUT", help="Input file", nargs="?", default="./example programs/p1_example.spl")
    args = argparser.parse_args()
    

    test1 = [
        Token(None, TOKEN.TYPESYN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "String"),
        Token(None, TOKEN.OP_IDENTIFIER, "="),
        
    ]
    test2 = [
        Token(None, TOKEN.BRACK_OPEN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "Char"),
        Token(None, TOKEN.BRACK_CLOSE, None)
    ]
    test3 = [
        Token(None, TOKEN.TYPESYN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "String"),
        Token(None, TOKEN.OP_IDENTIFIER, "="),
        Token(None, TOKEN.BRACK_OPEN, None),
        Token(None, TOKEN.TYPE_IDENTIFIER, "Char"),
        Token(None, TOKEN.BRACK_CLOSE, None)
    ]
    #TypeSyn.parse(test3)
    import io
    testprog = io.StringIO('''
prefix !! (x){
    return x;
}
''')
    testprog = io.StringIO('''
Int -> Void
''')
    #print(list(tokenize(testprog)))
    FunType.parse(list(tokenize(testprog)))

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

