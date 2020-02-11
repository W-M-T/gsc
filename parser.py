#!/usr/bin/env python3

from util import pointToPosition, Position, TOKEN, Token, Node
import parsec as ps

# Evaluate return types

@ps.generate
def IdField():
    i = yield ps.token(TOKEN.IDENTIFIER)
    fields = yield ps.many(ps.token(TOKEN.ACCESSOR))
    return (i, fields)

# Need to be tested
@ps.generate
def PrefixOpDecl():
    yield ps.token(TOKEN.PREFIX)
    operator = yield ps.token(TOKEN.OP_IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    varname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_CLOSE)
    typesig = yield ps.times(PreFunTypeSig,0,1)
    yield ps.token(TOKEN.CURL_OPEN)
    #decls = yield ps.many(VarDecl)
    #stmts = yield ps.many1(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return (operator, varname, typesig)

@ps.generate
def Dumb_PrefixOpDecl():
    yield ps.token(TOKEN.PREFIX)
    operator = yield ps.token(TOKEN.OP_IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    varname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_CLOSE)
    typesig = yield ps.optional(PreFunTypeSig)
    yield ps.token(TOKEN.CURL_OPEN)
    #decls = yield ps.many(VarDecl)
    #stmts = yield ps.many1(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return (operator, varname, typesig)

@ps.generate
def InfixOpDecl():
    side = yield (ps.token(TOKEN.INFIXL) | ps.token(TOKEN.INFIXR))
    fixity = yield ps.token(TOKEN.INT)
    operator = yield ps.token(TOKEN.OP_IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    a = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == ","))
    b = ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_CLOSE)
    typesig = yield ps.times(InfFunTypeSig,0,1)
    yield ps.token(TOKEN.CURL_OPEN)
    #decls = yield ps.many(VarDecl)
    #stmts = yield ps.many1(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return ""

@ps.generate
def VarDecl():
    typ = yield (ps.token(TOKEN.VAR) | Type)
    varname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "="))
    expr = yield Exp
    yield ps.token(TOKEN.SEMICOLON)
    return (typ, varname, expr)

#@ps.generate
#def FunDecl():

OpDecl = PrefixOpDecl #| InfixOpDecl


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

@ps.generate
def PreFunType():
    a = yield Type
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == "->"))
    b = yield RetType
    return (a,b)

@ps.generate
def PreFunTypeSig():
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "::"))
    a = yield PreFunType
    return a

@ps.generate
def InfFunType():
    a = yield Type
    b = yield Type
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x : x == "->"))
    out = yield Type
    return ((a, b), out)

@ps.generate
def InfFunTypeSig():
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "::"))
    a = yield InfFunType
    return a

# CONTROL FLOW ==================================================
@ps.generate
def StmtIfElse():
    yield ps.token(TOKEN.IF)
    yield ps.token(TOKEN.PAR_OPEN)
    condition = yield Exp
    yield ps.token(TOKEN.PAR_CLOSE)
    yield ps.token(TOKEN.CURL_OPEN)
    if_contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    elifs = yield ps.many(StmtElif)
    elses = yield ps.times(StmtElse, 0,1)
    return (condition, if_contents, elifs, elses)

@ps.generate
def StmtElif():
    yield ps.token(TOKEN.ELIF)
    yield ps.token(TOKEN.PAR_OPEN)
    condition = yield Exp
    yield ps.token(TOKEN.PAR_CLOSE)
    yield ps.token(TOKEN.CURL_OPEN)
    contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return (condition, contents)

@ps.generate
def StmtElse():
    yield ps.token(TOKEN.ELSE)
    yield ps.token(TOKEN.CURL_OPEN)
    contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return contents

@ps.generate
def StmtWhile():
    yield ps.token(TOKEN.WHILE)
    yield ps.token(TOKEN.PAR_OPEN)
    expr = yield Exp
    yield ps.token(TOKEN.PAR_CLOSE)
    yield ps.token(TOKEN.CURL_OPEN)
    contents = yield ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return (expr, contents)

@ps.generate
def StmtFor():
    yield ps.token(TOKEN.FOR)
    yield ps.token(TOKEN.PAR_OPEN)
    initial = yield ps.times(ActStmt, 0,1)
    yield ps.token(TOKEN.SEMICOLON)
    condition = yield Exp
    yield ps.token(TOKEN.SEMICOLON)
    update = yield ActStmt
    yield ps.token(TOKEN.PAR_CLOSE)
    yield ps.token(TOKEN.CURL_OPEN)
    contents = ps.many(Stmt)
    yield ps.token(TOKEN.CURL_CLOSE)
    return (initial, condition, update, contents)

@ps.generate
def StmtActSem():
    a = yield ActStmt
    yield ps.token(TOKEN.SEMICOLON)
    return a

@ps.generate
def StmtRet():
    yield ps.token(TOKEN.RETURN)
    expr = yield ps.times(Exp, 0,1)
    yield ps.token(TOKEN.SEMICOLON)
    return expr


Stmt = StmtIfElse ^ StmtWhile ^ StmtFor ^ StmtActSem ^ StmtRet
# EXPRESSIONS ===================================================
# Need to be tested

@ps.generate
def Exp():
    a = yield ConvExp
    b = yield ps.many(ExpMore)
    return [a, *b]

@ps.generate
def ExpMore():
    op = yield ps.token(TOKEN.OP_IDENTIFIER)
    exp = yield ConvExp
    return (op, exp)

@ps.generate
def PrefixOpExp():
    op = yield ps.token(TOKEN.OP_IDENTIFIER)
    exp = yield Exp
    return (op, exp)

@ps.generate
def ExpLiteral():
    # Choice without backtrack fine here because they're all single tokens
    tok = yield ps.token(TOKEN.INT) | ps.token(TOKEN.CHAR) | ps.token(TOKEN.STRING) | ps.token(TOKEN.BOOL) | ps.token(TOKEN.EMPTY_LIST)
    return tok.val

@ps.generate
def ExpSub():
    yield ps.token(TOKEN.PAR_OPEN)
    subexp = yield Exp
    yield ps.token(TOKEN.PAR_CLOSE)
    return subexp

ConvExp = IdField ^ PrefixOpExp ^ ExpLiteral ^ ExpSub


# STATEMENTS ====================================================
@ps.generate
def FunCall():
    fname = yield ps.token(TOKEN.IDENTIFIER)
    yield ps.token(TOKEN.PAR_OPEN)
    args = yield ps.times(ActArgs, 0,1)
    yield ps.token(TOKEN.PAR_CLOSE)

# Kijk naar de "seperated" combinator
@ps.generate
def ActArgs():
    a = yield Exp
    b = yield ps.many(ps.token(TOKEN.OP_IDENTIFIER) >> ConvExp)
    return (a,b)

@ps.generate
def Ass():
    var = yield IdField
    yield ps.token(TOKEN.OP_IDENTIFIER, cond=(lambda x: x == "="))
    expression = yield Exp
    return (varname, field, expression)

ActStmt = Ass | FunCall






def parseTokenStream(instream):

    pass


prefixtest = '''

prefix *%* (a) :: { }
'''

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

    testprog = io.StringIO('''
a + + b - 2 * "heyo" - - False + (2*2) - []
''')

    testprog3 = io.StringIO('''
("heyo" + + False) - myvar.snd
''')
    #print(list(tokenize(testprog)))
    #Type.parse(test2)
    #Dumb_PrefixOpDecl.parse(list(tokenize(io.StringIO(prefixtest))))
    #print(list(tokenize(testprog)))
    Exp.parse_strict(list(tokenize(testprog3)))

    exit()

    '''
    with open(args.infile, "r") as infile:
        tokenstream = tokenize(infile)
        parseTokenStream(tokenstream)
        tokenlist = list(tokenstream)
        import random
        randtoken = random.choice(tokenlist)
        print(randtoken)
        print(pointToPosition(infile, randtoken.pos))
    '''

    print("DONE")

